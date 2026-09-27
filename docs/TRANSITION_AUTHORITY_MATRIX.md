# Transition & Authority Matrix (Section 5)

This document formalizes every lifecycle transition in ResearchForge across project, hypothesis/thread, experiment, run, and artifact state machines.

---

## 1. Project & Hypothesis Lifecycle State Transitions

| From State | To State | Trigger | Actor | Authority Tier | Guard Conditions | Required Artifacts | Required Provenance Event | Failure & Invalidation Handling |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `DRAFT` | `FORMED` | `formulate_hypothesis` | Human / AI | Tier 0 / Tier 3 | Falsification criteria $\ge 1$, mechanism defined | `Hypothesis` | `HYPOTHESIS_FORMED` | Reverts to `DRAFT` if criteria missing |
| `FORMED` | `CRITIQUE_PENDING` | `submit_for_critique` | ResearchForge | Tier 2 | Hypothesis valid and schema checked | `Hypothesis` | `HYPOTHESIS_SUBMITTED` | Remains in `FORMED` |
| `CRITIQUE_PENDING` | `CRITIQUED` | `receive_critique` | Cognitia | Tier 1 | Assessment contains soundness & assumptions | `EpistemicAssessment` | `HYPOTHESIS_CRITIQUED` | Remains pending on timeout |
| `CRITIQUED` | `EXPERIMENT_DESIGN_PENDING`| `accept_critique` | Human Researcher | Tier 3 | Human review decision recorded | `HumanDecision` | `DECISION_ACCEPTED` | Loops back to `FORMED` if revised |
| `EXPERIMENT_DESIGN_PENDING` | `EXPERIMENT_READY` | `finalize_experiment_plan` | ResearchForge | Tier 2 | Variables, bounds, and protocol validated | `ExperimentPlan` | `EXPERIMENT_DESIGNED` | Rejects unconstrained plan |
| `EXPERIMENT_READY` | `UNDER_TEST` | `start_experiment_run` | ResearchForge | Tier 2 | Approved `ExecutionPolicy`, `CapabilityGrant` | `ExecutionRequest` | `RUN_STARTED` | Blocked if capability missing |
| `UNDER_TEST` | `EVIDENCE_AVAILABLE` | `collect_run_results` | Sandbox Engine | Tier 2 | Deterministic output hash, metrics present | `ExperimentResult` | `RESULTS_RECORDED` | Marks run as `FAILED` on error |
| `EVIDENCE_AVAILABLE` | `FALSIFICATION_PENDING` | `initiate_falsification` | ResearchForge | Tier 2 | Metrics map to hypothesis falsification criteria | `ExperimentResult` | `STATE_TRANSITIONED` | Remains in `EVIDENCE_AVAILABLE` |
| `FALSIFICATION_PENDING` | `EVALUATION_PENDING` | `evaluate_falsification` | Cognitia | Tier 1 | Status in `{SUPPORTED, WEAKENED, CONTRADICTED}` | `FalsificationEvaluation`| `FALSIFICATION_EVALUATED` | Inconclusive if data insufficient |
| `EVALUATION_PENDING` | `HUMAN_REVIEW` | `submit_to_human_gatekeeper` | ResearchForge | Tier 2 | Evidence graph and statistical tests compiled | `StatisticalAnalysis` | `HUMAN_REVIEW_STARTED` | Awaits human reviewer |
| `HUMAN_REVIEW` | `ACCEPTED` | `approve_conclusion` | Human Researcher | **Tier 3 (MANDATORY)** | Verified evidence, falsification not contradicted, Human decision == APPROVE | `HumanDecision`, `Evidence` | `DECISION_ACCEPTED` | Rejects without human signature |
| `HUMAN_REVIEW` | `REJECTED` | `reject_conclusion` | Human Researcher | **Tier 3 (MANDATORY)** | Human rationale provided | `HumanDecision` | `DECISION_REJECTED` | Thread terminates or branches |
| Any Active State | `INVALIDATED` | `invalidate_upstream` | System / Human | Tier 2 / Tier 3 | Upstream dataset, code, or assumption mutated | `ResearchArtifact` | `ARTIFACT_INVALIDATED` | Cascades to all child artifacts |

---

## 2. Invariant Rules
1. No transition to `ACCEPTED` or `CONCLUSION_ACCEPTED` may occur without Tier 3 Human Authority.
2. An experiment run can only transition from `READY` to `RUNNING` with an explicit, unexpired `CapabilityGrant`.
3. Invalidation is an append-only state transition producing `ARTIFACT_INVALIDATED` provenance events without erasing history.
