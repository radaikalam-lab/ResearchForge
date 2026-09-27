# Provenance Event Schema & Cryptographic Ledger Specification (Section 15, 16, 17, 18, 19)

ResearchForge implements an append-only cryptographic event ledger structured as a Merkle DAG.

---

## 1. Canonical Event Schema (`ProvenanceEvent`)

```json
{
  "event_id": "prov_01j7abc12345",
  "event_type": "HYPOTHESIS_FORMED",
  "schema_version": "1.1.0",
  "timestamp": "2026-09-27T12:00:00.000000Z",
  "actor": "RESEARCHFORGE",
  "actor_tier": "TIER_2_COMPUTATION",
  "actor_id": "system_engine",
  "session_id": "sess_89ab...",
  "operation": "HYPOTHESIS_FORMED",
  "entity_id": "hyp_01j7...",
  "entity_type": "Hypothesis",
  "entity_refs": ["hyp_01j7..."],
  "input_refs": ["gap_01j7...", "evid_01j7..."],
  "output_refs": ["hyp_01j7..."],
  "parameters": {
    "mechanism": "Strain-induced bandgap deformation",
    "falsification_criteria_count": 2
  },
  "redaction_metadata": {
    "redacted_fields": [],
    "policy": "SECRET_REDACTION_V1"
  },
  "environment": {
    "os": "windows",
    "python": "3.13"
  },
  "software_version": "0.1.0",
  "provider_identity": "local_engine",
  "parent_event_hash": "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
  "event_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
}
```

---

## 2. Cryptographic Hash Calculation (Section 17)

```text
event_hash = SHA256(canonical_event_payload + parent_event_hash)
```

* **Canonical Payload**: Serialized via RFC 8785 JSON Canonicalization Scheme (sorted keys, UTF-8, no whitespace, `event_hash` excluded).
* **Secret Redaction**: Credentials, tokens, and authorization headers are cleansed **BEFORE** hashing, and recorded in `redaction_metadata`.

---

## 3. Signed Checkpoints (Section 18)

A `Checkpoint` locks the state of the ledger up to a specific event count:
```json
{
  "checkpoint_id": "chk_01j7abc...",
  "latest_event_hash": "e3b0c442...",
  "event_count": 42,
  "timestamp": "2026-09-27T12:30:00Z",
  "ledger_version": "1.0.0",
  "signature": "sig_..."
}
```
Tampering, truncating, or altering prior events immediately causes checkpoint verification failure.
