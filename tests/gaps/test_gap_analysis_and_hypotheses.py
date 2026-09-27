"""Tests for research gap classification, hypothesis candidate generation, and Cognitia advisory boundary."""

import pytest
from researchforge.domain.models.gap import GapType
from researchforge.providers.cognitia.adapter import CognitiaAdapter
from researchforge.providers.evidence.reference import ReferenceEvidenceExtractionProvider
from researchforge.providers.gap.reference import ReferenceGapAnalysisProvider
from researchforge.providers.literature.reference import ReferenceLiteratureProvider


@pytest.mark.asyncio
async def test_gap_analysis_and_candidate_promotion() -> None:
    """Validate that GapAnalysisProvider identifies contradiction and boundary gaps and promotes to ResearchGap."""
    lit_provider = ReferenceLiteratureProvider()
    sources = await lit_provider.search("parameter_x", limit=4)
    extractor = ReferenceEvidenceExtractionProvider()

    all_evidence = []
    all_claims = []
    for s in sources:
        frags = await extractor.extract_fragments(s)
        claims = await extractor.extract_candidate_claims(s, frags)
        all_claims.extend(claims)
        if claims:
            ev = await extractor.synthesize_evidence(frags, claims[0])
            all_evidence.append(ev)

    contradictions = extractor.detect_contradictions("proj_01", all_claims)

    gap_provider = ReferenceGapAnalysisProvider()
    candidates = await gap_provider.analyze_gaps(all_evidence, all_claims, contradictions)

    # Must contain both contradiction gap and boundary condition gap
    gap_types = [c.gap_type for c in candidates]
    assert GapType.CONTRADICTION_GAP in gap_types
    assert GapType.BOUNDARY_CONDITION_GAP in gap_types

    # Promote candidate to verified ResearchGap
    verified_gap = await gap_provider.evaluate_gap_validity(candidates[0], all_evidence)
    assert verified_gap is not None
    assert len(verified_gap.supporting_evidence_ids) >= 1
    assert verified_gap.impact_score > 0.0


@pytest.mark.asyncio
async def test_hypothesis_formulation_mandatory_falsification() -> None:
    """Validate hypothesis candidates formulated from gaps strictly enforce falsification criteria."""
    lit_provider = ReferenceLiteratureProvider()
    sources = await lit_provider.search("parameter_x", limit=4)
    extractor = ReferenceEvidenceExtractionProvider()

    all_evidence = []
    for s in sources:
        frags = await extractor.extract_fragments(s)
        claims = await extractor.extract_candidate_claims(s, frags)
        if claims:
            ev = await extractor.synthesize_evidence(frags, claims[0])
            all_evidence.append(ev)

    gap_provider = ReferenceGapAnalysisProvider()
    candidates = await gap_provider.analyze_gaps(all_evidence)
    verified_gap = await gap_provider.evaluate_gap_validity(candidates[0], all_evidence)

    assert verified_gap is not None
    hypothesis = gap_provider.propose_hypothesis_candidate(verified_gap, "proj_01")

    assert hypothesis.statement != ""
    assert hypothesis.mechanism != ""
    assert len(hypothesis.falsification_criteria) >= 2
    for fc in hypothesis.falsification_criteria:
        assert fc.condition_expression != ""
        assert fc.metric_name != ""
        assert fc.is_fatal_to_hypothesis is True


@pytest.mark.asyncio
async def test_cognitia_advisory_boundary_on_phase_1_hypotheses() -> None:
    """Validate Cognitia provides epistemic critiques without possessing execution or conclusion authority."""
    lit_provider = ReferenceLiteratureProvider()
    sources = await lit_provider.search("parameter_x", limit=2)
    extractor = ReferenceEvidenceExtractionProvider()
    all_evidence = []
    for s in sources:
        frags = await extractor.extract_fragments(s)
        claims = await extractor.extract_candidate_claims(s, frags)
        if claims:
            ev = await extractor.synthesize_evidence(frags, claims[0])
            all_evidence.append(ev)

    gap_provider = ReferenceGapAnalysisProvider()
    candidates = await gap_provider.analyze_gaps(all_evidence)
    verified_gap = await gap_provider.evaluate_gap_validity(candidates[0], all_evidence)
    assert verified_gap is not None
    hypothesis = gap_provider.propose_hypothesis_candidate(verified_gap, "proj_01")

    adapter = CognitiaAdapter()
    critique = await adapter.evaluate_hypothesis(hypothesis)

    # Verify advisory nature
    assert critique.target_id == hypothesis.id
    assert critique.epistemic_soundness >= 0.0
    assert hasattr(critique, "vulnerabilities")
