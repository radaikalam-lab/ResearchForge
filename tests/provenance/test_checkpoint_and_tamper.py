"""Unit tests for Provenance Checkpoints, secret redaction, and tamper detection."""

from researchforge.provenance.event_types import ProvenanceEventType
from researchforge.provenance.ledger import ProvenanceLedger
from researchforge.provenance.models import ProvenanceActor
from researchforge.provenance.tracker import ProvenanceTracker


def test_checkpoint_creation_and_verification() -> None:
    """Verify signed checkpoint creation and consistency check."""
    ledger = ProvenanceLedger()
    tracker = ProvenanceTracker(ledger)

    tracker.track(
        actor=ProvenanceActor.RESEARCHFORGE,
        actor_id="engine",
        operation=ProvenanceEventType.PROJECT_CREATED,
        entity_id="proj_chk",
        entity_type="ResearchProject",
    )
    tracker.track(
        actor=ProvenanceActor.RESEARCHFORGE,
        actor_id="engine",
        operation=ProvenanceEventType.QUESTION_DEFINED,
        entity_id="q_chk",
        entity_type="ResearchQuestion",
    )

    checkpoint = ledger.create_checkpoint(secret_signer="test_node_key")
    assert checkpoint.event_count == 2
    assert checkpoint.latest_event_hash == ledger.all_events()[-1].event_hash
    assert ledger.verify_checkpoint(checkpoint) is True


def test_redaction_metadata_recording() -> None:
    """Verify that redaction metadata is explicitly recorded upon secret scrubbing."""
    ledger = ProvenanceLedger()
    tracker = ProvenanceTracker(ledger)

    event = tracker.track(
        actor=ProvenanceActor.HUMAN,
        actor_id="researcher",
        operation=ProvenanceEventType.SOURCE_RETRIEVED,
        entity_id="src_sec",
        entity_type="Source",
        parameters={"api_key": "sk-supersecret12345678", "endpoint": "https://api.crossref.org"},
    )

    assert event.parameters["api_key"] == "[REDACTED_SECRET]"
    assert "redaction_metadata" in event.model_dump()
    assert "api_key" in event.redaction_metadata["redacted_fields"]
