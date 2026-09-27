"""Tests for sandbox execution policy enforcement and capability bounds (Section 13, 14, 16)."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from researchforge.execution.policy import Capability, CapabilityGrant, ExecutionPolicy
from researchforge.execution.request import ExecutionRequest
from researchforge.execution.sandbox import ExecutionSandbox, SandboxPolicyViolationError


@pytest.mark.asyncio
async def test_expired_capability_grant_is_rejected() -> None:
    """Proves that an expired capability grant is rejected by the sandbox."""
    sandbox = ExecutionSandbox()
    expired_grant = CapabilityGrant(
        grant_id="grant_expired",
        capability=Capability.RUN_SIMULATION,
        granted_by="admin",
        expires_at=datetime.now(UTC) - timedelta(hours=1),  # Expired in past
    )

    req = ExecutionRequest(
        request_id="req_expired_test",
        command_or_function="simulate_something",
        required_capabilities={Capability.RUN_SIMULATION},
        policy=ExecutionPolicy(allowed_capabilities=set()),
    )

    with pytest.raises(SandboxPolicyViolationError, match="lacks required capabilities"):
        await sandbox.execute(req, lambda: "ok", grants=[expired_grant])


@pytest.mark.asyncio
async def test_network_denial_policy_enforcement() -> None:
    """Proves that execution requiring network is blocked when policy denies network."""
    sandbox = ExecutionSandbox()
    req = ExecutionRequest(
        request_id="req_net_deny",
        command_or_function="fetch_remote_data",
        required_capabilities={Capability.NETWORK_QUERY},
        policy=ExecutionPolicy(allowed_capabilities={Capability.NETWORK_QUERY}, allow_network=False),
    )

    with pytest.raises(SandboxPolicyViolationError, match="policy has network=DENY"):
        await sandbox.execute(req, lambda: "network_result")


@pytest.mark.asyncio
async def test_filesystem_readonly_enforcement() -> None:
    """Proves that execution requiring filesystem writes is blocked under READ_ONLY policy."""
    sandbox = ExecutionSandbox()
    req = ExecutionRequest(
        request_id="req_fs_deny",
        command_or_function="write_local_file",
        required_capabilities={Capability.WRITE_ARTIFACT},
        policy=ExecutionPolicy(
            allowed_capabilities={Capability.WRITE_ARTIFACT},
            allow_filesystem_write=False,
        ),
    )

    with pytest.raises(SandboxPolicyViolationError, match="policy has filesystem=READ_ONLY"):
        await sandbox.execute(req, lambda: "file_written")


@pytest.mark.asyncio
async def test_failing_computational_run_records_failure() -> None:
    """Proves that a runtime error produces a FAILED ExecutionResult rather than crashing."""
    sandbox = ExecutionSandbox()
    req = ExecutionRequest(
        request_id="req_error_test",
        command_or_function="buggy_computation",
        required_capabilities={Capability.COMPUTE_NUMERICAL},
        policy=ExecutionPolicy(allowed_capabilities={Capability.COMPUTE_NUMERICAL}),
    )

    def _buggy_handler(**_kwargs: Any) -> None:
        raise ZeroDivisionError("Numerical singularity at X=0")

    result = await sandbox.execute(req, _buggy_handler)
    assert result.status == "FAILED"
    assert "ZeroDivisionError" in (result.error_message or "")
