"""Contract test for EvidenceProvider implementations."""

import pytest
from researchforge.domain.contracts.evidence import EvidenceProvider
from researchforge.domain.models.evidence import Claim
from researchforge.domain.models.literature import Source
from researchforge.providers.evidence.mock import MockEvidenceProvider


@pytest.mark.asyncio
async def test_evidence_provider_contract_conformance() -> None:
    """Verify provider implements EvidenceProvider protocol."""
    provider: EvidenceProvider = MockEvidenceProvider()
    assert isinstance(provider, EvidenceProvider)

    source = Source(
        id="src_01",
        uri="https://doi.org/10.1000/182",
        provider_name="openalex",
        provider_record_id="rec_01",
        retrieved_content="High-pressure synthesis showed 35% improvement.",
    )

    fragments = await provider.extract_fragments(source)
    assert len(fragments) > 0
    assert fragments[0].source_id == source.id

    is_valid = await provider.validate_extraction(fragments[0], source)
    assert is_valid is True

    claim = Claim(id="claim_01", statement="High-pressure synthesis enhances properties.")
    evidence = await provider.synthesize_evidence(fragments, claim)
    assert evidence.validation_status == "VALIDATED"
    assert claim.id in evidence.claim_ids
