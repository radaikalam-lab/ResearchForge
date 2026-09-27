# ADR-013: Hierarchical Lifecycle State Model

## Status
Accepted

## Context
A single 17-state machine at the project root over-simplifies concurrent lines of investigation. If one hypothesis is rejected while another is under experiment, a single project state cannot accurately reflect research reality.

## Decision
Establish a hierarchical state model:
- `ResearchProject`: Coarse aggregate program state.
- `ResearchThread` / `Hypothesis`: 16-state granular hypothesis exploration.
- `Experiment`: 10-state design and readiness lifecycle.
- `ExperimentRun`: 9-state computational execution lifecycle.
- `ResearchArtifact`: 6-state verification and invalidation lifecycle.

## Consequences
- Independent hypothesis lifecycles prevent state corruption during concurrent exploration.
