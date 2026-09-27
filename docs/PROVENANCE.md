# ResearchForge — Cryptographic Provenance Specification

## 1. Append-Only Provenance Model

Every domain entity mutation, computational run, literature query, and human decision emits an immutable `ProvenanceEvent` into an append-only ledger (`provenance.jsonl`).

```json
{
  "event_id": "prov_01j7abc123...",
  "timestamp": "2026-09-27T12:00:00Z",
  "actor": "HUMAN",
  "actor_id": "usr_lead_researcher",
  "operation": "DECISION_ACCEPTED",
  "entity_id": "concl_01j7...",
  "entity_type": "Conclusion",
  "input_refs": ["evid_01j7...", "stat_01j7..."],
  "output_refs": ["concl_01j7..."],
  "parameters": {
    "rationale": "Statistical significance verified (p < 0.001, d = 0.85)"
  },
  "content_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
  "parent_event_hash": "2c26b46b68ffc68ff99b453c1d30413413422d706483bfa0f98a5e886266e7ae",
  "software_version": "0.1.0"
}
```

---

## 2. Provenance Guarantees

1. **Hash Chaining**: Each event hashes its canonical payload along with the preceding `parent_event_hash`, forming a Merkle DAG.
2. **Replayability**: Any research run can be deterministically replayed and verified from the raw ledger.
3. **Actor Classification**: Actors are strictly categorized as `HUMAN`, `RESEARCHFORGE`, `COGNITIA`, `LLM`, `PROVIDER`, or `EXTERNAL_SYSTEM`.
4. **Secret Scrubbing**: API keys, passwords, and sensitive system paths are automatically redacted prior to hashing and ledger persistence.
