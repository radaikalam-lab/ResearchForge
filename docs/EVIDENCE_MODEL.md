# Evidence Model & Fragment Grounding (Phase 1)

## 1. Overview

The Evidence model represents empirical data, observations, and assertions extracted from literature sources. It bridges raw external documents to structured research knowledge.

## 2. Core Entities

### EvidenceFragment
Preserves precise location and content attribution:
- `id`: Fragment identifier.
- `source_id`: Reference to originating `Source`.
- `evidence_type`: Observation, measurement, assertion, text, table, figure.
- `location_reference`: Page, paragraph, section, or line reference.
- `content`: Exact extracted text or representation.
- `extracted_data`: Structured key-value measurements (e.g. parameter bounds, thresholds).
- `confidence`: Extraction model confidence score.

### Evidence
Aggregate grouping supporting a claim or question:
- `id`: Unique evidence identifier.
- `project_id`: Research project identifier.
- `source_id`: Primary literature source.
- `summary`: High-level synthesis.
- `fragments`: List of grounded `EvidenceFragment` items.
- `claims`: Associated candidate claims.
- `provenance_refs`: SHA-256 provenance chain tracking ingestion and normalization events.

## 3. Grounding & Honest Validation

Extraction providers must validate that fragments are strictly grounded in their source text before synthesizing evidence entities. External text injections or instructions remain inert string data.
