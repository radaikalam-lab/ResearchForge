# ADR-026: Experiment Design & Computation Planning Semantic Graph Extension

## Status
Accepted

## Date
2026-09-27

## Context
ResearchForge Phase 2 requires formal representations of experiment planning, parameter exploration, computational pipelines, and falsification evaluations. In accordance with the Phase 0.4 architecture, all scientific entities must enter the system through the Semantic Graph Contract first before domain models and persistence structures are instantiated.

## Decision
1. **Extend Semantic Graph Ontology**:
   - Added 10 new node types: `EXPERIMENT_DESIGN`, `EXPERIMENT_SPECIFICATION`, `PARAMETER_SPACE`, `PARAMETER_DEFINITION`, `PARAMETER_CONSTRAINT`, `COMPUTATION_PLAN`, `EXECUTION_SPECIFICATION`, `DATASET_SPECIFICATION`, `ANALYSIS_SPECIFICATION`, and `STATISTICAL_ANALYSIS`.
   - Added 13 new relation types: `TESTED_BY`, `HAS_DESIGN`, `HAS_PARAMETER_SPACE`, `CONTAINS_PARAMETER`, `CONSTRAINED_BY`, `HAS_COMPUTATION_PLAN`, `SPECIFIES_EXECUTION`, `SPECIFIES_DATASET`, `SPECIFIES_ANALYSIS`, `EXECUTED_AS`, `PRODUCES_DATASET`, `ANALYSIS_CONSUMES`, and `INFORMS_FALSIFICATION`.
2. **Domain Models Derived from Graph**:
   - `ExperimentDesign`, `ParameterSpace`, `ComputationPlan`, and their associated component specifications (`ExecutionSpecification`, `DatasetSpecification`, `AnalysisSpecification`).
3. **Semantic vs Execution Boundary**:
   - Explicitly distinguish semantic intent (`Hypothesis TESTED_BY Experiment`) from execution instantiation (`Experiment EXECUTED_AS ExperimentRun`).
4. **Falsification Integration**:
   - Connect hypothesis falsification criteria to experimental statistical analysis and evaluation nodes (`StatisticalAnalysis INFORMS_FALSIFICATION FalsificationEvaluation EVALUATES Hypothesis`).
5. **Epistemic Safeguards**:
   - Cognitia remains strictly advisory.
   - Declarative specifications have no automatic execution authority.

## Consequences
- Fully typed, contract-governed, and machine-validatable experiment planning trajectory.
- Deterministic canonical serialization and provenance replay for all experiment artifacts.
- Zero regressions across existing Phase 0 and Phase 1 test suites.
