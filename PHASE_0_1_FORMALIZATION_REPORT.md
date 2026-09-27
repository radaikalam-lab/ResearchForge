# PHASE 0.1 ARCHITECTURE FORMALIZATION & REVIEW REMEDIATION REPORT

**Repository**: `https://github.com/radaikalam-lab/ResearchForge`  
**Local Workspace**: `E:\ResearchForge`  
**Date**: September 27, 2026  
**Status**: COMPLETE (All 58 Tests Passing, 0 Errors, 0 Warnings, Ruff Clean, Doctor Healthy)

---

## 1. Existing Scaffold Baseline

The Phase 0 scaffold established the fundamental architectural boundaries of ResearchForge:
- **Core Environment**: Python 3.13.14, FastAPI, Typer CLI, Pydantic v2, pytest with zero warning tolerance (`-W error`).
- **Original Baseline**: 39 passed tests covering epistemic boundaries, provider contracts (Citation, Cognitia, Evidence, Experiment, Gap, Literature, Publication, Reasoning, Retrieval, Simulation, Statistics), execution sandboxing, artifact registration, and architectural invariants A–J.
- **Doctor CLI**: CLI health checks verifying all 11 provider contracts dynamically.

---

## 2. Review Findings Addressed

The Phase 0.1 pass formalized conceptual definitions into executable specifications:
1. **Lifecycle Granularity**: Replaced single-level 17-state project assumption with a hierarchical state machine model.
2. **Authority Enforcement**: Enforced authority tier requirements in transition engine and execution runtime.
3. **Domain Metamodel**: Categorized domain types into `ValueObject`, `Entity`, and `AggregateRoot` with proper mutability semantics.
4. **Canonical Schemas**: Established typed DTOs, request/response models, and error hierarchies across all provider contracts.
5. **Cryptographic Provenance**: Implemented canonical hashing (RFC 8785 semantics), redaction before hashing, and signed checkpoint verifications.
6. **Artifact DAG & Invalidation**: Added direct dependency tracking and recursive cascade invalidation (`INVALIDATED` state).
7. **Threat Model & Security**: Documented comprehensive threat taxonomy and implemented security controls against path traversal, network exfiltration, prompt injection as untrusted data, and capability violations.

---

## 3. State Machine Changes

Introduced discrete, hierarchical state machines in [`backend/researchforge/domain/state_machine.py`](file:///e:/ResearchForge/backend/researchforge/domain/state_machine.py):
- **Project Lifecycle** (`ResearchLifecycleState`): Aggregate state derived from sub-threads without conflating heterogeneous progress.
- **Hypothesis Lifecycle** (`HypothesisLifecycleState`): `DRAFT` -> `FORMED` -> `CRITIQUE_PENDING` -> `CRITIQUED` -> `EXPERIMENT_DESIGN_PENDING` -> `EXPERIMENT_READY` -> `UNDER_TEST` -> `EVIDENCE_AVAILABLE` -> `FALSIFICATION_PENDING` -> `EVALUATION_PENDING` -> `HUMAN_REVIEW` -> `ACCEPTED` / `REJECTED` / `INCONCLUSIVE` / `SUPERSEDED` / `INVALIDATED`.
- **Experiment Lifecycle** (`ExperimentLifecycleState`): `DRAFT` -> `DESIGNED` -> `VALIDATED` -> `READY` -> `QUEUED` -> `RUNNING` -> `COMPLETED` / `FAILED` / `CANCELED` / `INVALIDATED`.
- **Run Lifecycle** (`RunLifecycleState`): `CREATED` -> `APPROVED` -> `STARTED` -> `RUNNING` -> `COMPLETED` / `FAILED` / `CANCELED` / `INVALIDATED`.
- **Artifact Lifecycle** (`ArtifactLifecycleState`): `DRAFT` -> `BUILDING` -> `VERIFIED` -> `PUBLISHED` / `INVALIDATED` / `SUPERSEDED`.
- **Executable Transition Engine** (`TransitionEngine`): Enforces required actor tiers, guard conditions, required artifacts, and typed errors (`InvalidStateTransitionError`, `AuthorityViolationError`, `MissingArtifactError`, `GuardViolationError`, `InvalidatedDependencyError`).

---

## 4. Authority Model Changes

Enforced the four-tier epistemic authority matrix in [`docs/AUTHORITY_MATRIX.md`](file:///e:/ResearchForge/docs/AUTHORITY_MATRIX.md) and [`backend/researchforge/epistemic/boundary.py`](file:///e:/ResearchForge/backend/researchforge/epistemic/boundary.py):
- **Tier 0 (Proposal / LLM)**: May propose, retrieve, and extract. Prohibited from validating claims, approving executions, or modifying policies.
- **Tier 1 (Critique / Cognitia)**: May identify assumptions, critique hypotheses, evaluate representations, and plan candidate paths. Prohibited from executing experiments, invoking hardware, or approving scientific conclusions.
- **Tier 2 (Computation / Execution)**: May execute approved sandboxed computations within explicit `ExecutionPolicy` and `CapabilityGrant`. Prohibited from accepting scientific conclusions autonomously.
- **Tier 3 (Scientific Human Authority)**: Holds exclusive authority to accept or reject scientific conclusions, validate experimental findings, and authorize public artifact release.

---

## 5. Domain Model Changes

Refactored domain models in [`backend/researchforge/domain/base.py`](file:///e:/ResearchForge/backend/researchforge/domain/base.py) and [`backend/researchforge/domain/models/`](file:///e:/ResearchForge/backend/researchforge/domain/models/):
- **Base Classes**: `ValueObject` (immutable, hashable, no spurious ID/timestamp fields), `Entity` (identity-bearing with provenance tracking), and `AggregateRoot` (consistency boundary owner).
- **Research Thread Aggregate** ([`backend/researchforge/domain/models/thread.py`](file:///e:/ResearchForge/backend/researchforge/domain/models/thread.py)): Encapsulates concurrent investigation lines within a project.
- **Corrected Domain Directionality**: `ResearchGap` -> informs -> `Hypothesis` -> `Prediction` -> `Experiment` -> `Result` -> `FalsificationEvaluation` -> `HumanDecision` -> `Conclusion`.

---

## 6. Provider Contract Changes

Standardized typed DTOs and error hierarchies in [`backend/researchforge/domain/schemas/`](file:///e:/ResearchForge/backend/researchforge/domain/schemas/):
- Typed request/response models for all 11 providers (`LiteratureSearchRequest`, `EvidenceExtractionRequest`, `ExperimentExecutionRequest`, `SimulationRunRequest`, etc.).
- Uniform error taxonomy: `ProviderError`, `ProviderUnavailable`, `ProviderTimeout`, `ProviderRateLimited`, `ProviderAuthenticationError`, `ProviderCapabilityError`, `InvalidProviderRequest`, `ProviderResponseValidationError`, `ProviderConflict`.
- Explicit idempotency, pagination, and provenance tagging semantics across provider protocols.

---

## 7. Provenance Changes

Enhanced the provenance subsystem in [`backend/researchforge/provenance/`](file:///e:/ResearchForge/backend/researchforge/provenance/):
- **Canonical Event Registry** (`ProvenanceEventType`): 25+ formal event types covering full lifecycle operations.
- **Deterministic Hashing**: Canonical serialization and SHA-256 parent-chain chaining (`SHA256(canonical_payload + parent_hash)`).
- **Secret Redaction**: Redaction policy applied strictly *before* hashing with recorded metadata.
- **Ledger Checkpoints & Tamper Detection**: Signed checkpoints and verifiable integrity checks that detect modified or reordered events.

---

## 8. Reproducibility Changes

Formalized reproducibility mechanisms in [`docs/REPRODUCIBILITY_BUNDLE_SPEC.md`](file:///e:/ResearchForge/docs/REPRODUCIBILITY_BUNDLE_SPEC.md) and [`backend/researchforge/artifacts/manager.py`](file:///e:/ResearchForge/backend/researchforge/artifacts/manager.py):
- **Artifact Dependency DAG**: Explicit upstream-downstream references across datasets, runs, figures, and manuscripts.
- **Cascade Invalidation**: When an upstream artifact or dataset is modified or invalidated, all downstream descendants transition to `INVALIDATED`.
- **Reproducibility Tiers**: Formally separated `BITWISE_REPRODUCIBLE`, `NUMERICALLY_REPRODUCIBLE`, and `SCIENTIFICALLY_REPRODUCIBLE`.

---

## 9. Security Changes

Implemented security controls and specifications in [`docs/THREAT_MODEL.md`](file:///e:/ResearchForge/docs/THREAT_MODEL.md) and [`docs/SECURITY_TEST_PLAN.md`](file:///e:/ResearchForge/docs/SECURITY_TEST_PLAN.md):
- **Untrusted Research Input Law**: External literature, PDFs, and scraped datasets are strictly DATA, never instruction sources for execution policies or authority grants.
- **Execution Sandboxing**: Default deny for network, filesystem, and subprocess execution without explicit `CapabilityGrant`.
- **Path Traversal & Resource Limits**: Path containment checks and execution timeout enforcement.

---

## 10. New Tests

Expanded test suite from 39 to 58 tests:
- `tests/domain/test_hierarchical_state_machine.py`: Verifies hypothesis/run state transitions, authority enforcement, and invalidation guards.
- `tests/provenance/test_checkpoint_and_tamper.py`: Verifies cryptographic checkpoint generation, tamper detection, and secret redaction.
- `tests/security/test_threat_controls.py`: Verifies path traversal blocking, capability denial, and untrusted literature injection resistance.
- `tests/integration/test_architectural_invariants.py`: Formally validates all 22 Architectural Invariants A through V.

---

## 11. Regression & Invariant Results

### Test Execution Summary
```text
pytest -v -W error
============================= 58 passed in 0.54s ==============================

ruff check .
All checks passed!

researchforge doctor --json
{"all_contracts_loaded":true,"contracts_registered":{"citation":true,"cognitia":true,"evidence":true,"experiment":true,"gap":true,"literature":true,"publication":true,"reasoning":true,"retrieval":true,"simulation":true,"statistics":true},"debug":false,"environment":"development","python_version":"3.13.14","status":"HEALTHY"}
```

### Architectural Invariants Status Table (A–V)
| Invariant | Description | Status |
|---|---|---|
| **A** | LLM cannot validate hypothesis | **PASS** |
| **B** | Cognitia cannot execute experiment | **PASS** |
| **C** | Execution requires ExecutionPolicy | **PASS** |
| **D** | Unsupported claim cannot reach CONCLUSION_ACCEPTED | **PASS** |
| **E** | Accepted finding requires evidence + provenance | **PASS** |
| **F** | Statistical conclusion requires numerical results | **PASS** |
| **G** | Manuscript claims require traceability | **PASS** |
| **H** | Upstream mutation invalidates artifacts | **PASS** |
| **I** | Providers can be swapped | **PASS** |
| **J** | Research trajectory can be replayed | **PASS** |
| **K** | Project state does not conflate heterogeneous child states | **PASS** |
| **L** | Hypothesis lifecycle is independent of other hypotheses | **PASS** |
| **M** | Experiment failure is preserved as research history | **PASS** |
| **N** | Invalidated artifacts cannot remain VERIFIED | **PASS** |
| **O** | Human authority is enforced at the transition layer | **PASS** |
| **P** | Provenance events have canonical typed schemas | **PASS** |
| **Q** | Tampering with the provenance chain is detectable | **PASS** |
| **R** | External literature cannot grant execution authority | **PASS** |
| **S** | Provider failures cannot corrupt domain state | **PASS** |
| **T** | Duplicate commands do not duplicate scientific artifacts | **PASS** |
| **U** | Changing upstream dependency invalidates descendants in DAG | **PASS** |
| **V** | Cognitia remains isolated behind its provider boundary | **PASS** |

---

## 12. Remaining Risks

1. **Storage Growth**: Immutable provenance ledgers with dense checkpoints will require compaction and archiving policies in enterprise workloads.
2. **Provider Rate Limiting**: Real-world external APIs (Semantic Scholar, Crossref, arXiv) will necessitate robust backoff, caching, and rate limiting queues in Phase 1.

---

## 13. Deferred Implementation

Intentionally deferred to Phase 1 and beyond (in compliance with Section 49):
- Live external API integrations (Scopus, Web of Science, OpenAlex, Semantic Scholar).
- Distributed task runners (Celery/Arq/HPC schedulers).
- Full multi-tenant enterprise IAM and OAuth2 servers.
- Autonomous publication pipeline.

---

## 14. Recommended Phase 1

With Phase 0.1 fully hardened and verified:
1. **Vertical Slice Implementation**: Implement the end-to-end flow:
   `Research Question` -> `Literature Search` -> `Evidence Extraction` -> `Research Gap Analysis` -> `Hypothesis Formulation`.
2. **Local Vector & Semantic Indexing**: Implement local SQLite / LanceDB / DuckDB storage for cached literature fragments.
3. **Cognitia Protocol Bridge**: Connect Cognitia formal epistemic critique models to evaluate formulated hypotheses against empirical literature bases.
