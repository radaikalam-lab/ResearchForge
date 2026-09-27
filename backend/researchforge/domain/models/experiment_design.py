"""Experiment Design and Experiment Specification aggregate models."""

from typing import Any

from pydantic import Field

from researchforge.domain.base import DomainModel
from researchforge.domain.models.computation_plan import ComputationPlan
from researchforge.domain.models.parameter_space import ParameterSpace


class ExperimentSpecification(DomainModel):
    """Immutable specification fingerprint linking parameter space and computation plan."""

    design_id: str
    version: int = 1
    parameter_space_id: str
    computation_plan_id: str
    execution_spec_id: str
    falsification_criteria_ids: list[str] = Field(default_factory=list)


class ExperimentDesign(DomainModel):
    """First-class semantic experiment design connecting hypothesis, parameter space, and computation plan."""

    project_id: str
    hypothesis_id: str
    name: str
    description: str = ""
    parameter_space: ParameterSpace = Field(
        default_factory=lambda: ParameterSpace(id="ps_default", name="Default Space")
    )
    computation_plan: ComputationPlan = Field(
        default_factory=lambda: ComputationPlan(id="cp_default", name="Default Plan")
    )
    falsification_criteria_refs: list[str] = Field(default_factory=list)
    version: int = 1
    metadata: dict[str, Any] = Field(default_factory=dict)
