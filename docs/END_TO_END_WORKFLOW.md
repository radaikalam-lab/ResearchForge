# RESEARCHFORGE — END-TO-END WORKFLOW SPECIFICATION

## 1. Lifecycle Trajectory Topology

```text
[1. Project Creation] (DRAFT)
       ↓
[2. Thread Genesis] (DRAFT)
       ↓
[3. Question Definition] (QUESTION_DEFINED)
       ↓
[4. Literature Search & Ingestion] (EVIDENCE_COLLECTION)
       ↓
[5. Evidence Extraction & Claim Binding] (EVIDENCE_STRUCTURED)
       ↓
[6. Gap Analysis] (GAP_ANALYSIS)
       ↓
[7. Hypothesis Formulation] (HYPOTHESIS_FORMED)
       ↓
[8. Cognitia Epistemic Critique] (HYPOTHESIS_CRITIQUE — Advisory Only)
       ↓
[9. Experiment Design] (EXPERIMENT_DESIGNED)
       ↓
[10. Execution Authorization] (EXPERIMENT_READY — CapabilityGrant Issued)
       ↓
[11. Sandboxed Computational Execution] (COMPUTATION_RUNNING → RESULTS_AVAILABLE)
       ↓
[12. Statistical Analysis] (Rigorous Numerical Backing)
       ↓
[13. Falsification Evaluation] (FALSIFICATION → EVIDENCE_EVALUATION)
       ↓
[14. Human Decision & Cryptographic Signature] (HUMAN_REVIEW)
       ↓
[15. Scientific Conclusion Acceptance] (CONCLUSION_ACCEPTED)
       ↓
[16. Reproducible Artifact Generation] (ARTIFACT_GENERATION → PUBLISHABLE_ARTIFACT)
       ↓
[17. Cryptographic Checkpoint & Provenance Chain Verification]
```

---

## 2. Step-by-Step Contract Mechanics

1. **Project & Thread Genesis**: The Principal Investigator initializes a top-level aggregate project and branch thread.
2. **Question Definition**: Formulates research question with explicit primary variables and scope bounds.
3. **Evidence Extraction**: Normalizes external papers into `Evidence` records holding discrete `EvidenceFragment` and `Claim` linkages.
4. **Gap Analysis**: Identifies unexplored parameter regimes or contradictions with quantifiable confidence.
5. **Hypothesis Formulation**: Constructs $H_1$ with at least one mandatory `FalsificationCriterion`. Hypotheses lacking falsification criteria are rejected by domain invariants.
6. **Cognitia Advisory Review**: Epistemic engine computes assumption vulnerabilities and falsifiability assessment without authority escalation.
7. **Experiment Design & Granting**: Specifies parameter space. Execution engine requires an explicit, active `CapabilityGrant`.
8. **Sandboxed Run**: Executes under network isolation and timeout limits, producing hashed outputs.
9. **Falsification & Human Gate**: Falsification engine evaluates hypothesis against numerical results. Transition to `CONCLUSION_ACCEPTED` is strictly blocked without valid Ed25519/HMAC human signature.
10. **Publishable Artifact**: Generates structured report (`reference_research_report.json`) and seals provenance chain with a signed cryptographic checkpoint.
