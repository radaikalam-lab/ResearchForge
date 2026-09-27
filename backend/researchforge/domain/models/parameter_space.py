"""Parameter Space models, parameter definitions, constraints, and sampling strategies."""

from enum import StrEnum
from typing import Any

from pydantic import Field

from researchforge.domain.base import DomainModel


class ParameterType(StrEnum):
    """Data types for experiment parameters."""

    CONTINUOUS = "CONTINUOUS"
    DISCRETE = "DISCRETE"
    CATEGORICAL = "CATEGORICAL"
    ORDINAL = "ORDINAL"
    BOOLEAN = "BOOLEAN"


class SamplingStrategy(StrEnum):
    """Strategies for parameter exploration and discretization."""

    GRID = "GRID"
    RANDOM_UNIFORM = "RANDOM_UNIFORM"
    LATIN_HYPERCUBE = "LATIN_HYPERCUBE"
    SOBOL = "SOBOL"
    MANUAL_LIST = "MANUAL_LIST"


class ParameterConstraint(DomainModel):
    """Logical or algebraic constraint binding one or more parameters."""

    id: str = Field(default="", description="Constraint ID")
    name: str
    expression: str
    description: str = ""
    parameters_involved: list[str] = Field(default_factory=list)


class ParameterDefinition(DomainModel):
    """Formal definition of a single experimental parameter."""

    id: str = Field(default="", description="Parameter ID")
    parameter_name: str
    parameter_type: ParameterType = ParameterType.CONTINUOUS
    unit: str = ""
    min_value: float | None = None
    max_value: float | None = None
    default_value: Any = None
    allowed_values: list[Any] = Field(default_factory=list)
    discretization_step: float | None = None
    distribution: str | None = None
    dependencies: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)


class ParameterSpace(DomainModel):
    """Aggregate representing the multi-dimensional parameter exploration space."""

    id: str = Field(default="", description="Parameter Space ID")
    name: str
    description: str = ""
    parameters: dict[str, ParameterDefinition] = Field(default_factory=dict)
    constraints: list[ParameterConstraint] = Field(default_factory=list)
    sampling_strategy: SamplingStrategy = SamplingStrategy.GRID
    sample_count: int = Field(default=10, ge=1)
    metadata: dict[str, Any] = Field(default_factory=dict)
