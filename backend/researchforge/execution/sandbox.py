"""Execution sandbox enforcing policies and capability grants prior to computational execution."""

import hashlib
import time
from collections.abc import Callable
from typing import Any

from researchforge.domain.base import canonical_json_dumps
from researchforge.execution.policy import Capability, CapabilityGrant, ExecutionPolicy
from researchforge.execution.request import ExecutionRequest, ExecutionResult


class SandboxPolicyViolationError(Exception):
    """Raised when an execution request exceeds or violates its policy."""


class ExecutionSandbox:
    """Execution container with policy and capability verification."""

    def __init__(self, default_policy: ExecutionPolicy | None = None) -> None:
        self.default_policy = default_policy or ExecutionPolicy(
            allowed_capabilities={
                Capability.COMPUTE_NUMERICAL,
                Capability.RUN_SIMULATION,
                Capability.WRITE_ARTIFACT,
            }
        )

    def validate_request(
        self,
        request: ExecutionRequest,
        grants: list[CapabilityGrant] | None = None,
    ) -> None:
        """Verify that request capabilities match granted policy permissions."""
        effective_capabilities = set(request.policy.allowed_capabilities)
        if grants:
            for g in grants:
                if g.is_active():
                    effective_capabilities.add(g.capability)

        missing = request.required_capabilities - effective_capabilities
        if missing:
            missing_str = ", ".join(c.value for c in missing)
            raise SandboxPolicyViolationError(
                f"Execution request '{request.request_id}' lacks required capabilities: {missing_str}."
            )

        if not request.policy.allow_network and any(
            c in request.required_capabilities for c in {Capability.NETWORK_QUERY, Capability.NETWORK_FETCH_SCHOLARLY}
        ):
            raise SandboxPolicyViolationError(
                f"Execution request '{request.request_id}' requires network access but policy has network=DENY."
            )

        if Capability.WRITE_ARTIFACT in request.required_capabilities and not request.policy.allow_filesystem_write:
            raise SandboxPolicyViolationError(
                f"Execution request '{request.request_id}' requires filesystem write "
                "but policy has filesystem=READ_ONLY."
            )

    async def execute(
        self,
        request: ExecutionRequest,
        handler: Callable[..., Any],
        grants: list[CapabilityGrant] | None = None,
    ) -> ExecutionResult:
        """Run execution within validated boundaries."""
        self.validate_request(request, grants=grants)
        start_time = time.perf_counter()
        try:
            output = handler(**request.arguments)
            elapsed = time.perf_counter() - start_time
            if elapsed > request.policy.max_time_sec:
                raise SandboxPolicyViolationError(
                    f"Execution exceeded timeout of {request.policy.max_time_sec}s (ran for {elapsed:.2f}s)."
                )
            out_canonical = canonical_json_dumps(output)
            out_hash = hashlib.sha256(out_canonical.encode("utf-8")).hexdigest()
            return ExecutionResult(
                request_id=request.request_id,
                status="COMPLETED",
                output=output,
                output_hash=out_hash,
                execution_time_sec=elapsed,
            )
        except Exception as e:
            elapsed = time.perf_counter() - start_time
            return ExecutionResult(
                request_id=request.request_id,
                status="FAILED",
                error_message=f"{type(e).__name__}: {e}",
                execution_time_sec=elapsed,
            )
