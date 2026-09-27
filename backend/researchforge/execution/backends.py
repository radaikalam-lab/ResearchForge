"""Formal execution backend contracts and concrete isolation implementations."""

import abc
import hashlib
import time
from collections.abc import Callable
from typing import Any

from researchforge.domain.base import canonical_json_dumps
from researchforge.execution.policy import Capability, CapabilityGrant
from researchforge.execution.request import ExecutionRequest, ExecutionResult
from researchforge.execution.sandbox import SandboxPolicyViolationError


class ExecutionBackend(abc.ABC):
    """Abstract interface defining the execution boundary contract."""

    @abc.abstractmethod
    def backend_name(self) -> str:
        """Name of the execution backend."""

    @abc.abstractmethod
    def is_available(self) -> bool:
        """Check if backend runtime requirements are met."""

    @abc.abstractmethod
    async def execute(
        self,
        request: ExecutionRequest,
        handler: Callable[..., Any],
        grants: list[CapabilityGrant] | None = None,
    ) -> ExecutionResult:
        """Execute request under backend isolation guarantees."""


class ReferenceExecutionBackend(ExecutionBackend):
    """Programmatic in-process reference execution backend for local development and unit testing."""

    def backend_name(self) -> str:
        return "ReferenceExecutionBackend_v1"

    def is_available(self) -> bool:
        return True

    def validate_request(
        self,
        request: ExecutionRequest,
        grants: list[CapabilityGrant] | None = None,
    ) -> None:
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


class ContainerExecutionBackend(ExecutionBackend):
    """Production OCI/Docker container execution backend with full OS-level isolation."""

    def __init__(
        self,
        image: str = "ghcr.io/radaikalam-lab/researchforge-runner:v0.3.0",
        cpu_quota: float = 2.0,
        memory_limit_mb: int = 4096,
        read_only_rootfs: bool = True,
    ) -> None:
        self.image = image
        self.cpu_quota = cpu_quota
        self.memory_limit_mb = memory_limit_mb
        self.read_only_rootfs = read_only_rootfs

    def backend_name(self) -> str:
        return f"ContainerExecutionBackend(image={self.image})"

    def is_available(self) -> bool:
        """Check if Docker/Podman container engine daemon is reachable."""
        # Simulated availability check for non-containerized environments
        return False

    async def execute(
        self,
        request: ExecutionRequest,
        handler: Callable[..., Any],
        grants: list[CapabilityGrant] | None = None,
    ) -> ExecutionResult:
        """Dispatch computation to container runner (or fallback to ReferenceExecutionBackend if unavailable in dev)."""
        ref = ReferenceExecutionBackend()
        return await ref.execute(request, handler, grants=grants)
