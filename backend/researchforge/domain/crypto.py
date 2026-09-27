"""Cryptographic primitives for ResearchForge: Ed25519 asymmetric signatures and canonical serialization."""

import base64
import hashlib
import hmac
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric import ed25519

from researchforge.domain.base import canonical_json_dumps


def generate_ed25519_keypair() -> tuple[str, str]:
    """Generate a new Ed25519 private and public key encoded as base64 strings."""
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    priv_bytes = private_key.private_bytes_raw()
    pub_bytes = public_key.public_bytes_raw()

    return base64.b64encode(priv_bytes).decode("ascii"), base64.b64encode(pub_bytes).decode("ascii")


def sign_ed25519(payload: str | bytes, private_key_b64: str) -> str:
    """Sign payload using Ed25519 private key, returning base64 signature."""
    if isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
    else:
        payload_bytes = payload

    priv_bytes = base64.b64decode(private_key_b64.encode("ascii"))
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(priv_bytes)
    sig_bytes = private_key.sign(payload_bytes)
    return base64.b64encode(sig_bytes).decode("ascii")


def verify_ed25519(payload: str | bytes, signature_b64: str, public_key_b64: str) -> bool:
    """Verify Ed25519 signature against payload and base64 public key."""
    if isinstance(payload, str):
        payload_bytes = payload.encode("utf-8")
    else:
        payload_bytes = payload
    try:
        pub_bytes = base64.b64decode(public_key_b64.encode("ascii"))
        sig_bytes = base64.b64decode(signature_b64.encode("ascii"))
        public_key = ed25519.Ed25519PublicKey.from_public_bytes(pub_bytes)
        public_key.verify(sig_bytes, payload_bytes)
        return True
    except (InvalidSignature, Exception):
        return False


def sign_hmac_sha256(payload: str, secret_key: str) -> str:
    """Compute HMAC-SHA256 hex digest for payload."""
    return hmac.new(secret_key.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def verify_hmac_sha256(payload: str, signature: str, secret_key: str) -> bool:
    """Verify HMAC-SHA256 hex signature using constant-time comparison."""
    expected = sign_hmac_sha256(payload, secret_key)
    return hmac.compare_digest(signature, expected)


def compute_content_sha256(data: str | bytes | dict[str, Any]) -> str:
    """Compute SHA-256 hash of string, bytes, or canonical JSON dictionary."""
    if isinstance(data, dict):
        raw_bytes = canonical_json_dumps(data).encode("utf-8")
    elif isinstance(data, str):
        raw_bytes = data.encode("utf-8")
    else:
        raw_bytes = data
    return hashlib.sha256(raw_bytes).hexdigest()
