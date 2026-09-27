# SECURITY THREAT MODEL (PHASE 0.3 HARDENING)

## 1. Scope and Boundary
This document updates the ResearchForge security threat model to formalize threat boundaries across untrusted literature, sandbox execution, human cryptographic identity, replay integrity, and observability.

---

## 2. Threat Analysis Matrix

| Asset | Attacker Profile | Attack Vector | Boundary | Mitigation Mechanism | Verified By Test | Residual Risk |
|---|---|---|---|---|---|---|
| **Scientific State Machine** | Rogue Agent / Compromised Provider | Direct transition to `CONCLUSION_ACCEPTED` | Application Service / Domain Model | State machine transition guards; Human decision signature check | `test_state_machine.py`, `test_phase_0_3_contract_matrix.py` | None (enforced in domain) |
| **Human Scientific Authority** | Impersonator / Adversary | Forged or revoked human review signature | `ResearcherIdentity` / `HumanDecision` | Asymmetric Ed25519 cryptographic verification; status checks | `test_ed25519_human_decision_signature_and_revocation` | Local private key theft |
| **Execution Host / OS** | Malicious Experiment Code | Arbitrary command execution / filesystem breakout | Execution Backend & Capability Grants | Read-only mounts, `--network none`, container isolation, capability grants | `test_sandbox_policy_enforcement.py` | Container escape 0-day |
| **Provenance Ledger** | Insider / Database Tamperer | Altering historical events or reordering chain | Provenance Ledger / Checkpoints | SHA-256 parent hash chaining, signed checkpoints, chain verification | `test_checkpoint_and_tamper.py` | Key compromise of checkpoint signer |
| **System Credentials** | Telemetry Eavesdropper | Logging private keys / API tokens | Telemetry & Observability Filter | `sanitize_telemetry_payload()` redaction and hashing | `test_observability_secret_leakage.py` | Obfuscated secrets in custom fields |
| **Idempotency Store** | Concurrent Attacker / Race condition | Replaying request with different payload under same key | `IdempotencyRepository` | Request payload hash comparison; `IdempotencyConflict` exception | `test_idempotency_conflict_on_mismatched_payload` | Key collision in SHA-256 (negligible) |
| **Thread State** | Concurrent Worker | Concurrent mutation of same thread branch | Aggregate Root / Repository | Optimistic concurrency version check (`OptimisticConcurrencyError`) | `test_optimistic_concurrency_conflict_on_stale_thread` | None |
| **External Literature** | Hostile Web / PDF Source | Prompt injection in abstracts / hostile URLs | Literature Provider Boundary | Literature marked untrusted; sanitization before extraction | `test_threat_controls.py` | Semantic adversarial text |

---

## 3. Assumptions & Trust Anchors
- Host kernel and Python runtime are trusted.
- Database access credentials and local filesystem keys are safeguarded by host OS permissions.
- Ed25519 private keys for researchers remain on researcher client devices and are never submitted to servers or logged.
