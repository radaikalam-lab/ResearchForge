# PHASE 2: EXPERIMENT DESIGN & COMPUTATION PLANNING — SEMANTIC GRAPH FIRST

## 1. Overview and Core Philosophy

ResearchForge Phase 2 implements **Experiment Design and Computation Planning** grounded in the authoritative **Phase 0.4 Semantic Graph Contract**.

The foundational architectural sequence is frozen:

```
SEMANTIC VOCABULARY
        ↓
SEMANTIC GRAPH CONTRACT
        ↓
DOMAIN MODEL
        ↓
STATE / AUTHORITY
        ↓
PROVENANCE
        ↓
EXECUTION
        ↓
GRAPH PERSISTENCE BOUNDARY
        ↓
PHYSICAL STORAGE
```

Scientific entities and relationships enter the system through the semantic graph contract before they enter the domain model or persistence layer. The relational database (PostgreSQL/SQLite) serves as a physical realization and storage mechanism, while the semantic graph is the authoritative communication boundary.

---

## 2. Phase 2 Semantic Concepts & Graph Nodes

Phase 2 introduces the following 10 semantic node types:
1. `EXPERIMENT_DESIGN`: Declarative scientific experimental setup linked to hypotheses and parameter exploration.
2. `EXPERIMENT_SPECIFICATION`: Specific formal configurations for an experiment.
3. `PARAMETER_SPACE`: Multi-dimensional parameter domain covering continuous, discrete, categorical, and grid spaces.
4. `PARAMETER_DEFINITION`: Formal definition of an individual scientific parameter (type, bounds, unit, default).
5. `PARAMETER_CONSTRAINT`: Constraint rules governing parameter combinations (inequalities, dependencies, mutual exclusivity).
6. `COMPUTATION_PLAN`: Declarative computation workflow describing operators, dependencies, resource limits, and determinism.
7. `EXECUTION_SPECIFICATION`: Concrete container/backend environment requirements (CPU, memory, timeout, environment).
8. `DATASET_SPECIFICATION`: Declarative schema and expected format for inputs/outputs.
9. `ANALYSIS_SPECIFICATION`: Specification for downstream processing, statistical analysis, and falsification rules.
10. `STATISTICAL_ANALYSIS`: Results and effect sizes computed from experiment data.

---

## 3. Semantic vs Execution Distinction

Semantic graph relationships are strictly partitioned between **semantic** intent and **execution** mechanics:
* **Semantic relations**:
  * `Hypothesis ──TESTED_BY──> Experiment`
  * `Experiment ──HAS_DESIGN──> ExperimentDesign`
  * `ExperimentDesign ──HAS_PARAMETER_SPACE──> ParameterSpace`
  * `ParameterSpace ──CONTAINS_PARAMETER──> ParameterDefinition`
  * `ParameterDefinition ──CONSTRAINED_BY──> ParameterConstraint`
  * `ExperimentDesign ──HAS_COMPUTATION_PLAN──> ComputationPlan`
  * `ComputationPlan ──SPECIFIES_EXECUTION──> ExecutionSpecification`
  * `ComputationPlan ──SPECIFIES_DATASET──> DatasetSpecification`
  * `ComputationPlan ──SPECIFIES_ANALYSIS──> AnalysisSpecification`
  * `StatisticalAnalysis ──INFORMS_FALSIFICATION──> FalsificationEvaluation`
* **Execution relations**:
  * `Experiment ──EXECUTED_AS──> ExperimentRun`
  * `ExperimentRun ──PRODUCES_DATASET──> DatasetSpecification / Artifact`
  * `AnalysisSpecification ──ANALYSIS_CONSUMES──> Artifact`

---

## 4. Falsification-First Architecture

Experiments exist to rigorously test and potentially falsify hypotheses. The full semantic trajectory is:

```
Hypothesis
   ↓ [HAS_FALSIFICATION_CRITERIA]
FalsificationCriteria
   ↓ [TESTED_BY]
Experiment
   ↓ [HAS_DESIGN]
ExperimentDesign (ParameterSpace + ComputationPlan)
   ↓ [EXECUTED_AS]
ExperimentRun
   ↓ [PRODUCES_DATASET]
Dataset Artifact
   ↓ [ANALYSIS_CONSUMES]
StatisticalAnalysis
   ↓ [INFORMS_FALSIFICATION]
FalsificationEvaluation
   ↓ [EVALUATES]
Hypothesis (SUPPORTED / REFUTED / INCONCLUSIVE)
   ↓ [INFORMS]
HumanDecision (Approved Finding)
   ↓ [ESTABLISHES]
Conclusion
```

---

## 5. Persistence and Reproducibility Invariants

1. **Graph Persistence Port (`GraphPersistencePort`)**: The domain interacts with persistence via a graph contract protocol (`persist_graph`, `load_graph`, `append_graph_delta`, `verify_graph_integrity`).
2. **Deterministic Canonical Serialization & Hashing**: Graphs are serialized canonically and hashed via SHA-256 (`canonical_hash(graph) == canonical_hash(graph')`).
3. **Graph Delta Model (`GraphDelta`)**: Supports incremental mutations (`ADD_NODE`, `UPDATE_NODE`, `REMOVE_NODE`, `ADD_EDGE`, `REMOVE_EDGE`) validated against ontology invariants.
4. **UnitOfWork Integration**: Mutations to domain entities, semantic graphs, and provenance events occur inside a single atomic transaction.

---

## 6. Epistemic and Authority Safeguards

* **Cognitia**: Strictly advisory. Inspects hypotheses, gaps, designs, and plans, but has zero execution or state-mutation authority.
* **Execution Subsystem**: Autonomous execution is prohibited in Phase 2; specifications are strictly declarative and require human approval before dispatch to sandboxed execution backends.
