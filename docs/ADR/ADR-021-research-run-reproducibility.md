# ADR-021: Research Run Reproducibility

## Status
Accepted (Phase 0.2)

## Context
Scientific computational runs require clear distinctions regarding the level of reproducibility guaranteed across environments, seeds, and hardware configurations.

## Decision
1. Explicitly categorize run outputs and artifact bundles into:
   * `BITWISE_REPRODUCIBLE`: Identical bytecode, container digest, and floating-point bitwise results.
   * `NUMERICALLY_REPRODUCIBLE`: Equivalent numerical convergence within specified $\epsilon$ tolerances across different architectures.
   * `SCIENTIFICALLY_REPRODUCIBLE`: Statistically consistent effect sizes and falsification conclusions under repeated random samplings.
2. Store comprehensive environment metadata (Python version, OS, random seed, input hashes, parameter hashes) on every `ExperimentRun`.

## Consequences
* Honest, transparent scientific lineage without claiming unrealistic bitwise parity across disparate CPU/GPU hardware.
