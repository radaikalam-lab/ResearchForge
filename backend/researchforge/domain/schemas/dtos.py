"""Canonical request and response DTOs for all provider boundaries."""

from typing import Any

from pydantic import BaseModel, Field

from researchforge.domain.models.artifact import Manuscript
from researchforge.domain.models.evidence import Claim, Evidence, EvidenceFragment, ScientificModel
from researchforge.domain.models.experiment import ExperimentPlan, ExperimentResult, ExperimentRun
from researchforge.domain.models.gap import GapCandidate
from researchforge.domain.models.hypothesis import Hypothesis
from researchforge.domain.models.literature import Citation, Paper, Source
from researchforge.domain.models.simulation import Simulation, SimulationMetadata, SimulationRun
from researchforge.domain.value_objects.directional import DirectionalSpecification


# ------------------------------------------------------------------------------
# 1. Literature Provider DTOs
# ------------------------------------------------------------------------------
class LiteratureSearchRequest(BaseModel):
    query: str
    limit: int = 10
    year_start: int | None = None
    year_end: int | None = None
    request_id: str | None = None


class LiteratureSearchResponse(BaseModel):
    sources: list[Source] = Field(default_factory=list)
    total_found: int = 0
    provider_name: str = ""
    query_hash: str = ""


class LiteratureFetchRequest(BaseModel):
    record_id: str


class LiteratureCitationRequest(BaseModel):
    paper_id: str


class LiteratureRelatedRequest(BaseModel):
    paper_id: str
    limit: int = 5


# ------------------------------------------------------------------------------
# 2. Citation Provider DTOs
# ------------------------------------------------------------------------------
class DoiResolveRequest(BaseModel):
    doi: str


class BibtexFormatRequest(BaseModel):
    paper: Paper


class CitationGraphValidationRequest(BaseModel):
    citations: list[Citation]


# ------------------------------------------------------------------------------
# 3. Evidence Provider DTOs
# ------------------------------------------------------------------------------
class EvidenceExtractRequest(BaseModel):
    source: Source


class EvidenceExtractResponse(BaseModel):
    fragments: list[EvidenceFragment] = Field(default_factory=list)


class EvidenceValidateRequest(BaseModel):
    fragment: EvidenceFragment
    source: Source


class EvidenceSynthesizeRequest(BaseModel):
    fragments: list[EvidenceFragment]
    claim: Claim


# ------------------------------------------------------------------------------
# 4. Retrieval Provider DTOs
# ------------------------------------------------------------------------------
class IndexRequest(BaseModel):
    fragments: list[EvidenceFragment]


class SemanticSearchRequest(BaseModel):
    query: str
    top_k: int = 5


class EvidenceSearchRequest(BaseModel):
    exact_pattern: str
    top_k: int = 5


class RetrievalResponse(BaseModel):
    fragments: list[EvidenceFragment] = Field(default_factory=list)
    retrieval_mode: str = "SEMANTIC"


# ------------------------------------------------------------------------------
# 5. Reasoning Provider DTOs
# ------------------------------------------------------------------------------
class ReasoningProposeRequest(BaseModel):
    prompt: str
    context_refs: list[str] = Field(default_factory=list)


class ReasoningCritiqueRequest(BaseModel):
    hypothesis: Hypothesis
    evidence: list[EvidenceFragment] = Field(default_factory=list)


class ReasoningExtractRequest(BaseModel):
    raw_text: str
    target_schema_name: str


class ReasoningSynthesizeRequest(BaseModel):
    claims: list[Claim]


# ------------------------------------------------------------------------------
# 6. Cognitia Provider DTOs
# ------------------------------------------------------------------------------
class CognitiaEvaluateClaimRequest(BaseModel):
    claim: Claim


class CognitiaEvaluateHypothesisRequest(BaseModel):
    hypothesis: Hypothesis


class CognitiaIdentifyAssumptionsRequest(BaseModel):
    hypothesis: Hypothesis


class CognitiaCompareModelsRequest(BaseModel):
    models: list[ScientificModel]


class CognitiaEvaluateRepresentationRequest(BaseModel):
    representation_spec: dict[str, Any]


class CognitiaCandidatePathsRequest(BaseModel):
    directional_spec: DirectionalSpecification


class CognitiaEvaluateFalsificationRequest(BaseModel):
    hypothesis: Hypothesis
    results: list[ExperimentResult]


class CognitiaTheoryTransitionRequest(BaseModel):
    prior_theory: str
    proposed_theory: str
    anomalies: list[str] = Field(default_factory=list)


# ------------------------------------------------------------------------------
# 7. Experiment Provider DTOs
# ------------------------------------------------------------------------------
class ExperimentDesignRequest(BaseModel):
    hypothesis: Hypothesis


class ExperimentValidateRequest(BaseModel):
    plan: ExperimentPlan


class ExperimentExecuteRequest(BaseModel):
    plan: ExperimentPlan


class ExperimentCollectRequest(BaseModel):
    run: ExperimentRun


# ------------------------------------------------------------------------------
# 8. Simulation Provider DTOs
# ------------------------------------------------------------------------------
class SimulationPrepareRequest(BaseModel):
    simulation: Simulation
    parameters: dict[str, Any] = Field(default_factory=dict)
    seed: int = 42


class SimulationValidateRequest(BaseModel):
    metadata: SimulationMetadata


class SimulationRunRequest(BaseModel):
    metadata: SimulationMetadata


class SimulationCollectRequest(BaseModel):
    run: SimulationRun


# ------------------------------------------------------------------------------
# 9. Statistics Provider DTOs
# ------------------------------------------------------------------------------
class DescriptiveStatsRequest(BaseModel):
    data: list[float]


class HypothesisTestRequest(BaseModel):
    sample_a: list[float]
    sample_b: list[float] | None = None
    test_type: str = "t_test"
    alpha: float = 0.05


class EffectSizeRequest(BaseModel):
    sample_a: list[float]
    sample_b: list[float]
    metric: str = "cohens_d"


class UncertaintyPropagationRequest(BaseModel):
    variables: dict[str, tuple[float, float]]
    formula: str


class FullAnalysisRequest(BaseModel):
    project_id: str
    datasets: dict[str, list[float]]


# ------------------------------------------------------------------------------
# 10. Publication Provider DTOs
# ------------------------------------------------------------------------------
class ManuscriptRenderRequest(BaseModel):
    manuscript: Manuscript
    format_type: str = "MARKDOWN"


class ReproducibilityBundleRequest(BaseModel):
    project_id: str
    artifact_ids: list[str]


class TraceabilityVerifyRequest(BaseModel):
    manuscript: Manuscript


# ------------------------------------------------------------------------------
# 11. Gap Analysis Provider DTOs
# ------------------------------------------------------------------------------
class GapAnalyzeRequest(BaseModel):
    evidence_items: list[Evidence]


class GapValidateRequest(BaseModel):
    candidate: GapCandidate
    evidence_items: list[Evidence]


# ------------------------------------------------------------------------------
# 12. Reproducibility Bundle Schema (Section 20)
# ------------------------------------------------------------------------------
class ReproducibilityBundle(BaseModel):
    """Complete computational reproducibility descriptor package."""

    project_id: str
    source_hashes: list[str] = Field(default_factory=list)
    dataset_hashes: list[str] = Field(default_factory=list)
    parameter_hashes: list[str] = Field(default_factory=list)
    random_seeds: list[int] = Field(default_factory=list)
    code_commit_hash: str | None = None
    dependency_lock_hash: str | None = None
    python_version: str = "3.13"
    os_descriptor: str = "windows"
    hardware_descriptor: dict[str, str] = Field(default_factory=dict)
    # Level: BITWISE_REPRODUCIBLE, NUMERICALLY_REPRODUCIBLE, SCIENTIFICALLY_REPRODUCIBLE
    reproducibility_level: str = "NUMERICALLY_REPRODUCIBLE"
    artifact_dependency_dag: dict[str, list[str]] = Field(default_factory=dict)
    provenance_ledger_hash: str = ""
