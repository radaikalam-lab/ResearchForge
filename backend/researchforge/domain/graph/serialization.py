"""Deterministic Serialization and Hashing for ResearchGraph (Phase 0.4)."""

import hashlib
from typing import Any

from researchforge.domain.base import canonical_json_dumps
from researchforge.domain.graph.models import ResearchEdge, ResearchGraph, ResearchNode
from researchforge.domain.graph.types import ResearchNodeType, ResearchRelationType


def serialize_graph(graph: ResearchGraph) -> dict[str, Any]:
    """Serialize ResearchGraph into a deterministic canonical dictionary."""
    sorted_nodes = [
        {
            "node_id": node.node_id,
            "node_type": str(node.node_type),
            "entity_id": node.entity_id,
            "entity_version": node.entity_version,
            "label": node.label,
            "metadata": node.metadata,
        }
        for node in sorted(graph.nodes.values(), key=lambda n: n.node_id)
    ]

    sorted_edges = [
        {
            "edge_id": edge.edge_id,
            "relation_type": str(edge.relation_type),
            "source_node_id": edge.source_node_id,
            "target_node_id": edge.target_node_id,
            "provenance_ref": edge.provenance_ref or "",
            "confidence": edge.confidence,
            "metadata": edge.metadata,
        }
        for edge in sorted(graph.edges.values(), key=lambda e: e.edge_id)
    ]

    return {
        "graph_id": graph.graph_id,
        "schema_version": graph.schema_version,
        "nodes": sorted_nodes,
        "edges": sorted_edges,
    }


def deserialize_graph(data: dict[str, Any]) -> ResearchGraph:
    """Reconstruct a ResearchGraph from serialized dictionary payload."""
    graph = ResearchGraph(
        graph_id=data["graph_id"],
        schema_version=data.get("schema_version", "0.4.0"),
    )

    for n_data in data.get("nodes", []):
        node = ResearchNode(
            node_id=n_data["node_id"],
            node_type=ResearchNodeType(n_data["node_type"]),
            entity_id=n_data["entity_id"],
            entity_version=n_data.get("entity_version", "1.0.0"),
            label=n_data.get("label", ""),
            metadata=n_data.get("metadata", {}),
        )
        graph.add_node(node)

    for e_data in data.get("edges", []):
        edge = ResearchEdge(
            edge_id=e_data["edge_id"],
            relation_type=ResearchRelationType(e_data["relation_type"]),
            source_node_id=e_data["source_node_id"],
            target_node_id=e_data["target_node_id"],
            provenance_ref=e_data.get("provenance_ref") or None,
            confidence=e_data.get("confidence"),
            metadata=e_data.get("metadata", {}),
        )
        graph.add_edge(edge, validate_nodes=False)

    return graph


def compute_graph_content_hash(graph: ResearchGraph) -> str:
    """Compute deterministic SHA-256 digest over canonical serialized graph payload."""
    canonical = canonical_json_dumps(serialize_graph(graph))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
