# Contradiction Detection Model (Phase 1)

## 1. Epistemic Role of Contradictions

Contradictions in scientific literature represent vital opportunities for gap discovery rather than errors to be discarded. When two claims conflict, ResearchForge surfaces the underlying discrepancy without unilaterally declaring either paper invalid.

## 2. Contradiction Schema (`PotentialContradiction`)

- `id`: Contradiction identifier.
- `project_id`: Research project identifier.
- `claim_a_id`: First conflicting claim ID.
- `claim_b_id`: Second conflicting claim ID.
- `source_a_id`: Literature source for Claim A.
- `source_b_id`: Literature source for Claim B.
- `contradiction_type`:
  - `DIRECT_OPPOSITION`: Positive slope vs. null effect.
  - `PARAMETER_DISCREPANCY`: Discrepancy in quantitative values.
  - `METHODOLOGICAL_DIFFERENCE`: High-power assay vs. low-sample noisy assay.
  - `BOUNDARY_CONDITION_DISCREPANCY`: Regime transition differences.
- `scope_difference`: Description of overlapping vs divergent experimental regimes.
- `parameter_difference`: Specific conflicting parameter values (e.g., slope 2.14 vs slope 0.03).
- `methodological_difference`: Procedural differences (e.g. sample size N=100 vs N=20).
