# Execution Policy & Capability Specification (Section 23, 24)

This specification defines the runtime isolation and capability controls governing computational experiments.

---

## 1. Execution Policy Dimensions (`ExecutionPolicy`)

* **`allow_network`**: `False` (DENY by default).
* **`allow_filesystem_write`**: `False` (READ_ONLY by default).
* **`allowed_write_directories`**: Whitelist of explicit directories (e.g. `["./artifacts/runs"]`).
* **`max_time_sec`**: Hard timeout (default: 300s).
* **`max_memory_mb`**: Memory limit (default: 2048 MB).
* **`max_cpu_percent`**: CPU ceiling (default: 80.0%).
* **`max_processes`**: Process concurrency limit (default: 1).
* **`allowed_commands`**: Allowlist of non-destructive executable commands.
* **`environment_allowlist`**: Whitelist of host environment variables exposed to the sandbox.

---

## 2. Capability Grants (`CapabilityGrant`)

A capability grant is an explicit token assigned to an execution request:
```json
{
  "grant_id": "grant_01j7abc...",
  "capability": "RUN_SIMULATION",
  "granted_by": "usr_lead_investigator",
  "granted_at": "2026-09-27T12:00:00Z",
  "expires_at": "2026-09-27T18:00:00Z",
  "provenance_event_id": "prov_01j7..."
}
```
Capabilities are NEVER granted implicitly to providers or external models.
