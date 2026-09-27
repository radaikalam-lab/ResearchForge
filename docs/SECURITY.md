# ResearchForge — Security & Execution Sandbox Specification

## 1. Execution Sandbox & Isolation

ResearchForge protects the host system and preserves data integrity through multi-layer execution policies:

1. **Explicit Execution Policies**: Code execution requires an explicit `ExecutionPolicy` specifying filesystem scope, network permission, memory limit, and timeout.
2. **Capability Grants**: Providers and tools must request specific permissions (`EXECUTE_SIMULATION`, `READ_DATASET`, `NETWORK_QUERY`).
3. **Secret Redaction**: API keys and auth headers are stripped from logs and provenance records.
4. **Local-First Boundary**: No private telemetry or unvetted external communication occurs.
