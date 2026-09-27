"""Experiment models, execution plans, and result containers."""

from enum import StrEnum
from typing import Any

from pydantic import Field

from researchforge.domain.base import DomainModel
from researchforge.domain.value_objects.uncertainty import UncertaintyProfile


class ExperimentType(StrEnum):
    """Categorization of experiment execution types."""

    SIMULATION = "SIMULATION"
    NUMERICAL_EXPERIMENT = "NUMERICAL_EXPERIMENT"
    STATISTICAL_EXPERIMENT = "STATISTICAL_EXPERIMENT"
    DATASET_EXPERIMENT = "DATASET_EXPERIMENT"
    PHYSICAL_EXPERIMENT_PLACEHOLDER = "PHYSICAL_EXPERIMENT_PLACEHOLDER"
    EXTERNAL_LABORATORY = "EXTERNAL_LABORATORY"


class ExperimentPlan(DomainModel):
    """Declarative specification for executing an experiment."""

    hypothesis_id: str
    experiment_type: ExperimentType
    protocol_description: str
    independent_variable_values: dict[str, Any] = Field(default_factory=dict)
    control_variables: dict[str, Any] = Field(default_factory=dict)
    sample_size: int = Field(default=100, ge=1)
    random_seed: int = 42
    compute_budget_sec: int = 300


class ExperimentResult(DomainModel):
    """Deterministic output and metrics collected from an experiment run."""

    run_id: str
    raw_data_uri: str | None = None
    metrics: dict[str, float] = Field(default_factory=dict)
    output_hash: str
    uncertainty: UncertaintyProfile = Field(default_factory=UncertaintyProfile)
    logs: list[str] = Field(default_factory=list)


class ExperimentRun(DomainModel):
    """Individual execution instance of an experiment plan."""

    experiment_plan_id: str = ""
    experiment_id: str = ""
    project_id: str = "default"
    status: str = "PENDING"  # PENDING, RUNNING, COMPLETED, FAILED, CANCELLED
    random_seed_used: int = 42
    random_seed: int = 42
    parameter_hash: str = ""
    input_hash: str = ""
    environment_snapshot: dict[str, str] = Field(default_factory=dict)
    environment_metadata: dict[str, Any] = Field(default_factory=dict)
    execution_policy_ref: str | None = None
    capability_grant_ref: str | None = None
    execution_time_sec: float = 0.0
    output_hash: str = ""
    result: ExperimentResult | None = None
    results: dict[str, Any] = Field(default_factory=dict)
    error_message: str | None = None


class Experiment(DomainModel):
    """Composite domain entity representing an experimental inquiry."""

    project_id: str
    hypothesis_id: str
    name: str
    description: str = ""
    experiment_type: ExperimentType = ExperimentType.NUMERICAL_EXPERIMENT
    plan: ExperimentPlan | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    run_ids: list[str] = Field(default_factory=list)
