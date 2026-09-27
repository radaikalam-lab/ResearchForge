"""Computation Plan, Execution Specification, Dataset Specification, and Analysis Specification models."""

from enum import StrEnum
from typing import Any

from pydantic import Field

from researchforge.domain.base import DomainModel


class ExecutionBackendType(StrEnum):
    """Supported computational execution environments."""

    LOCAL_SANDBOX = "LOCAL_SANDBOX"
    DOCKER_CONTAINER = "DOCKER_CONTAINER"
    PROCESS_ISOLATION = "PROCESS_ISOLATION"
    SIMULATION_ENGINE = "SIMULATION_ENGINE"


class DatasetSpecification(DomainModel):
    """Specification of expected input or generated output datasets."""

    name: str
    schema_format: str = "CSV"  # CSV, PARQUET, JSON, HDF5
    expected_columns: list[str] = Field(default_factory=list)
    storage_protocol: str = "LOCAL_FILESYSTEM"
    expected_rows: int | None = None
    checksum_algorithm: str = "SHA256"


class AnalysisSpecification(DomainModel):
    """Declarative specification for post-execution statistical analysis."""

    name: str
    analysis_type: str = "OLS_REGRESSION"  # OLS_REGRESSION, ANOVA, T_TEST, BAYESIAN_INFERENCE
    statistical_tests: list[str] = Field(default_factory=lambda: ["OLS", "P_VALUE"])
    alpha_threshold: float = Field(default=0.05, gt=0.0, lt=1.0)
    power_target: float = Field(default=0.80, gt=0.0, lt=1.0)
    target_variables: list[str] = Field(default_factory=list)
    covariates: list[str] = Field(default_factory=list)


class StatisticalAnalysis(DomainModel):
    """Concrete statistical evaluation executed against dataset outputs."""

    analysis_spec_id: str
    dataset_spec_id: str = ""
    dataset_uri: str = ""
    test_results: dict[str, Any] = Field(default_factory=dict)
    p_values: dict[str, float] = Field(default_factory=dict)
    effect_sizes: dict[str, float] = Field(default_factory=dict)
    confidence_intervals: dict[str, list[float]] = Field(default_factory=dict)
    falsification_verdict: str = "PENDING"  # SUPPORTED, FALSIFIED, INCONCLUSIVE
    summary: str = ""


class ExecutionSpecification(DomainModel):
    """Hermetic runtime environment and resource specification for execution."""

    backend_type: ExecutionBackendType = ExecutionBackendType.LOCAL_SANDBOX
    environment_requirements: dict[str, str] = Field(default_factory=dict)
    resource_limits: dict[str, Any] = Field(
        default_factory=lambda: {
            "max_memory_mb": 2048,
            "max_cpu_cores": 2,
            "max_wallclock_seconds": 300,
        }
    )
    timeout_seconds: int = Field(default=300, ge=1)
    reproducibility_seed: int = 42
    entrypoint_command: str = ""
    network_isolated: bool = True
    deterministic_required: bool = True


class ComputationPlan(DomainModel):
    """Aggregate plan encapsulating execution environment, dataset schemas, and analysis protocols."""

    name: str
    description: str = ""
    execution_spec: ExecutionSpecification = Field(default_factory=lambda: ExecutionSpecification(id="exec_default"))
    dataset_specs: list[DatasetSpecification] = Field(default_factory=list)
    analysis_specs: list[AnalysisSpecification] = Field(default_factory=list)
    deterministic_execution_required: bool = True
    metadata: dict[str, Any] = Field(default_factory=dict)
