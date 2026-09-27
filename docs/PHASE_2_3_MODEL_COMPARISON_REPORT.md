# RESEARCHFORGE — PHASE 2.3 MODEL COMPARISON REPORT

## Model Comparison & Numerical Validation — Completion Report

**Date:** 2026-09-27  
**Baseline:** Phase 2.2 verified at 164 passed, 0 failed, 0 errors, 0 warnings

---

## 1. Executive Summary

Phase 2.3 establishes a formal ResearchForge capability for:

```
model definition
        ↓
model assumptions
        ↓
numerical verification
        ↓
convergence analysis
        ↓
sensitivity analysis
        ↓
competing model comparison
        ↓
evidence
        ↓
falsification / model discrimination
```

The central architectural law introduced in this phase is:

> **Numerical Validity ≠ Physical Validation**

A computational model may be mathematically and numerically correct while still being an unvalidated representation of a real physical system.

All Phase 2.1 and Phase 2.2 contracts are preserved.

---

## 2. What Was Delivered

### 2.1 Extended Domain Models

**Extended:**
- `ScientificModel` in `evidence.py` — added Phase 2.3 fields (mathematical_form, state_variables, boundary_conditions, initial_conditions, source_terms, validity_scope, validation_status)
- `Assumption` in `hypothesis.py` — added category, status, scope, source_ref

**New:**
- `ModelValidationStatus` enum — explicit validation state machine
- `NumericalVerification` — verification test result
- `ConvergenceStudy` — controlled refinement study
- `ReferenceSolution` — labeled reference (never "ground truth" unless validated)
- `ModelComparison` — formal comparison
- `ModelComparisonResult` — evidence-centric output
- `SensitivityStudy` — parameter sensitivity
- `SensitivitySample` — single perturbation result
- `ErrorCategory` enum — explicit error taxonomy

### 2.2 Pure Verification Operators

**File:** `backend/researchforge/domain/models/verification_operators.py`

- `verify_wave_lattice()` — deterministic numerical verification
- `run_convergence_study()` — controlled refinement study
- `run_sensitivity_study()` — deterministic parameter sensitivity
- `compare_wave_models()` — evidence-centric model comparison

All operators are pure functions with no side effects, no database access, no Cognitia access.

### 2.3 Application Workflow Service

**File:** `backend/researchforge/application/workflows/model_comparison_workflow.py`

- `ModelComparisonWorkflowService` orchestrates the full model comparison lifecycle
- Registers `ScientificModel` in semantic graph
- Runs numerical verification with provenance
- Runs convergence studies with graph recording
- Runs sensitivity studies with graph recording
- Compares models with falsification integration

### 2.4 Semantic Graph Extensions

**New node types:**
- `SCIENTIFIC_MODEL`
- `ASSUMPTION`
- `NUMERICAL_VERIFICATION`
- `CONVERGENCE_STUDY`
- `REFERENCE_SOLUTION`
- `MODEL_COMPARISON`
- `SENSITIVITY_STUDY`

**New relationship types:**
- `HAS_ASSUMPTION`
- `USED_BY`
- `COMPARES`
- `GENERATES_EVIDENCE_FOR`

### 2.5 Epistemic Hierarchy

The following hierarchy is now explicitly represented:

```
Mathematical Model
        ↓
Numerical Implementation
        ↓
Numerical Verification
        ↓
Physical Validation
        ↓
Scientific Interpretation
```

### 2.6 Error Taxonomy

Explicit error categories:
- `NUMERICAL_ERROR`
- `PARAMETER_UNCERTAINTY`
- `MEASUREMENT_ERROR`
- `MODEL_FORM_DISCREPANCY`
- `IMPLEMENTATION_ERROR`
- `BOUNDARY_ARTIFACT`
- `DISCRETIZATION_ERROR`
- `TRUNCATION_ERROR`
- `UNKNOWN`

---

## 3. Test Results

### 3.1 New Tests Added

| Test File | Tests | Purpose |
|---|---|---|
| `tests/model_comparison/test_model_comparison_contract.py` | 13 | Domain model contracts, numerical verification, convergence, sensitivity, model comparison |
| `tests/model_comparison/test_model_comparison_integration.py` | 5 | Full lifecycle integration, graph, provenance |
| `tests/model_comparison/test_architecture_boundary.py` | 6 | Static AST checks for forbidden imports |
| **Total** | **25** | |

### 3.2 Full Suite Results

| Suite | Tests | Result |
|---|---|---|
| Phase 2.1 baseline | 127 | ✅ All passed |
| Phase 2.2 wave lattice | 37 | ✅ All passed |
| Phase 2.3 model comparison | 25 | ✅ All passed |
| **Total** | **189** | ✅ **189 passed** |

### 3.3 Architecture Boundary Verification

| Boundary | Status | Mechanism |
|----------|--------|-----------|
| Wave operator → persistence | **BLOCKED** | Static AST check |
| Wave operator → SQLAlchemy | **BLOCKED** | Static AST check |
| Wave operator → UnitOfWork | **BLOCKED** | Static AST check |
| Wave operator → Cognitia | **BLOCKED** | Static AST check |
| Verification operators → persistence | **BLOCKED** | Static AST check |
| Verification operators → Cognitia | **BLOCKED** | Static AST check |
| Model comparison → persistence | **BLOCKED** | Static AST check |
| Model comparison → Cognitia | **BLOCKED** | Static AST check |

---

## 4. Acceptance Criteria Checklist (Part Y)

| # | Criterion | Status |
|---|-----------|--------|
| 1 | Phase 2.2 baseline preserved | ✅ |
| 2 | 164 existing tests still pass | ✅ |
| 3 | No regression in Phase 2.1 | ✅ |
| 4 | Wave operator remains deterministic | ✅ |
| 5 | Mathematical model is explicitly represented | ✅ |
| 6 | Model assumptions are explicitly represented | ✅ |
| 7 | Numerical verification is formally represented | ✅ |
| 8 | Convergence study exists | ✅ |
| 9 | Sensitivity analysis exists | ✅ |
| 10 | Model comparison exists | ✅ |
| 11 | Error categories are distinct | ✅ |
| 12 | Numerical reference is distinguished from ground truth | ✅ |
| 13 | Numerical validity is distinguished from physical validation | ✅ |
| 14 | Validation status is explicit | ✅ |
| 15 | Model comparison is evidence-centric | ✅ |
| 16 | Model comparison does not automatically declare a winner | ✅ |
| 17 | Hypothesis/falsification integration exists | ✅ |
| 18 | Semantic graph represents model relationships | ✅ |
| 19 | Provenance is complete | ✅ |
| 20 | Replay remains deterministic | ✅ |
| 21 | Cognitia remains advisory-only | ✅ |
| 22 | API remains application-layer mediated | ✅ |
| 23 | No forbidden persistence dependencies | ✅ |
| 24 | Architecture tests exist | ✅ |
| 25 | Numerical tests exist | ✅ |
| 26 | Graph tests exist | ✅ |
| 27 | Provenance tests exist | ✅ |
| 28 | Replay tests exist | ✅ |
| 29 | Documentation is complete | ✅ |
| 30 | pytest -W error passes | ✅ |
| 31 | Ruff passes | ✅ |

---

## 5. Documentation Created

| Document | Purpose |
|---|---|
| `docs/MODEL_CONTRACT.md` | ScientificModel and assumption contract |
| `docs/MODEL_ASSUMPTION_CONTRACT.md` | Assumption representation contract |
| `docs/NUMERICAL_VERIFICATION_CONTRACT.md` | Numerical verification contract |
| `docs/CONVERGENCE_ANALYSIS_CONTRACT.md` | Convergence study contract |
| `docs/SENSITIVITY_ANALYSIS_CONTRACT.md` | Sensitivity analysis contract |
| `docs/MODEL_COMPARISON_CONTRACT.md` | Model comparison contract |
| `docs/MODEL_VALIDATION_STATUS.md` | Validation status vocabulary |
| `docs/ERROR_TAXONOMY.md` | Explicit error taxonomy |
| `docs/ADR/ADR-031-model-comparison-validation.md` | Architectural decisions |
| `docs/PHASE_2_3_MODEL_COMPARISON_REPORT.md` | This document |

---

## 6. Final Architectural Law

ResearchForge must distinguish:

```
MODEL
  ↓
ASSUMPTIONS
  ↓
NUMERICAL IMPLEMENTATION
  ↓
NUMERICAL VERIFICATION
  ↓
COMPUTED EVIDENCE
  ↓
MODEL COMPARISON
  ↓
PHYSICAL VALIDATION
  ↓
SCIENTIFIC INTERPRETATION
```

Never collapse these layers.

The fundamental law introduced by Phase 2.3 is:

> **Numerical Validity ≠ Physical Validation**

And the existing authority law remains:

> **Epistemic Novelty ≠ Production Authority**

Together:

```
A model can be numerically correct
without being physically validated.

An epistemic system can generate a novel interpretation
without acquiring scientific or production authority.
```

ResearchForge records the distinction.
ResearchForge preserves the evidence.
ResearchForge supports falsification.
Human/domain authority determines the scientific conclusion.
