# ResearchForge — Architecture Specification

## 1. System Overview

ResearchForge is a local-first, reproducible computational engine that orchestrates scientific discovery across 17 formal state transitions. It acts as an auditable bridge between research questions, literature evidence, computational experiments, epistemic criticism, and reproducible scientific artifacts.

```text
                               +-----------------------------+
                               |      Human Researcher       |
                               | (Ultimate Epistemic Auth.)  |
                               +--------------+--------------+
                                              |
                                              v
+-----------------------------------------------------------------------------------------+
|                                    ResearchForge                                        |
|                                                                                         |
|  +--------------------+   +-----------------------+   +------------------------------+  |
|  | Research Lifecycle |-->|   Evidence Graph &    |-->|     Experiment & Simulation  |  |
|  |   State Machine    |   |     Gap Engine        |   |           Engine             |  |
|  +--------------------+   +-----------------------+   +------------------------------+  |
|            |                         |                               |                  |
|            v                         v                               v                  |
|  +--------------------+   +-----------------------+   +------------------------------+  |
|  | Provenance Ledger  |   | Statistical Engine &  |   | Reproducible Artifact &      |  |
|  | (Append-Only SHA)  |   | Uncertainty Profiler  |   | Manuscript Pipeline          |  |
|  +--------------------+   +-----------------------+   +------------------------------+  |
|                                      |                                                  |
+--------------------------------------|--------------------------------------------------+
                                       |
                                       v (Directional Program / Epistemic Query)
                        +------------------------------+
                        |       Cognitia Adapter       |
                        +--------------+---------------+
                                       |
                                       v
                        +------------------------------+
                        |           Cognitia           |
                        | (Reasoning & Epistemic Plane)|
                        |  - Assumption Critique       |
                        |  - Hypothesis Critique       |
                        |  - Model Comparison          |
                        |  - Falsification Evaluation  |
                        +------------------------------+
```

---

## 2. Architectural Layers

### 2.1 Domain Layer (`backend/researchforge/domain`)
* **Purity**: Zero third-party infrastructure dependencies.
* **Deterministic Core**: Pure Python datamodels, value objects, immutable domain entities, formal state machine, and typing protocols.
* **Invariants**: Strict lifecycle transitions, falsification requirement on hypotheses, provenance references on all claims and findings.

### 2.2 Providers Layer (`backend/researchforge/providers`)
* **Contract-Driven**: All IO, external scholarly services, LLM engines, solvers, and simulation drivers are isolated behind Python `Protocol` contracts.
* **Provider Independence**: Swapping a literature provider or LLM reasoning provider does not require any changes to domain logic.

### 2.3 Epistemic & Execution Boundaries (`backend/researchforge/epistemic`, `backend/researchforge/execution`)
* **Execution Boundary**: No autonomous code execution without an explicit `ExecutionPolicy`, `ExecutionSandbox`, and capability grant.
* **Epistemic Authority**: Neither Cognitia nor internal LLM reasoning can directly promote an unverified hypothesis or claim to `CONCLUSION_ACCEPTED`. Human validation is required.

### 2.4 Provenance Subsystem (`backend/researchforge/provenance`)
* **Append-Only Ledger**: Cryptographically chained JSONL event records capturing `actor`, `operation`, `input_refs`, `output_refs`, `hashes`, and `software_version`.
* **Zero Secret Leakage**: Strict redaction of credentials prior to ledger commitment.

### 2.5 Presentation & Integration (`backend/researchforge/api`, `backend/researchforge/cli`)
* **FastAPI v1 REST API**: Clean endpoints for managing projects, sources, evidence, gaps, hypotheses, runs, and artifacts.
* **Typer CLI**: Command-line tool with `--json` output support for scriptable research pipelines.

---

## 3. Communication & Data Invariants

1. **Evidence Grounding**: No scientific claim exists without an explicit `EvidenceFragment` link.
2. **Deterministic Hashes**: All entities provide a `.content_hash()` computed over canonical JSON representations.
3. **Multi-dimensional Uncertainty**: Every result records epistemic, measurement, model, parameter, and sampling uncertainties separately.
