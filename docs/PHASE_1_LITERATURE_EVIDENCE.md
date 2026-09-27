# ResearchForge Phase 1 — Literature & Evidence Intelligence

## 1. Executive Summary

ResearchForge Phase 1 implements the first complete research knowledge vertical slice:
```text
ResearchQuestion
      ↓
LiteratureProvider (Reference & OpenAlex)
      ↓
LiteratureSource (Canonical, Deduplicated, Provenanced)
      ↓
EvidenceExtractionProvider
      ↓
EvidenceFragment & Extracted Claims
      ↓
EvidenceClaimBinding & PotentialContradictions
      ↓
GapAnalysisProvider (Contradiction & Boundary Gaps)
      ↓
HypothesisCandidate (Mandatory Falsification Criteria)
      ↓
Cognitia Epistemic Critique (Advisory Only)
      ↓
research_evidence_bundle.json (Content-Addressed)
```

## 2. Core Epistemic Principles

1. **External Literature is Untrusted Input**: External literature provides observations, claims, parameter measurements, and methods. It never has authority to directly transition the project to `CONCLUSION_ACCEPTED` or grant execution capabilities.
2. **Evidence vs. Claim Decoupling**: An observation reported in a paper (`EvidenceFragment`) is strictly separated from the formal proposition (`Claim`). A paper saying *X* is never equivalent to ResearchForge asserting *X*.
3. **Explicit Provenance and Traceability**: Every ingested source, normalized document, extracted fragment, claim binding, contradiction, and generated gap candidate carries an immutable SHA-256 provenance link in the cryptographic ledger.
4. **Mandatory Falsification**: All generated hypothesis candidates must define explicit, falsifiable criteria with designated metrics and failure thresholds.
5. **Replayability**: The entire trajectory can be deterministically replayed and reconstructed from the provenance event stream without external network access or LLM calls.
