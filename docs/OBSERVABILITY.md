# RESEARCHFORGE — OBSERVABILITY & STRUCTURED LOGGING

## 1. Structured Log Standard

All major lifecycle operations, state transitions, API requests, and sandbox executions emit structured log events containing standard context fields:

```json
{
  "timestamp": "2026-09-27T08:12:00.000000Z",
  "request_id": "req_a1b2c3d4",
  "project_id": "proj_12345678",
  "thread_id": "th_87654321",
  "entity_id": "exp_abcdef12",
  "operation": "EXPERIMENT_EXECUTED",
  "actor": "RESEARCHFORGE",
  "duration_ms": 142.5,
  "status": "SUCCESS",
  "error_type": null
}
```

---

## 2. Privacy & Secret Protections

1. **No Secrets in Logs**: Cryptographic private keys, API secrets, and raw authentication tokens are never written to log outputs or persisted provenance parameters.
2. **Deterministic Hashes**: Heavy payloads and data matrices are referenced by SHA-256 content hashes rather than dumping full payload bytes into observability streams.
