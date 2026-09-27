"""Contract test for GapAnalysisProvider implementations."""

import pytest
from researchforge.domain.contracts.gap import GapAnalysisProvider
from researchforge.domain.models.evidence import Evidence, EvidenceType
from researchforge.domain.models.gap import GapType
from researchforge.providers.gap.mock import MockGapAnalysisProvider


@pytest.mark.asyncio
async def test_gap_provider_contract_conformance() -> None:
    """Verify provider implements GapAnalysisProvider protocol."""
    provider: GapAnalysisProvider = MockGapAnalysisProvider()
    assert isinstance(provider, GapAnalysisProvider)

    evidence_item = Evidence(
        id="evid_01",
        evidence_type=EvidenceType.EXPERIMENTAL_RESULT,
        summary="High-temperature measurement inconsistent with classical law.",
        validation_status="VALIDATED",
    )

    candidates = await provider.analyze_gaps([evidence_item])
    assert len(candidates) > 0
    assert candidates[0].gap_type == GapType.CONTRADICTION

    gap = await provider.evaluate_gap_validity(candidates[0], [evidence_item])
    assert gap is not None
    assert len(gap.supporting_evidence_ids) > 0
