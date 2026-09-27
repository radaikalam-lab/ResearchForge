# ADR-002: Cognitia Integration Boundary

## Status
Accepted

## Context
Cognitia provides advanced reasoning and epistemic critique capabilities. Direct embedding of Cognitia throughout ResearchForge would create tight coupling and risk unauthorized autonomous execution.

## Decision
Integrate Cognitia strictly via an isolated `CognitiaProvider` adapter. Cognitia acts as an advisory epistemic plane (evaluating claims, critiquing hypotheses, identifying hidden assumptions). Cognitia is explicitly prohibited from physical execution, unvetted state mutations, or autonomous publication.

## Consequences
- Clean boundary between epistemic evaluation and research orchestration.
- ResearchForge can operate standalone with mock or alternate reasoning providers.
