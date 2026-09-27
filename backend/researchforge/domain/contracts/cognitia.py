"""Cognitia Epistemic Plane adapter protocol contract."""

from typing import Any, Protocol, runtime_checkable

from pydantic import Field

from researchforge.domain.base import DomainModel
from researchforge.domain.models.epistemic import EpistemicAssessment
from researchforge.domain.models.evidence import Claim, ScientificModel
from researchforge.domain.models.experiment import ExperimentResult
from researchforge.domain.models.falsification import FalsificationEvaluation
from researchforge.domain.models.hypothesis import Assumption, Hypothesis
from researchforge.domain.value_objects.directional import CandidatePath, DirectionalSpecification


class CognitiaSemanticContext(DomainModel):
    """Bounded semantic graph context extracted for Cognitia advisory reasoning."""

    project_id: str
    context_graph_hash: str
    subgraph: dict[str, Any]
    semantic_contract_version: str = "0.4.0"
    provenance_references: list[str] = Field(default_factory=list)


class CognitiaAdvisoryRequest(DomainModel):
    """Formal advisory request payload sent to Cognitia reasoning plane."""

    request_id: str
    project_id: str
    operation_type: str
    context_graph_hash: str
    semantic_contract_version: str = "0.4.0"
    semantic_context: CognitiaSemanticContext
    provenance_references: list[str] = Field(default_factory=list)
    constraints: dict[str, Any] = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=list)


class CognitiaAdvisoryResult(DomainModel):
    """Advisory-only result emitted by Cognitia reasoning plane."""

    result_id: str
    request_id: str
    context_graph_hash: str
    recommendations: list[str] = Field(default_factory=list)
    criticisms: list[str] = Field(default_factory=list)
    candidate_hypotheses: list[str] = Field(default_factory=list)
    candidate_relationships: list[dict[str, Any]] = Field(default_factory=list)
    uncertainty: float = 0.0
    provenance: dict[str, Any] = Field(default_factory=dict)
    model_metadata: dict[str, Any] = Field(default_factory=dict)
    advisory_status: str = "ADVISORY"


@runtime_checkable
class CognitiaProvider(Protocol):
    """Contract for Cognitia Epistemic Plane integration."""

    provider_name: str

    async def evaluate_claim(self, claim: Claim) -> EpistemicAssessment:
        """Critique and assess the epistemic rigor of a scientific claim."""
        ...

    async def evaluate_hypothesis(self, hypothesis: Hypothesis) -> EpistemicAssessment:
        """Critique hypothesis falsifiability, coherence, and testability."""
        ...

    async def identify_assumptions(self, hypothesis: Hypothesis) -> list[Assumption]:
        """Decompose and uncover hidden domain and mechanistic assumptions."""
        ...

    async def compare_models(self, models: list[ScientificModel]) -> dict[str, Any]:
        """Perform epistemic model comparison across predictive scope and complexity."""
        ...

    async def evaluate_representation(self, representation_spec: dict[str, Any]) -> dict[str, Any]:
        """Evaluate mathematical or conceptual representation adequacy."""
        ...

    async def generate_candidate_paths(self, spec: DirectionalSpecification) -> list[CandidatePath]:
        """Generate non-authoritative candidate exploratory paths."""
        ...

    async def evaluate_falsification(
        self, hypothesis: Hypothesis, results: list[ExperimentResult]
    ) -> FalsificationEvaluation:
        """Perform formal Popperian falsification assessment against experimental data."""
        ...

    async def track_theory_transition(
        self, prior_theory: str, proposed_theory: str, anomalies: list[str]
    ) -> dict[str, Any]:
        """Analyze conceptual continuity and Kuhn/Lakatos theory transitions."""
        ...

    async def consult_advisory(self, request: CognitiaAdvisoryRequest) -> CognitiaAdvisoryResult:
        """Provide non-authoritative advisory analysis over a bounded semantic graph context."""
        ...
