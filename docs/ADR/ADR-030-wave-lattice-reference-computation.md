# ADR-030: Wave Lattice Reference Computation

**Status:** Accepted  
**Date:** 2026-09-27  
**Phase:** 2.2 — Wave Computation Integration  

---

## Context

ResearchForge Phase 2.1 established a formally verified architecture:

```
API / CLI
    ↓
Application Services
    ↓
Semantic Graph
    ↓
Graph Persistence Port
    ↓
Persistence Adapter
    ↓
Physical Database
```

with the following boundaries:

- API must not import `UnitOfWork`, `persistence.models`, or `SQLAlchemy`
- Domain must be persistence-independent
- Cognitia is advisory-only

Phase 2.2 introduces a scientific computation workload (1-D heterogeneous
damped-wave lattice) that must be governed by ResearchForge as a scientific
experiment, not as a standalone utility.

---

## Decision

### 1. The wave operator is a pure domain function

`simulate_1d_damped_wave_lattice(WaveLatticeParameters) → dict` is a pure,
deterministic function in `researchforge.domain.models.wave_lattice`.

It has:
- No side effects
- No database access
- No Cognitia access
- No network access
- No mutable state
- Deterministic output (same params → same output_hash)

### 2. The operator is governed by an explicit input contract

`WaveLatticeParameters` is a Pydantic model with:
- CFL stability validation at construction time
- Fully explicit material properties (density, stiffness, damping — separately)
- Fully explicit core region geometry
- Fully explicit source and boundary conditions

### 3. The operator uses a correct explicit finite-difference scheme

The governing equation is:

```
rho(x) · u_tt + gamma(x) · u_t = d/dx [ E(x) · du/dx ] + source(x,t)
```

NOT a spatial-only iteration (the previous code had no time dimension).

The scheme:
- Has explicit time and space dimensions (`u[x, t]`)
- Uses previous-time (`u_prev`) and current-time (`u_curr`) state
- Computes interface stiffness via harmonic mean
- Checks CFL stability condition

### 4. Material properties are distinct concepts

| Property | Symbol | Meaning |
|----------|--------|---------|
| Density | ρ | Inertia |
| Stiffness | E | Wave speed, restoring force |
| Damping | γ | Energy dissipation |

These are independent parameters, not aliases for each other.

### 5. The heterogeneous core is represented as a material region

The "core" is represented as spatial indices `[core_start, core_end)` with
independent `core_density`, `core_stiffness`, `core_damping` — not as
mystical damping or hard-coded conclusions.

### 6. The experiment is represented in the semantic graph

All wave experiments flow through the ResearchForge experiment trajectory:
```
Hypothesis → TESTED_BY → Experiment → EXECUTED_AS → ExperimentRun
ExperimentRun → PRODUCES → (implicitly, observables stored in ExperimentRun.results)
StatisticalAnalysis → INFORMS_FALSIFICATION → FalsificationEvaluation
FalsificationEvaluation → EVALUATES → Hypothesis
```

This uses the existing ontology without parallel frameworks.

### 7. Persistence goes through UnitOfWork in the application layer

`WaveLatticeWorkflowService` owns the `UnitOfWork` and calls the pure operator
BEFORE opening the transaction:

```python
# Pure computation — no persistence
raw_output = simulate_1d_damped_wave_lattice(params)

# Atomic persistence — application boundary
with UnitOfWork(db_manager) as uow:
    ...persist results...
```

### 8. Cognitia boundary is preserved

The wave simulation never calls Cognitia.
Cognitia may receive bounded semantic graph context for advisory analysis
through the existing advisory workflow, but this is never automatic.

### 9. Replay is deterministic

Replay requires only `WaveLatticeParameters` — no Cognitia, no LLM, no network.

---

## Rejected Alternatives

| Alternative | Reason Rejected |
|-------------|-----------------|
| Promote existing spatial-iteration code | No time dimension; not a wave simulation |
| Hard-code damping as stiffness | Conflates physically distinct properties |
| Call Cognitia during computation | Violates determinism and Cognitia isolation |
| Encode conclusion in simulator | Violates falsifiability; not scientific |
| Direct SQLAlchemy access in operator | Violates persistence boundary |
| Separate experimental framework | ResearchForge already has the trajectory |

---

## Consequences

### Positive
- Wave simulation is a reproducible ResearchForge experiment with full provenance
- Hypothesis is falsifiable; conclusion is not pre-encoded
- Architecture boundaries are preserved
- Replay is deterministic without external dependencies
- Scientific operator is testable in isolation

### Negative / Mitigations
- Energy observables are discrete approximations (documented as limitations)
- Mur absorbing boundary is 1st-order (sufficient for reference; higher-order is future work)
- No adaptive time-stepping (CFL restriction documented explicitly)
