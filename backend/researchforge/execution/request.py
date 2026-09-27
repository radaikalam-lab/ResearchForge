"""Execution request and response containers."""

import hashlib
from typing import Any

from pydantic import BaseModel, Field

from researchforge.domain.base import canonical_json_dumps
from researchforge.execution.policy import Capability, ExecutionPolicy


class ExecutionRequest(BaseModel):
    """Specification of an isolated execution job."""

    request_id: str
    command_or_function: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    required_capabilities: set[Capability] = Field(default_factory=set)
    policy: ExecutionPolicy
    random_seed: int = 42

    def request_hash(self) -> str:
        """Deterministic hash of the execution specification."""
        data = self.model_dump(mode="json")
        canonical = canonical_json_dumps(data)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class ExecutionResult(BaseModel):
    """Output and status from sandbox execution."""

    request_id: str
    status: str = "COMPLETED"  # COMPLETED, FAILED, TIMED_OUT, POLICY_VIOLATION
    output: Any = None
    output_hash: str = ""
    execution_time_sec: float = 0.0
    error_message: str | None = None
    logs: list[str] = Field(default_factory=list)
