# ResearchForge — Provider Contracts

All external integration boundaries in ResearchForge are governed by strict Python `Protocol` contracts. Domain services depend purely on these protocols, guaranteeing 100% provider isolation and offline testability.

## 1. Provider Protocol Catalog

| Protocol | Purpose | Key Methods |
| :--- | :--- | :--- |
| `LiteratureProvider` | Query scholarly databases and retrieve bibliographic records | `search()`, `fetch()`, `citations()`, `related()` |
| `CitationProvider` | Parse, resolve, and format citations | `resolve_doi()`, `format_bibtex()`, `validate_citation_graph()` |
| `EvidenceProvider` | Extract and structure evidence fragments from sources | `extract_fragments()`, `validate_extraction()` |
| `RetrievalProvider` | Multi-modal semantic and exact evidence indexing | `index()`, `search_semantic()`, `search_evidence()` |
| `ReasoningProvider` | AI/LLM proposal and critique interface | `propose()`, `critique()`, `extract()`, `synthesize()` |
| `CognitiaProvider` | Formal epistemic evaluation and directional planning | `evaluate_claim()`, `evaluate_hypothesis()`, `identify_assumptions()`, `compare_models()`, `generate_candidate_paths()`, `evaluate_falsification()` |
| `ExperimentProvider` | Design, execute, and collect computational runs | `design()`, `validate()`, `execute()`, `collect_results()` |
| `SimulationProvider` | Run deterministic numerical simulations | `prepare()`, `validate()`, `run()`, `collect()` |
| `StatisticsProvider` | Deterministic statistical tests and power calculations | `compute_descriptive()`, `hypothesis_test()`, `compute_effect_size()`, `uncertainty_propagation()` |
| `PublicationProvider` | Export reproducible manuscripts and formats | `render_manuscript()`, `build_reproducibility_bundle()`, `verify_traceability()` |
| `GapAnalysisProvider` | Identify evidence contradictions and unexplored regions | `analyze_gaps()`, `evaluate_gap_validity()` |

---

## 2. Invariant Rules for Providers

1. **Protocol Adherence**: Every provider implementation must satisfy `typing.runtime_checkable` protocol definitions.
2. **Immutable Returns**: Returned domain transfer objects (DTOs) are validated through Pydantic v2 schemas.
3. **Provenance Tagging**: Every provider response contains `provider_name`, `provider_version`, `retrieval_timestamp`, and request parameter hashes.
4. **Offline Fallback**: Every provider interface has a corresponding mock/local-first reference implementation for zero-dependency local testing.
