# CONTRACT FREEZE SPECIFICATION (PHASE 0.3)

## 1. Scope and Authority
This document serves as the normative contract freeze specification for **ResearchForge Phase 0.3**. All domain entity interfaces, state machine definitions, transition guards, provenance ledger schemas, persistence abstractions, cryptographic signing protocols, execution boundaries, and provider contracts specified herein are **FROZEN**.

---

## 2. Domain Entities & Invariants

### 2.1 Core Aggregate Roots & Entities
- **ResearchProject**: Root entity tracking project metadata, overall lifecycle state, and thread membership.
- **ResearchThread**: Independent exploratory branch possessing its own version counter (`optimistic concurrency control`), lifecycle state, hypotheses, runs, and artifacts.
- **ResearchQuestion**: Formulates empirical investigation with scope boundaries, primary variable, and target phenomenon.
- **Evidence**: Grounded empirical fact synthesizing one or more `EvidenceFragment` records tied to literature or experimental sources.
- **ResearchGap**: Formal scientific divergence or under-explored region between existing literature and target question.
- **Hypothesis**: Testable mechanistic assertion. **Invariant**: Must contain at least one explicit, falsifiable `FalsificationCriterion`.
- **Experiment**: Formal experimental design specifying variable manipulation, metrics, and parameters.
- **ExperimentRun**: Concrete execution instance capturing execution duration, return codes, output parameters, and stdout/stderr hashes.
- **StatisticalAnalysis**: Computed inferential statistics (p-values, effect sizes, confidence intervals).
- **FalsificationEvaluation**: Deterministic comparison between statistical metrics and hypothesis falsification thresholds.
- **HumanDecision**: Authorized researcher review record with mandatory cryptographic signature (Ed25519) and rationale.
- **Conclusion**: Accepted or rejected scientific finding binding evidence, analysis, falsification evaluation, and human decision.
- **ResearchArtifact**: Content-addressed research deliverable (reports, datasets, manuscripts) with SHA-256 integrity hash.

---

## 3. State Machine Transitions & Authority Matrix

| Transition | From State | To State | Required Authority | Transition Guard / Preconditions | Provenance Event |
|---|---|---|---|---|---|
| Define Question | `DRAFT` | `QUESTION_DEFINED` | System / Researcher | Non-empty question & primary variable | `PROJECT_CREATED` / `QUESTION_DEFINED` |
| Structure Evidence | `QUESTION_DEFINED` | `EVIDENCE_STRUCTURED` | Provider / Researcher | Verified source & valid fragments | `EVIDENCE_EXTRACTED` |
| Formulate Gap | `EVIDENCE_STRUCTURED` | `GAP_FORMULATED` | Provider / Researcher | Evidence refs & gap statement | `GAP_IDENTIFIED` |
| Propose Hypothesis | `GAP_FORMULATED` | `HYPOTHESIS_PROPOSED` | Provider / Researcher | At least 1 falsification criterion | `HYPOTHESIS_GENERATED` |
| Design Experiment | `HYPOTHESIS_PROPOSED` | `EXPERIMENT_DESIGNED` | Provider / Researcher | Metrics, variables, and parameters defined | `EXPERIMENT_DESIGNED` |
| Execute Experiment | `EXPERIMENT_DESIGNED` | `EXPERIMENT_EXECUTED` | Sandbox Backend | Active CapabilityGrant, execution policy | `EXPERIMENT_EXECUTED` |
| Analyze Results | `EXPERIMENT_EXECUTED` | `RESULTS_ANALYZED` | Statistics Provider | Valid run outputs & statistical metrics | `ANALYSIS_COMPUTED` |
| Evaluate Falsification | `RESULTS_ANALYZED` | `FALSIFICATION_EVALUATED` | Falsification Provider | Evaluated against all hypothesis criteria | `FALSIFICATION_EVALUATED` |
| Human Review Gate | `FALSIFICATION_EVALUATED` | `HUMAN_REVIEW` | System Pipeline | Falsification evaluation ready for gatekeeper | `HUMAN_REVIEW_REQUESTED` |
| Accept Conclusion | `HUMAN_REVIEW` | `CONCLUSION_ACCEPTED` | **Human Researcher Only** | **Valid Ed25519 signature by Active Researcher** | `CONCLUSION_ACCEPTED` |
| Reject Conclusion | `HUMAN_REVIEW` | `REJECTED` | **Human Researcher Only** | Valid Ed25519 signature & rejection rationale | `CONCLUSION_REJECTED` |
| Generate Artifact | `CONCLUSION_ACCEPTED` | `PUBLISHABLE_ARTIFACT` | System / Artifact Gen | Valid Conclusion & content hash calculation | `ARTIFACT_GENERATED` |

---

## 4. Cryptographic Identity & Verification
- **Algorithm**: `Ed25519` (canonical asymmetric signature).
- **Researcher Identity**: Every human decision must reference an active, unrevoked `ResearcherIdentity`.
- **Signed Payload**: Canonical JSON representation of decision metadata, project ID, hypothesis ID, evidence references, analysis references, and timestamp.
- **Rejection of Revoked Keys**: Signatures produced by revoked keys fail verification automatically.

---

## 5. Execution Boundary & Capability Model
- **Execution Backend Contract**: Abstract boundary separating domain logic from execution engines (`ReferenceExecutionBackend` vs. `ContainerExecutionBackend`).
- **Capability Grants**: Strict cryptographic grants specifying permitted actions (`execute_command`, `network_access`, `filesystem_write`) with bounded expiration and scope.
- **Security Boundary**: OS command strings and sub-processes are strictly untrusted and executed inside sandbox boundaries.

---

## 6. Provenance & Replay Invariants
- **Immutable Event Ledger**: Monotonically growing, SHA-256 hash-chained event stream.
- **Provenance Checkpoints**: Cryptographically signed milestones asserting event ledger integrity.
- **Replay Determinism**: Replay reconstructs complete in-memory domain graphs without network, LLM, or sandbox dependencies, acting as a regression oracle.
