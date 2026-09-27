"""Convenience tracker for emitting lifecycle provenance events."""

import uuid
from typing import Any

from researchforge.domain.models.epistemic import EpistemicTier
from researchforge.provenance.event_types import ProvenanceEventType
from researchforge.provenance.ledger import ProvenanceLedger
from researchforge.provenance.models import ProvenanceActor, ProvenanceEvent


class ProvenanceTracker:
    """Helper service for recording domain lifecycle actions into the ledger."""

    def __init__(self, ledger: ProvenanceLedger) -> None:
        self.ledger = ledger

    def track(
        self,
        actor: ProvenanceActor,
        actor_id: str,
        operation: str,
        entity_id: str,
        entity_type: str,
        actor_tier: EpistemicTier = EpistemicTier.TIER_2_COMPUTATION,
        event_type: ProvenanceEventType | None = None,
        session_id: str | None = None,
        entity_refs: list[str] | None = None,
        input_refs: list[str] | None = None,
        output_refs: list[str] | None = None,
        parameters: dict[str, Any] | None = None,
        environment: dict[str, str] | None = None,
        provider_identity: str | None = None,
    ) -> ProvenanceEvent:
        """Create and commit a canonical provenance event."""
        event_id = f"prov_{uuid.uuid4().hex[:12]}"

        # Resolve event_type
        resolved_type = event_type
        if resolved_type is None:
            try:
                resolved_type = ProvenanceEventType(str(operation))
            except ValueError:
                resolved_type = ProvenanceEventType.STATE_TRANSITIONED

        event = ProvenanceEvent(
            event_id=event_id,
            event_type=resolved_type,
            actor=actor,
            actor_tier=actor_tier,
            actor_id=actor_id,
            session_id=session_id,
            operation=str(operation),
            entity_id=entity_id,
            entity_type=entity_type,
            entity_refs=entity_refs or ([entity_id] if entity_id else []),
            input_refs=input_refs or [],
            output_refs=output_refs or [],
            parameters=parameters or {},
            environment=environment or {},
            provider_identity=provider_identity,
        )
        return self.ledger.record_event(event)
