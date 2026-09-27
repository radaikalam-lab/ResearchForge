"""Tests for HumanDecision cryptographic signatures and validation (Section 19, 27)."""

from researchforge.domain.models.conclusion import DecisionType, HumanDecision


def test_human_decision_signing_and_verification() -> None:
    """Proves that a human decision can be cryptographically signed and verified."""
    decision = HumanDecision(
        id="dec_sig_01",
        project_id="proj_sig",
        target_entity_id="hyp_sig",
        decision=DecisionType.APPROVE,
        reviewer_id="lead_investigator_dr_jones",
        rationale="Evidence and falsification testing conclusively prove linear relationship.",
        evidence_ids=["evid_01", "evid_02"],
        analysis_ids=["stat_01"],
        falsification_id="fals_01",
    )

    # Initial state without signature
    assert decision.signature is None
    assert decision.verify_signature(secret_key="secret_key_123") is False

    # Sign decision
    sig = decision.sign(secret_key="secret_key_123")
    assert sig is not None
    assert len(sig) == 64  # SHA-256 hex digest

    # Verify with correct key
    assert decision.verify_signature(secret_key="secret_key_123") is True

    # Verify with wrong key fails
    assert decision.verify_signature(secret_key="wrong_key_999") is False

    # Tamper with decision rationale -> verification must fail
    decision.rationale = "Tampered rationale injected by attacker."
    assert decision.verify_signature(secret_key="secret_key_123") is False
