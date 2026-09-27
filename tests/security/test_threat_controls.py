"""Security threat control validation tests (SEC-01 through SEC-05)."""

import pytest
from researchforge.execution.policy import Capability, CapabilityGrant, ExecutionPolicy
from researchforge.execution.request import ExecutionRequest
from researchforge.execution.sandbox import ExecutionSandbox, SandboxPolicyViolationError


@pytest.mark.asyncio
async def test_sec_01_network_denial_enforcement() -> None:
    """SEC-01: Execution requests requiring network are denied when allow_network=False."""
    sandbox = ExecutionSandbox()
    policy = ExecutionPolicy(
        allowed_capabilities={Capability.NETWORK_QUERY},
        allow_network=False,  # Explicit DENY
    )
    req = ExecutionRequest(
        request_id="req_sec_01",
        command_or_function="fetch_remote_dataset",
        required_capabilities={Capability.NETWORK_QUERY},
        policy=policy,
    )

    with pytest.raises(SandboxPolicyViolationError):
        await sandbox.execute(req, lambda: "net_data")


@pytest.mark.asyncio
async def test_sec_02_capability_grant_enforcement() -> None:
    """SEC-02: Capabilities not granted in policy or grants list cause execution rejection."""
    sandbox = ExecutionSandbox()
    policy = ExecutionPolicy(allowed_capabilities=set())

    req = ExecutionRequest(
        request_id="req_sec_02",
        command_or_function="run_finite_element",
        required_capabilities={Capability.RUN_SIMULATION},
        policy=policy,
    )

    # Denied without grant
    with pytest.raises(SandboxPolicyViolationError):
        await sandbox.execute(req, lambda: "sim_result")

    # Allowed with explicit grant
    grant = CapabilityGrant(
        grant_id="grant_01",
        capability=Capability.RUN_SIMULATION,
        granted_by="admin_researcher",
    )
    res = await sandbox.execute(req, lambda: "sim_result", grants=[grant])
    assert res.status == "COMPLETED"
    assert res.output == "sim_result"
