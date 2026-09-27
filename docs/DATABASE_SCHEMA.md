# RESEARCHFORGE — DATABASE SCHEMA & PERSISTENCE SPECIFICATION

## 1. Overview

ResearchForge adopts a canonical relational persistence model targeting PostgreSQL in production and SQLite for local development.

The database serves as the **primary source of truth** for:
1. Domain Aggregates and Entities
2. Provenance Event Log (`provenance_events`)
3. Checkpoints and Signatures
4. Idempotency Records (`idempotency_records`)

---

## 2. Table Specifications

### 2.1 `research_projects`
* `id` (`VARCHAR(64)`, PK) — Unique project identifier (`proj_...`)
* `title` (`VARCHAR(256)`, NOT NULL)
* `description` (`TEXT`)
* `state` (`VARCHAR(64)`, default `'DRAFT'`)
* `question_ids_json` (`TEXT`)
* `hypothesis_ids_json` (`TEXT`)
* `experiment_ids_json` (`TEXT`)
* `artifact_ids_json` (`TEXT`)
* `source_ids_json` (`TEXT`)
* `created_at` (`VARCHAR(64)`)

### 2.2 `research_threads`
* `id` (`VARCHAR(64)`, PK) — Thread identifier (`th_...`)
* `project_id` (`VARCHAR(64)`, FK / Indexed)
* `title` (`VARCHAR(256)`)
* `state` (`VARCHAR(64)`, default `'DRAFT'`)
* `version` (`INTEGER`, default `1`)
* `hypothesis_id` (`VARCHAR(64)`, Nullable)
* `active_experiment_id` (`VARCHAR(64)`, Nullable)
* `active_run_id` (`VARCHAR(64)`, Nullable)
* `artifact_ids_json` (`TEXT`)
* `created_at` (`VARCHAR(64)`)

### 2.3 `research_questions`
* `id` (`VARCHAR(64)`, PK)
* `project_id` (`VARCHAR(64)`, Indexed)
* `question_text` (`TEXT`, NOT NULL)
* `scope_boundaries_json` (`TEXT`)
* `primary_variable` (`VARCHAR(128)`)
* `target_phenomenon` (`VARCHAR(128)`)
* `created_at` (`VARCHAR(64)`)

### 2.4 `evidence`
* `id` (`VARCHAR(64)`, PK)
* `project_id` (`VARCHAR(64)`, Indexed)
* `source_id` (`VARCHAR(64)`)
* `summary` (`TEXT`)
* `fragments_json` (`TEXT`)
* `claims_json` (`TEXT`)
* `created_at` (`VARCHAR(64)`)

### 2.5 `research_gaps`
* `id` (`VARCHAR(64)`, PK)
* `project_id` (`VARCHAR(64)`, Indexed)
* `title` (`VARCHAR(256)`)
* `description` (`TEXT`)
* `unexplored_region` (`TEXT`)
* `affected_variables_json` (`TEXT`)
* `supporting_evidence_ids_json` (`TEXT`)
* `confidence` (`FLOAT`)
* `created_at` (`VARCHAR(64)`)

### 2.6 `hypotheses`
* `id` (`VARCHAR(64)`, PK)
* `project_id` (`VARCHAR(64)`, Indexed)
* `statement` (`TEXT`, NOT NULL)
* `mechanism` (`TEXT`)
* `assumptions_json` (`TEXT`)
* `predictions_json` (`TEXT`)
* `falsification_criteria_json` (`TEXT`, NOT NULL)
* `evidence_ids_json` (`TEXT`)
* `state` (`VARCHAR(64)`)
* `created_at` (`VARCHAR(64)`)

### 2.7 `experiments`
* `id` (`VARCHAR(64)`, PK)
* `project_id` (`VARCHAR(64)`, Indexed)
* `hypothesis_id` (`VARCHAR(64)`, Indexed)
* `name` (`VARCHAR(256)`)
* `design_spec_json` (`TEXT`)
* `parameters_json` (`TEXT`)
* `execution_policy_ref` (`VARCHAR(128)`)
* `state` (`VARCHAR(64)`)
* `created_at` (`VARCHAR(64)`)

### 2.8 `experiment_runs`
* `id` (`VARCHAR(64)`, PK)
* `experiment_id` (`VARCHAR(64)`, Indexed)
* `project_id` (`VARCHAR(64)`, Indexed)
* `status` (`VARCHAR(64)`)
* `random_seed` (`INTEGER`)
* `parameter_hash` (`VARCHAR(64)`)
* `input_hash` (`VARCHAR(64)`)
* `output_hash` (`VARCHAR(64)`)
* `raw_results_json` (`TEXT`)
* `capability_grant_ref` (`VARCHAR(128)`)
* `error_message` (`TEXT`)
* `created_at` (`VARCHAR(64)`)

### 2.9 `falsification_evaluations`
* `id` (`VARCHAR(64)`, PK)
* `project_id` (`VARCHAR(64)`, Indexed)
* `hypothesis_id` (`VARCHAR(64)`, Indexed)
* `status` (`VARCHAR(64)`)
* `reasoning` (`TEXT`)
* `evidence_ids_json` (`TEXT`)
* `analysis_ids_json` (`TEXT`)
* `created_at` (`VARCHAR(64)`)

### 2.10 `human_decisions`
* `id` (`VARCHAR(64)`, PK)
* `project_id` (`VARCHAR(64)`, Indexed)
* `decision` (`VARCHAR(64)`)
* `rationale` (`TEXT`)
* `hypothesis_id` (`VARCHAR(64)`)
* `evidence_ids_json` (`TEXT`)
* `analysis_ids_json` (`TEXT`)
* `signer_identity` (`VARCHAR(128)`)
* `signature` (`VARCHAR(256)`)
* `created_at` (`VARCHAR(64)`)

### 2.11 `conclusions`
* `id` (`VARCHAR(64)`, PK)
* `project_id` (`VARCHAR(64)`, Indexed)
* `statement` (`TEXT`)
* `status` (`VARCHAR(64)`)
* `decision_id` (`VARCHAR(64)`)
* `evidence_ids_json` (`TEXT`)
* `analysis_ids_json` (`TEXT`)
* `falsification_id` (`VARCHAR(64)`)
* `artifact_ids_json` (`TEXT`)
* `created_at` (`VARCHAR(64)`)

### 2.12 `research_artifacts`
* `id` (`VARCHAR(64)`, PK)
* `project_id` (`VARCHAR(64)`, Indexed)
* `name` (`VARCHAR(256)`)
* `artifact_type` (`VARCHAR(64)`)
* `file_path` (`VARCHAR(512)`)
* `content_sha256` (`VARCHAR(64)`)
* `status` (`VARCHAR(64)`)
* `upstream_artifact_ids_json` (`TEXT`)
* `upstream_dataset_hashes_json` (`TEXT`)
* `metadata_json` (`TEXT`)
* `created_at` (`VARCHAR(64)`)

### 2.13 `provenance_events`
* `event_id` (`VARCHAR(64)`, PK)
* `event_type` (`VARCHAR(64)`, NOT NULL, Indexed)
* `schema_version` (`VARCHAR(16)`)
* `timestamp` (`VARCHAR(64)`, NOT NULL)
* `actor` (`VARCHAR(64)`, NOT NULL)
* `actor_id` (`VARCHAR(128)`, NOT NULL)
* `entity_id` (`VARCHAR(64)`, NOT NULL, Indexed)
* `entity_type` (`VARCHAR(64)`, NOT NULL)
* `parent_event_hash` (`VARCHAR(64)`, Nullable)
* `event_hash` (`VARCHAR(64)`, NOT NULL)
* `input_refs_json` (`TEXT`)
* `output_refs_json` (`TEXT`)
* `parameters_json` (`TEXT`)
* `metadata_json` (`TEXT`)

### 2.14 `idempotency_records`
* `key` (`VARCHAR(128)`, PK)
* `operation` (`VARCHAR(64)`, NOT NULL)
* `entity_id` (`VARCHAR(64)`, NOT NULL)
* `response_payload_json` (`TEXT`, NOT NULL)
* `created_at` (`VARCHAR(64)`, NOT NULL)
