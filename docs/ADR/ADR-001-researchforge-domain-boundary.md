# ADR-001: ResearchForge Domain Boundary

## Status
Accepted

## Context
Scientific research systems frequently conflate literature search, reasoning, automated code execution, and manuscript generation into amorphous "AI agent" architectures. This leads to untraceable hallucinated claims and loss of experimental rigor.

## Decision
Establish ResearchForge as an auditable computational research lifecycle engine. ResearchForge coordinates projects, sources, evidence, computational experiments, statistical validations, and provenance. Human researchers maintain ultimate scientific authority.

## Consequences
- Domain layer remains free of external framework dependencies.
- Clear separation between computational plausibility and scientific validity.
