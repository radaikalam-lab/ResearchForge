"""Deterministic computational simulation entities."""

from typing import Any

from pydantic import Field

from researchforge.domain.base import DomainModel


class SimulationMetadata(DomainModel):
    """Execution and provenance metadata for a simulation run."""

    model_name: str
    model_version: str
    parameter_set: dict[str, Any] = Field(default_factory=dict)
    software_version: str
    environment: dict[str, str] = Field(default_factory=dict)
    random_seed: int = 42
    input_hash: str
    output_hash: str
    execution_time_sec: float = 0.0
    resource_usage: dict[str, float] = Field(default_factory=dict)


class SimulationRun(DomainModel):
    """Specific invocation of a simulation model."""

    simulation_id: str
    metadata: SimulationMetadata
    raw_outputs: dict[str, Any] = Field(default_factory=dict)
    summary_metrics: dict[str, float] = Field(default_factory=dict)


class Simulation(DomainModel):
    """Domain specification for a computational or numerical simulation."""

    project_id: str
    name: str
    description: str
    engine_name: str
    base_parameters: dict[str, Any] = Field(default_factory=dict)
    run_ids: list[str] = Field(default_factory=list)
