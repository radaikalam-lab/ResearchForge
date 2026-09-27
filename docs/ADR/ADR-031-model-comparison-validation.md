# ADR-031: Model Comparison and Numerical Validation

**Status:** Accepted  
**Date:** 2026-09-27  
**Phase:** 2.3 — Model Comparison & Numerical Validation

---

## Context

Phase 2.2 introduced a deterministic 1-D heterogeneous damped-wave reference computation. The computation is numerically correct and architecturally isolated.

However, ResearchForge lacked formal representations for:
1. Scientific models (mathematical specification separate from implementation)
2. Model assumptions (explicit, categorized, tracked)
3. Numerical verification (stability, convergence, reference agreement)
4. Convergence studies (controlled refinement analysis)
5. Sensitivity analysis (parameter perturbation)
6. Model comparison (evidence-centric, no automatic winner)

Without these, ResearchForge could not distinguish:
- Numerical validity from physical validation
- Sensitivity analysis from uncertainty quantification
- Model comparison from automatic verdicts

## Decision

### 1. Extend existing domain models

Rather than creating parallel frameworks, extend existing domain models:
- `ScientificModel` in `evidence.py` — extended with Phase 2.3 fields
- `Assumption` in `hypothesis.py` — extended with category, status, scope, source_ref

### 2. Introduce new domain models

New pure domain models with no persistence/Cognitia dependencies:
- `ModelValidationStatus` — explicit validation state machine
- `NumericalVerification` — verification test result
- `ConvergenceStudy` — refinement study
- `ReferenceSolution` — labeled reference (never "ground truth" unless validated)
- `ModelComparison` — formal comparison
- `ModelComparisonResult` — evidence-centric output
- `SensitivityStudy` — parameter sensitivity
- `SensitivitySample` — single perturbation result

### 3. Extend semantic graph ontology

New node types:
- `SCIENTIFIC_MODEL`
- `ASSUMPTION`
- `NUMERICAL_VERIFICATION`
- `CONVERGENCE_STUDY`
- `REFERENCE_SOLUTION`
- `MODEL_COMPARISON`
- `SENSITIVITY_STUDY`

New relationship types:
- `HAS_ASSUMPTION`
- `USED_BY`
- `COMPARES`
- `GENERATES_EVIDENCE_FOR`

### 4. Implement pure verification operators

Pure deterministic functions in `verification_operators.py`:
- `verify_wave_lattice()` — numerical verification
- `run_convergence_study()` — convergence study
- `run_sensitivity_study()` — sensitivity analysis
- `compare_wave_models()` — model comparison

These functions have no side effects, no database access, no Cognitia access.

### 5. Implement workflow service

`ModelComparisonWorkflowService` orchestrates:
- Scientific model registration in semantic graph
- Numerical verification with provenance
- Convergence study with graph recording
- Sensitivity study with graph recording
- Model comparison with falsification integration

### 6. Enforce architectural boundaries

Static AST tests verify that:
- Verification operators do not import persistence
- Verification operators do not import Cognitia
- Model comparison domain models do not import persistence
- Model comparison domain models do not import Cognitia

## Consequences

### Positive

1. **Explicit epistemic hierarchy**: Mathematical model → Numerical implementation → Numerical verification → Physical validation → Scientific interpretation
2. **Numerical validity ≠ Physical validation**: Enforced by separate enum values and tests
3. **Evidence-centric model comparison**: No automatic winner; human/domain authority decides
4. **Reuse of existing architecture**: No new database, no new graph database, no new provenance system
5. **Phase 2.2 preserved**: All 164 existing tests pass, 25 new tests added

### Negative

1. **Increased complexity**: More domain models and relationships to maintain
2. **Longer onboarding**: New developers must understand the epistemic hierarchy

## References

- `docs/MODEL_CONTRACT.md`
- `docs/MODEL_ASSUMPTION_CONTRACT.md`
- `docs/NUMERICAL_VERIFICATION_CONTRACT.md`
- `docs/CONVERGENCE_ANALYSIS_CONTRACT.md`
- `docs/SENSITIVITY_ANALYSIS_CONTRACT.md`
- `docs/MODEL_COMPARISON_CONTRACT.md`
- `docs/MODEL_VALIDATION_STATUS.md`
- `docs/ERROR_TAXONOMY.md`
