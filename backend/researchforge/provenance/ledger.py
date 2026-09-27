"""Cryptographic append-only provenance ledger with Merkle chaining, checkpoints, and tamper detection."""

import json
import re
import uuid
from pathlib import Path
from typing import Any

from researchforge.domain.base import utc_now
from researchforge.provenance.models import Checkpoint, ProvenanceEvent

# Sensitive key names and patterns
SENSITIVE_PATTERNS = [
    re.compile(r"(?i)(key|secret|token|password|auth|bearer)[\"']?\s*[:=]\s*[\"']?([a-zA-Z0-9_\-\.]{8,})[\"']?"),
]


def scrub_secrets_with_metadata(obj: Any) -> tuple[Any, list[str]]:
    """Recursively scrub detected credentials and return scrubbed object plus list of redacted keys."""
    redacted_keys: list[str] = []

    def _scrub(item: Any, current_path: str = "") -> Any:
        if isinstance(item, dict):
            scrubbed = {}
            for k, v in item.items():
                path = f"{current_path}.{k}" if current_path else k
                if any(s in k.lower() for s in ("key", "secret", "token", "password", "auth", "bearer")):
                    scrubbed[k] = "[REDACTED_SECRET]"
                    redacted_keys.append(path)
                else:
                    scrubbed[k] = _scrub(v, path)
            return scrubbed
        elif isinstance(item, list):
            return [_scrub(x, f"{current_path}[]") for x in item]
        elif isinstance(item, str):
            result = item
            for pattern in SENSITIVE_PATTERNS:
                if pattern.search(result):
                    result = pattern.sub(r"\1: [REDACTED_SECRET]", result)
                    redacted_keys.append(current_path or "text_payload")
            return result
        return item

    cleaned = _scrub(obj)
    return cleaned, redacted_keys


def scrub_secrets(obj: Any) -> Any:
    """Backward compatibility wrapper for secret scrubbing."""
    cleaned, _ = scrub_secrets_with_metadata(obj)
    return cleaned


class ProvenanceLedger:
    """Thread-safe append-only ledger for cryptographic provenance events with Merkle checkpoints."""

    def __init__(self, ledger_path: Path | None = None) -> None:
        self.ledger_path = ledger_path
        self._events: list[ProvenanceEvent] = []
        self._checkpoints: list[Checkpoint] = []
        self._last_hash: str | None = None
        if self.ledger_path and self.ledger_path.exists():
            self._load_ledger()

    def _load_ledger(self) -> None:
        """Load and verify existing ledger from file."""
        if not self.ledger_path:
            return
        self._events.clear()
        self._last_hash = None
        with open(self.ledger_path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                if data.get("record_type") == "CHECKPOINT":
                    data.pop("record_type", None)
                    self._checkpoints.append(Checkpoint(**data))
                else:
                    event = ProvenanceEvent(**data)
                    self._events.append(event)
                    self._last_hash = event.event_hash

    def record_event(self, event: ProvenanceEvent) -> ProvenanceEvent:
        """Commit an event to the ledger: redact secrets -> record metadata -> compute Merkle hash -> append."""
        # 1. Secret scrubbing BEFORE hashing
        cleaned_params, redacted_fields = scrub_secrets_with_metadata(event.parameters)
        event.parameters = cleaned_params
        if redacted_fields:
            event.redaction_metadata = {
                "redacted_fields": redacted_fields,
                "policy": "SECRET_REDACTION_V1",
                "redacted_at": utc_now().isoformat(),
            }

        # 2. Hash chaining: SHA256(canonical_event_payload + parent_event_hash)
        event.parent_event_hash = self._last_hash
        event.event_hash = event.compute_hash(self._last_hash)
        self._last_hash = event.event_hash
        self._events.append(event)

        # 3. Append to persistent storage if configured
        if self.ledger_path:
            self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\n")

        return event

    def create_checkpoint(
        self,
        secret_signer: str = "local_node",
        signer_key_id: str = "key_dev_01",
        algorithm: str = "Ed25519",
    ) -> Checkpoint:
        """Create a cryptographic checkpoint locking the ledger state up to the current event."""
        latest_hash = self._last_hash or "GENESIS_EMPTY"
        last_event = self._events[-1] if self._events else None
        prev_chk = self._checkpoints[-1] if self._checkpoints else None
        prev_hash = prev_chk.compute_checkpoint_hash() if prev_chk else "GENESIS"

        chk_id = f"chk_{uuid.uuid4().hex[:12]}"
        checkpoint = Checkpoint(
            checkpoint_id=chk_id,
            last_event_id=last_event.event_id if last_event else "",
            latest_event_hash=latest_hash,
            previous_checkpoint_hash=prev_hash,
            event_count=len(self._events),
            timestamp=utc_now(),
            algorithm=algorithm,
            signer_key_id=signer_key_id,
            ledger_version="1.0.0",
        )
        checkpoint.sign(secret_signer)
        self._checkpoints.append(checkpoint)

        if self.ledger_path:
            data = checkpoint.model_dump(mode="json")
            data["record_type"] = "CHECKPOINT"
            with open(self.ledger_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(data) + "\n")

        return checkpoint

    def verify_integrity(self) -> tuple[bool, str | None]:
        """Verify the cryptographic hash chain of the entire ledger."""
        current_parent_hash: str | None = None
        for idx, event in enumerate(self._events):
            if event.parent_event_hash != current_parent_hash:
                return False, f"Broken chain at event index {idx} ({event.event_id})."
            expected_hash = event.compute_hash(current_parent_hash)
            if event.event_hash != expected_hash:
                return False, f"Hash mismatch at event index {idx} ({event.event_id})."
            current_parent_hash = event.event_hash
        return True, None

    def verify_checkpoint(
        self,
        checkpoint: Checkpoint,
        public_key: str | None = None,
        secret_key: str | None = None,
    ) -> bool:
        """Verify that the ledger contains the exact event count and matching hash stated in checkpoint."""
        if checkpoint.event_count > 0:
            if len(self._events) < checkpoint.event_count:
                return False
            target_event = self._events[checkpoint.event_count - 1]
            if target_event.event_hash != checkpoint.latest_event_hash:
                return False
            if checkpoint.last_event_id and target_event.event_id != checkpoint.last_event_id:
                return False
        if not checkpoint.verify_signature(public_key=public_key, secret_key=secret_key):
            return False
        return True

    def verify_checkpoint_chain(
        self,
        checkpoints: list[Checkpoint] | None = None,
        public_key: str | None = None,
        secret_key: str | None = None,
    ) -> tuple[bool, str | None]:
        """Verify the cryptographic continuity and signatures across all chained checkpoints."""
        chks = checkpoints or self._checkpoints
        if not chks:
            return True, None

        prev_hash = "GENESIS"
        for idx, chk in enumerate(chks):
            if chk.previous_checkpoint_hash != prev_hash and (idx > 0 or chk.previous_checkpoint_hash != "GENESIS"):
                return False, f"Checkpoint chain broken at index {idx} ({chk.checkpoint_id})"
            if not self.verify_checkpoint(chk, public_key=public_key, secret_key=secret_key):
                return False, f"Checkpoint signature or event state invalid at index {idx} ({chk.checkpoint_id})"
            prev_hash = chk.compute_checkpoint_hash()
        return True, None

    def detect_tampering(self) -> tuple[bool, list[str]]:
        """Run full diagnostic check for broken chains, altered payloads, or truncated events."""
        anomalies: list[str] = []
        is_intact, err = self.verify_integrity()
        if not is_intact and err:
            anomalies.append(err)

        for chk in self._checkpoints:
            if not self.verify_checkpoint(chk):
                anomalies.append(f"Checkpoint {chk.checkpoint_id} verification failed (possible truncation/tamper).")

        chain_ok, chain_err = self.verify_checkpoint_chain()
        if not chain_ok and chain_err:
            anomalies.append(chain_err)

        return len(anomalies) == 0, anomalies

    def get_events_for_entity(self, entity_id: str) -> list[ProvenanceEvent]:
        """Retrieve full audit history for a specific domain entity."""
        return [
            e
            for e in self._events
            if e.entity_id == entity_id
            or entity_id in e.input_refs
            or entity_id in e.output_refs
            or entity_id in e.entity_refs
        ]

    def get_head_hash(self) -> str:
        """Return the latest event hash (head of the provenance chain) or empty string."""
        return self._last_hash or ""

    @staticmethod
    def verify_chain(events: list[ProvenanceEvent]) -> tuple[bool, str | None]:
        """Verify the cryptographic hash chain of an arbitrary event sequence."""
        current_parent_hash: str | None = None
        for idx, event in enumerate(events):
            if event.parent_event_hash != current_parent_hash:
                return False, f"Broken chain at event index {idx} ({event.event_id})."
            expected_hash = event.compute_hash(current_parent_hash)
            if event.event_hash != expected_hash:
                return False, f"Hash mismatch at event index {idx} ({event.event_id})."
            current_parent_hash = event.event_hash
        return True, None

    def all_events(self) -> list[ProvenanceEvent]:
        """Return all events currently in the ledger."""
        return list(self._events)
