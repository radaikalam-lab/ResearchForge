# ResearchForge — Domain Model

## 1. Domain Entities & Value Objects

The ResearchForge domain model reflects the scientific method with mathematical and computational precision. Every entity implements base fields: `id`, `schema_version`, `created_at`, `updated_at`, `provenance_id`, and `status`.

```text
+-----------------------------------------------------------------------------------+
|                                ResearchProject                                    |
|  - id: ProjectId                                                                  |
|  - title: str                                                                     |
|  - state: ResearchLifecycleState (State Machine)                                  |
|  - directional_spec: DirectionalSpecification                                     |
+-----------------------------------------------------------------------------------+
       |                    |                    |                   |
       v                    v                    v                   v
+--------------+    +---------------+    +---------------+    +-------------------+
|   Research   |    |   Research    |    |   Research    |    |     Research      |
|   Question   |    |   Objective   |    |  Constraint   |    |     Context       |
+--------------+    +---------------+    +---------------+    +-------------------+
       |
       v
+--------------+    +---------------+    +---------------+    +-------------------+
|    Source    |--->|     Paper     |--->|   Evidence    |--->| EvidenceFragment  |
+--------------+    +---------------+    +---------------+    +-------------------+
                                                 |
                                                 v
+------------------+    +---------------+    +---------------+
|  ResearchGap     |<---|  Hypothesis   |--->|  Assumption   |
+------------------+    +---------------+    +---------------+
                                |                    |
                                v                    v
                        +---------------+    +---------------+
                        | Falsification |    |  Prediction   |
                        |   Criterion   |    +---------------+
                        +---------------+
                                |
                                v
                        +---------------+    +---------------+
                        |  Experiment   |--->| ExperimentRun |
                        +---------------+    +---------------+
                                |                    |
                                v                    v
                        +---------------+    +---------------+
                        |  Simulation   |--->| SimulationRun |
                        +---------------+    +---------------+
                                                     |
                                                     v
                        +---------------+    +---------------+
                        |  Statistical  |--->| Falsification |
                        |   Analysis    |    |  Evaluation   |
                        +---------------+    +---------------+
                                                     |
                                                     v
                        +---------------+    +---------------+
                        | HumanDecision |--->|  Conclusion   |
                        +---------------+    +---------------+
                                                     |
                                                     v
                                             +---------------+
                                             |  Manuscript   |
                                             |  & Artifact   |
                                             +---------------+
```

---

## 2. Research Lifecycle State Machine

ResearchForge enforces a strict sequence of 17 lifecycle states:

```text
 1. DRAFT                     -> Initial creation
 2. QUESTION_DEFINED          -> Research question and boundaries articulated
 3. EVIDENCE_COLLECTION       -> Literature search and source acquisition
 4. EVIDENCE_STRUCTURED       -> Normalized evidence fragments extracted
 5. GAP_ANALYSIS              -> Formal research gaps identified
 6. HYPOTHESIS_FORMED         -> Falsifiable hypothesis formulated
 7. HYPOTHESIS_CRITIQUE       -> Epistemic critique via Cognitia / domain review
 8. EXPERIMENT_DESIGNED       -> Variables, protocols, and measurements planned
 9. EXPERIMENT_READY          -> Execution sandbox configured and validated
10. COMPUTATION_RUNNING       -> Deterministic simulation/experiment executing
11. RESULTS_AVAILABLE         -> Raw datasets and metrics stored
12. FALSIFICATION             -> Hypothesis tested against falsification criteria
13. EVIDENCE_EVALUATION       -> Synthesis of experiment data with prior evidence
14. HUMAN_REVIEW              -> Explicit human gatekeeper evaluation
15. CONCLUSION_ACCEPTED       -> Formal scientific claim accepted with provenance
16. ARTIFACT_GENERATION       -> Figures, tables, and reproducible bundle created
17. PUBLISHABLE_ARTIFACT      -> Verified manuscript and reproducible archive
```

---

## 3. Core Domain Entities

* **`ResearchQuestion`**: Formal scientific query with scope boundaries and directional objectives.
* **`Evidence` & `EvidenceFragment`**: Concrete empirical or computational extract (text, table, equation, figure, dataset) linked to a provenance source.
* **`ResearchGap`**: Candidate gap in literature backed by supporting/contradicting evidence citations.
* **`Hypothesis`**: Mechanistic statement with explicit predictions, assumptions, alternative explanations, and **falsification criteria**.
* **`Experiment` & `Simulation`**: Computational plans declaring required resources, parameter sets, seeds, and execution policies.
* **`StatisticalAnalysis`**: Deterministic statistical summary (p-values, effect sizes, confidence intervals, power) referencing concrete raw data.
* **`FalsificationEvaluation`**: State of hypothesis support (`SUPPORTED`, `WEAKENED`, `CONTRADICTED`, `INCONCLUSIVE`, `UNTESTED`).
* **`HumanDecision`**: Immutable record of human scientific authority review.
* **`ResearchArtifact` & `Manuscript`**: Verifiable deliverables traceable back to primary evidence and computation runs.
