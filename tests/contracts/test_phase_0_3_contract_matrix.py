"""Comprehensive Phase 0.3 contract matrix tests (Workstream P)."""

import pytest
from researchforge.domain.crypto import generate_ed25519_keypair
from researchforge.domain.models.conclusion import DecisionType, HumanDecision, ResearcherIdentity
from researchforge.domain.models.hypothesis import Hypothesis
from researchforge.domain.state_machine import (
    InvalidStateTransitionError,
    ResearchLifecycleState,
    validate_transition,
)
from researchforge.execution.backends import ReferenceExecutionBackend
from researchforge.execution.policy import Capability, CapabilityGrant, ExecutionPolicy
from researchforge.execution.request import ExecutionRequest
from researchforge.execution.sandbox import SandboxPolicyViolationError
from researchforge.provenance.ledger import ProvenanceLedger
from researchforge.provenance.models import ProvenanceEvent, ProvenanceEventType


def test_state_machine_legal_and_illegal_transitions() -> None:
    """Validate strict topology enforcement across lifecycle states."""
    # Legal transition
    validate_transition(ResearchLifecycleState.DRAFT, ResearchLifecycleState.QUESTION_DEFINED)

    # Illegal jump without going through intermediate states
    with pytest.raises(InvalidStateTransitionError):
        validate_transition(ResearchLifecycleState.DRAFT, ResearchLifecycleState.CONCLUSION_ACCEPTED)

    # Advancing to CONCLUSION_ACCEPTED without human approval
    with pytest.raises(InvalidStateTransitionError, match="human approval"):
        validate_transition(
            ResearchLifecycleState.HUMAN_REVIEW,
            ResearchLifecycleState.CONCLUSION_ACCEPTED,
            has_human_approval=False,
            has_evidence=True,
        )


def test_ed25519_human_decision_signature_and_revocation() -> None:
    """Validate asymmetric Ed25519 signing and verification with ResearcherIdentity status."""
    priv_b64, pub_b64 = generate_ed25519_keypair()

    identity = ResearcherIdentity(
        researcher_id="dr_curie",
        name="Marie Curie",
        public_key=pub_b64,
        algorithm="Ed25519",
        status="ACTIVE",
    )

    decision = HumanDecision(
        id="dec_ed25519_01",
        project_id="proj_01",
        target_entity_id="hyp_01",
        decision=DecisionType.APPROVE,
        reviewer_id="dr_curie",
        rationale="Hypothesis rigorously verified with statistical significance.",
        evidence_ids=["ev_01", "ev_02"],
        analysis_ids=["stat_01"],
    )

    # Sign with private key
    decision.sign(secret_key=priv_b64, algorithm="Ed25519")
    assert decision.signature is not None

    # Verify with active identity
    assert decision.verify_signature(identity=identity) is True

    # Verify with wrong public key
    _, wrong_pub = generate_ed25519_keypair()
    assert decision.verify_signature(public_key=wrong_pub) is False

    # Verify with revoked identity
    identity.status = "REVOKED"
    assert decision.verify_signature(identity=identity) is False


def test_hypothesis_mandatory_falsification_criteria() -> None:
    """Validate that a Hypothesis cannot exist without at least one falsification criterion."""
    with pytest.raises((ValueError, Exception)):
        Hypothesis(
            id="hyp_invalid",
            project_id="proj_01",
            statement="Any claim",
            mechanism="Test mechanism",
            falsification_criteria=[],
        )


@pytest.mark.asyncio
async def test_execution_backend_policy_and_timeout() -> None:
    """Validate ReferenceExecutionBackend enforces capabilities and policy boundaries."""
    backend = ReferenceExecutionBackend()

    req = ExecutionRequest(
        request_id="req_test_01",
        command_or_function="noop",
        arguments={"val": 42},
        required_capabilities={Capability.RUN_SIMULATION},
        policy=ExecutionPolicy(
            allowed_capabilities=set(),
            allow_network=False,
            max_time_sec=1,
        ),
    )

    # Blocked without capability grant
    with pytest.raises(SandboxPolicyViolationError, match="lacks required capabilities"):
        backend.validate_request(req, grants=[])

    # Allowed with active grant
    grant = CapabilityGrant(
        grant_id="grant_01",
        capability=Capability.RUN_SIMULATION,
        granted_by="admin",
    )
    backend.validate_request(req, grants=[grant])

    # Test execution
    res = await backend.execute(req, lambda val: {"result": val * 2}, grants=[grant])
    assert res.status == "COMPLETED"
    assert res.output == {"result": 84}


def test_checkpoint_chain_integrity_and_tampering() -> None:
    """Validate Merkle checkpoint chain integrity and tamper detection."""
    ledger = ProvenanceLedger()
    e1 = ProvenanceEvent(
        event_id="prov_01",
        event_type=ProvenanceEventType.PROJECT_CREATED,
        entity_id="proj_01",
        entity_type="ResearchProject",
    )
    ledger.record_event(e1)

    chk1 = ledger.create_checkpoint(secret_signer="key_01")
    assert chk1.event_count == 1
    assert ledger.verify_checkpoint(chk1) is True

    e2 = ProvenanceEvent(
        event_id="prov_02",
        event_type=ProvenanceEventType.QUESTION_DEFINED,
        entity_id="q_01",
        entity_type="ResearchQuestion",
    )
    ledger.record_event(e2)
    chk2 = ledger.create_checkpoint(secret_signer="key_01")

    # Verify chain
    chain_ok, err = ledger.verify_checkpoint_chain([chk1, chk2])
    assert chain_ok is True
    assert err is None

    # Alter previous checkpoint hash -> broken chain
    chk2.previous_checkpoint_hash = "TAMPERED_HASH"
    chain_ok, err = ledger.verify_checkpoint_chain([chk1, chk2])
    assert chain_ok is False
    assert "Checkpoint chain broken" in (err or "")
