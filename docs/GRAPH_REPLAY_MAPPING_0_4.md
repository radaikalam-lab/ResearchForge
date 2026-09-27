# RESEARCHFORGE GRAPH REPLAY MAPPING (v0.4)

## 1. Provenance Event to Semantic Graph Mapping

The ResearchForge Provenance Replay Engine (`ProvenanceReplayEngine`) translates append-only provenance event logs into both typed domain entity indexes and a validated `ResearchGraph`.

---

## 2. Event Mapping Matrix

| Provenance Event (`operation`) | Entity Created / Updated | Semantic Graph Node Added | Semantic Graph Edge Added |
|---|---|---|---|
| `PROJECT_CREATED` | `ResearchProject` | `PROJECT` (id = `entity_id`) | - |
| `QUESTION_DEFINED` | `ResearchQuestion` | `QUESTION` (id = `entity_id`) | `PROJECT -[ASKS]-> QUESTION` |
| `SOURCE_INGESTED` | `Source` | `SOURCE` (id = `entity_id`) | - |
| `CLAIM_CREATED` | `Claim` | `CLAIM` (id = `entity_id`) | `CLAIM -[DERIVED_FROM]-> SOURCE` (if source referenced) |
| `CLAIM_BOUND` | `EvidenceClaimBinding` | `EVIDENCE`, `CLAIM` (ensured) | `EVIDENCE -[SUPPORTS / REFUTES]-> CLAIM` |
| `CONTRADICTION_IDENTIFIED` | `PotentialContradiction` | `CONTRADICTION` (id = `entity_id`) | `CONTRADICTION -[CONTRADICTS]-> CLAIM` (for both claim A & B) |
| `EVIDENCE_EXTRACTED` | `Evidence` | `EVIDENCE` (id = `entity_id`) | `EVIDENCE -[SOURCED_FROM]-> SOURCE` |
| `GAP_IDENTIFIED` | `ResearchGap` | `RESEARCH_GAP` (id = `entity_id`) | `RESEARCH_GAP -[DERIVED_FROM]-> EVIDENCE` |
| `HYPOTHESIS_FORMED` | `Hypothesis` | `HYPOTHESIS` (id = `entity_id`) | `RESEARCH_GAP -[MOTIVATES]-> HYPOTHESIS` |
| `EXPERIMENT_DESIGNED` | `Experiment` | `EXPERIMENT` (id = `entity_id`) | `EXPERIMENT -[TESTS]-> HYPOTHESIS` |
| `RUN_STARTED` / `COMPLETED` | `ExperimentRun` | `EXPERIMENT_RUN` (id = `entity_id`) | `EXPERIMENT -[PRODUCES]-> EXPERIMENT_RUN` |
| `FALSIFICATION_EVALUATED` | `FalsificationEvaluation` | `FALSIFICATION_EVALUATION` (id = `entity_id`) | `FALSIFICATION_EVALUATION -[EVALUATES]-> HYPOTHESIS` |
| `DECISION_ACCEPTED` | `HumanDecision` | `HUMAN_DECISION` (id = `entity_id`) | `TARGET_ENTITY -[INFORMS]-> HUMAN_DECISION` |
| `CONCLUSION_ACCEPTED` | `Conclusion` | `CONCLUSION` (id = `entity_id`) | `HUMAN_DECISION -[ESTABLISHES]-> CONCLUSION` |
| `ARTIFACT_GENERATED` | `ResearchArtifact` | `ARTIFACT` (id = `entity_id`) | `PROJECT -[MATERIALIZES_AS]-> ARTIFACT` |

---

## 3. Replay Verification Pipeline

Replay operates in three deterministic stages:

```
[Provenance Event Log]
         ↓
1. Event Ingestion & State Accumulation (ReconstructedResearchState)
         ↓
2. Semantic Graph Node & Edge Assembly (ResearchGraph)
         ↓
3. Contract Invariant Validation (validate_graph())
```

Replay guarantees:
* **Determinism**: Identical event streams yield identical graph nodes, edges, and content hashes.
* **Hermetic Execution**: Zero LLM calls, zero network calls, zero file system writes.
* **Backward Compatibility**: All existing Phase 0.1–Phase 1 domain entity projections (`state.projects`, `state.evidence`, etc.) remain fully accessible and tested.
