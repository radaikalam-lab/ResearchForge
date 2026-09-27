# Security Threat Model (Section 25, 26)

ResearchForge treats all external scientific content, literature, LLM responses, and provider queries as **UNTRUSTED DATA**.

---

## 1. Threat Analysis & Concrete Mitigations

| Threat | Attack Surface | Likelihood | Impact | Control & Mitigation | Detection Mechanism | Test Identifier |
| :--- | :--- | :---: | :---: | :--- | :--- | :--- |
| **Sandbox Escape** | Simulation & Experiment Execution | Low | Critical | Strict `ExecutionPolicy`, memory caps, timeout enforcement, process limits | Sandbox monitor & OS exit codes | `test_security_sandbox_isolation` |
| **Prompt Injection via Papers/PDFs** | Literature parsing & Evidence extraction | High | High | **Untrusted Data Invariant**: Literature is purely data, never parsed as system instructions or capability grants | Schema validation on extracted text | `test_untrusted_literature_injection_treated_as_data` |
| **Prompt Injection via Datasets** | Ingested tabular/numerical datasets | Medium | High | Strict Pydantic parsing into float arrays, rejecting executable macros | Type validation error on ingestion | `test_dataset_injection_rejection` |
| **Malicious Provider Response** | External APIs / Mock LLMs | Medium | High | Runtime contract validation (`ProviderResponseValidationError`), zero execution authority for Tier 0 | Schema parser exceptions | `test_malicious_provider_response_handling` |
| **Network Exfiltration** | Computational simulation scripts | Medium | High | `allow_network = False` (DENY by default) in all sandbox policies | Sandbox policy validator | `test_network_denial_enforcement` |
| **Secret Leakage** | Provenance Ledger & Artifacts | High | High | Recursive secret scrubbing BEFORE Merkle hashing, recording `redaction_metadata` | Audit scanner & regex filter | `test_secret_redaction_before_hash` |
| **Tampered Provenance Ledger** | File modification on disk | Low | Critical | Merkle parent hash chaining, signed checkpoints, `detect_tampering()` | Cryptographic hash verification | `test_tampered_provenance_detection` |
| **Path Traversal** | Artifact writing / Source import | Medium | High | Strict path normalization and allowlist validation (`allowed_write_directories`) | Directory scope checker | `test_path_traversal_prevention` |
| **Resource Exhaustion** | Runaway numerical simulations | High | Medium | `max_time_sec`, `max_memory_mb`, `max_processes` limits | Process timeout & kill | `test_resource_limits_enforced` |
| **Artifact Poisoning** | Swapped dataset on disk | Medium | Critical | Content-addressable SHA-256 verification and cascade DAG invalidation | Checksum mismatch detector | `test_artifact_poisoning_detection` |
