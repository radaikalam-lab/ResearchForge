# RESEARCHFORGE — PHASE 2.2 WAVE COMPUTATION REPORT

## Wave Lattice Reference Computation — Completion Report

**Date:** 2026-09-27  
**Baseline:** Phase 2.1 verified at 127 passed, 0 failed, 0 errors, 0 warnings  

---

## 1. Executive Summary

Phase 2.2 integrates a scientifically valid, deterministic 1-D heterogeneous
damped-wave reference computation into ResearchForge.

The wave experiment is governed by ResearchForge as a full scientific
experiment with hypothesis, experiment design, parameter space,
computation plan, provenance, graph representation, and falsification
evaluation — not as a standalone utility.

All Phase 2.1 architecture boundaries are preserved.

---

## 2. What Was Delivered

### 2.1 Wave Operator (Domain Layer)

**File:** [`backend/researchforge/domain/models/wave_lattice.py`](file:///e:/ResearchForge/backend/researchforge/domain/models/wave_lattice.py)

- Implements the correct 1-D damped-wave equation with explicit time + space dimensions
- `WaveLatticeParameters` — fully typed input contract with CFL stability check
- `WaveLatticeObservables` — typed output contract with all required energy observables
- `simulate_1d_damped_wave_lattice()` — pure deterministic function (no side effects)
- Distinct material properties: density, stiffness, damping (not conflated)
- Mur 1st-order absorbing boundary condition
- Dirichlet fixed-wall boundary condition
- Sin²-ramped source to avoid step-discontinuity artifacts
- SHA-256 input_hash + output_hash for determinism verification

### 2.2 Workflow Service (Application Layer)

**File:** [`backend/researchforge/application/workflows/wave_lattice_workflow.py`](file:///e:/ResearchForge/backend/researchforge/application/workflows/wave_lattice_workflow.py)

- `WaveLatticeWorkflowService` orchestrates the full experiment lifecycle
- Pure wave operator called **outside** any database transaction
- All persistence through `UnitOfWork` / `GraphPersistencePort`
- Provenance recorded for every authoritative mutation
- Semantic graph updated with correct relationship types

### 2.3 Graph Integration

| Relationship | Source | Target | Status |
|---|---|---|---|
| TESTED_BY | Hypothesis | Experiment | ✅ |
| TESTS | Experiment | Hypothesis | ✅ |
| EXECUTED_AS | Experiment | ExperimentRun | ✅ |
| INFORMS_FALSIFICATION | StatisticalAnalysis | FalsificationEvaluation | ✅ |
| EVALUATES | FalsificationEvaluation | Hypothesis | ✅ |
| EVALUATES | FalsificationEvaluation | ExperimentRun | ✅ |

### 2.4 Experiment Design Registration

`plan_wave_experiment()` registers the full experiment design in the semantic graph via `ExperimentPlanningWorkflowService`, including:
- 16 typed `ParameterDefinition` entries
- CFL stability `ParameterConstraint`
- `ExecutionSpecification` with deterministic_required=True, network_isolated=True
- `DatasetSpecification` with all 8 observable column names
- `AnalysisSpecification` targeting attenuation observables

### 2.5 Falsification

The hypothesis is falsifiable via `attenuation_threshold`:

```
SUPPORTED:     attenuation_ratio <= threshold
CONTRADICTED:  attenuation_ratio >  threshold
```

The threshold is a parameter — not a hidden constant.

---

## 3. Scientific Corrections Applied

| Problem (from PART B) | Correction Applied |
|---|---|
| No time dimension | `u[t]`, `u[t-1]`, `u[t+1]` explicit time stepping |
| Future spatial value used before calculation | Interior nodes computed first; boundaries applied after |
| Not a finite-difference wave equation | Full explicit central-difference scheme implemented |
| Damping confused with stiffness | `density`, `stiffness`, `damping` are separate parameters |
| No measurable physical output | 9 typed observables in `WaveLatticeObservables` |
| No heterogeneous core | `core_[density/stiffness/damping]` are independent material fields |
| Conclusion encoded in simulator | Simulator produces observations; ResearchForge evaluates falsification |

---

## 4. Architecture Verification

### 4.1 Phase 2.1 Boundaries Preserved

| Boundary | Status |
|---|---|
| API → UnitOfWork | **BLOCKED** (static AST check) |
| API → SQLAlchemy | **BLOCKED** (static AST check) |
| API → persistence.models | **BLOCKED** (static AST check) |
| Domain → persistence | **BLOCKED** (static AST check) |
| Cognitia → persistence | **BLOCKED** (static AST check) |
| Cognitia → execution | **BLOCKED** (static AST check) |

### 4.2 New Operator Boundary

| Boundary | Status |
|---|---|
| Wave operator → persistence | **BLOCKED** (static AST check in test suite) |
| Wave operator → SQLAlchemy | **BLOCKED** (static AST check) |
| Wave operator → UnitOfWork | **BLOCKED** (static AST check) |
| Wave operator → Cognitia | **BLOCKED** (static AST check) |
| Wave operator → execution subsystem | **BLOCKED** (static AST check) |

---

## 5. Test Results

### 5.1 New Tests Added

| Test File | Tests | Purpose |
|---|---|---|
| `tests/experiment/test_wave_lattice_operator.py` | 30 | Operator unit + architecture + physics |
| `tests/integration/test_wave_lattice_integration.py` | 7 | Full lifecycle + graph + provenance |

### 5.2 Test Categories

| Category | Count | Status |
|---|---|---|
| Parameter validation (CFL, geometry) | 5 | ✅ |
| Physical sanity (zero source, damping effects) | 4 | ✅ |
| Numerical correctness (boundary, propagation) | 7 | ✅ |
| Determinism verification | 3 | ✅ |
| Baseline vs heterogeneous comparison | 5 | ✅ |
| Observables contract | 2 | ✅ |
| Architecture boundary (AST static) | 4 | ✅ |
| Integration — full lifecycle | 1 | ✅ |
| Integration — deterministic replay | 1 | ✅ |
| Integration — baseline vs heterogeneous | 1 | ✅ |
| Integration — falsification | 1 | ✅ |
| Integration — graph relationships | 1 | ✅ |
| Integration — provenance recorded | 1 | ✅ |
| Replay without Cognitia/network | 1 | ✅ |

---

## 6. Documentation Created

| Document | Purpose |
|---|---|
| [`docs/WAVE_LATTICE_COMPUTATION_CONTRACT.md`](file:///e:/ResearchForge/docs/WAVE_LATTICE_COMPUTATION_CONTRACT.md) | Formal numerical contract |
| [`docs/WAVE_LATTICE_EXPERIMENT_DESIGN.md`](file:///e:/ResearchForge/docs/WAVE_LATTICE_EXPERIMENT_DESIGN.md) | Experiment A + B design |
| [`docs/ADR/ADR-030-wave-lattice-reference-computation.md`](file:///e:/ResearchForge/docs/ADR/ADR-030-wave-lattice-reference-computation.md) | Architectural decisions |
| `docs/PHASE_2_2_WAVE_COMPUTATION_REPORT.md` | This document |

---

## 7. Acceptance Criteria Checklist

```
[✅] Phase 2.1 API/application boundary preserved
[✅] API does not import UnitOfWork
[✅] API does not import SQLAlchemy
[✅] API does not import persistence internals
[✅] Domain remains persistence-independent
[✅] Cognitia remains advisory-only
[✅] Replay does not invoke Cognitia
[✅] Graph remains the semantic contract
[✅] Persistence remains an adapter
[✅] Wave model has explicit time dimension
[✅] Wave model has explicit spatial discretisation
[✅] Material properties are explicit
[✅] Damping is distinct from stiffness
[✅] Boundary conditions are explicit
[✅] Numerical stability is checked (CFL at construction time)
[✅] Baseline experiment exists (Experiment A)
[✅] Heterogeneous experiment exists (Experiment B)
[✅] Scientific observables exist (9 typed observables)
[✅] Hypothesis is falsifiable (attenuation_threshold parameter)
[✅] Computation is deterministic (SHA-256 hash verification)
[✅] Provenance is recorded (prov_ event per run)
[✅] Experiment is represented in the semantic graph
[✅] Graph persistence uses the existing boundary
[✅] Replay is deterministic
[✅] Architecture tests cover the new computation boundary
[✅] Documentation is complete
[✅] pytest passes with -W error
[✅] Ruff passes
```
