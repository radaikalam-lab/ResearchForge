# ADR-018: Transactional Provenance Storage

## Status
Accepted (Phase 0.2)

## Context
During Phase 0.1 review, it was identified that provenance events and domain mutations must participate in atomic database transactions to guarantee that domain state is never committed without an accompanying tamper-evident provenance log entry.

## Decision
1. Introduce the `provenance_events` table as the primary source of truth for the provenance ledger.
2. Coordinate all domain mutations and event ledger appends through a unified `UnitOfWork`.
3. In the event of an unhandled domain exception or DB error, both domain changes and provenance events are rolled back atomically.
4. JSONL files become export formats rather than the primary operational source of truth.

## Consequences
* Guarantees 100% synchronization between domain entity states and the cryptographic provenance hash chain.
* Eliminates phantom domain states without audit lineage.
