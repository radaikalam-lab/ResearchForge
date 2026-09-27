# ResearchForge

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python Version](https://img.shields.io/badge/python-3.12%20%7C%203.13-blue)](https://www.python.org/)
[![Status](https://img.shields.io/badge/Status-Phase_0_Scaffold-green.svg)]()

> **Local-First, Reproducible Computational Research Lifecycle Engine**

---

## 0. Mission

**ResearchForge** (`https://github.com/radaikalam-lab/ResearchForge`) is a production-oriented, local-first, reproducible engine designed to compress and structure the repetitive, computationally expensive, and fragile phases of the scientific discovery lifecycle.

ResearchForge is **NOT**:
* An autonomous AI paper writer
* A generic literature chatbot
* An uncontrolled multi-agent playground
* A surrogate for human peer review or scientific authority
* A citation manipulation tool

ResearchForge **IS**:
A computational engine that structures the journey from question to reproducible research artifact:

```text
Research Question
      ↓
Evidence Gathering & Graphing
      ↓
Research Gap Identification
      ↓
Falsifiable Hypothesis Generation
      ↓
Experiment Design
      ↓
Computational Experiment / Simulation
      ↓
Statistical & Uncertainty Analysis
      ↓
Rigorous Falsification
      ↓
Evidence Evaluation
      ↓
Human Scientific Review
      ↓
Conclusion & Finding
      ↓
Reproducible Research Artifact & Manuscript
```

---

## 1. The Core Architectural Law

```text
================================================================================
                           RESEARCH AUTHORITY LAW
================================================================================
ResearchForge may discover, compute, propose, compare, simulate, and evaluate.
Cognitia may reason, critique, classify, and propose.

Neither system may autonomously declare a scientific claim experimentally
validated without explicit evidence accepted by the human/domain validation
boundary.
================================================================================
```

### Critical Epistemic Boundaries
* Computational plausibility $\neq$ scientific validity
* Epistemic novelty $\neq$ production authority
* Generated hypothesis $\neq$ accepted scientific claim
* Simulation result $\neq$ experimental validation
* LLM reasoning $\neq$ empirical evidence

Human researchers remain the final scientific authority at all evaluation checkpoints.

---

## 2. Relationship with Cognitia

ResearchForge coordinates research workflows, datasets, simulations, statistics, provenance, and artifact generation. It integrates with **Cognitia** (`https://github.com/radaikalam-lab/Cognitia`) strictly via formal adapter/provider boundaries:

```text
                    ResearchForge
                         │
                         ▼
                Cognitia Adapter
                         │
                         ▼
                     Cognitia
                         │
             ┌───────────┴───────────┐
             │                       │
       Reasoning Plane        Epistemic Plane
```

* **ResearchForge owns**: Research lifecycle, literature normalization, evidence graphs, computational experiments, datasets, simulation runs, statistics, provenance ledger, and manuscript generation.
* **Cognitia owns**: Epistemic critique, assumption decomposition, hypothesis critique, model comparison, representation criticism, and directional candidate path evaluation.
* **Prohibition**: Cognitia is strictly isolated from physical execution authority, unvetted publication, or irreversible state mutations.

---

## 3. Core Design Principles

1. **Local-First & Offline-Capable**: Fully functional without mandatory internet or external SaaS APIs.
2. **Provenance-First**: Append-only cryptographic provenance ledger for every entity, computation, and decision.
3. **Deterministic & Reproducible**: Fixed seeds, canonical JSON representations, content-addressable SHA-256 hashes.
4. **Contract-First & Provider-Isolated**: Protocols isolate all literature APIs, LLMs, solvers, and engines.
5. **Explicit Uncertainty & Assumptions**: Multi-dimensional uncertainty (measurement, model, sampling, computational, epistemic).
6. **Falsification-Centered**: Every hypothesis requires explicit falsification conditions before experimentation.

---

## 4. Repository Layout

```text
ResearchForge/
├── README.md
├── LICENSE
├── pyproject.toml
├── .gitignore
├── .env.example
├── docs/
│   ├── ARCHITECTURE.md
│   ├── DOMAIN_MODEL.md
│   ├── CONTRACTS.md
│   ├── EPISTEMIC_BOUNDARY.md
│   ├── PROVENANCE.md
│   ├── REPRODUCIBILITY.md
│   ├── SECURITY.md
│   ├── ADR/
│   └── research/
├── backend/
│   └── researchforge/
│       ├── api/               # FastAPI REST endpoints (/api/v1)
│       ├── domain/            # Core models, value objects, contracts, state machine
│       ├── application/       # Commands, queries, workflow orchestration
│       ├── providers/         # Cognitia, literature, statistics, simulation providers
│       ├── provenance/        # Cryptographic append-only provenance subsystem
│       ├── epistemic/         # Epistemic assessment & authority boundary
│       ├── execution/         # Sandboxing, execution requests, policy enforcement
│       ├── artifacts/         # Research artifact manager & checksums
│       ├── configuration/     # Pydantic Settings & environment validation
│       └── cli/               # Typer/Rich CLI interface
├── tests/
│   ├── contracts/             # Protocol compliance tests
│   ├── domain/                # Model serialization & invariant tests
│   ├── providers/             # Cognitia and mock adapter tests
│   ├── epistemic/             # Authority boundary validation tests
│   ├── provenance/            # Ledger immutability & replay tests
│   └── integration/           # Architectural invariant tests (Tests A-J)
├── examples/
├── datasets/
├── artifacts/
└── docker/
```

---

## 5. Quickstart (Phase 0)

### Installation

```bash
# Clone the repository
git clone https://github.com/radaikalam-lab/ResearchForge.git
cd ResearchForge

# Install in editable mode with development dependencies
pip install -e ".[scientific,dev]"
```

### Running Tests

To verify zero errors, zero warnings, and full invariant compliance:

```bash
pytest -q -W error
```

### Starting the API

```bash
uvicorn researchforge.api.app:app --host 127.0.0.1 --port 8000 --reload
```

### Using the CLI

```bash
# Verify system readiness
researchforge doctor

# Create a new research project
researchforge project create --title "Investigation of Causal Effects in Material Lattices"

# Inspect provenance
researchforge provenance inspect
```

---

## 6. Development Phases

* **Phase 0 (Current)**: Foundation, domain models, contracts, provenance, Cognitia adapter, CLI, API skeleton, and mandatory invariant tests (A through J).
* **Phase 1**: Literature ingestion, source normalization, evidence extraction, local storage.
* **Phase 2**: Knowledge Graph, contradiction detection, research gap engine, hypothesis generation.
* **Phase 3**: Computational experiment execution, deterministic simulation, statistical analysis.
* **Phase 4**: Full Cognitia epistemic plane integration, assumption tracking, automated falsification engine.
* **Phase 5**: Research compression metrics, reproducibility bundle export, manuscript pipeline (Quarto/LaTeX).
* **Phase 6**: Publication intelligence, journal scope compliance, citation verification.
* **Phase 7**: Extensible MCP ecosystem and specialized laboratory tool bridges.

---

## 7. License

Licensed under the [Apache License, Version 2.0](LICENSE).
