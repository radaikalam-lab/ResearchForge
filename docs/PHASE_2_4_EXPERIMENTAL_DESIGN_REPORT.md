# ResearchForge — Phase 2.4 Experimental Design & Parameter Exploration Report

**Phase:** Phase 2.4  
**Date:** September 2026  
**Status:** COMPLETE & VERIFIED  

---

## 1. Summary of Deliverables

Phase 2.4 introduces the formal capability to **construct and evaluate candidate experimental designs** intended to discriminate between competing scientific models:

1. **Domain Models (`experimental_design_candidate.py`)**:
   - `ExperimentalDesignCandidate`
   - `CandidateDesignEvaluation`
   - `ParetoCandidateSet`
   - `DiscriminationMetric`
   - `ObservableTarget`
   - `ResourceRequirements`
   - `DesignObjective`
   - `DesignCandidateStatus`

2. **Pure Numerical & Exploration Operators (`design_exploration_operators.py`)**:
   - `generate_candidate_designs`: Deterministic, constraint-enforcing sampling (GRID, LATIN_HYPERCUBE, RANDOM_UNIFORM, ONE_AT_A_TIME). Consumes existing Phase 2.3 `SensitivityStudy` to prioritize high-sensitivity parameters without deleting other variables.
   - `evaluate_candidate_for_model_discrimination`: Simulates competing models on wave lattice PDE, computes predicted observable divergence, isolates physical signal from numerical discretization uncertainty, and documents formal `DiscriminationMetric`.
   - `compute_pareto_frontier`: Calculates non-dominated candidate set across multi-objective trade-offs (discrimination, cost, robustness) without declaring an arbitrary single winner.

3. **Semantic Graph Extensions (`types.py` & `ontology.py`)**:
   - Node Types: `EXPERIMENTAL_DESIGN_CANDIDATE`, `CANDIDATE_DESIGN_EVALUATION`, `PARETO_CANDIDATE_SET`, `OBSERVABLE_DEFINITION`.
   - Relation Types: `INFORMS_DESIGN`, `EVALUATES_CANDIDATE`, `PROMOTED_TO`, `TARGETS_OBSERVABLE`, `INCLUDES_CANDIDATE`.

4. **Persistence & Workflow Layer**:
   - `ExperimentalDesignCandidateRecord`, `CandidateDesignEvaluationRecord`, `ParetoCandidateSetRecord` ORM tables.
   - `ExperimentalDesignCandidateRepository`, `CandidateDesignEvaluationRepository`, `ParetoCandidateSetRepository` repositories.
   - `ExperimentalDesignWorkflowService` managing the complete candidate lifecycle with strict human-gated promotion.
   - Read projections in `GraphQueryApplicationService`.
   - API endpoints in `endpoints.py`.

5. **Test Suite & Verification Metrics**:
   - Baseline: Phase 2.3 (189 tests)
   - Final: Phase 2.4 (**203 tests**)
   - Results: **203 passed, 0 failed, 0 errors, 0 warnings** under `pytest -W error`
   - Linter: **Ruff PASS** (`All checks passed!`)
   - Architecture Boundaries: **PASS** (AST static checks confirm numerical operators have zero DB/ORM/Cognitia dependencies)
   - Semantic Graph Invariants: **PASS** (Strict ontological validation on all relations and cardinalities)
   - Provenance Tracking: **PASS** (Deterministic event hashes and lineage tracking)
   - Offline Replay: **PASS** (Deterministic candidate regeneration without network, Cognitia, or LLM)
   - Human-Gated Promotion: **PASS** (Candidate $\neq$ Authoritative Experiment; promotion requires signed `HumanDecision`)
   - Cognitia Isolation: **PASS** (Advisory only; zero execution or persistence authority)

---

## 2. Phase 2.4 Architectural Laws Frozen

1. **Semantic Graph $\neq$ Database**: The graph enforces ontological relations and epistemic lineage, while domain models preserve structured properties in transactional persistence.
2. **Graph Persistence $\neq$ Graph Semantics**: Storage adapters do not alter domain invariant validation.
3. **Numerical Verification $\neq$ Physical Validation**: Code correctness and order-of-accuracy verification do not substitute for empirical validation.
4. **Sensitivity $\neq$ Uncertainty Quantification**: Parameter sensitivity informs candidate prioritization without deleting uninfluential variables or defining confidence intervals.
5. **Numerical Reference $\neq$ Ground Truth**: Finite-difference lattice computations serve as verifiable reference models, not absolute physical truth.
6. **Model Difference $\neq$ Model Truth**: Observable divergence between Model A and Model B is assessed relative to discretization uncertainty $\mathcal{O}(\Delta x^2 + \Delta t^2)$.
7. **Candidate Experiment $\neq$ Authoritative Experiment**: Candidates are unexecutable until promoted by explicit human review (`HumanDecision`).
8. **Epistemic Novelty $\neq$ Production Authority**: Cognitia and automated generators propose; human gatekeepers decide.

---

## 3. Git Baseline & Publication

- **Repository Remote:** `https://github.com/radaikalam-lab/ResearchForge.git`
- **Branch:** `master`
- **Verification:** 203/203 unit & integration tests pass with zero warnings under `-W error`.
- **Status:** `PHASE 2.4 FROZEN — GITHUB PUBLISHED`

