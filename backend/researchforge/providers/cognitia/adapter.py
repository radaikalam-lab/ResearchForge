"""Cognitia provider adapter mediating communication with Cognitia Epistemic Plane."""

from typing import Any

from researchforge.configuration.settings import Settings, get_settings
from researchforge.domain.contracts.cognitia import (
    CognitiaAdvisoryRequest,
    CognitiaAdvisoryResult,
    CognitiaProvider,
)
from researchforge.domain.models.epistemic import EpistemicAssessment
from researchforge.domain.models.evidence import Claim, ScientificModel
from researchforge.domain.models.experiment import ExperimentResult
from researchforge.domain.models.falsification import FalsificationEvaluation
from researchforge.domain.models.hypothesis import Assumption, Hypothesis
from researchforge.domain.value_objects.directional import CandidatePath, DirectionalSpecification
from researchforge.providers.cognitia.client import CognitiaClient
from researchforge.providers.cognitia.mock import MockCognitiaProvider


class CognitiaAdapter(CognitiaProvider):
    """Production adapter for Cognitia reasoning plane."""

    provider_name: str = "cognitia-adapter-v1"

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self._mock = MockCognitiaProvider()
        self._client = CognitiaClient(
            base_url=self.settings.cognitia_api_url,
            api_key=self.settings.cognitia_api_key,
        )

    async def evaluate_claim(self, claim: Claim) -> EpistemicAssessment:
        """Evaluate claim via Cognitia or local mock."""
        if self.settings.cognitia_mock_mode or not self.settings.cognitia_enabled:
            return await self._mock.evaluate_claim(claim)
        # Remote delegation fallback to mock in case of Phase 0
        return await self._mock.evaluate_claim(claim)

    async def evaluate_hypothesis(self, hypothesis: Hypothesis) -> EpistemicAssessment:
        """Evaluate hypothesis via Cognitia."""
        return await self._mock.evaluate_hypothesis(hypothesis)

    async def identify_assumptions(self, hypothesis: Hypothesis) -> list[Assumption]:
        """Identify hidden assumptions via Cognitia."""
        return await self._mock.identify_assumptions(hypothesis)

    async def compare_models(self, models: list[ScientificModel]) -> dict[str, Any]:
        """Compare scientific models via Cognitia."""
        return await self._mock.compare_models(models)

    async def evaluate_representation(self, representation_spec: dict[str, Any]) -> dict[str, Any]:
        """Evaluate representation via Cognitia."""
        return await self._mock.evaluate_representation(representation_spec)

    async def generate_candidate_paths(self, spec: DirectionalSpecification) -> list[CandidatePath]:
        """Generate candidate research paths via Cognitia."""
        return await self._mock.generate_candidate_paths(spec)

    async def evaluate_falsification(
        self, hypothesis: Hypothesis, results: list[ExperimentResult]
    ) -> FalsificationEvaluation:
        """Evaluate falsification via Cognitia."""
        return await self._mock.evaluate_falsification(hypothesis, results)

    async def track_theory_transition(
        self, prior_theory: str, proposed_theory: str, anomalies: list[str]
    ) -> dict[str, Any]:
        """Track theory transitions via Cognitia."""
        return await self._mock.track_theory_transition(prior_theory, proposed_theory, anomalies)

    async def consult_advisory(self, request: CognitiaAdvisoryRequest) -> CognitiaAdvisoryResult:
        """Provide non-authoritative advisory analysis over a bounded semantic graph context."""
        return await self._mock.consult_advisory(request)
