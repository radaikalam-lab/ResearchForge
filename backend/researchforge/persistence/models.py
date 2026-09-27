"""SQLAlchemy ORM models for ResearchForge canonical persistence."""

import json
from typing import Any

from sqlalchemy import (
    Boolean,
    Float,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from researchforge.domain.base import utc_now


class Base(DeclarativeBase):
    """Base declarative class for all ResearchForge tables."""

    pass


def current_iso_timestamp() -> str:
    """Return current UTC timestamp in ISO 8601 string format."""
    return utc_now().isoformat()


class ProjectRecord(Base):
    """Persisted ResearchProject record."""

    __tablename__ = "research_projects"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    state: Mapped[str] = mapped_column(String(64), nullable=False, default="DRAFT")
    version: Mapped[int] = mapped_column(Integer, default=1)
    question_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    source_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    hypothesis_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    experiment_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    artifact_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)
    updated_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp, onupdate=current_iso_timestamp)


class ThreadRecord(Base):
    """Persisted ResearchThread aggregate record."""

    __tablename__ = "research_threads"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(256), nullable=False)
    state: Mapped[str] = mapped_column(String(64), nullable=False, default="DRAFT")
    version: Mapped[int] = mapped_column(Integer, default=1)
    hypothesis_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    active_experiment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    active_run_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    artifact_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)
    updated_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp, onupdate=current_iso_timestamp)


class QuestionRecord(Base):
    """Persisted ResearchQuestion record."""

    __tablename__ = "research_questions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    scope_boundaries_json: Mapped[str] = mapped_column(Text, default="[]")
    primary_variable: Mapped[str] = mapped_column(String(128), default="")
    target_phenomenon: Mapped[str] = mapped_column(String(128), default="")
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


class EvidenceRecord(Base):
    """Persisted Evidence record."""

    __tablename__ = "evidence_records"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    fragments_json: Mapped[str] = mapped_column(Text, default="[]")
    claims_json: Mapped[str] = mapped_column(Text, default="[]")
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


class GapRecord(Base):
    """Persisted ResearchGap record."""

    __tablename__ = "research_gaps"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    unexplored_region: Mapped[str] = mapped_column(Text, default="")
    affected_variables_json: Mapped[str] = mapped_column(Text, default="[]")
    supporting_evidence_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    confidence: Mapped[float] = mapped_column(Float, default=1.0)
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


class HypothesisRecord(Base):
    """Persisted Hypothesis record."""

    __tablename__ = "hypotheses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    thread_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    mechanism: Mapped[str] = mapped_column(Text, default="")
    assumptions_json: Mapped[str] = mapped_column(Text, default="[]")
    predictions_json: Mapped[str] = mapped_column(Text, default="[]")
    falsification_criteria_json: Mapped[str] = mapped_column(Text, default="[]")
    evidence_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    state: Mapped[str] = mapped_column(String(64), default="DRAFT")
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


class ExperimentRecord(Base):
    """Persisted Experiment design record."""

    __tablename__ = "experiments"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    hypothesis_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    design_spec_json: Mapped[str] = mapped_column(Text, default="{}")
    parameters_json: Mapped[str] = mapped_column(Text, default="{}")
    execution_policy_ref: Mapped[str] = mapped_column(String(128), default="")
    state: Mapped[str] = mapped_column(String(64), default="DRAFT")
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


class RunRecord(Base):
    """Persisted ExperimentRun record."""

    __tablename__ = "experiment_runs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    experiment_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), default="CREATED")
    random_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    parameter_hash: Mapped[str] = mapped_column(String(64), default="")
    input_hash: Mapped[str] = mapped_column(String(64), default="")
    output_hash: Mapped[str] = mapped_column(String(64), default="")
    raw_results_json: Mapped[str] = mapped_column(Text, default="{}")
    execution_policy_ref: Mapped[str] = mapped_column(String(128), default="")
    capability_grant_ref: Mapped[str | None] = mapped_column(String(128), nullable=True)
    environment_metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    started_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    completed_at: Mapped[str | None] = mapped_column(String(64), nullable=True)


class AnalysisRecord(Base):
    """Persisted StatisticalAnalysis record."""

    __tablename__ = "statistical_analyses"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    run_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    test_name: Mapped[str] = mapped_column(String(128), nullable=False)
    test_statistic: Mapped[float] = mapped_column(Float, nullable=False)
    p_value: Mapped[float] = mapped_column(Float, nullable=False)
    effect_size: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_significant: Mapped[bool] = mapped_column(Boolean, default=False)
    raw_data_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


class FalsificationRecord(Base):
    """Persisted FalsificationEvaluation record."""

    __tablename__ = "falsification_evaluations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    hypothesis_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(64), nullable=False)
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    analysis_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


class HumanDecisionRecord(Base):
    """Persisted HumanDecision record with cryptographic signature."""

    __tablename__ = "human_decisions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    decision: Mapped[str] = mapped_column(String(64), nullable=False)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    hypothesis_id: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    analysis_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    falsification_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    signer_identity: Mapped[str] = mapped_column(String(128), nullable=False)
    signature: Mapped[str] = mapped_column(String(512), nullable=False)
    timestamp: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")


class ConclusionRecord(Base):
    """Persisted scientific Conclusion record."""

    __tablename__ = "conclusions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="VALID")
    decision_id: Mapped[str] = mapped_column(String(64), nullable=False)
    evidence_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    analysis_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    falsification_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    artifact_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


class ArtifactRecord(Base):
    """Persisted ResearchArtifact metadata record."""

    __tablename__ = "research_artifacts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    artifact_type: Mapped[str] = mapped_column(String(64), nullable=False)
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    content_sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    status: Mapped[str] = mapped_column(String(64), default="VERIFIED")
    upstream_artifact_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    upstream_dataset_hashes_json: Mapped[str] = mapped_column(Text, default="[]")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


class ProvenanceEventRecord(Base):
    """Persisted transactional ProvenanceEvent record."""

    __tablename__ = "provenance_events"

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    schema_version: Mapped[str] = mapped_column(String(16), default="1.1.0")
    timestamp: Mapped[str] = mapped_column(String(64), nullable=False)
    actor: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_tier: Mapped[str] = mapped_column(String(64), nullable=False)
    actor_id: Mapped[str] = mapped_column(String(128), nullable=False)
    session_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    operation: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    entity_type: Mapped[str] = mapped_column(String(64), default="")
    entity_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    input_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    output_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    parameters_json: Mapped[str] = mapped_column(Text, default="{}")
    environment_json: Mapped[str] = mapped_column(Text, default="{}")
    redaction_metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    provider_identity: Mapped[str | None] = mapped_column(String(128), nullable=True)
    event_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    parent_event_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)


class IdempotencyRecord(Base):
    """Persisted record for idempotency deduplication."""

    __tablename__ = "idempotency_records"

    key: Mapped[str] = mapped_column(String(128), primary_key=True)
    operation: Mapped[str] = mapped_column(String(128), nullable=False)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False)
    request_hash: Mapped[str] = mapped_column(String(64), default="")
    actor_id: Mapped[str] = mapped_column(String(128), default="")
    response_payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


class SourceRecord(Base):
    """Persisted literature source record."""

    __tablename__ = "literature_sources"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    title: Mapped[str] = mapped_column(String(512), default="")
    source_type: Mapped[str] = mapped_column(String(64), default="SCHOLARLY_PAPER")
    uri: Mapped[str] = mapped_column(String(512), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(128), nullable=False)
    provider_record_id: Mapped[str] = mapped_column(String(128), nullable=False)
    retrieval_query: Mapped[str] = mapped_column(Text, default="")
    retrieved_content: Mapped[str] = mapped_column(Text, default="")
    content_hash: Mapped[str] = mapped_column(String(64), default="")
    metadata_hash: Mapped[str] = mapped_column(String(64), default="")
    retrieval_timestamp: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)
    paper_json: Mapped[str] = mapped_column(Text, default="{}")
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


class ClaimRecord(Base):
    """Persisted scientific claim record."""

    __tablename__ = "claims"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), default="", index=True)
    statement: Mapped[str] = mapped_column(Text, nullable=False)
    claim_type: Mapped[str] = mapped_column(String(64), default="EMPIRICAL")
    subject: Mapped[str] = mapped_column(String(256), default="")
    predicate: Mapped[str] = mapped_column(String(256), default="")
    object: Mapped[str] = mapped_column(String(256), default="")
    parameter_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    parameter_range_json: Mapped[str] = mapped_column(Text, default="[]")
    source_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    evidence_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    extraction_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    source_reported_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    domain_assessment: Mapped[str] = mapped_column(String(64), default="PENDING")
    is_grounded_in_evidence: Mapped[bool] = mapped_column(Boolean, default=False)
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


class EvidenceClaimBindingRecord(Base):
    """Persisted link binding evidence to a claim."""

    __tablename__ = "evidence_claim_bindings"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    evidence_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    fragment_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    claim_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_id: Mapped[str] = mapped_column(String(64), nullable=False)
    binding_type: Mapped[str] = mapped_column(String(64), default="SUPPORTS")
    extraction_confidence: Mapped[float] = mapped_column(Float, default=1.0)
    source_reported_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    domain_assessment: Mapped[str] = mapped_column(String(64), default="ACCEPTED")
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


class ContradictionRecord(Base):
    """Persisted record for scientific contradictions."""

    __tablename__ = "contradictions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    claim_a_id: Mapped[str] = mapped_column(String(64), nullable=False)
    claim_b_id: Mapped[str] = mapped_column(String(64), nullable=False)
    source_a_id: Mapped[str] = mapped_column(String(64), default="")
    source_b_id: Mapped[str] = mapped_column(String(64), default="")
    contradiction_type: Mapped[str] = mapped_column(String(64), default="PARAMETER_DISCREPANCY")
    description: Mapped[str] = mapped_column(Text, nullable=False)
    scope_difference: Mapped[str] = mapped_column(Text, default="")
    parameter_difference: Mapped[str] = mapped_column(Text, default="")
    methodological_difference: Mapped[str] = mapped_column(Text, default="")
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


class GraphNodeRecord(Base):
    """Persisted record for a Semantic Graph node."""

    __tablename__ = "graph_nodes"

    graph_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    node_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    node_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    entity_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    label: Mapped[str] = mapped_column(Text, default="")
    entity_version: Mapped[int] = mapped_column(Integer, default=1)
    provenance_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)
    updated_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp, onupdate=current_iso_timestamp)


class GraphEdgeRecord(Base):
    """Persisted record for a Semantic Graph edge."""

    __tablename__ = "graph_edges"

    graph_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    edge_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    relation_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    source_node_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    target_node_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    provenance_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)
    updated_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp, onupdate=current_iso_timestamp)


class GraphMetadataRecord(Base):
    """Persisted metadata header and content hash for a Semantic Graph."""

    __tablename__ = "graph_metadata"

    graph_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    schema_version: Mapped[str] = mapped_column(String(32), default="0.4.0")
    content_hash: Mapped[str] = mapped_column(String(64), default="")
    node_count: Mapped[int] = mapped_column(Integer, default=0)
    edge_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)
    updated_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp, onupdate=current_iso_timestamp)


class GraphDeltaRecord(Base):
    """Persisted journal record of atomic graph delta operations."""

    __tablename__ = "graph_deltas"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    graph_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    delta_id: Mapped[str] = mapped_column(String(64), nullable=False)
    delta_index: Mapped[int] = mapped_column(Integer, default=0)
    operations_json: Mapped[str] = mapped_column(Text, default="[]")
    provenance_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


class ExperimentDesignRecord(Base):
    """Persisted declarative ExperimentDesign record."""

    __tablename__ = "experiment_designs"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    hypothesis_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(256), nullable=False)
    description: Mapped[str] = mapped_column(Text, default="")
    version: Mapped[int] = mapped_column(Integer, default=1)
    parameter_space_json: Mapped[str] = mapped_column(Text, default="{}")
    computation_plan_json: Mapped[str] = mapped_column(Text, default="{}")
    falsification_criteria_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)
    updated_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp, onupdate=current_iso_timestamp)


class ExperimentalDesignCandidateRecord(Base):
    """Persisted ExperimentalDesignCandidate record."""

    __tablename__ = "experimental_design_candidates"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    research_question_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    hypothesis_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    model_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    parameter_assignments_json: Mapped[str] = mapped_column(Text, default="{}")
    controlled_variables_json: Mapped[str] = mapped_column(Text, default="{}")
    independent_variables_json: Mapped[str] = mapped_column(Text, default="[]")
    dependent_variables_json: Mapped[str] = mapped_column(Text, default="[]")
    target_observables_json: Mapped[str] = mapped_column(Text, default="[]")
    constraints_json: Mapped[str] = mapped_column(Text, default="[]")
    expected_information_json: Mapped[str] = mapped_column(Text, default="{}")
    design_objective: Mapped[str] = mapped_column(String(64), default="MODEL_DISCRIMINATION")
    execution_requirements_json: Mapped[str] = mapped_column(Text, default="{}")
    resource_requirements_json: Mapped[str] = mapped_column(Text, default="{}")
    risk_constraints_json: Mapped[str] = mapped_column(Text, default="[]")
    assumptions_json: Mapped[str] = mapped_column(Text, default="[]")
    design_status: Mapped[str] = mapped_column(String(64), default="CANDIDATE")
    design_strategy: Mapped[str] = mapped_column(String(64), default="GRID")
    random_seed: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sensitivity_study_ref: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)
    updated_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp, onupdate=current_iso_timestamp)


class CandidateDesignEvaluationRecord(Base):
    """Persisted CandidateDesignEvaluation record."""

    __tablename__ = "candidate_design_evaluations"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    candidate_design_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    model_predictions_json: Mapped[str] = mapped_column(Text, default="{}")
    predicted_differences_json: Mapped[str] = mapped_column(Text, default="{}")
    numerical_uncertainties_json: Mapped[str] = mapped_column(Text, default="{}")
    sensitivities_json: Mapped[str] = mapped_column(Text, default="{}")
    discrimination_metric_json: Mapped[str] = mapped_column(Text, default="{}")
    discrimination_score: Mapped[float] = mapped_column(Float, default=0.0)
    numerical_robustness: Mapped[float] = mapped_column(Float, default=1.0)
    parameter_coverage: Mapped[float] = mapped_column(Float, default=1.0)
    resource_cost: Mapped[float] = mapped_column(Float, default=0.0)
    constraint_satisfaction: Mapped[bool] = mapped_column(Boolean, default=True)
    sensitivity_alignment: Mapped[float] = mapped_column(Float, default=1.0)
    expected_observable_difference: Mapped[float] = mapped_column(Float, default=0.0)
    evaluation_status: Mapped[str] = mapped_column(String(64), default="COMPLETED")
    notes: Mapped[str] = mapped_column(Text, default="")
    provenance_refs_json: Mapped[str] = mapped_column(Text, default="[]")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


class ParetoCandidateSetRecord(Base):
    """Persisted ParetoCandidateSet record."""

    __tablename__ = "pareto_candidate_sets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    project_id: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    non_dominated_candidate_ids_json: Mapped[str] = mapped_column(Text, default="[]")
    objectives_json: Mapped[str] = mapped_column(Text, default="[]")
    evaluations_json: Mapped[str] = mapped_column(Text, default="[]")
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    created_at: Mapped[str] = mapped_column(String(64), default=current_iso_timestamp)


def json_dumps_helper(obj: Any) -> str:
    """Helper for converting Python structures to JSON strings."""
    return json.dumps(obj)


def json_loads_helper(raw: str) -> Any:
    """Helper for safely decoding JSON strings."""
    if not raw:
        return []
    try:
        return json.loads(raw)
    except Exception:
        return []
