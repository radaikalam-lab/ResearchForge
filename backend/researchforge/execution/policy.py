"""Execution policy, capability grants, and safety bounds (Section 23, 24)."""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field

from researchforge.domain.base import utc_now


class Capability(StrEnum):
    """Declared execution capability tokens."""

    COMPUTE_NUMERICAL = "COMPUTE_NUMERICAL"
    RUN_SIMULATION = "RUN_SIMULATION"
    EXECUTE_STATISTICS = "EXECUTE_STATISTICS"
    READ_DATASET = "READ_DATASET"
    WRITE_ARTIFACT = "WRITE_ARTIFACT"
    NETWORK_QUERY = "NETWORK_QUERY"
    NETWORK_FETCH_SCHOLARLY = "NETWORK_FETCH_SCHOLARLY"
    INVOKE_LLM = "INVOKE_LLM"
    ACCESS_LITERATURE_PROVIDER = "ACCESS_LITERATURE_PROVIDER"
    ACCESS_LLM_PROVIDER = "ACCESS_LLM_PROVIDER"
    ACCESS_COGNITIA = "ACCESS_COGNITIA"


class CapabilityGrant(BaseModel):
    """Explicit, auditable grant of a capability recorded in provenance."""

    grant_id: str
    capability: Capability
    granted_by: str  # Human researcher or authorized system policy
    granted_at: datetime = Field(default_factory=utc_now)
    expires_at: datetime | None = None
    provenance_event_id: str | None = None

    def is_active(self, current_time: datetime | None = None) -> bool:
        """Check if capability grant is unexpired."""
        now = current_time or utc_now()
        if self.expires_at and now > self.expires_at:
            return False
        return True


class ExecutionPolicy(BaseModel):
    """Guards defining what an execution request is allowed to do. Defaults: network=DENY, filesystem=READ_ONLY."""

    allowed_capabilities: set[Capability] = Field(default_factory=set)
    max_time_sec: int = 300
    max_memory_mb: int = 2048
    max_cpu_percent: float = 80.0
    max_processes: int = 1
    allow_network: bool = False  # Default DENY
    allow_filesystem_write: bool = False  # Default READ_ONLY
    allowed_write_directories: list[str] = Field(default_factory=lambda: ["./artifacts"])
    allowed_commands: list[str] = Field(default_factory=list)
    environment_allowlist: list[str] = Field(default_factory=lambda: ["PATH", "PYTHONPATH"])
    working_directory: str = "./artifacts/runs"
    risk_level: str = "LOW"  # LOW, MEDIUM, HIGH
    reversibility: str = "FULLY_REVERSIBLE"  # FULLY_REVERSIBLE, REVERSIBLE, IRREVERSIBLE
