# RESEARCHFORGE — PHASE 0.4 SEMANTIC GRAPH & ONTOLOGY REPORT

## 1. Executive Summary

Phase 0.4 (Semantic Graph Contract & Ontology Retrofit) has been successfully designed, implemented, and verified for ResearchForge.

The implementation introduces a formal, typed, machine-validatable semantic graph abstraction and research domain ontology that models epistemic connections across the entire scientific discovery lifecycle without replacing relational persistence or destabilizing the Phase 1 operational baseline.

---

## 2. Verification Baseline Summary

| Subsystem / Metric | Status | Result |
|---|---|---|
| **Semantic Graph Contract** | **PASS** | 16 Node Types, 18 Relation Types, Invariant Validator |
| **Research Ontology** | **PASS** | `ONTOLOGY_RELATION_RULES` with Cardinality & Directionality Matrix |
| **Graph Invariants** | **PASS** | Type compatibility, Referential integrity, Cardinality bounds, Determinism |
| **Graph Replay Integration** | **PASS** | ProvenanceReplayEngine deterministically reconstructs validated `ResearchGraph` |
| **Phase 1 Baseline** | **PASS** | Literature & Evidence pipeline fully preserved & verified |
| **Test Suite** | **PASS** | **110 passed, 0 failed, 0 errors, 0 warnings under `-W error`** |
| **Ruff Linter** | **PASS** | `ruff check .` clean |
| **Doctor Diagnostic** | **HEALTHY** | All 11 registered contracts loaded & verified |
| **Cognitia Boundary** | **PASS** | Epistemic novelty decoupled from production/scientific authority |

---

## 3. Existing Semantic Inventory

Inspection of the Phase 0.3/Phase 1 codebase identified the following entities and their semantic roles:
1. **`ResearchProject`**: Root container defining scientific scope and state machine lifecycle.
2. **`ResearchThread`**: Concurrent or specialized investigative paths.
3. **`ResearchQuestion`**: Formal scientific query defining variables and scope boundaries.
4. **`Source`**: External paper, preprint, or literature record.
5. **`EvidenceFragment`**: Verifiable atomic text/data extracted from literature sources.
6. **`Claim`**: Structured assertion with subject-predicate-object and parameter bounds.
7. **`Evidence`**: Synthesized multi-fragment empirical aggregate with uncertainty profiles.
8. **`EvidenceClaimBinding`**: Explicit association linking evidence to claims with `SUPPORTS` or `REFUTES`.
9. **`PotentialContradiction`**: Identified discrepancies between conflicting empirical claims.
10. **`ResearchGap`**: Validated void in existing literature and empirical evidence.
11. **`Hypothesis`**: Falsifiable proposition addressing research gaps with explicit refutation thresholds.
12. **`Experiment`**: Protocol designed to execute empirical falsification tests.
13. **`ExperimentRun`**: Reproducible run execution record with random seed and output hash.
14. **`FalsificationEvaluation`**: Evaluation assessing hypothesis refutation status.
15. **`HumanDecision`**: Cryptographically signed human authorization.
16. **`Conclusion`**: Validated finding ratified by human review.
17. **`ResearchArtifact`**: Verified reproducible publication package.

---

## 4. Final Node & Relationship Vocabulary

### 4.1 Node Vocabulary (`ResearchNodeType`)
`PROJECT`, `THREAD`, `QUESTION`, `SOURCE`, `EVIDENCE_FRAGMENT`, `CLAIM`, `EVIDENCE`, `BINDING`, `CONTRADICTION`, `RESEARCH_GAP`, `HYPOTHESIS`, `EXPERIMENT`, `EXPERIMENT_RUN`, `FALSIFICATION_EVALUATION`, `HUMAN_DECISION`, `CONCLUSION`, `ARTIFACT`.

### 4.2 Relationship Vocabulary (`ResearchRelationType`)
`CONTAINS`, `HAS_THREAD`, `ASKS`, `SOURCED_FROM`, `CONTAINS_EVIDENCE`, `SUPPORTS`, `REFUTES`, `QUALIFIES`, `CONTRADICTS`, `ADDRESSES`, `MOTIVATES`, `DERIVED_FROM`, `TESTS`, `PRODUCES`, `EVALUATES`, `INFORMS`, `ESTABLISHES`, `MATERIALIZES_AS`.

---

## 5. Cardinality & Directionality Matrix

| Relation | Direction | Cardinality | Semantic Requirement |
|---|---|---|---|
| `CONTAINS` | `PROJECT -> THREAD / ARTIFACT` | `ONE_TO_MANY` | Container membership |
| `HAS_THREAD` | `PROJECT -> THREAD` | `ONE_TO_MANY` | Thread allocation |
| `ASKS` | `PROJECT / THREAD -> QUESTION` | `ONE_TO_MANY` | Formal inquiry definition |
| `SOURCED_FROM` | `EVIDENCE / CLAIM -> SOURCE` | `MANY_TO_ONE` | Grounding in literature |
| `CONTAINS_EVIDENCE` | `SOURCE / EVIDENCE -> FRAGMENT` | `ONE_TO_MANY` | Granular fragment composition |
| `SUPPORTS` | `EVIDENCE / CLAIM -> CLAIM / HYPOTHESIS` | `MANY_TO_MANY` | Epistemic affirmation |
| `REFUTES` | `EVIDENCE / CLAIM -> CLAIM / HYPOTHESIS` | `MANY_TO_MANY` | Epistemic refutation |
| `QUALIFIES` | `EVIDENCE / CLAIM -> CLAIM / HYPOTHESIS` | `MANY_TO_MANY` | Scope boundary qualification |
| `CONTRADICTS` | `CLAIM / CONTRADICTION -> CLAIM` | `MANY_TO_MANY` | Discrepancy / opposition |
| `ADDRESSES` | `GAP / HYPOTHESIS -> QUESTION / GAP` | `MANY_TO_MANY` | Direct response to void/question |
| `MOTIVATES` | `QUESTION / CONTRADICTION / GAP -> GAP / HYPOTHESIS` | `MANY_TO_MANY` | Epistemic driver |
| `DERIVED_FROM` | `CLAIM / EVIDENCE / GAP -> SOURCE / FRAGMENT / EVIDENCE` | `MANY_TO_MANY` | Analytical lineage |
| `TESTS` | `EXPERIMENT -> HYPOTHESIS` | `MANY_TO_ONE` | Falsification protocol |
| `PRODUCES` | `EXPERIMENT / RUN -> RUN / ARTIFACT` | `ONE_TO_MANY` | Execution output |
| `EVALUATES` | `FALSIFICATION_EVALUATION -> HYPOTHESIS / RUN` | `MANY_TO_ONE` | Falsification assessment |
| `INFORMS` | `EVALUATION / HYPOTHESIS / EVIDENCE -> HUMAN_DECISION` | `MANY_TO_MANY` | Reviewer evidence packet |
| `ESTABLISHES` | `HUMAN_DECISION -> CONCLUSION` | `ONE_TO_ONE` | Human scientific ratification |
| `MATERIALIZES_AS` | `PROJECT / CONCLUSION -> ARTIFACT` | `ONE_TO_MANY` | Persistent artifact packaging |

---

## 6. Graph Invariants & Validation

The contract validator (`validate_graph(graph)`) enforces 10 machine-verifiable invariants:
1. **Type Closedness**: Unrecognized node or relation types fail validation.
2. **Referential Integrity**: All edge endpoints must exist in `graph.nodes`.
3. **Type Compatibility**: Endpoints must match `allowed_sources` and `allowed_targets`.
4. **Canonical Direction**: Reverse traversal allowed only via query APIs; stored edges strictly directed.
5. **Cardinality Bounds**: Enforces `ONE_TO_ONE`, `ONE_TO_MANY`, `MANY_TO_ONE` constraints.
6. **No Semantic Aliasing**: Duplicate parallel edges rejected.
7. **Provenance Traceability**: Required provenance references verified.
8. **Authority Decoupling**: Graph relationships do not bypass human decision authority.
9. **Deterministic Serialization**: Canonical JSON with deterministic SHA-256 digests.
10. **Replay Purity**: Purely functional, offline, deterministic reconstruction.

---

## 7. Provenance Replay Integration

The Provenance Replay Engine (`ProvenanceReplayEngine.replay()`) reconstructs both:
1. The domain entity dictionaries (`state.projects`, `state.evidence`, `state.claims`, etc.) for direct domain access.
2. The typed, connected `ResearchGraph` (`state.semantic_graph`) representing the epistemic structure of the research.

Replaying a full Phase 1 Literature Trajectory builds a fully validated `ResearchGraph` with verified node and edge counts matching domain expectations.

---

## 8. Cognitia Authority Boundary

* The principle **Epistemic Novelty $\ne$ Production Authority** is preserved.
* Cognitia advisory insights may suggest semantic edges (e.g. `QUALIFIES`, `MOTIVATES`), but cannot transition project state or ratify conclusions without cryptographically signed `HUMAN_DECISION` records.

---

## 9. Tests Added & Coverage

Dedicated graph test suite created in `tests/graph/`:
- `tests/graph/test_semantic_graph_contract.py`: Ontology validation, node/edge mutations, traversal queries (`GraphQueryEngine`), and serialization roundtrips.
- `tests/graph/test_graph_invariants_and_validation.py`: Referential integrity, type compatibility errors, cardinality violations, and validation result reporting.
- `tests/graph/test_graph_replay_integration.py`: End-to-end provenance replay into a valid, verified `ResearchGraph`.

**Full Test Suite Result**:
```
pytest -v -W error: 110 passed in 60.64s
ruff check .: All checks passed!
researchforge doctor --json: HEALTHY
```

---

## 10. Phase 2 Readiness Recommendation

Phase 0.4 is **COMPLETE** and **VERIFIED**.

The Semantic Graph Contract and Ontology are comprehensive and provide typed primitives for:
* Experiment Design (`EXPERIMENT -[TESTS]-> HYPOTHESIS`)
* Execution Tracking (`EXPERIMENT -[PRODUCES]-> EXPERIMENT_RUN`)
* Falsification Evaluation (`FALSIFICATION_EVALUATION -[EVALUATES]-> HYPOTHESIS`)
* Human Ratification (`HUMAN_DECISION -[ESTABLISHES]-> CONCLUSION`)

ResearchForge is structurally and epistemically ready for **Phase 2 (Experiment Design, Execution & Falsification)**.
