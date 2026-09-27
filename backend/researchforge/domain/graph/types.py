"""Semantic Graph Types, Node/Relation Vocabularies, Cardinality, and Invariants (Phase 0.4)."""

from dataclasses import dataclass
from enum import StrEnum


class ResearchNodeType(StrEnum):
    """Controlled vocabulary of semantic node types in ResearchForge."""

    PROJECT = "PROJECT"
    THREAD = "THREAD"
    QUESTION = "QUESTION"
    SOURCE = "SOURCE"
    EVIDENCE_FRAGMENT = "EVIDENCE_FRAGMENT"
    EVIDENCE = "EVIDENCE"
    CLAIM = "CLAIM"
    CONTRADICTION = "CONTRADICTION"
    RESEARCH_GAP = "RESEARCH_GAP"
    HYPOTHESIS = "HYPOTHESIS"
    EXPERIMENT = "EXPERIMENT"
    EXPERIMENT_DESIGN = "EXPERIMENT_DESIGN"
    EXPERIMENT_SPECIFICATION = "EXPERIMENT_SPECIFICATION"
    PARAMETER_SPACE = "PARAMETER_SPACE"
    PARAMETER_DEFINITION = "PARAMETER_DEFINITION"
    PARAMETER_CONSTRAINT = "PARAMETER_CONSTRAINT"
    COMPUTATION_PLAN = "COMPUTATION_PLAN"
    EXECUTION_SPECIFICATION = "EXECUTION_SPECIFICATION"
    DATASET_SPECIFICATION = "DATASET_SPECIFICATION"
    ANALYSIS_SPECIFICATION = "ANALYSIS_SPECIFICATION"
    STATISTICAL_ANALYSIS = "STATISTICAL_ANALYSIS"
    EXPERIMENT_RUN = "EXPERIMENT_RUN"
    FALSIFICATION_EVALUATION = "FALSIFICATION_EVALUATION"
    HUMAN_DECISION = "HUMAN_DECISION"
    CONCLUSION = "CONCLUSION"
    ARTIFACT = "ARTIFACT"
    SCIENTIFIC_MODEL = "SCIENTIFIC_MODEL"
    ASSUMPTION = "ASSUMPTION"
    NUMERICAL_VERIFICATION = "NUMERICAL_VERIFICATION"
    CONVERGENCE_STUDY = "CONVERGENCE_STUDY"
    REFERENCE_SOLUTION = "REFERENCE_SOLUTION"
    MODEL_COMPARISON = "MODEL_COMPARISON"
    SENSITIVITY_STUDY = "SENSITIVITY_STUDY"
    EXPERIMENTAL_DESIGN_CANDIDATE = "EXPERIMENTAL_DESIGN_CANDIDATE"
    CANDIDATE_DESIGN_EVALUATION = "CANDIDATE_DESIGN_EVALUATION"
    PARETO_CANDIDATE_SET = "PARETO_CANDIDATE_SET"
    OBSERVABLE_DEFINITION = "OBSERVABLE_DEFINITION"


class ResearchRelationType(StrEnum):
    """Controlled vocabulary of semantic relationship types in ResearchForge."""

    CONTAINS = "CONTAINS"
    HAS_THREAD = "HAS_THREAD"
    ASKS = "ASKS"
    SOURCED_FROM = "SOURCED_FROM"
    CONTAINS_FRAGMENT = "CONTAINS_FRAGMENT"
    SUPPORTS = "SUPPORTS"
    REFUTES = "REFUTES"
    QUALIFIES = "QUALIFIES"
    CONTRADICTS = "CONTRADICTS"
    ADDRESSES = "ADDRESSES"
    MOTIVATES = "MOTIVATES"
    DERIVED_FROM = "DERIVED_FROM"
    TESTS = "TESTS"
    TESTED_BY = "TESTED_BY"
    HAS_DESIGN = "HAS_DESIGN"
    HAS_PARAMETER_SPACE = "HAS_PARAMETER_SPACE"
    CONTAINS_PARAMETER = "CONTAINS_PARAMETER"
    CONSTRAINED_BY = "CONSTRAINED_BY"
    HAS_COMPUTATION_PLAN = "HAS_COMPUTATION_PLAN"
    SPECIFIES_EXECUTION = "SPECIFIES_EXECUTION"
    SPECIFIES_DATASET = "SPECIFIES_DATASET"
    SPECIFIES_ANALYSIS = "SPECIFIES_ANALYSIS"
    EXECUTED_AS = "EXECUTED_AS"
    PRODUCES = "PRODUCES"
    PRODUCES_DATASET = "PRODUCES_DATASET"
    ANALYSIS_CONSUMES = "ANALYSIS_CONSUMES"
    INFORMS_FALSIFICATION = "INFORMS_FALSIFICATION"
    EVALUATES = "EVALUATES"
    INFORMS = "INFORMS"
    ESTABLISHES = "ESTABLISHES"
    MATERIALIZES_AS = "MATERIALIZES_AS"
    HAS_ASSUMPTION = "HAS_ASSUMPTION"
    USED_BY = "USED_BY"
    COMPARES = "COMPARES"
    GENERATES_EVIDENCE_FOR = "GENERATES_EVIDENCE_FOR"
    INFORMS_DESIGN = "INFORMS_DESIGN"
    EVALUATES_CANDIDATE = "EVALUATES_CANDIDATE"
    PROMOTED_TO = "PROMOTED_TO"
    TARGETS_OBSERVABLE = "TARGETS_OBSERVABLE"
    INCLUDES_CANDIDATE = "INCLUDES_CANDIDATE"


class Cardinality(StrEnum):
    """Cardinality constraints for semantic relationships."""

    ONE_TO_ONE = "ONE_TO_ONE"
    ONE_TO_MANY = "ONE_TO_MANY"
    MANY_TO_ONE = "MANY_TO_ONE"
    MANY_TO_MANY = "MANY_TO_MANY"


@dataclass(frozen=True)
class RelationRule:
    """Ontological definition and constraints governing a specific relation type."""

    relation_type: ResearchRelationType
    valid_source_types: set[ResearchNodeType]
    valid_target_types: set[ResearchNodeType]
    cardinality: Cardinality
    description: str
    requires_provenance: bool = True


class GraphError(Exception):
    """Base exception for all semantic graph operations."""

    pass


class GraphValidationError(GraphError):
    """Raised when a semantic graph violates ontology or invariant rules."""

    pass


class InvalidNodeError(GraphValidationError):
    """Raised when a node type or identity is invalid."""

    pass


class InvalidEdgeError(GraphValidationError):
    """Raised when an edge connects incompatible node types or violates relation rules."""

    pass


class DanglingEdgeError(GraphValidationError):
    """Raised when an edge references non-existent source or target nodes."""

    pass


class CardinalityViolationError(GraphValidationError):
    """Raised when relationship cardinality constraints are breached."""

    pass
