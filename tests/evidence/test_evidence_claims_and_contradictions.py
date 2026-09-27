"""Tests for evidence extraction, claim typing, confidence decomposition, and contradiction detection."""

import pytest
from researchforge.domain.models.evidence import ClaimType, EvidenceType
from researchforge.providers.evidence.reference import ReferenceEvidenceExtractionProvider
from researchforge.providers.literature.reference import ReferenceLiteratureProvider


@pytest.mark.asyncio
async def test_evidence_fragment_extraction_and_traceability() -> None:
    """Validate that fragments retain precise location references and extraction metadata."""
    lit_provider = ReferenceLiteratureProvider()
    sources = await lit_provider.search("parameter_x", limit=4)
    extractor = ReferenceEvidenceExtractionProvider()

    all_frags = []
    for s in sources:
        frags = await extractor.extract_fragments(s)
        all_frags.extend(frags)
        for f in frags:
            assert f.source_id == s.id
            assert f.location_reference != ""
            assert f.confidence > 0.0
            assert f.evidence_type in {
                EvidenceType.STATISTICAL_RESULT,
                EvidenceType.EXPERIMENTAL_RESULT,
                EvidenceType.OBSERVATION,
                EvidenceType.REVIEWER_ASSERTION,
                EvidenceType.TEXT,
            }

    assert len(all_frags) >= 4


@pytest.mark.asyncio
async def test_claim_confidence_decomposition_and_bindings() -> None:
    """Validate that claim confidence is decomposed into extraction, reported, and domain assessment."""
    lit_provider = ReferenceLiteratureProvider()
    sources = await lit_provider.search("parameter_x", limit=1)
    primary_src = sources[0]

    extractor = ReferenceEvidenceExtractionProvider()
    frags = await extractor.extract_fragments(primary_src)
    claims = await extractor.extract_candidate_claims(primary_src, frags)

    assert len(claims) == 1
    claim = claims[0]
    assert claim.claim_type == ClaimType.PARAMETER_RELATIONSHIP
    assert claim.extraction_confidence == 0.98
    assert claim.source_reported_confidence == 0.99
    assert claim.domain_assessment == "ACCEPTED"
    assert claim.is_grounded_in_evidence is True

    # Test explicit bindings
    bindings = extractor.create_bindings(
        project_id="proj_01",
        claims=claims,
        fragments=frags,
        evidence_id="ev_01",
    )
    assert len(bindings) == len(frags)
    for b in bindings:
        assert b.binding_type == "SUPPORTS"
        assert b.source_id == primary_src.id
        assert b.claim_id == claim.id


@pytest.mark.asyncio
async def test_deterministic_contradiction_detection() -> None:
    """Validate detection of conflicting positive monotonic vs. null claims in identical parameter space."""
    lit_provider = ReferenceLiteratureProvider()
    sources = await lit_provider.search("parameter_x", limit=4)
    extractor = ReferenceEvidenceExtractionProvider()

    all_claims = []
    for s in sources:
        frags = await extractor.extract_fragments(s)
        claims = await extractor.extract_candidate_claims(s, frags)
        all_claims.extend(claims)

    contradictions = extractor.detect_contradictions(project_id="proj_01", claims=all_claims)
    assert len(contradictions) >= 1

    contra = contradictions[0]
    assert contra.contradiction_type == "DIRECT_OPPOSITION"
    assert "Discrepancy on Parameter X" in contra.description
    assert contra.scope_difference == "Overlapping range [0.0, 2.0]"
    assert "OLS" in contra.methodological_difference
