# RESEARCHFORGE — SANDBOX IMPLEMENTATION & EXECUTION ISOLATION

## 1. Execution Boundary Architecture

ResearchForge enforces multi-layer isolation for computational experiment runs via `ExecutionSandbox`.

```text
               [ExecutionRequest]
                       ↓
         [ExecutionPolicy & Capability Verification]
          ├── Valid CapabilityGrant Present?
          ├── Unexpired Grant?
          ├── Scope Matches Request?
                       ↓
             [Execution Isolation Boundary]
          ├── Network Disabled (Default Deny)
          ├── Filesystem Confinement (allow_filesystem_write check)
          └── Timeout Watchdog (max_time_sec enforcement)
                       ↓
             [ExperimentResult + SHA-256 Output Hash]
```

---

## 2. Windows & Development Environment Enforcement

For local development and Windows environments, `ReferenceExecutionBackend` operates with explicit security assertions:
* **Capability Guard**: Execution is aborted immediately if required capabilities are not actively granted.
* **Network Deny Guard**: Blocked when policy `allow_network=False`.
* **Filesystem Boundary**: Writes outside permitted temporary/artifact directories are strictly prohibited.
* **Timeout Enforcement**: Long-running simulations exceeding `max_time_sec` are terminated by async timeouts.
* **Container Isolation**: In production, containerized execution (Docker/OCI runtime) provides OS-level network namespace dropping and CPU/memory cgroup limits.
