# ADR-025: Formal Semantic Graph Contract and Domain Ontology

## Status
Accepted

## Date
2026-09-27

## Context
ResearchForge Phase 1 successfully delivered Literature and Evidence Intelligence, completing a deterministic pipeline from literature ingestion to evidence synthesis, claim binding, contradiction detection, gap discovery, and hypothesis formation.

Prior to Phase 2 (Experiment Execution & Falsification), the system required a formal Semantic Graph Contract to make epistemic relationships explicit, machine-validatable, and contract-governed without conflating domain meaning, provenance origins, or execution sequencing.

## Decision
1. **Semantic Graph as In-Memory Contract**:
   - Introduce `ResearchGraph`, `ResearchNode`, and `ResearchEdge` in `backend/researchforge/domain/graph/`.
   - Maintain relational storage (SQLite/PostgreSQL) as the persistence layer. No graph databases (e.g. Neo4j, RDF triple stores) are introduced.
2. **Strict Graph Layer Decoupling**:
   - *Semantic Graph*: Defines epistemic meaning ("What is related to what?").
   - *Provenance Graph*: Captures immutable creation history ("How did this entity come into existence?").
   - *Execution Graph*: Governs orchestration paths ("What execution path occurred?").
3. **Ontological Governance**:
   - Establish closed vocabularies: `ResearchNodeType` (16 node types) and `ResearchRelationType` (18 relation types).
   - Enforce machine-verifiable invariants (type compatibility, referential integrity, canonical directionality, cardinality constraints, deterministic serialization).
4. **Replay Integration**:
   - Integrate `ResearchGraph` directly into `ReconstructedResearchState` during `ProvenanceReplayEngine.replay()`.
   - Preserve existing domain dictionary projections for complete backward compatibility.
5. **Epistemic Authority Boundary**:
   - Graph relationships cannot grant execution authority or declare scientific truth without cryptographically signed `HUMAN_DECISION` events.

## Consequences
### Positive
- Fully explicit, typed, machine-validatable epistemic relationships across the research lifecycle.
- Deterministic reconstruction of semantic graphs from append-only provenance event logs.
- Robust query primitives (`GraphQueryEngine`) for neighbor, incoming, outgoing, and path-existence lookups.
- 100% green test baseline with 110 passed unit/integration tests under `-W error`.

### Neutral / Trade-offs
- In-memory graph nodes reference domain entities rather than replicating full entity payloads. Full entity state is accessed via domain projections.
- SOURCED_FROM and other relations enforce cardinality checks at validation time.

## Compliance
- `pytest -v -W error` PASS (110 tests)
- `ruff check .` PASS
- `researchforge doctor --json` HEALTHY
