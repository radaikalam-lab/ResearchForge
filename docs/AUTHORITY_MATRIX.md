# Authority Matrix (Section 13, 14)

ResearchForge enforces a strict 4-tier authority model across every scientific and computational operation.

---

## 1. The Four Epistemic Authority Tiers

```text
+-----------------------------------------------------------------------------------+
| Tier 3: Human Scientific Authority (Domain Researcher, Review Panel)              |
| - Approves/Rejects conclusions                                                    |
| - Authorizes publication and artifact releases                                    |
| - Grants computational capabilities and overrides                                |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
| Tier 2: Computational Execution Authority (ResearchForge Engine, Solvers, Sandbox)|
| - Executes deterministic simulations and statistical runs                         |
| - Enforces execution sandboxes and resource caps                                  |
| - Maintains append-only provenance ledgers and Merkle checkpoints                 |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
| Tier 1: Epistemic Critique Authority (Cognitia Reasoning Plane)                  |
| - Critiques hypotheses, assumptions, and mathematical representations             |
| - Compares models and evaluates Lakatosian/Kuhnian theory transitions             |
| - Evaluates falsification criteria against experimental observations              |
| - Strictly ADVISORY: CANNOT execute code, modify files, or accept claims         |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+-----------------------------------------------------------------------------------+
| Tier 0: Computational & Proposal Authority (LLMs, Heuristic Crawlers, Parsers)    |
| - Generates candidate text, extracts fragments, proposes search queries          |
| - Zero authority: All output is treated as unverified candidate data             |
+-----------------------------------------------------------------------------------+
```

---

## 2. Operation Permission Matrix

| Operation | Tier 0 (LLM/Proposal) | Tier 1 (Cognitia) | Tier 2 (ResearchForge Engine) | Tier 3 (Human Authority) |
| :--- | :---: | :---: | :---: | :---: |
| Literature Search & Fetch | Proposal only | No | **Execute** | Authorize |
| Evidence Fragment Extraction | Proposal only | No | **Execute** | Validate |
| Research Gap Proposal | Proposal only | Advisory Critique | Structure | Validate |
| Hypothesis Formulation | Proposal only | Advisory Critique | Validate structure | **Authorize** |
| Epistemic Critique & Assumptions | No | **Execute** | Coordinate | Review |
| Experiment Design | Suggest | Critique | Validate Bounds | **Authorize** |
| Simulation Execution | **FORBIDDEN** | **FORBIDDEN** | **Execute in Sandbox** | Grant Policy |
| Statistical Analysis | **FORBIDDEN** | Critique | **Execute Deterministic** | Interpret |
| Falsification Evaluation | Suggest | **Evaluate** | Record Status | Review |
| Conclusion Acceptance | **FORBIDDEN** | **FORBIDDEN** | **FORBIDDEN** | **MANDATORY EXCLUSIVE** |
| Artifact Release & Publication | **FORBIDDEN** | **FORBIDDEN** | Build / Package | **MANDATORY EXCLUSIVE** |
| Capability Grant Allocation | **FORBIDDEN** | **FORBIDDEN** | Check / Enforce | **MANDATORY EXCLUSIVE** |

---

## 3. Human Authority Separation (Section 14)

* **`ResearcherIdentity`**: Security credential and user ID (managed outside domain core).
* **`AuthorizationContext`**: Context containing user roles and tenant scopes.
* **`HumanDecision`**: Scientific domain object recording explicit decision (`APPROVE`, `REJECT`), rationale, referenced evidence IDs, and review timestamp.
