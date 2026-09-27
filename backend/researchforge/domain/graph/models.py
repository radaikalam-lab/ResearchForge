"""Semantic Graph Domain Models (Phase 0.4)."""

import hashlib
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from researchforge.domain.base import canonical_json_dumps
from researchforge.domain.graph.types import (
    DanglingEdgeError,
    ResearchNodeType,
    ResearchRelationType,
)


class ResearchNode(BaseModel):
    """A first-class node in the ResearchForge semantic graph representing a domain entity."""

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    node_id: str
    node_type: ResearchNodeType
    entity_id: str
    entity_version: str = "1.0.0"
    label: str = ""
    provenance_ref: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def compute_node_hash(self) -> str:
        """Compute deterministic SHA-256 hash of canonical node payload."""
        payload = {
            "node_id": self.node_id,
            "node_type": str(self.node_type),
            "entity_id": self.entity_id,
            "entity_version": self.entity_version,
            "label": self.label,
            "provenance_ref": self.provenance_ref,
            "metadata": self.metadata,
        }
        return hashlib.sha256(canonical_json_dumps(payload).encode("utf-8")).hexdigest()


class ResearchEdge(BaseModel):
    """A first-class directed edge in the semantic graph representing a typed relationship."""

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    edge_id: str
    relation_type: ResearchRelationType
    source_node_id: str
    target_node_id: str
    provenance_ref: str | None = None
    confidence: float | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def compute_edge_hash(self) -> str:
        """Compute deterministic SHA-256 hash of canonical edge payload."""
        payload = {
            "edge_id": self.edge_id,
            "relation_type": str(self.relation_type),
            "source_node_id": self.source_node_id,
            "target_node_id": self.target_node_id,
            "provenance_ref": self.provenance_ref or "",
            "confidence": self.confidence,
            "metadata": self.metadata,
        }
        return hashlib.sha256(canonical_json_dumps(payload).encode("utf-8")).hexdigest()


class ResearchGraph(BaseModel):
    """In-memory, typed, validated semantic graph for the computational research lifecycle."""

    model_config = ConfigDict(populate_by_name=True, validate_assignment=True)

    graph_id: str
    schema_version: str = "0.4.0"
    nodes: dict[str, ResearchNode] = Field(default_factory=dict)
    edges: dict[str, ResearchEdge] = Field(default_factory=dict)

    def add_node(self, node: ResearchNode) -> ResearchNode:
        """Add or update a node in the graph."""
        self.nodes[node.node_id] = node
        return node

    def add_edge(self, edge: ResearchEdge, validate_nodes: bool = True) -> ResearchEdge:
        """Add an edge to the graph. If validate_nodes is True, verifies source and target exist."""
        if validate_nodes:
            if edge.source_node_id not in self.nodes:
                raise DanglingEdgeError(
                    f"Edge {edge.edge_id} source node {edge.source_node_id} does not exist in graph."
                )
            if edge.target_node_id not in self.nodes:
                raise DanglingEdgeError(
                    f"Edge {edge.edge_id} target node {edge.target_node_id} does not exist in graph."
                )
        self.edges[edge.edge_id] = edge
        return edge

    def get_node(self, node_id: str) -> ResearchNode | None:
        """Retrieve node by ID."""
        return self.nodes.get(node_id)

    def get_edge(self, edge_id: str) -> ResearchEdge | None:
        """Retrieve edge by ID."""
        return self.edges.get(edge_id)

    def has_node(self, node_id: str) -> bool:
        """Check if node exists."""
        return node_id in self.nodes

    def has_edge(self, edge_id: str) -> bool:
        """Check if edge exists."""
        return edge_id in self.edges

    def remove_node(self, node_id: str) -> ResearchNode | None:
        """Remove a node and any attached edges."""
        if node_id not in self.nodes:
            return None
        node = self.nodes.pop(node_id)
        # Remove incident edges
        edges_to_remove = [
            e_id for e_id, e in self.edges.items() if e.source_node_id == node_id or e.target_node_id == node_id
        ]
        for e_id in edges_to_remove:
            self.edges.pop(e_id, None)
        return node

    def remove_edge(self, edge_id: str) -> ResearchEdge | None:
        """Remove an edge by ID."""
        return self.edges.pop(edge_id, None)

    @property
    def node_count(self) -> int:
        """Total number of nodes."""
        return len(self.nodes)

    @property
    def edge_count(self) -> int:
        """Total number of edges."""
        return len(self.edges)

    def compute_graph_hash(self) -> str:
        """Compute deterministic SHA-256 hash of entire sorted graph structure."""
        sorted_nodes = sorted([n.compute_node_hash() for n in self.nodes.values()])
        sorted_edges = sorted([e.compute_edge_hash() for e in self.edges.values()])
        manifest = {
            "graph_id": self.graph_id,
            "schema_version": self.schema_version,
            "node_hashes": sorted_nodes,
            "edge_hashes": sorted_edges,
        }
        return hashlib.sha256(canonical_json_dumps(manifest).encode("utf-8")).hexdigest()
