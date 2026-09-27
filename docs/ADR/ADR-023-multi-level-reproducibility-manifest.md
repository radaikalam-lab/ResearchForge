# ADR-023: Multi-Level Reproducibility Classification and Verifiable Manifests

## Status
Accepted (Frozen in Phase 0.3)

## Context
Scientific computational results cannot always guarantee bitwise identical binary representations across heterogeneous hardware, compilers, operating systems, and floating-point units. Conflating provenance reproducibility with bitwise binary reproducibility creates false guarantees or rejects valid reproducible research.

## Decision
1. Establish a formal 4-level reproducibility taxonomy:
   - **LEVEL_0_PROVENANCE**: Full audit trail, immutable hash DAG, and event causality preserved.
   - **LEVEL_1_COMPUTATIONAL**: Deterministic logic, seeded pseudo-random number generators, and reproducible statistical outcomes.
   - **LEVEL_2_ENVIRONMENT**: Pinned Python runtime, OS architecture, and exact locked dependencies.
   - **LEVEL_3_BITWISE**: Exact container digest, pinned BLAS/LAPACK runtime, and bit-for-bit identical floating-point arithmetic.
2. Require every completed research trajectory to generate a machine-verifiable `reproducibility/manifest.json` capturing parameter hashes, input/output content digests, git revisions, platform metadata, and checkpoint links.

## Consequences
- Transparent, auditable reproducibility claims with precise boundary criteria.
- Support for machine-automated reproducibility validation across execution environments.
