# EXECUTION BACKEND CONTRACT SPECIFICATION

## 1. Overview
The execution subsystem decouples research workflow orchestration from code execution environments. Domain services never invoke OS-level subprocesses or binaries directly; all computational experiments run through implementations of the `ExecutionBackend` protocol.

---

## 2. Backend Classification

### 2.1 ReferenceExecutionBackend
- **Target Use Cases**:
  - Deterministic local unit and integration tests.
  - Trusted developer experiments and synthetic mathematical simulations.
  - Offline reference research trajectories.
- **Enforcement Mechanics**:
  - Validates `ExecutionPolicy` and active `CapabilityGrant` tokens.
  - Restricts execution scope to authorized function handles.
  - Enforces execution wall-clock timeouts.
- **Explicit Security Limitations**:
  - Does NOT provide hardware-level kernel namespace isolation on host systems.
  - Cannot strictly isolate raw arbitrary C/C++ binaries without underlying OS containers.
  - Windows environments rely on logical isolation rather than Linux cgroups.

### 2.2 ContainerExecutionBackend (Production Standard)
- **Target Use Cases**:
  - Arbitrary user-submitted research code, scripts, and model evaluations.
  - Multi-tenant execution environments and cloud runners.
- **Isolation Policy**:
  - **Runtime**: OCI-compliant container runtime (Docker / containerd / crun).
  - **Network Policy**: Denied by default (`--network none`). Egress allowed only via explicit `network_egress` capability.
  - **Filesystem Mounts**: Read-only root filesystem (`--read-only`), ephemeral tmpfs for workspace, and dedicated volume mount for artifact outputs.
  - **Resource Limits**: Pinned CPU core quota (`--cpus`), hard memory limit (`--memory`), and process count limit (`--pids-limit`).
  - **Secrets Injection**: Zero ambient secret propagation; credentials injected strictly on demand via in-memory environment variables.

---

## 3. Capability Grant Token Model

Every execution request requires an active `CapabilityGrant`:
```json
{
  "grant_id": "grant_991823",
  "capability": "execute_command",
  "scope": "run_sim_01",
  "granted_to": "service_orchestrator",
  "granted_at": "2026-09-27T08:00:00Z",
  "expires_at": "2026-09-27T08:15:00Z"
}
```

Any request lacking a matching, unexpired capability grant is rejected before dispatch.
