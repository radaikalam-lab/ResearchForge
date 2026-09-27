# RESEARCHFORGE GRAPH INVARIANTS (v0.4)

## 1. Formal Invariant Definitions

The ResearchForge Semantic Graph enforces 10 machine-verifiable invariants to preserve structural integrity, deterministic reproducibility, and scientific validity.

---

## 2. Invariant Catalog

### Invariant 1: Closed Controlled Vocabulary
* **Rule**: All node types MUST belong to `ResearchNodeType`, and all edge relation types MUST belong to `ResearchRelationType`.
* **Validation**: Free-form string types or unmapped enumerations are rejected immediately with `InvalidNodeError` or `InvalidEdgeError`.

### Invariant 2: Referential Integrity (No Dangling Edges)
* **Rule**: For every edge $E = (u, v, r)$, both source node $u$ and target node $v$ MUST exist within the graph's node table (`graph.nodes`).
* **Validation**: If $u \notin graph.nodes$ or $v \notin graph.nodes$, validation fails with `DanglingEdgeError`.

### Invariant 3: Type Compatibility
* **Rule**: For every edge $E = (u, v, r)$, $type(u) \in allowed\_sources(r)$ and $type(v) \in allowed\_targets(r)$.
* **Validation**: Violations fail with `InvalidEdgeError` specifying the incompatible source or target node type.

### Invariant 4: Canonical Directionality
* **Rule**: Every semantic relation is inherently directed ($u \xrightarrow{r} v$). Reverse traversal is supported via query APIs (`GraphQueryEngine.incoming`), but reverse edges cannot be synthesized without explicit semantic justification.
* **Validation**: Edge orientation must match ontology definitions (e.g. `Evidence -> SUPPORTS -> Claim`, never `Claim -> SUPPORTS -> Evidence`).

### Invariant 5: Cardinality Compliance
* **Rule**: Graph topologies must strictly respect declared relationship cardinalities:
  * `ONE_TO_ONE`: Source has $\le 1$ outgoing edge of type $r$; target has $\le 1$ incoming edge of type $r$.
  * `ONE_TO_MANY`: Source may have $N$ outgoing edges; target has $\le 1$ incoming edge of type $r$.
  * `MANY_TO_ONE`: Source has $\le 1$ outgoing edge of type $r$; target may have $N$ incoming edges.
  * `MANY_TO_MANY`: Arbitrary cardinality permitted within referential bounds.
* **Validation**: Violations fail with `CardinalityViolationError`.

### Invariant 6: No Semantic Aliasing
* **Rule**: Distinct relation types must not represent identical semantics. Synonyms must be mapped to the canonical relation enum before insertion.
* **Validation**: Duplicate parallel edges between identical endpoints with identical relations are rejected.

### Invariant 7: Provenance Traceability
* **Rule**: When `rule.requires_provenance == True`, every edge MUST record a non-empty `provenance_ref` pointing to a valid `ProvenanceEvent.event_id`.
* **Validation**: Edge validation reports missing provenance references.

### Invariant 8: Authority Isolation
* **Rule**: Presence in the Semantic Graph conveys epistemic relationships, not execution or administrative authority. State transitions and experiment executions require explicit UnitOfWork authorizations and signed events.

### Invariant 9: Deterministic Serialization & Hashing
* **Rule**: Two graphs with identical nodes and edges must produce identical canonical JSON strings and identical SHA-256 content hashes, regardless of in-memory insertion order.
* **Validation**: Tested via `compute_graph_content_hash(graph)`.

### Invariant 10: Replay Purity
* **Rule**: Reconstructing the semantic graph from an append-only provenance event stream must be purely functional, offline, deterministic, side-effect free, and require no network or LLM access.
* **Validation**: Validated across all replay regression test suites.
