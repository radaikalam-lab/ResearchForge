# ADR-009: Execution Authority Boundary

## Status
Accepted

## Context
Running arbitrary computational experiments or simulations without explicit security and resource boundaries exposes systems to unconstrained resource consumption or side effects.

## Decision
All executable operations must be packaged as an `ExecutionRequest` validated against an `ExecutionPolicy` within an `ExecutionSandbox`. Epistemic and reasoning components have zero direct execution authority.

## Consequences
- Strict containment of simulation runs, code execution, and filesystem operations.
