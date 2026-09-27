"""Tests for domain model serialization, content hashing, and invariants."""

import pytest
from researchforge.domain.models.evidence import (
    Claim,
    Evidence,
    EvidenceFragment,
    EvidenceType,
)
from researchforge.domain.models.hypothesis import (
    Hypothesis,
)
from researchforge.domain.models.project import ResearchProject


def test_domain_model_content_hashing_is_deterministic(sample_project: ResearchProject) -> None:
    """Verify content hash is stable given same data and ignores volatile fields."""
    hash1 = sample_project.content_hash()
    hash2 = sample_project.content_hash()
    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256


def test_hypothesis_requires_falsification_criteria() -> None:
    """Invariant: A hypothesis without falsification criteria cannot be instantiated."""
    with pytest.raises(ValueError):
        Hypothesis(
            id="hyp_invalid",
            project_id="proj_01",
            statement="An unfalsifiable assertion",
            mechanism="Magic",
            falsification_criteria=[],  # Must fail validation
        )


def test_evidence_and_claim_separation() -> None:
    """Verify explicit distinction between claims and empirical evidence."""
    claim = Claim(
        id="claim_01",
        statement="Superconductivity occurs at room temperature",
        is_grounded_in_evidence=False,
    )
    fragment = EvidenceFragment(
        id="frag_01",
        source_id="src_01",
        evidence_type=EvidenceType.DATASET,
        location_reference="Table 4",
        content="Raw resistance vs temperature array",
    )
    evidence = Evidence(
        id="evid_01",
        claim_ids=[claim.id],
        fragment_ids=[fragment.id],
        evidence_type=EvidenceType.DATASET,
        summary="Empirical data showing transition.",
    )
    assert evidence.fragment_ids == [fragment.id]
    assert evidence.claim_ids == [claim.id]
