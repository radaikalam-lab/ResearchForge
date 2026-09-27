# ADR-032: Experimental Design Candidate Exploration & Model Discrimination

## Status
Accepted (Phase 2.4)

## Context
Following Phase 2.3 (Model Comparison & Numerical Verification), ResearchForge requires the capability to systematically construct and evaluate candidate experimental designs intended to discriminate between competing models and test scientific hypotheses over structured parameter spaces.

Crucially:
- Generated experimental designs are **proposals/candidates**, not authoritative experiments.
- Automated ranking must not silently declare a "best experiment" winner.
- Model discrimination must isolate true physical observable divergence from numerical discretization uncertainty ($D = \frac{\Delta}{\text{uncertainty}}$).
- Candidate designs must only become authoritative `ExperimentDesign` objects via explicit human/domain authorization (`HumanDecision`).
- Cognitia participates strictly in an advisory capacity (suggesting variables, observables, or confounders) with zero mutation or promotion authority.

## Decision
1. **Domain Models**:
   - `ExperimentalDesignCandidate`: Non-authoritative candidate specifying parameter assignments, controlled variables, independent/dependent variables, target observables, resource requirements, and design objectives.
   - `CandidateDesignEvaluation`: Multi-objective evaluation recording model predictions, predicted differences, numerical uncertainties, formal `DiscriminationMetric`, robustness, and resource cost.
   - `ParetoCandidateSet`: Non-dominated trade-off set across multiple criteria (e.g., maximizing discrimination while minimizing resource cost).
2. **Pure Numerical Operators**:
   - `design_exploration_operators.py`: Pure functions (`generate_candidate_designs`, `evaluate_candidate_for_model_discrimination`, `compute_pareto_frontier`) with zero persistence, network, or Cognitia dependencies.
3. **Semantic Graph Extensions**:
   - Node types: `EXPERIMENTAL_DESIGN_CANDIDATE`, `CANDIDATE_DESIGN_EVALUATION`, `PARETO_CANDIDATE_SET`, `OBSERVABLE_DEFINITION`.
   - Relations: `INFORMS_DESIGN`, `EVALUATES_CANDIDATE`, `PROMOTED_TO`, `TARGETS_OBSERVABLE`, `INCLUDES_CANDIDATE`.
4. **Authority Boundary**:
   - Explicit human gatekeeper transition via `ExperimentalDesignWorkflowService.promote_candidate_to_experiment_design` using signed `HumanDecision`.

## Consequences
- Preserves the core principle: **Candidate Design $\neq$ Authoritative Experiment**.
- Ensures reproducible, deterministic replay without external network or LLM dependencies.
- Retains complete backwards compatibility with all Phase 0.3 - 2.3 contracts and tests.
