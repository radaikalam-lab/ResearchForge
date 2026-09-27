"""Mock gap analysis provider."""

import uuid

from researchforge.domain.contracts.gap import GapAnalysisProvider
from researchforge.domain.models.evidence import Evidence
from researchforge.domain.models.gap import GapCandidate, GapType, ResearchGap


class MockGapAnalysisProvider(GapAnalysisProvider):
    """Mock implementation of GapAnalysisProvider."""

    provider_name: str = "mock-gap-analysis-v1"

    async def analyze_gaps(self, evidence_items: list[Evidence]) -> list[GapCandidate]:
        """Analyze evidence to identify candidate gaps."""
        cand_id = f"cand_{uuid.uuid4().hex[:8]}"
        return [
            GapCandidate(
                id=cand_id,
                description="Contradictory findings in high-temperature phase transition regimes.",
                gap_type=GapType.CONTRADICTION,
                supporting_source_ids=[e.id for e in evidence_items],
                affected_variables=["temperature", "lattice_constant"],
                unexplored_region="Temperatures above 1200K under 5GPa pressure.",
                confidence=0.88,
                unresolved_questions=["Does phase transition follow first-order or continuous kinetics?"],
            )
        ]

    async def evaluate_gap_validity(
        self, candidate: GapCandidate, evidence_items: list[Evidence]
    ) -> ResearchGap | None:
        """Validate candidate gap against evidence."""
        if not evidence_items:
            return None
        return ResearchGap(
            id=f"gap_{uuid.uuid4().hex[:8]}",
            project_id="proj_default",
            title=f"Gap: {candidate.description[:40]}",
            description=candidate.description,
            gap_type=candidate.gap_type,
            supporting_evidence_ids=[e.id for e in evidence_items],
            affected_variable_ids=candidate.affected_variables,
            impact_score=0.90,
        )
