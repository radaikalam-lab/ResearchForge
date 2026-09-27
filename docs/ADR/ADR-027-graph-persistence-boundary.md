# ADR-027: Graph as Authoritative Persistence Boundary

## Status
Accepted

## Date
2026-09-27

## Context
In ResearchForge, the semantic graph is the authoritative communication boundary between scientific domain semantics and persistence. Relational databases (PostgreSQL/SQLite) serve as the physical storage backend rather than the definer of scientific semantics.

## Decision
1. **Graph Persistence Port**:
   - Introduce `GraphPersistencePort` protocol defining `persist_graph`, `load_graph`, `append_graph_delta`, `load_subgraph`, `graph_exists`, `get_graph_version`, and `verify_graph_integrity`.
2. **Relational Adapter**:
   - Implement `GraphPersistenceAdapter` backed by `graph_nodes`, `graph_edges`, `graph_metadata`, and `graph_deltas` tables.
3. **Graph Delta Model**:
   - Support deterministic incremental updates via `GraphDelta` (`ADD_NODE`, `UPDATE_NODE`, `REMOVE_NODE`, `ADD_EDGE`, `REMOVE_EDGE`), validated before persistence.
4. **UnitOfWork Transaction Integrity**:
   - Semantic graph persistence, domain entity persistence, and provenance event appending execute within a unified atomic transaction.
5. **Fail-Closed Verification**:
   - When loading graphs from storage, nodes, edges, cardinalities, and canonical content hashes are strictly validated. Corrupted graphs fail closed.

## Consequences
- Domain logic is decoupled from SQL schemas, table layouts, and joins.
- Strict consistency between semantic graph state and append-only provenance event streams.
- Hash-verified round-trip persistence: `canonical_hash(graph) == canonical_hash(load_graph(graph_id))`.
