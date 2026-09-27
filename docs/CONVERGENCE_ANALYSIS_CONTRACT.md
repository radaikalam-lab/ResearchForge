# Convergence Analysis Contract (Phase 2.3)

## Overview

This document specifies the contract for convergence studies in ResearchForge Phase 2.3.

A convergence study measures how a numerical solution approaches the exact solution as spatial and temporal resolution are refined.

## ConvergenceStudy Entity

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `id` | `str` | Unique study identifier |
| `study_id` | `str` | Unique study identifier (semantic) |
| `model_id` | `str` | Model under study |
| `base_params` | `dict[str, Any]` | Base parameter set held fixed |
| `refinement_params` | `list[str]` | Parameters varied (e.g. `["dx", "dt"]`) |
| `refinement_levels` | `list[dict[str, Any]]` | Specific parameter values at each level |
| `metric_name` | `str` | Observable or error metric tracked |
| `metric_values` | `list[float]` | Metric value at each level |
| `convergence_order` | `float \| None` | Estimated convergence order |
| `reference_solution_id` | `str \| None` | Reference solution used |
| `is_convergent` | `bool \| None` | Whether study demonstrates convergence |
| `metadata` | `dict[str, Any]` | Additional metadata |

## Refinement Strategy

For the wave-lattice reference model, convergence is studied by refining:
- `dx` (spatial resolution)
- `dt` (temporal resolution)

While holding physical parameters fixed:
- `density`
- `stiffness`
- `damping`
- `source_amplitude`
- `source_location`
- `source_duration`
- `boundary_condition`

## Metrics

Supported metrics:
- `max_displacement`
- `max_core_displacement`
- `max_velocity`
- `incident_energy`
- `dissipated_energy`
- `core_energy`
- `attenuation_ratio`

## Convergence Order Estimation

For refinement factors `f_1, f_2, ..., f_n` and corresponding metric values `m_1, m_2, ..., m_n`:

```
convergence_order ≈ -d(log(m) / d(log(f))
```

Computed via linear regression on log-log plot.

## Reference Solutions

Reference solutions are labeled with their type:
- `ANALYTICAL` — exact analytical solution
- `MANUFACTURED` — deliberately constructed known solution
- `HIGH_RESOLUTION_NUMERICAL` — high-resolution numerical reference
- `CROSS_SOLVER` — comparison with different solver
- `EXPERIMENTAL_DATA` — experimental measurements

**Never label a high-resolution simulation as "ground truth" unless an actual validated ground truth exists.**

## Critical Rules

1. **Do not invent an analytical reference solution where none exists.**
2. **A high-resolution numerical reference is a numerical reference, not ground truth.**
3. **Convergence studies must hold physical parameters fixed while refining resolution.**
4. **The comparison must answer: Is the difference larger than numerical discretization effects?**
