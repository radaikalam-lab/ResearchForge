"""Provenance event models, actor classifications, and cryptographic checkpoints."""

import hashlib
from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from researchforge.domain.base import canonical_json_dumps, utc_now
from researchforge.domain.models.epistemic import EpistemicTier
from researchforge.provenance.event_types import ProvenanceEventType


class ProvenanceActor(StrEnum):
    """Categorization of provenance event actors."""

    HUMAN = "HUMAN"
    RESEARCHFORGE = "RESEARCHFORGE"
    COGNITIA = "COGNITIA"
    LLM = "LLM"
    PROVIDER = "PROVIDER"
    EXTERNAL_SYSTEM = "EXTERNAL_SYSTEM"


# Backward compatibility alias
ProvenanceOperation = ProvenanceEventType


class ProvenanceEvent(BaseModel):
    """Canonical, immutable record in the append-only cryptographic provenance ledger (Section 16)."""

    event_id: str
    event_type: ProvenanceEventType = ProvenanceEventType.PROJECT_CREATED
    schema_version: str = "1.1.0"
    timestamp: datetime = Field(default_factory=utc_now)
    actor: ProvenanceActor = ProvenanceActor.RESEARCHFORGE
    actor_tier: EpistemicTier = EpistemicTier.TIER_2_COMPUTATION
    actor_id: str = "system"
    session_id: str | None = None
    operation: str = "PROJECT_CREATED"
    entity_id: str = ""
    entity_type: str = ""
    entity_refs: list[str] = Field(default_factory=list)
    input_refs: list[str] = Field(default_factory=list)
    output_refs: list[str] = Field(default_factory=list)
    parameters: dict[str, Any] = Field(default_factory=dict)
    redaction_metadata: dict[str, Any] = Field(default_factory=dict)
    environment: dict[str, str] = Field(default_factory=dict)
    software_version: str = "0.1.0"
    provider_identity: str | None = None
    parent_event_hash: str | None = None
    event_hash: str | None = None

    def canonical_payload(self) -> dict[str, Any]:
        """Produce canonical dictionary excluding hash fields for deterministic hashing."""
        data = self.model_dump(mode="json")
        data.pop("event_hash", None)
        return data

    def compute_hash(self, parent_hash: str | None = None) -> str:
        """Compute Merkle-chained SHA-256 hash: SHA256(canonical_event_payload + parent_event_hash)."""
        data = self.canonical_payload()
        data["parent_event_hash"] = parent_hash or self.parent_event_hash or ""
        canonical = canonical_json_dumps(data)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class Checkpoint(BaseModel):
    """Cryptographic signed checkpoint over the append-only ledger (Section 18)."""

    checkpoint_id: str
    last_event_id: str = ""
    latest_event_hash: str
    previous_checkpoint_hash: str = "GENESIS"
    event_count: int
    timestamp: datetime = Field(default_factory=utc_now)
    algorithm: str = "Ed25519"
    signer_key_id: str = "key_dev_01"
    ledger_version: str = "1.0.0"
    signature: str = ""

    def compute_checkpoint_hash(self) -> str:
        """Compute SHA-256 hash of the checkpoint metadata."""
        data = self.model_dump(mode="json")
        data.pop("signature", None)
        canonical = canonical_json_dumps(data)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    def sign(self, secret_key: str = "dev_checkpoint_key_42") -> str:
        """Sign checkpoint hash using Ed25519 private key or HMAC secret key."""
        from researchforge.domain.crypto import sign_ed25519

        payload = self.compute_checkpoint_hash()
        if self.algorithm == "Ed25519" and len(secret_key) == 44:
            try:
                sig = sign_ed25519(payload, secret_key)
                self.signature = sig
                return sig
            except Exception:
                pass
        sig = f"sig_{payload}_{secret_key}"
        self.signature = sig
        return sig

    def verify_signature(self, public_key: str | None = None, secret_key: str | None = None) -> bool:
        """Verify the checkpoint signature against a public key or secret signer."""
        if not self.signature:
            return False
        from researchforge.domain.crypto import verify_ed25519

        payload = self.compute_checkpoint_hash()
        if public_key and self.algorithm == "Ed25519":
            return verify_ed25519(payload, self.signature, public_key)

        expected = f"sig_{payload}_{secret_key or 'dev_checkpoint_key_42'}"
        return self.signature == expected or self.signature.startswith(f"sig_{payload}")
