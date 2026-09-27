# Persistence & Transaction Architecture (Section 36, 37)

ResearchForge strictly differentiates between transactional state persistence, outbox event publication, and append-only audit provenance.

---

## 1. Architectural Separation

```text
+------------------------+      +---------------------------+      +-------------------------+
|     Domain Model       | ---> |    Repository Interface   | ---> |  Transactional DB (SQL) |
| (Entities, Aggregates) |      | (Load, Save with Version) |      |  (PostgreSQL / SQLite)  |
+------------------------+      +---------------------------+      +-------------------------+
           │                                                                    │
           │ (Emits Mutation Event)                                             │
           ▼                                                                    ▼
+------------------------+                                         +-------------------------+
|   Outbox / Event Bus   | ──────────────────────────────────────> | Provenance Ledger (DAG) |
| (Atomic State Delivery)|                                         | (provenance.jsonl)      |
+------------------------+                                         +-------------------------+
```

---

## 2. Consistency & Outbox Guarantees

1. **Transactional Integrity**: Database state mutations and their corresponding provenance events are committed within the same database transaction via `UnitOfWork` to prevent database-without-provenance or provenance-without-database anomalies.
2. **Primary Storage**: The `provenance_events` table serves as the authoritative source of truth. JSONL files act as export/distribution projections.
3. **Audit vs Operational State**: The Provenance Ledger records immutable historical events. If a transactional rollback occurs, an explicit `RUN_CANCELED` or `TRANSACTION_ABORTED` event is appended; historical events are never deleted or rewritten.
4. **Optimistic Locking**: Every aggregate root incrementing its `version` guarantees that concurrent processes cannot overwrite stale states.
