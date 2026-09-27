# ADR-007: Directional Research Specification

## Status
Accepted

## Context
Research rarely proceeds along a fixed linear script. It operates directionally toward targets subject to compute budgets, domain constraints, and epistemic boundaries.

## Decision
Incorporate Directional Programming constructs (`DirectionalSpecification`) defining `current_state`, `target_state`, `objectives`, `constraints`, `forbidden_actions`, and `success_criteria`. Candidate execution paths are generated as exploratory proposals rather than binding execution plans.

## Consequences
- Preserves human steering and constraint validation at every step.
