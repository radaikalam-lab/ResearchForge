# Canonical Schema Pack (Section 10)

This document formalizes the canonical schemas and data transfer objects (DTOs) used across domain boundaries and provider protocols.

---

## 1. Domain Entities vs Aggregates vs Value Objects (Section 8)

* **Aggregate Roots**: `ResearchProject`, `ResearchThread`, `Experiment`, `ResearchArtifact`.
* **Entities**: `ResearchQuestion`, `Source`, `Paper`, `Claim`, `Evidence`, `EvidenceFragment`, `ResearchGap`, `Hypothesis`, `ExperimentPlan`, `ExperimentRun`, `Simulation`, `SimulationRun`, `StatisticalAnalysis`, `FalsificationEvaluation`, `HumanDecision`, `Conclusion`, `ProvenanceEvent`.
* **Value Objects (Immutable, Identity-less)**: `UncertaintyProfile`, `DirectionalSpecification`, `CandidatePath`, `FalsificationCriterion`, `CapabilityGrant`, `ExecutionPolicy`.

---

## 2. Canonical DTO Catalog (Implemented in `researchforge.domain.schemas`)

| Domain Area | Request DTO | Response DTO | Idempotency Semantics |
| :--- | :--- | :--- | :--- |
| **Literature** | `LiteratureSearchRequest`, `LiteratureFetchRequest` | `LiteratureSearchResponse`, `Source` | `READ_ONLY` / `IDEMPOTENT` |
| **Citation** | `DoiResolveRequest`, `BibtexFormatRequest` | `Paper`, `str` | `READ_ONLY` / `IDEMPOTENT` |
| **Evidence** | `EvidenceExtractRequest`, `EvidenceSynthesizeRequest` | `EvidenceExtractResponse`, `Evidence` | `IDEMPOTENT` |
| **Retrieval** | `IndexRequest`, `SemanticSearchRequest`, `EvidenceSearchRequest` | `int`, `RetrievalResponse` | `IDEMPOTENT` |
| **Reasoning (Tier 0)** | `ReasoningProposeRequest`, `ReasoningCritiqueRequest` | `str`, `dict[str, str]` | `IDEMPOTENT` |
| **Cognitia (Tier 1)** | `CognitiaEvaluateHypothesisRequest`, `CognitiaCandidatePathsRequest` | `EpistemicAssessment`, `list[CandidatePath]` | `READ_ONLY` / `IDEMPOTENT` |
| **Experiment** | `ExperimentDesignRequest`, `ExperimentExecuteRequest` | `ExperimentPlan`, `ExperimentRun` | `NON_IDEMPOTENT` (Execution) |
| **Simulation** | `SimulationPrepareRequest`, `SimulationRunRequest` | `SimulationMetadata`, `SimulationRun` | `IDEMPOTENT` (Given Seed) |
| **Statistics** | `HypothesisTestRequest`, `FullAnalysisRequest` | `StatisticalTestResult`, `StatisticalAnalysis` | `IDEMPOTENT` |
| **Publication** | `ManuscriptRenderRequest`, `ReproducibilityBundleRequest` | `ResearchArtifact` | `IDEMPOTENT` |
| **Gap Analysis** | `GapAnalyzeRequest`, `GapValidateRequest` | `list[GapCandidate]`, `ResearchGap` | `IDEMPOTENT` |

---

## 3. Provider Error Taxonomy (Section 29)

All provider exceptions subclass `ProviderError`:
* `ProviderUnavailable` (503 Service Unavailable / Daemon Offline)
* `ProviderTimeout` (408 Request Timeout)
* `ProviderRateLimited` (429 Rate Limit Exceeded)
* `ProviderAuthenticationError` (401 / 403 Credentials Invalid)
* `ProviderCapabilityError` (Missing Capability Grant)
* `InvalidProviderRequest` (400 Bad Request Payload)
* `ProviderResponseValidationError` (Malformed Provider Response)
* `ProviderConflict` (409 Conflict / Concurrency Race)
