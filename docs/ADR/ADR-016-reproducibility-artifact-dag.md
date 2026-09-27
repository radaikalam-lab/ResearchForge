# ADR-016: Reproducibility Artifact DAG

## Status
Accepted

## Context
Scientific artifacts (figures, tables, manuscripts) are derived from upstream datasets, simulations, and statistical analyses. Modifying an upstream entity must cleanly invalidate downstream artifacts.

## Decision
Implement an explicit `ArtifactDependencyDAG` in `ArtifactManager`. Modifying or invalidating an upstream artifact recursively marks child artifacts as `INVALIDATED` and emits `ARTIFACT_INVALIDATED` provenance events.

## Consequences
- Prevents stale or corrupted figures and manuscripts from being treated as verified.
