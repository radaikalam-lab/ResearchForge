# ADR-015: Canonical Provenance Event Model

## Status
Accepted

## Context
Provenance events without canonical schemas and verifiable checkpoints risk ambiguity, inconsistent hash calculation, and undetected tampering or truncation.

## Decision
Formalize `ProvenanceEvent` with 24 distinct typed event types, canonical RFC 8785 JSON payload hashing (`SHA256(canonical_payload + parent_event_hash)`), secret scrubbing prior to hashing, and signed periodic `Checkpoint` records.

## Consequences
- Full cryptographic auditability and deterministic tamper detection.
