# Wave Lattice Numerical Model (Phase 2.2)

## Governing Equation

The reference operator solves the 1-D heterogeneous damped-wave equation:

```
rho(x) * u_tt(x,t) + gamma(x) * u_t(x,t) = d/dx [ E(x) * du/dx ] + source(x,t)
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

## Spatial Discretization

Uniform grid: `x_i = i * dx`, `i = 0, ..., N-1`

### Material Fields

Each node `i` has its own material properties:

```text
rho[i] = density if i not in [core_start, core_end)
       = core_density otherwise

E[i] = stiffness if i not in [core_start, core_end)
     = core_stiffness otherwise

gamma[i] = damping if i not in [core_start, core_end)
         = core_damping otherwise
```

### Interface Stiffness

At interfaces between cells with different stiffness, use the harmonic mean:

```
E_{i+1/2} = 2 * E[i] * E[i+1] / (E[i] + E[i+1])
```

This provides a conservative approximation of the flux continuity condition.

---

## Temporal Discretization

Uniform time steps: `t_n = n * dt`, `n = 0, ..., T-1`

---

## Finite-Difference Scheme

### Central Differences

Temporal:
```
u_tt ≈ (u[t+1,i] - 2*u[t,i] + u[t-1,i]) / dt²
u_t  ≈ (u[t+1,i] - u[t-1,i]) / (2*dt)
```

Spatial:
```
d/dx[E * du/dx] ≈ (E_{i+1/2}*(u[t,i+1]-u[t,i]) - E_{i-1/2}*(u[t,i]-u[t,i-1])) / dx²
```

### Update Coefficients

```
A[i] = rho[i]/dt² + gamma[i]/(2*dt)
B[i] = 2*rho[i]/dt²
C[i] = rho[i]/dt² - gamma[i]/(2*dt)
```

### Update Equation

Solving for `u[t+1,i]`:

```
u[t+1,i] = (B[i]*u[t,i] - C[i]*u[t-1,i] + stiffness_term_i + source[t,i]) / A[i]
```

where:
```
stiffness_term_i = (E_{i+1/2}*(u[t,i+1]-u[t,i]) - E_{i-1/2}*(u[t,i]-u[t,i-1])) / dx²
```

---

## Boundary Conditions

### DIRICHLET (Fixed Wall)

```
u[0,t] = 0    for all t
u[N-1,t] = 0  for all t
```

Wave reflects from both ends.

### ABSORBING (Mur 1st-Order Transparent)

```
u_next[0] = u_curr[1] + mur_left * (u_next[1] - u_curr[0])
u_next[N-1] = u_curr[N-2] + mur_right * (u_next[N-2] - u_curr[N-1])
```

where:
```
mur_left  = (c_left * dt - dx) / (c_left * dt + dx)
mur_right = (c_right * dt - dx) / (c_right * dt + dx)

c_left  = sqrt(E[0] / rho[0])
c_right = sqrt(E[N-1] / rho[N-1])
```

This approximates a one-way absorbing boundary, reducing spurious reflections.

---

## Source Function

Smooth Gaussian-shaped pulse applied at `source_location`:

```
source[source_location, t] = A * sin²(π * t / T_src)   for t < T_src
source[source_location, t] = 0                           for t ≥ T_src
```

where `A = source_amplitude`, `T_src = source_duration`.

The sin² ramp provides smooth onset and avoids Gibbs-like numerical artifacts from a step source.

---

## Stability Condition (CFL)

The explicit scheme requires:

```
dt ≤ dx / max_x( c(x) )   where  c(x) = sqrt(E(x)/rho(x))
```

This is the Courant-Friedrichs-Lewy condition for the 1-D wave equation.

**Enforcement:** This condition is checked at `WaveLatticeParameters` construction time. Invalid parameters raise `ValueError` before any computation is performed.

---

## Algorithm Summary

```
1. Initialize material fields rho, E, gamma with core region overrides
2. Compute interface stiffness E_half
3. Compute update coefficients A, B, C
4. Initialize u_prev = 0, u_curr = 0
5. Initialize accumulators for observables
6. Compute Mur boundary coefficients
7. For t = 0 to T-1:
   a. Compute u_next for interior nodes using update equation
   b. Apply boundary conditions
   c. Accumulate observables (max displacement, fluxes, dissipation)
   d. Advance: u_prev = u_curr, u_curr = u_next
8. Compute final observables (velocity, core energy, hashes)
9. Return WaveLatticeObservables and final state
```

---

## Numerical Accuracy Notes

- The scheme is second-order accurate in space and time for smooth solutions.
- At material interfaces, the harmonic mean approximation introduces O(dx) error in the flux.
- The Mur absorbing boundary is first-order accurate; higher-order schemes are possible but not implemented.
- Energy quantities are discrete approximations consistent with the numerical scheme; they do not satisfy exact continuum conservation laws.
