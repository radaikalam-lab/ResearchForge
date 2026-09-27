# ADR-019: Reference Execution Backend

## Status
Accepted (Phase 0.2)

## Context
Phase 0.2 requires executing sandboxed computational runs across varied developer environments (including Windows without root privileges) while strictly enforcing capability grants, network denial, filesystem confinement, and compute timeouts.

## Decision
1. Implement `ExecutionSandbox` / `ReferenceExecutionBackend` with explicit programmatic policy guards.
2. Verify active, unexpired `CapabilityGrant` objects before dispatching computation.
3. Reject network access requests when `allow_network=False`.
4. Restrict filesystem write paths to verified sandbox working directories.
5. In production environments with Docker/OCI available, delegate to containerized workers; in local reference mode, enforce through the Python execution sandbox.

## Consequences
* Verifiable security guarantees across all environments.
* Transparent documentation of isolation mechanisms without claiming unsupported OS-level sandboxing.
