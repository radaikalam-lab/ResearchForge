# Architecture Amendment 0.1: Formalization & Review Remediation

This amendment records the formalization upgrades introduced in Phase 0.1 over the Phase 0 baseline.

---

## 1. Summary of Upgrades

1. **Hierarchical State Machines**: Introduced dedicated state machines for `ResearchThread`/`Hypothesis` (16 states), `Experiment` (10 states), `Run` (9 states), and `Artifact` (6 states), preventing coarse project-level state conflation.
2. **Transition Engine & Typed Errors**: Transitions are now guarded by `TransitionEngine` with typed exceptions (`AuthorityViolationError`, `MissingArtifactError`, `GuardViolationError`, `InvalidatedDependencyError`).
3. **Canonical Schema Pack & DTOs**: Standardized typed request/response DTOs and `ProviderError` taxonomy across all 11 provider protocols.
4. **Cryptographic Checkpoints & Tamper Detection**: Provenance ledger extended with signed checkpoints and active tamper/truncation detection.
5. **Reproducibility DAG & Cascade Invalidation**: Formalized dependency tracking with recursive cascade invalidation upon upstream mutation.
6. **Security Threat Model & Untrusted Data Invariant**: Established formal rule that external literature and datasets are untrusted data, never instruction sources.
