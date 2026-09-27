# Wave Lattice Observables (Phase 2.2)

## Overview

The wave lattice operator produces a set of deterministic observables that characterize the wave propagation, attenuation, and energy distribution in the 1-D heterogeneous medium.

All observables are computed from the discrete numerical approximation. They are internally consistent within that approximation but are not guaranteed to satisfy exact continuum energy conservation beyond the discretization error.

---

## Observable Definitions

### `max_displacement`

**Description:** Maximum absolute displacement across all spatial nodes and all time steps.

**Formula:** `max(|u[i,t]|)` over all `i`, `t`

**Units:** Same as displacement input units (caller-defined)

**Interpretation:** Global peak amplitude of the wave field. Serves as the reference for computing `attenuation_ratio`.

---

### `max_core_displacement`

**Description:** Maximum absolute displacement within the core region `[core_start, core_end)`.

**Formula:** `max(|u[i,t]|)` over all `i in [core_start, core_end)`, all `t`

**Units:** Same as displacement input units (caller-defined)

**Interpretation:** Peak amplitude of the wave within the heterogeneous region. Used to quantify the attenuation effect of the core material.

---

### `max_velocity`

**Description:** Maximum absolute velocity across all spatial nodes at the final time step.

**Formula:** `max(|v[i]|)` where `v[i] = (u_final[i] - u_prev[i]) / dt` (backward difference)

**Units:** Displacement/time (caller-defined)

**Interpretation:** Peak particle velocity at the end of the simulation. Approximate proxy for maximum kinetic energy.

---

### `incident_energy`

**Description:** Approximate energy injected by the source.

**Formula:** `Σ (source[i,t] * u[i,t]) * dx * dt` over source duration

**Units:** Energy units consistent with the caller's unit system

**Interpretation:** Discrete approximation of the work done by the source force on the medium. Represents the total incident energy entering the system.

**Limitation:** This is a discrete trapezoidal-style integral of `source * displacement`. It does not account for energy that may reflect back and do negative work on the source.

---

### `reflected_energy`

**Description:** Approximate reflected energy at the left boundary (`x=0`).

**Formula:** `Σ (0.5 * rho[0] * v[0,t]^2) * dx * dt` over all time steps where `t > 0`

**Units:** Energy units consistent with the caller's unit system

**Interpretation:** Kinetic energy proxy at the left boundary node. Approximates energy that has reflected from the left boundary.

**Limitation:** This is a kinetic-energy proxy at a single boundary node, not a rigorous energy flux integral. It is useful for qualitative comparison but should not be interpreted as an exact reflection coefficient.

---

### `transmitted_energy`

**Description:** Approximate transmitted energy at the right boundary (`x=L`).

**Formula:** `Σ (0.5 * rho[N-1] * v[N-1,t]^2) * dx * dt` over all time steps where `t > 0`

**Units:** Energy units consistent with the caller's unit system

**Interpretation:** Kinetic energy proxy at the right boundary node. Approximates energy that has transmitted through the domain.

**Limitation:** Same as `reflected_energy` — this is a proxy, not a rigorous flux integral.

---

### `dissipated_energy`

**Description:** Estimated energy dissipated via viscous damping.

**Formula:** `Σ (gamma[i] * v[i,t]^2) * dx * dt` over all nodes and time steps

**Units:** Energy units consistent with the caller's unit system

**Interpretation:** Total viscous dissipation over the simulation duration. Should increase monotonically with increased damping.

**Note:** This quantity is consistent with the numerical scheme's dissipation model. For zero damping, this value should be approximately zero (up to floating-point roundoff).

---

### `core_energy`

**Description:** Total discrete mechanical energy within the core region at the final time step.

**Formula:** `kinetic_core + elastic_core`

where:
```
kinetic_core = Σ (0.5 * rho[i] * v[i]^2) * dx   over i in core region
elastic_core = Σ (0.5 * E[i] * (du/dx)^2) * dx  over core interior edges
```

**Units:** Energy units consistent with the caller's unit system

**Interpretation:** Snapshot of mechanical energy in the core at the final time step. Reflects how much wave energy remains trapped or attenuated in the heterogeneous region.

**Limitation:** This is a snapshot at the final time step, not an integral over the full simulation duration. It captures the residual energy state.

---

### `attenuation_ratio`

**Description:** Normalized peak displacement within the core relative to global peak displacement.

**Formula:** `max_core_displacement / max_displacement` (or `0.0` if `max_displacement == 0`)

**Units:** Dimensionless ratio

**Interpretation:** A value of `0.0` means the core was completely undisturbed. A value of `1.0` means the core experienced the same peak amplitude as the global maximum (no attenuation). Values between `0` and `1` indicate partial attenuation.

**Note:** This is a spatial-peak ratio, not a rigorous energy transmission coefficient. It is sensitive to where the global maximum occurs and does not account for energy distribution shape.

---

## Energy Accounting Limitations

The energy observables (`incident_energy`, `reflected_energy`, `transmitted_energy`, `dissipated_energy`, `core_energy`) are computed from the discrete numerical approximation. They are internally consistent within that approximation but:

1. They do not satisfy exact continuum energy conservation laws.
2. Boundary proxies (`reflected_energy`, `transmitted_energy`) are computed at single nodes, not as rigorous flux integrals.
3. The `core_energy` is a snapshot at the final time, not a time-integrated quantity.
4. Numerical dispersion and discretization error mean the sum of these quantities may not equal the incident energy.

For scientific comparisons, the important property is that the same discretization and parameters produce consistent relative results. Absolute energy conservation is not claimed.

---

## Determinism Verification

Each run produces two SHA-256 hashes:

- `input_hash`: Hash of the canonical parameter JSON. Verifies that the same inputs produce the same computation.
- `output_hash`: Hash of the canonical observable values. Verifies that the same inputs produce the same outputs.

For identical `WaveLatticeParameters` and identical software version, the output is bit-for-bit reproducible on the same CPU and Python/NumPy version.

---

## Observable Bounds and Expected Ranges

| Observable | Expected Range | Notes |
|------------|----------------|-------|
| `max_displacement` | `[0, ∞)` | Non-negative; depends on source amplitude |
| `max_core_displacement` | `[0, ∞)` | Non-negative; should be less than `max_displacement` for attenuating cores |
| `max_velocity` | `[0, ∞)` | Non-negative |
| `incident_energy` | `[0, ∞)` | Zero when `source_amplitude = 0` |
| `reflected_energy` | `[0, ∞)` | Zero for perfect absorbing boundaries |
| `transmitted_energy` | `[0, ∞)` | Zero for perfect reflecting boundaries |
| `dissipated_energy` | `[0, ∞)` | Zero when `damping = 0` everywhere |
| `core_energy` | `[0, ∞)` | Non-negative |
| `attenuation_ratio` | `[0, ∞)` | Typically `[0, 1]` for passive materials; can exceed 1 in rare cases with local amplification |

---

## Scientific Usage Guidelines

1. **Use relative comparisons, not absolute values:** The numerical model is unit-agnostic. Compare ratios and differences between experiments rather than absolute magnitudes.
2. **Verify energy budget consistency:** When comparing baseline and heterogeneous experiments, check that `dissipated_energy` and `core_energy` differences are consistent with the `attenuation_ratio`.
3. **Treat boundary proxies as qualitative:** `reflected_energy` and `transmitted_energy` are proxies, not rigorous transmission/reflection coefficients.
4. **Use `attenuation_ratio` for hypothesis testing:** The primary falsifiable metric is `attenuation_ratio` relative to the experiment's `attenuation_threshold`.
5. **Document discretization parameters:** Always record `nodes`, `dx`, `dt`, `time_steps` alongside observables for reproducibility.
