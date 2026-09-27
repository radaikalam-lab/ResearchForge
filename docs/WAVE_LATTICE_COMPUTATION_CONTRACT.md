# Wave Lattice Computation Contract (Phase 2.2)

## Overview

This document specifies the formal numerical contract for the ResearchForge
1-D Heterogeneous Damped-Wave Reference Operator (`simulate_1d_damped_wave_lattice`).

The operator is the **authoritative scientific computation** for wave attenuation
experiments in ResearchForge Phase 2.2. All inputs, outputs, and determinism
guarantees are defined below.

---

## Governing Equation

The operator implements the 1-D heterogeneous damped-wave equation:

```
rho(x) · u_tt + gamma(x) · u_t = d/dx [ E(x) · du/dx ] + source(x, t)
```

where:

| Symbol | Description | Units (caller-defined) |
|--------|-------------|------------------------|
| `u(x,t)` | Displacement field | length |
| `rho(x)` | Mass density | mass/length³ |
| `E(x)` | Elastic stiffness | pressure |
| `gamma(x)` | Viscous damping coefficient | mass/(length³·time) |
| `source(x,t)` | External body force density | force/length³ |

Local wave speed: `c(x) = sqrt(E(x) / rho(x))`

---

## Discretisation

### Spatial
Uniform grid: `x_i = i · dx`, `i = 0, ..., N-1`

Interface stiffness (harmonic mean):
```
E_{i+½} = 2·E_i·E_{i+1} / (E_i + E_{i+1})
```

### Temporal
Uniform time steps: `t_n = n · dt`, `n = 0, ..., T-1`

### Finite-Difference Scheme (explicit)

```
u^{n+1}_i = [B_i · u^n_i - C_i · u^{n-1}_i + stiffness_term_i / dx² + source^n_i] / A_i
```

where:
```
A_i = rho_i/dt² + gamma_i/(2·dt)
B_i = 2·rho_i/dt²
C_i = rho_i/dt² - gamma_i/(2·dt)

stiffness_term_i = E_{i+½}·(u^n_{i+1} - u^n_i) - E_{i-½}·(u^n_i - u^n_{i-1})
```

---

## Stability Condition (CFL)

The explicit scheme requires:

```
dt ≤ dx / max_x( c(x) )   where  c(x) = sqrt(E(x)/rho(x))
```

**Enforcement:** This condition is checked at `WaveLatticeParameters` construction time.
Invalid parameters raise `ValueError` before any computation is performed.

---

## Inputs Contract

| Parameter | Type | Constraint | Description |
|-----------|------|------------|-------------|
| `nodes` | int | ≥ 4 | Number of spatial grid points |
| `time_steps` | int | ≥ 2 | Number of time integration steps |
| `dx` | float | > 0 | Spatial grid spacing |
| `dt` | float | > 0, CFL | Time step |
| `density` | float | > 0 | Background mass density ρ |
| `stiffness` | float | > 0 | Background elastic stiffness E |
| `damping` | float | ≥ 0 | Background viscous damping γ |
| `core_start` | int | 0 ≤ core_start < core_end | First core node index |
| `core_end` | int | core_start < core_end ≤ nodes | One-past-last core node index |
| `core_density` | float | > 0 | Core region density ρ_core |
| `core_stiffness` | float | > 0 | Core region stiffness E_core |
| `core_damping` | float | ≥ 0 | Core region damping γ_core |
| `source_amplitude` | float | any | Peak amplitude of incident pulse |
| `source_location` | int | < nodes | Source node index |
| `source_duration` | int | ≥ 1 | Source duration in time steps |
| `boundary_condition` | enum | DIRICHLET or ABSORBING | Boundary condition type |

---

## Source Function

The source is a smooth Gaussian-shaped pulse (sin² ramp) applied at `source_location`:

```
source(source_location, t) = A · sin²(π · t / T_src)   for t < T_src
source(source_location, t) = 0                           for t ≥ T_src
```

where `A = source_amplitude`, `T_src = source_duration`.

This provides a smooth onset and avoids Gibbs-like numerical artifacts from a step source.

---

## Boundary Conditions

### DIRICHLET
```
u(0, t) = 0     ∀t
u(L, t) = 0     ∀t
```
Represents fixed walls. Wave reflects from both ends.

### ABSORBING (Mur 1st-order)
```
u^{n+1}_{0}   = u^n_1   + mur_left  · (u^{n+1}_1   - u^n_0)
u^{n+1}_{N-1} = u^n_{N-2} + mur_right · (u^{n+1}_{N-2} - u^n_{N-1})
```
where `mur = (c·dt - dx) / (c·dt + dx)`.

Represents transparent absorbing boundaries reducing spurious reflections.

---

## Outputs Contract

| Observable | Description | Limitation |
|------------|-------------|-----------|
| `max_displacement` | Max absolute displacement over all x, t | Exact within double precision |
| `max_core_displacement` | Max absolute displacement within core region | Exact within double precision |
| `max_velocity` | Max absolute velocity (backward-difference at final step) | Approximation |
| `incident_energy` | Discrete work done by source: Σ source·u·dx·dt | Discrete approximation |
| `reflected_energy` | Kinetic proxy at x=0: Σ ½ρv²·dx·dt | Proxy, not rigorous flux |
| `transmitted_energy` | Kinetic proxy at x=N-1: Σ ½ρv²·dx·dt | Proxy, not rigorous flux |
| `dissipated_energy` | Σ γ·v²·dx·dt over all nodes | Consistent with numerical scheme |
| `core_energy` | Kinetic + elastic energy in core at final time | Snapshot, not total dissipated |
| `attenuation_ratio` | max_core_displacement / max_displacement | Spatial-peak ratio |
| `input_hash` | SHA-256 of canonical parameter JSON | Determinism verification |
| `output_hash` | SHA-256 of canonical observable values | Determinism verification |

> **Limitation:** `reflected_energy` and `transmitted_energy` are kinetic-energy
> proxies at the boundary nodes, not rigorous energy flux integrals. They are
> useful for qualitative comparison but should not be interpreted as exact
> transmission/reflection coefficients.

---

## Determinism Guarantee

For identical `WaveLatticeParameters` and identical software version, the output is:
- **bit-for-bit reproducible** on the same CPU and Python/NumPy version
- **canonically hash-equivalent** via `output_hash`

Determinism is verified by the test `test_identical_params_produce_identical_output`.

Replay requires only `WaveLatticeParameters` — no Cognitia, no LLM, no network, no database.

---

## Architecture Isolation Contract

The wave operator (`researchforge.domain.models.wave_lattice`) must **never** import:

- `researchforge.persistence.*`
- `sqlalchemy.*`
- `researchforge.persistence.unit_of_work`
- `researchforge.providers.cognitia.*`
- `researchforge.execution.*`

This is enforced by the static AST tests in `tests/experiment/test_wave_lattice_operator.py`.
