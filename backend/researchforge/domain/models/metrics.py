"""Research compression and process efficiency metrics."""

from pydantic import Field

from researchforge.domain.base import DomainModel


class ResearchEffortEstimate(DomainModel):
    """Estimate of traditional manual research effort for benchmark comparison."""

    estimated_manual_hours: float
    literature_review_hours: float
    experiment_setup_hours: float
    statistical_analysis_hours: float
    manuscript_drafting_hours: float


class ResearchCompressionMetrics(DomainModel):
    """Auditable metrics measuring the computational efficiency of the research cycle."""

    project_id: str
    papers_screened: int = 0
    papers_manually_inspected: int = 0
    automated_screening_ratio: float = Field(default=0.0, ge=0.0, le=1.0)
    hypotheses_generated: int = 0
    hypotheses_eliminated: int = 0
    experiments_simulated: int = 0
    physical_experiments_avoided: int = 0
    human_intervention_points: int = 0
    computation_time_seconds: float = 0.0
    research_iteration_count: int = 1
    evidence_coverage: float = Field(default=1.0, ge=0.0, le=1.0)
    provenance_coverage: float = Field(default=1.0, ge=0.0, le=1.0)
    reproducibility_score: float = Field(default=1.0, ge=0.0, le=1.0)
