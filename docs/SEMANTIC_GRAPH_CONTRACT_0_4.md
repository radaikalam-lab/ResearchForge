# RESEARCHFORGE SEMANTIC GRAPH CONTRACT (v0.4)

## 1. Executive Summary & Purpose

The **Semantic Graph Contract** establishes a formal, machine-validatable, typed ontological layer for ResearchForge prior to Phase 2 (Experiment Execution).

In ResearchForge:
> **The Semantic Graph Contract defines the meaning and allowable relationships of the research domain. Domain entities, provenance replay, persistence projections, APIs, and execution workflows must conform to that semantic contract.**

```
SEMANTIC VOCABULARY
        ↓
SEMANTIC GRAPH CONTRACT
        ↓
DOMAIN MODEL
        ↓
STATE / AUTHORITY MODEL
        ↓
PROVENANCE / EXECUTION
        ↓
PERSISTENCE PROJECTIONS
        ↓
API / CLI
```

The Semantic Graph is an **in-memory, deterministic domain abstraction**, not a graph database requirement. Relational storage (PostgreSQL/SQLite) remains the persistence backend, and domain aggregates remain the execution substrate.

---

## 2. Distinction Between Graph Concepts

ResearchForge maintains a strict boundary across three distinct graph layers:

| Graph Layer | Core Question | Architectural Subsystem | Mutability / Lifecycle |
|---|---|---|---|
| **Semantic Graph** | *What is related to what?* (Epistemic assertions, evidence bindings, contradiction relations, gap motivations) | `researchforge.domain.graph` | Reconstructed via replay; validated by `validate_graph()` |
| **Provenance Graph** | *How did this assertion/entity come into existence?* (Causal event lineage, actors, cryptographic hashes, input refs) | `researchforge.provenance` | Append-only event store; cryptographic SHA-256 chain |
| **Execution Graph** | *What execution path occurred?* (Workflow task DAGs, sandbox runs, parameter variations, evaluations) | `researchforge.execution` | Orchestration & runtime sandbox state machines |

Semantic relationships must **never** be collapsed into provenance events, nor should execution order be confused with epistemic derivation.

---

## 3. Node Vocabulary (`ResearchNodeType`)

The semantic graph recognizes 16 closed node types representing first-class domain entities:

| Node Type | Domain Entity Class | Epistemic Description |
|---|---|---|
| `PROJECT` | `ResearchProject` | Root container defining overall scientific campaign |
| `THREAD` | `ResearchThread` | Concurrent or specialized research line |
| `QUESTION` | `ResearchQuestion` | Formalized query driving inquiry and boundaries |
| `SOURCE` | `Source` | External literature paper, preprint, or dataset |
| `EVIDENCE_FRAGMENT` | `EvidenceFragment` | Atomic excerpt or verifiable factual snippet |
| `CLAIM` | `Claim` | Formal assertion extracted from literature or derived from data |
| `EVIDENCE` | `Evidence` | Synthesized empirical aggregate with uncertainty profile |
| `BINDING` | `EvidenceClaimBinding` | Explicit epistemic binding between evidence and claim |
| `CONTRADICTION` | `PotentialContradiction` | Detected discrepancy between conflicting claims |
| `RESEARCH_GAP` | `ResearchGap` | Validated void in existing scientific knowledge |
| `HYPOTHESIS` | `Hypothesis` | Falsifiable proposition addressing a research gap |
| `EXPERIMENT` | `Experiment` | Protocol designed to test a hypothesis |
| `EXPERIMENT_RUN` | `ExperimentRun` | Deterministic execution instance of an experiment protocol |
| `FALSIFICATION_EVALUATION` | `FalsificationEvaluation` | Epistemic assessment of hypothesis refutation criteria |
| `HUMAN_DECISION` | `HumanDecision` | Cryptographically signed human review gate |
| `CONCLUSION` | `Conclusion` | Scientifically accepted finding backed by decision |
| `ARTIFACT` | `ResearchArtifact` | Reproducible publication artifact or manuscript package |

---

## 4. Relationship Vocabulary (`ResearchRelationType`)

18 controlled relationship types with strictly governed direction, cardinalities, and allowed endpoints:

| Relation Type | Source Type(s) | Target Type(s) | Cardinality | Semantic Meaning |
|---|---|---|---|---|
| `CONTAINS` | `PROJECT` | `THREAD`, `ARTIFACT` | `ONE_TO_MANY` | Hierarchical ownership within a research project |
| `HAS_THREAD` | `PROJECT` | `THREAD` | `ONE_TO_MANY` | Project thread allocation |
| `ASKS` | `PROJECT`, `THREAD` | `QUESTION` | `ONE_TO_MANY` | Formal research question posed by project/thread |
| `SOURCED_FROM` | `EVIDENCE`, `EVIDENCE_FRAGMENT`, `CLAIM` | `SOURCE` | `MANY_TO_ONE` | Grounding of claims/evidence in primary literature |
| `CONTAINS_EVIDENCE` | `SOURCE`, `EVIDENCE` | `EVIDENCE_FRAGMENT` | `ONE_TO_MANY` | Aggregation of fragments into evidence or source |
| `SUPPORTS` | `EVIDENCE`, `EVIDENCE_FRAGMENT`, `CLAIM` | `CLAIM`, `HYPOTHESIS` | `MANY_TO_MANY` | Epistemic backing strengthening a claim or hypothesis |
| `REFUTES` | `EVIDENCE`, `EVIDENCE_FRAGMENT`, `CLAIM` | `CLAIM`, `HYPOTHESIS` | `MANY_TO_MANY` | Epistemic refutation weakening a claim or hypothesis |
| `QUALIFIES` | `EVIDENCE`, `CLAIM`, `CONTRADICTION` | `CLAIM`, `HYPOTHESIS` | `MANY_TO_MANY` | Scope boundary or contextual qualification |
| `CONTRADICTS` | `CLAIM`, `CONTRADICTION` | `CLAIM` | `MANY_TO_MANY` | Mutual exclusion or discrepancy between claims |
| `ADDRESSES` | `RESEARCH_GAP`, `HYPOTHESIS` | `QUESTION`, `RESEARCH_GAP` | `MANY_TO_MANY` | Direct investigative response to question or gap |
| `MOTIVATES` | `QUESTION`, `CONTRADICTION`, `RESEARCH_GAP` | `RESEARCH_GAP`, `HYPOTHESIS` | `MANY_TO_MANY` | Epistemic driver for new inquiry or hypothesis |
| `DERIVED_FROM` | `CLAIM`, `EVIDENCE`, `RESEARCH_GAP` | `SOURCE`, `EVIDENCE_FRAGMENT`, `EVIDENCE` | `MANY_TO_MANY` | Extraction or analytical derivation from prior entities |
| `TESTS` | `EXPERIMENT` | `HYPOTHESIS` | `MANY_TO_ONE` | Empirical protocol designed to falsify hypothesis |
| `PRODUCES` | `EXPERIMENT`, `EXPERIMENT_RUN` | `EXPERIMENT_RUN`, `ARTIFACT` | `ONE_TO_MANY` | Generation of execution runs or research artifacts |
| `EVALUATES` | `FALSIFICATION_EVALUATION` | `HYPOTHESIS`, `EXPERIMENT_RUN` | `MANY_TO_ONE` | Rigorous falsification evaluation of run/hypothesis |
| `INFORMS` | `FALSIFICATION_EVALUATION`, `HYPOTHESIS`, `EVIDENCE` | `HUMAN_DECISION` | `MANY_TO_MANY` | Epistemic inputs provided to human reviewer |
| `ESTABLISHES` | `HUMAN_DECISION` | `CONCLUSION` | `ONE_TO_ONE` | Authoritative human ratification of a conclusion |
| `MATERIALIZES_AS` | `PROJECT`, `CONCLUSION` | `ARTIFACT` | `ONE_TO_MANY` | Synthesis into persistent publication package |

---

## 5. Contract Invariants

1. **No Ad-Hoc Types**: Any node or relation not in `ResearchNodeType` or `ResearchRelationType` is rejected with `GraphValidationError`.
2. **Referential Integrity**: An edge cannot reference non-existent source or target node IDs (`DanglingEdgeError`).
3. **Type Compatibility**: Edges connecting unpermitted source/target type combinations trigger `InvalidEdgeError`.
4. **Cardinality Bounds**: Violations of `ONE_TO_ONE`, `ONE_TO_MANY`, or `MANY_TO_ONE` trigger `CardinalityViolationError`.
5. **Deterministic Serialization**: Canonical JSON serialization guarantees identical SHA-256 hashes across replays.
6. **Cognitia Epistemic Boundary**: Semantic graph edges never grant automated execution or scientific ratification authority without explicit `HUMAN_DECISION`.
