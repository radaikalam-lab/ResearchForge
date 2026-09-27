"""Falsification engine models and evaluation states."""

from enum import StrEnum

from pydantic import Field

from researchforge.domain.base import DomainModel
from researchforge.domain.value_objects.uncertainty import UncertaintyProfile


class FalsificationStatus(StrEnum):
    """Evidence status of a hypothesis under Popperian falsification evaluation."""

    SUPPORTED = "SUPPORTED"
    WEAKENED = "WEAKENED"
    CONTRADICTED = "CONTRADICTED"
    INCONCLUSIVE = "INCONCLUSIVE"
    UNTESTED = "UNTESTED"


class FalsificationEvaluation(DomainModel):
    """Evaluation output from testing a hypothesis against experimental data."""

    project_id: str = "default"
    hypothesis_id: str
    status: FalsificationStatus = FalsificationStatus.UNTESTED
    reason: str = Field(default="", description="Detailed mechanistic and statistical justification")
    reasoning: str = ""
    evidence_refs: list[str] = Field(
        default_factory=list,
        description="References to experiment results or evidence fragments supporting this status",
    )
    evidence_ids: list[str] = Field(default_factory=list)
    analysis_ids: list[str] = Field(default_factory=list)
    evaluated_criteria_ids: list[str] = Field(default_factory=list)
    failed_criteria_ids: list[str] = Field(default_factory=list)
    alternative_explanations: list[str] = Field(default_factory=list)
    uncertainty: UncertaintyProfile = Field(default_factory=UncertaintyProfile)
