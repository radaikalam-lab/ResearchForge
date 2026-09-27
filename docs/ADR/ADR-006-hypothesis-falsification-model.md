# ADR-006: Hypothesis and Falsification Model

## Status
Accepted

## Context
Scientific claims require Popperian falsifiability. Unfalsifiable hypotheses cannot produce valid experimental conclusions.

## Decision
Mandate that every `Hypothesis` entity includes explicit `falsification_conditions`, `variables`, `assumptions`, and `predictions`. The `FalsificationEngine` evaluates results strictly as evidence states (`SUPPORTED`, `WEAKENED`, `CONTRADICTED`, `INCONCLUSIVE`, `UNTESTED`).

## Consequences
- Hypotheses without falsification criteria fail validation and cannot advance to experiment design.
