"""Semantic Graph Delta Model and Application Logic (Phase 2)."""

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from researchforge.domain.base import utc_now
from researchforge.domain.graph.models import ResearchEdge, ResearchGraph, ResearchNode
from researchforge.domain.graph.types import GraphValidationError
from researchforge.domain.graph.validator import validate_graph


class GraphDeltaOp(StrEnum):
    """Supported graph mutation delta operations."""

    ADD_NODE = "ADD_NODE"
    UPDATE_NODE = "UPDATE_NODE"
    REMOVE_NODE = "REMOVE_NODE"
    ADD_EDGE = "ADD_EDGE"
    REMOVE_EDGE = "REMOVE_EDGE"


class GraphDeltaItem(BaseModel):
    """Atomic delta operation targeting a node or edge."""

    op: GraphDeltaOp
    node: ResearchNode | None = None
    edge: ResearchEdge | None = None
    target_id: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)


class GraphDelta(BaseModel):
    """Ordered collection of graph mutations with provenance attribution."""

    delta_id: str
    graph_id: str
    operations: list[GraphDeltaItem] = Field(default_factory=list)
    provenance_ref: str | None = None
    created_at: str = Field(default_factory=lambda: utc_now().isoformat())


def apply_delta(
    graph: ResearchGraph,
    delta: GraphDelta,
    validate_after: bool = True,
) -> ResearchGraph:
    """Apply an ordered graph delta sequence to a ResearchGraph, optionally validating invariants."""
    if graph.graph_id != delta.graph_id:
        raise GraphValidationError(
            f"Graph ID mismatch: Delta is for graph '{delta.graph_id}', but target graph is '{graph.graph_id}'."
        )

    for item in delta.operations:
        if item.op in (GraphDeltaOp.ADD_NODE, GraphDeltaOp.UPDATE_NODE):
            if not item.node:
                raise GraphValidationError(f"Delta operation {item.op} missing node payload.")
            graph.add_node(item.node)

        elif item.op == GraphDeltaOp.REMOVE_NODE:
            node_id = item.target_id or (item.node.node_id if item.node else "")
            if node_id:
                graph.remove_node(node_id)

        elif item.op == GraphDeltaOp.ADD_EDGE:
            if not item.edge:
                raise GraphValidationError("Delta operation ADD_EDGE missing edge payload.")
            graph.add_edge(item.edge, validate_nodes=False)

        elif item.op == GraphDeltaOp.REMOVE_EDGE:
            edge_id = item.target_id or (item.edge.edge_id if item.edge else "")
            if edge_id:
                graph.remove_edge(edge_id)

    if validate_after:
        val_res = validate_graph(graph)
        if not val_res.is_valid:
            raise GraphValidationError(
                f"Graph contract invariant violation after applying delta: {'; '.join(val_res.errors)}"
            )

    return graph
