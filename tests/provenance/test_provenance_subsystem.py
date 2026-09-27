"""Tests for append-only cryptographic provenance ledger."""

from researchforge.provenance.ledger import ProvenanceLedger, scrub_secrets
from researchforge.provenance.models import (
    ProvenanceActor,
    ProvenanceOperation,
)
from researchforge.provenance.tracker import ProvenanceTracker


def test_provenance_cryptographic_chaining_and_integrity() -> None:
    """Verify Merkle chaining of provenance events."""
    ledger = ProvenanceLedger()
    tracker = ProvenanceTracker(ledger)

    event1 = tracker.track(
        actor=ProvenanceActor.HUMAN,
        actor_id="researcher_1",
        operation=ProvenanceOperation.PROJECT_CREATED,
        entity_id="proj_01",
        entity_type="ResearchProject",
    )

    event2 = tracker.track(
        actor=ProvenanceActor.RESEARCHFORGE,
        actor_id="engine",
        operation=ProvenanceOperation.SOURCE_INGESTED,
        entity_id="src_01",
        entity_type="Source",
        input_refs=[event1.entity_id],
    )

    assert event1.parent_event_hash is None
    assert event2.parent_event_hash == event1.event_hash

    is_valid, err = ledger.verify_integrity()
    assert is_valid is True
    assert err is None


def test_secret_scrubbing_in_provenance() -> None:
    """Verify that credentials and tokens are redacted before ledger recording."""
    payload = {
        "api_key": "sk-1234567890abcdef12345",
        "nested": {"token": "secret_token_val_123"},
        "normal_field": "public_data",
    }
    scrubbed = scrub_secrets(payload)
    assert scrubbed["api_key"] == "[REDACTED_SECRET]"
    assert scrubbed["nested"]["token"] == "[REDACTED_SECRET]"
    assert scrubbed["normal_field"] == "public_data"
