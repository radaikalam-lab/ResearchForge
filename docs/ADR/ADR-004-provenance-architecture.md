# ADR-004: Provenance Architecture

## Status
Accepted

## Context
Scientific reproducibility requires an unbroken audit trail of every source, transformation, computation, and decision.

## Decision
Implement an append-only, cryptographic JSONL provenance ledger (`ProvenanceLedger`). Every meaningful operation records an immutable `ProvenanceEvent` containing actor, timestamp, input/output references, parameters, and content hashes.

## Consequences
- Full research trajectory replayability.
- Automatic verification of scientific lineage.
