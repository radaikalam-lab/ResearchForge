"""Research gap analysis entities."""

from enum import StrEnum

from pydantic import Field

from researchforge.domain.base import DomainModel


class GapType(StrEnum):
    """Taxonomy of scientific research gaps."""

    PARAMETER_GAP = "PARAMETER_GAP"
    BOUNDARY_CONDITION_GAP = "BOUNDARY_CONDITION_GAP"
    METHOD_GAP = "METHOD_GAP"
    DATA_GAP = "DATA_GAP"
    POPULATION_GAP = "POPULATION_GAP"
    TEMPORAL_GAP = "TEMPORAL_GAP"
    CONTRADICTION_GAP = "CONTRADICTION_GAP"
    REPRODUCIBILITY_GAP = "REPRODUCIBILITY_GAP"
    CONTRADICTION = "contradiction"
    MISSING_VARIABLE = "missing-variable"
    METHODOLOGICAL_GAP = "methodological-gap"
    DATASET_GAP = "dataset-gap"
    REPLICATION_GAP = "replication-gap"
    MODEL_COMPARISON_GAP = "model-comparison-gap"
    SCALE_GAP = "scale-gap"
    MEASUREMENT_GAP = "measurement-gap"
    THEORETICAL_GAP = "theoretical-gap"


class GapCandidate(DomainModel):
    """Candidate gap proposition prior to formal verification."""

    description: str
    gap_type: GapType = GapType.BOUNDARY_CONDITION_GAP
    supporting_source_ids: list[str] = Field(default_factory=list)
    contradictory_source_ids: list[str] = Field(default_factory=list)
    supporting_claim_ids: list[str] = Field(default_factory=list)
    affected_variables: list[str] = Field(default_factory=list)
    unexplored_region: str = Field(description="Description of the unexplored parameter or conceptual space")
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    unresolved_questions: list[str] = Field(default_factory=list)


class ResearchGap(DomainModel):
    """Validated scientific research gap backed by concrete evidence."""

    project_id: str
    title: str = ""
    description: str
    gap_type: GapType = GapType.BOUNDARY_CONDITION_GAP
    supporting_evidence_ids: list[str] = Field(
        min_length=1,
        description="Every valid gap must have at least one supporting evidence reference",
    )
    contradictory_evidence_ids: list[str] = Field(default_factory=list)
    supporting_claim_ids: list[str] = Field(default_factory=list)
    contradiction_ids: list[str] = Field(default_factory=list)
    affected_variables: list[str] = Field(default_factory=list)
    affected_variable_ids: list[str] = Field(default_factory=list)
    unexplored_region: str = ""
    confidence: float = Field(default=0.8, ge=0.0, le=1.0)
    impact_score: float = Field(default=0.8, ge=0.0, le=1.0)
