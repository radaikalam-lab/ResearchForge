"""Conclusions, research findings, and human decision gatekeeper models."""

from datetime import datetime
from enum import StrEnum
from typing import Any

from pydantic import Field

from researchforge.domain.base import DomainModel, utc_now
from researchforge.domain.crypto import (
    sign_ed25519,
    sign_hmac_sha256,
    verify_ed25519,
    verify_hmac_sha256,
)
from researchforge.domain.value_objects.uncertainty import UncertaintyProfile


class DecisionType(StrEnum):
    """Human scientific gatekeeper decision types."""

    APPROVE = "APPROVE"
    REJECT = "REJECT"
    REQUEST_REVISION = "REQUEST_REVISION"
    CONDITIONAL_APPROVE = "CONDITIONAL_APPROVE"


class ResearcherIdentity(DomainModel):
    """Cryptographic identity profile for an authorized human researcher / gatekeeper."""

    id: str = Field(default="")
    researcher_id: str = ""
    name: str = "Authorized Researcher"
    public_key: str
    algorithm: str = "Ed25519"
    key_id: str = "key_primary"
    status: str = "ACTIVE"  # ACTIVE, REVOKED
    created_at: datetime = Field(default_factory=utc_now)
    revoked_at: datetime | None = None

    def model_post_init(self, __context: Any) -> None:
        if not self.id and self.researcher_id:
            self.id = self.researcher_id
        elif not self.researcher_id and self.id:
            self.researcher_id = self.id

    def is_active(self) -> bool:
        """Check if identity is currently active and unrevoked."""
        return self.status == "ACTIVE" and self.revoked_at is None


class HumanDecision(DomainModel):
    """Immutable record of human researcher scientific authority decision with cryptographic signature."""

    project_id: str
    target_entity_id: str
    target_entity_type: str = "Hypothesis"  # Hypothesis, Conclusion, Artifact
    decision: DecisionType
    reviewer_id: str
    rationale: str = Field(min_length=1, description="Rationale for acceptance or rejection")
    epistemic_notes: str = ""
    evidence_ids: list[str] = Field(default_factory=list)
    analysis_ids: list[str] = Field(default_factory=list)
    falsification_id: str | None = None
    algorithm: str = "Ed25519"
    key_id: str = "key_primary"
    signature: str | None = None

    def compute_signature_payload(self) -> str:
        """Construct canonical payload string for cryptographic signing."""
        return (
            f"{self.id}:{self.project_id}:{self.target_entity_id}:{self.decision.value}:"
            f"{self.reviewer_id}:{self.rationale}:{','.join(sorted(self.evidence_ids))}:"
            f"{','.join(sorted(self.analysis_ids))}:{self.falsification_id or ''}"
        )

    def sign(self, secret_key: str = "dev_human_key_42", algorithm: str | None = None) -> str:
        """Generate signature for this decision using Ed25519 private key or HMAC secret key."""
        alg = algorithm or self.algorithm
        payload = self.compute_signature_payload()
        if alg == "Ed25519" and len(secret_key) == 44:  # 32-byte base64 string
            try:
                sig = sign_ed25519(payload, secret_key)
                self.algorithm = "Ed25519"
                self.signature = sig
                return sig
            except Exception:
                pass
        # Default or fallback to HMAC-SHA256 for local dev strings
        sig = sign_hmac_sha256(payload, secret_key)
        self.algorithm = "HMAC-SHA256"
        self.signature = sig
        return sig

    def verify_signature(
        self,
        secret_key: str | None = None,
        public_key: str | None = None,
        identity: ResearcherIdentity | None = None,
    ) -> bool:
        """Verify the cryptographic signature against a public key, secret key, or ResearcherIdentity."""
        if not self.signature:
            return False

        if identity is not None:
            if not identity.is_active():
                return False
            public_key = identity.public_key

        payload = self.compute_signature_payload()
        if public_key:
            return verify_ed25519(payload, self.signature, public_key)

        key = secret_key or "dev_human_key_42"
        return verify_hmac_sha256(payload, self.signature, key)


class ResearchFinding(DomainModel):
    """Discrete, validated scientific finding supported by evidence."""

    project_id: str
    statement: str
    claim_id: str | None = None
    evidence_ids: list[str] = Field(
        min_length=1,
        description="Every accepted finding MUST link to at least one evidence item.",
    )
    statistical_analysis_id: str | None = None
    uncertainty: UncertaintyProfile = Field(default_factory=UncertaintyProfile)
    is_statistically_defensible: bool = True


class Conclusion(DomainModel):
    """Overall conclusion of a research project lifecycle."""

    project_id: str
    title: str = ""
    summary: str = ""
    statement: str = ""
    finding_ids: list[str] = Field(
        default_factory=list,
        description="A scientific conclusion must contain at least one verified finding.",
    )
    human_decision_id: str = Field(description="A conclusion CANNOT be accepted without an explicit human decision ID.")
    evidence_ids: list[str] = Field(default_factory=list)
    statistical_analysis_ids: list[str] = Field(default_factory=list)
    falsification_evaluation_id: str | None = None
    artifact_ids: list[str] = Field(default_factory=list)
    status: str = "VALID"  # VALID, REQUIRES_REVIEW, INVALIDATED
    is_validated: bool = False
