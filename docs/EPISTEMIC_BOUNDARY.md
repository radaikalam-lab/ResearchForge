# ResearchForge — Epistemic Boundary & Authority Specification

## 1. The Epistemic Invariant

ResearchForge operates under a non-negotiable architectural invariant:

```text
================================================================================
                           RESEARCH AUTHORITY LAW
================================================================================
ResearchForge may discover, compute, propose, compare, simulate and evaluate.

Cognitia may reason, critique, classify and propose.

Neither system may autonomously declare a scientific claim experimentally
validated without explicit evidence accepted by the human/domain validation
boundary.
================================================================================
```

---

## 2. Distinction Between Epistemic Tiers

| Tier | Actor | Allowed Actions | Forbidden Actions |
| :--- | :--- | :--- | :--- |
| **Tier 0: Computational & Proposal** | LLMs, Heuristics, Literature Crawlers | Generate text, propose hypotheses, extract fragments, suggest candidate gaps | Declaring scientific truth, approving transitions, certifying findings |
| **Tier 1: Epistemic Critique** | Cognitia Plane | Decompose assumptions, evaluate logical consistency, rank hypotheses, assess falsification rigor | Initiating experiments, executing physical/system commands, approving publication |
| **Tier 2: Computational Execution** | ResearchForge Engine | Run deterministic simulations, compute statistics, execute sandbox tests | Overriding falsification results, claiming real-world physical validation |
| **Tier 3: Scientific Authority** | Human Researcher | Accept/Reject conclusions, validate evidence links, authorize publication | None (Ultimate gatekeeper) |

---

## 3. Explicit Prohibitions

1. **No Autonomous Validation**: An LLM or automated tool generating text saying *"The hypothesis is proven"* CANNOT advance state to `CONCLUSION_ACCEPTED`.
2. **No Unsanctioned Execution**: Neither Cognitia nor external agents can execute shell commands, network requests, or simulations without an approved `ExecutionPolicy`.
3. **No Phantom Claims**: Every accepted finding must reference concrete numerical data and primary evidence fragments.
