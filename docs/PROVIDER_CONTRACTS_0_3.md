# PROVIDER CONTRACTS SPECIFICATION (PHASE 0.3 FREEZE)

## 1. Architectural Boundary
All external integration services (scholarly search, LLM critique, sandbox execution, statistics, data extraction) reside behind strictly typed `Protocol` contracts.

### Core Architectural Invariant:
```text
Provider  -->  DTO  -->  Application Service  -->  Domain Validation  -->  State Transition  -->  Persistence / Provenance
```
**Providers NEVER directly mutate domain models or bypass unit-of-work transactions.**

---

## 2. Frozen Provider Interfaces

### 2.1 LiteratureProvider
- **Contract**: `search(query: str, limit: int) -> list[Source]`, `fetch_metadata(source_id: str) -> dict`
- **Output DTO**: `Source` containing `provider_name`, `provider_record_id`, `uri`, `retrieved_content`.
- **Untrusted Input Rule**: All retrieved literature content is marked untrusted data and requires domain extraction/validation before claim binding.

### 2.2 EvidenceProvider
- **Contract**: `extract_fragments(source: Source) -> list[EvidenceFragment]`, `validate_extraction(fragment, source) -> bool`, `synthesize_evidence(fragments, claim) -> Evidence`
- **Output DTO**: `EvidenceFragment` and `Evidence` entities with explicit source citations.

### 2.3 GapAnalysisProvider
- **Contract**: `identify_gaps(evidence_items: list[Evidence], question: ResearchQuestion) -> list[ResearchGap]`
- **Output DTO**: `ResearchGap` entities specifying unexplored scientific regions.

### 2.4 HypothesisProvider
- **Contract**: `propose_hypotheses(gap: ResearchGap, evidence: list[Evidence]) -> list[Hypothesis]`
- **Invariant**: Hypotheses returned must define testable predictions and at least one `FalsificationCriterion`.

### 2.5 EpistemicCritiqueProvider (Cognitia Boundary)
- **Contract**: `critique_hypothesis(hypothesis: Hypothesis, evidence: list[Evidence]) -> EpistemicCritique`
- **Advisory Role**: Cognitia critiques provide epistemic advice, plausibility ratings, and missing variable alerts. **Zero scientific authority.**

### 2.6 ExecutionProvider
- **Contract**: `execute_experiment(experiment: Experiment, parameters: dict) -> ExperimentRun`
- **Security**: Must execute through `ExecutionBackend` under verified `CapabilityGrant`.

### 2.7 StatisticsProvider
- **Contract**: `compute_statistics(run: ExperimentRun, hypothesis: Hypothesis) -> StatisticalAnalysis`
- **Output**: P-values, confidence intervals, test statistics, and effect sizes.

### 2.8 FalsificationProvider
- **Contract**: `evaluate_falsification(hypothesis: Hypothesis, analysis: StatisticalAnalysis) -> FalsificationEvaluation`
- **Output**: Deterministic decision (`SUPPORTED`, `FALSIFIED`, `INCONCLUSIVE`).

---

## 3. Provider Error Taxonomy
- `ProviderNotFoundError`: Requested provider name not in registry.
- `ProviderTimeoutError`: External API or compute exceeded deadline.
- `ProviderPayloadError`: Invalid or malformed response DTO.
- `ProviderAuthenticationError`: Credential verification failure.
