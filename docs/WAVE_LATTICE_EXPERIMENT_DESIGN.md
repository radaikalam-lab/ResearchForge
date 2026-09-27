# Wave Lattice Experiment Design (Phase 2.2)

## Experimental Hypothesis

> A heterogeneous material region with elevated damping properties produces
> measurable attenuation and/or reflection of an incident wave relative to
> a homogeneous reference material under identical source and boundary conditions.

This hypothesis is **falsifiable** via the `attenuation_ratio` observable:

```
attenuation_ratio = max_core_displacement / max_global_displacement
```

**Falsification criterion:** if `attenuation_ratio > attenuation_threshold`,
the experiment does NOT support the hypothesis for that threshold.

The threshold is an **experiment parameter**, not a hidden constant.

---

## Experiment A — Baseline (Homogeneous Control)

```
Material:
    density       = ρ₀    (uniform)
    stiffness     = E₀    (uniform)
    damping       = γ₀    (uniform, typically 0)
    core_damping  = 0     (no contrast with background)
```

Purpose: establish reference behaviour for the same source, domain, and
discretisation without any heterogeneous interface.

Expected result: `attenuation_ratio ≈ 1.0` (wave passes through without
material-boundary attenuation). Any residual attenuation is due to
boundary absorption alone.

---

## Experiment B — Heterogeneous Core

```
Material:
    Background:
        density    = ρ₀
        stiffness  = E₀
        damping    = γ₀
    Core [core_start, core_end):
        density    = ρ_core
        stiffness  = E_core
        damping    = γ_core   (elevated relative to background)
```

Purpose: test whether the heterogeneous core produces measurable wave attenuation
relative to Experiment A.

Expected result: `attenuation_ratio < A.attenuation_ratio` if core is effective.
This is an **experimental result**, not an assumption.

---

## Parameter Space

| Parameter | Default A | Default B | Range | Falsification Role |
|-----------|-----------|-----------|-------|--------------------|
| `nodes` | 200 | 200 | ≥ 4 | Spatial resolution |
| `time_steps` | 500 | 500 | ≥ 2 | Simulation duration |
| `dx` | 1.0 | 1.0 | > 0 | Grid spacing |
| `dt` | 0.4 | 0.4 | > 0, CFL | Time step |
| `density` | 1.0 | 1.0 | > 0 | Background inertia |
| `stiffness` | 1.0 | 1.0 | > 0 | Background wave speed |
| `damping` | 0.0 | 0.0 | ≥ 0 | Background dissipation |
| `core_start` | 80 | 80 | < core_end | Core region start |
| `core_end` | 120 | 120 | ≤ nodes | Core region end |
| `core_density` | 1.0 | 1.0 | > 0 | Core inertia |
| `core_stiffness` | 1.0 | 1.0 | > 0 | Core wave speed |
| `core_damping` | 0.0 | 5–20 | ≥ 0 | Core dissipation ← primary variable |
| `source_amplitude` | 1.0 | 1.0 | any | Source strength |
| `source_location` | 10 | 10 | < nodes | Where excitation occurs |
| `source_duration` | 20 | 20 | ≥ 1 | How long excitation lasts |
| `boundary_condition` | ABSORBING | ABSORBING | enum | Edge behaviour |
| `attenuation_threshold` | — | 0.5 | (0, 1] | Falsification criterion |

**Comparability constraint (PART J):**
Both A and B must use identical `nodes`, `time_steps`, `dx`, `dt`, `source_*`,
`density`, `stiffness`, `damping`, and `boundary_condition`.

---

## Computation Plan

1. Validate `WaveLatticeParameters` (CFL check)
2. Build material fields `rho(x)`, `E(x)`, `gamma(x)` from parameters
3. Compute interface stiffness (harmonic mean) for spatial discretisation
4. Time-step using explicit central-difference update
5. Apply boundary conditions each step
6. Accumulate observables per step
7. Return `WaveLatticeObservables` with `output_hash` for determinism verification

---

## Semantic Graph Trajectory

```
Hypothesis
    ──TESTED_BY──>
Experiment (A or B)
    ──HAS_DESIGN──>
ExperimentDesign
    ├──HAS_PARAMETER_SPACE──> ParameterSpace
    │                             └──CONTAINS_PARAMETER──> ParameterDefinitions
    └──HAS_COMPUTATION_PLAN──> ComputationPlan
                                   ├──SPECIFIES_EXECUTION──> ExecutionSpecification
                                   ├──SPECIFIES_DATASET──> DatasetSpecification
                                   └──SPECIFIES_ANALYSIS──> AnalysisSpecification

Experiment
    ──EXECUTED_AS──>
ExperimentRun (with results.observables)

StatisticalAnalysis
    ──INFORMS_FALSIFICATION──>
FalsificationEvaluation
    ──EVALUATES──>
Hypothesis
```

---

## Scientific Result Interpretation

| Observable | Supports Hypothesis | Contradicts Hypothesis |
|------------|--------------------|-----------------------|
| `attenuation_ratio ≤ threshold` | ✓ | |
| `attenuation_ratio > threshold` | | ✓ |
| `max_core_displacement < baseline` | Evidence of attenuation | |
| `dissipated_energy_B > dissipated_energy_A` | Evidence of core effect | |
| `incident_energy_A ≈ incident_energy_B` | Confirms source comparability | |

The experiment produces **observations**, not conclusions.
A `FalsificationEvaluation` is produced; the human scientific decision
is required to promote any conclusion to authoritative state.
