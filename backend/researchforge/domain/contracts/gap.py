"""Research gap provider protocol contract."""

from typing import Protocol, runtime_checkable

from researchforge.domain.models.evidence import Evidence
from researchforge.domain.models.gap import GapCandidate, ResearchGap


@runtime_checkable
class GapAnalysisProvider(Protocol):
    """Contract for discovering and evaluating candidate research gaps in literature."""

    provider_name: str

    async def analyze_gaps(self, evidence_items: list[Evidence]) -> list[GapCandidate]:
        """Analyze structured evidence to identify candidate contradictions, missing variables, etc."""
        ...

    async def evaluate_gap_validity(
        self, candidate: GapCandidate, evidence_items: list[Evidence]
    ) -> ResearchGap | None:
        """Verify that a gap candidate has empirical backing before creating a formal ResearchGap."""
        ...
