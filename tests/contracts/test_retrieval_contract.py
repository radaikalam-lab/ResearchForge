"""Contract test for RetrievalProvider implementations."""

import pytest
from researchforge.domain.contracts.retrieval import RetrievalProvider
from researchforge.domain.models.evidence import EvidenceFragment, EvidenceType
from researchforge.providers.retrieval.mock import MockRetrievalProvider


@pytest.mark.asyncio
async def test_retrieval_provider_contract_conformance() -> None:
    """Verify provider implements RetrievalProvider protocol with dual modes."""
    provider: RetrievalProvider = MockRetrievalProvider()
    assert isinstance(provider, RetrievalProvider)

    frag1 = EvidenceFragment(
        id="f1",
        source_id="s1",
        evidence_type=EvidenceType.TEXT,
        location_reference="p. 4",
        content="Superconducting transition temperature increased to 95K under pressure.",
    )
    frag2 = EvidenceFragment(
        id="f2",
        source_id="s2",
        evidence_type=EvidenceType.EQUATION,
        location_reference="Eq. 12",
        content="T_c = 1.14 * theta_D * exp(-1 / (N(0) * V))",
    )

    count = await provider.index([frag1, frag2])
    assert count == 2

    # Semantic search
    results_semantic = await provider.search_semantic("transition temperature", top_k=1)
    assert len(results_semantic) > 0

    # Exact evidence search
    results_exact = await provider.search_evidence("exp(-1", top_k=1)
    assert len(results_exact) == 1
    assert results_exact[0].id == "f2"
