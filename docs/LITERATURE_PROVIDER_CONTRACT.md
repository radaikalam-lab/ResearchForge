# Literature Provider Contract (Phase 1)

## 1. Scope & Purpose

The `LiteratureProvider` interface enables pluggable retrieval and metadata normalization of scholarly papers. External literature providers operate across the epistemic boundary, providing untrusted input data to the system.

## 2. Interface Specification

```python
class LiteratureProvider(ABC):
    provider_name: str
    version: str = "1.0.0"

    @abstractmethod
    async def search(
        self,
        query_or_request: str | LiteratureSearchRequest,
        limit: int = 10,
    ) -> list[Source] | LiteratureSearchResponse:
        """Search literature sources matching query parameters."""
        ...

    @abstractmethod
    async def fetch(
        self,
        record_id_or_request: str | LiteratureFetchRequest,
    ) -> Source | None:
        """Fetch a specific literature source by identifier."""
        ...
```

## 3. Implementations

1. **`ReferenceLiteratureProvider`**:
   - Deterministic offline reference dataset containing 4 synthetic fixtures:
     - `paper_ref_01`: Linear monotonic scaling in low parameter regime [0.0, 2.0].
     - `paper_ref_02`: Direct contradiction with null effect finding in unbuffered assay.
     - `paper_ref_03`: Boundary condition with saturation plateau at X > 2.5 and thermal degradation at X > 4.0.
     - `paper_ref_04`: Methodological limitation detailing false negative rates below sample size N=25.
   - All fixtures clearly marked `[SYNTHETIC REFERENCE LITERATURE]`.

2. **`OpenAlexLiteratureProvider`**:
   - Real-world provider querying OpenAlex API (`https://api.openalex.org/works`).
   - Normalizes titles, abstracts, DOIs, publication years, and venues into canonical `Source` models.
   - Includes graceful offline fallback for offline test environments.

## 4. Deterministic Identity & Content Hashes

- `source_id = compute_source_identity(provider_name, provider_record_id)` -> SHA-256 deterministic ID.
- `metadata_hash = SHA-256(canonical(title, authors, doi, venue, year))`
- `raw_content_hash = SHA-256(canonical(raw_text_or_abstract))`
- Duplicate ingestion of the same paper produces an identical `source_id`, guaranteeing idempotency.
