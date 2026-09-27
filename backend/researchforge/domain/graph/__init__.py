"""ResearchForge Semantic Graph Package (Phase 0.4)."""

from researchforge.domain.graph.delta import (
    GraphDelta,
    GraphDeltaItem,
    GraphDeltaOp,
    apply_delta,
)
from researchforge.domain.graph.models import ResearchEdge, ResearchGraph, ResearchNode
from researchforge.domain.graph.ontology import ONTOLOGY_RELATION_RULES, get_relation_rule
from researchforge.domain.graph.query import GraphQueryEngine
from researchforge.domain.graph.serialization import (
    compute_graph_content_hash,
    deserialize_graph,
    serialize_graph,
)
from researchforge.domain.graph.types import (
    Cardinality,
    CardinalityViolationError,
    DanglingEdgeError,
    GraphError,
    GraphValidationError,
    InvalidEdgeError,
    InvalidNodeError,
    RelationRule,
    ResearchNodeType,
    ResearchRelationType,
)
from researchforge.domain.graph.validator import GraphValidationResult, validate_graph

__all__ = [
    "ONTOLOGY_RELATION_RULES",
    "Cardinality",
    "CardinalityViolationError",
    "DanglingEdgeError",
    "GraphDelta",
    "GraphDeltaItem",
    "GraphDeltaOp",
    "GraphError",
    "GraphQueryEngine",
    "GraphValidationError",
    "GraphValidationResult",
    "InvalidEdgeError",
    "InvalidNodeError",
    "RelationRule",
    "ResearchEdge",
    "ResearchGraph",
    "ResearchNode",
    "ResearchNodeType",
    "ResearchRelationType",
    "apply_delta",
    "compute_graph_content_hash",
    "deserialize_graph",
    "get_relation_rule",
    "serialize_graph",
    "validate_graph",
]
