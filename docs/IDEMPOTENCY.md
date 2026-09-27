# RESEARCHFORGE — IDEMPOTENCY SPECIFICATION

## 1. Principle

All state-mutating commands (trajectory executions, experiment runs, project initializations) support optional client-provided idempotency keys (`Idempotency-Key` HTTP header or CLI `--idempotency-key` flag).

---

## 2. Mechanics

1. **Storage**: The `idempotency_records` database table stores `(key, operation, entity_id, response_payload_json, created_at)`.
2. **Transaction Integration**: Idempotency records are persisted within the same database transaction as the primary mutation.
3. **Behavior on Retry**:
   * If a command with an existing key is received, the service bypasses re-execution.
   * The previously committed `entity_id` and cached response payload are returned immediately.
   * No duplicate entities, duplicate runs, or redundant provenance events are generated.
