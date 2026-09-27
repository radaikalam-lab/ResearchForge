"""Semantic Graph Query Primitives (Phase 0.4)."""

from collections import deque
from typing import Literal

from researchforge.domain.graph.models import ResearchEdge, ResearchGraph, ResearchNode
from researchforge.domain.graph.types import ResearchNodeType, ResearchRelationType


class GraphQueryEngine:
    """Minimal, efficient query primitives for traversing and inspecting a ResearchGraph."""

    @staticmethod
    def outgoing(
        graph: ResearchGraph,
        node_id: str,
        relation_type: ResearchRelationType | str | None = None,
    ) -> list[ResearchEdge]:
        """Find all outgoing edges from node_id, optionally filtered by relation type."""
        rel_str = str(relation_type) if relation_type else None
        return [
            edge
            for edge in graph.edges.values()
            if edge.source_node_id == node_id and (rel_str is None or str(edge.relation_type) == rel_str)
        ]

    @staticmethod
    def incoming(
        graph: ResearchGraph,
        node_id: str,
        relation_type: ResearchRelationType | str | None = None,
    ) -> list[ResearchEdge]:
        """Find all incoming edges to node_id, optionally filtered by relation type."""
        rel_str = str(relation_type) if relation_type else None
        return [
            edge
            for edge in graph.edges.values()
            if edge.target_node_id == node_id and (rel_str is None or str(edge.relation_type) == rel_str)
        ]

    @staticmethod
    def neighbors(
        graph: ResearchGraph,
        node_id: str,
        direction: Literal["OUTGOING", "INCOMING", "BOTH"] = "BOTH",
    ) -> list[ResearchNode]:
        """Retrieve neighboring nodes connected to node_id."""
        neighbor_ids: set[str] = set()
        if direction in ("OUTGOING", "BOTH"):
            for e in graph.edges.values():
                if e.source_node_id == node_id:
                    neighbor_ids.add(e.target_node_id)
        if direction in ("INCOMING", "BOTH"):
            for e in graph.edges.values():
                if e.target_node_id == node_id:
                    neighbor_ids.add(e.source_node_id)

        return [graph.nodes[n_id] for n_id in neighbor_ids if n_id in graph.nodes]

    @staticmethod
    def related(
        graph: ResearchGraph,
        node_id: str,
        relation_type: ResearchRelationType | str,
        direction: Literal["OUTGOING", "INCOMING", "BOTH"] = "OUTGOING",
    ) -> list[ResearchNode]:
        """Find nodes connected to node_id via a specific relation type."""
        rel_str = str(relation_type)
        target_ids: set[str] = set()

        if direction in ("OUTGOING", "BOTH"):
            for e in graph.edges.values():
                if e.source_node_id == node_id and str(e.relation_type) == rel_str:
                    target_ids.add(e.target_node_id)

        if direction in ("INCOMING", "BOTH"):
            for e in graph.edges.values():
                if e.target_node_id == node_id and str(e.relation_type) == rel_str:
                    target_ids.add(e.source_node_id)

        return [graph.nodes[nid] for nid in target_ids if nid in graph.nodes]

    @staticmethod
    def find_nodes(
        graph: ResearchGraph,
        node_type: ResearchNodeType | str,
    ) -> list[ResearchNode]:
        """Find all nodes of a specific NodeType in the graph."""
        type_str = str(node_type)
        return [node for node in graph.nodes.values() if str(node.node_type) == type_str]

    @staticmethod
    def find_edges(
        graph: ResearchGraph,
        relation_type: ResearchRelationType | str,
    ) -> list[ResearchEdge]:
        """Find all edges of a specific RelationType in the graph."""
        rel_str = str(relation_type)
        return [edge for edge in graph.edges.values() if str(edge.relation_type) == rel_str]

    @staticmethod
    def path_exists(
        graph: ResearchGraph,
        source_node_id: str,
        target_node_id: str,
        max_depth: int = 10,
    ) -> bool:
        """Check if a directed semantic path exists between source and target nodes."""
        if source_node_id not in graph.nodes or target_node_id not in graph.nodes:
            return False
        if source_node_id == target_node_id:
            return True

        visited: set[str] = {source_node_id}
        queue: deque[tuple[str, int]] = deque([(source_node_id, 0)])

        while queue:
            curr_id, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for edge in graph.edges.values():
                if edge.source_node_id == curr_id:
                    nxt = edge.target_node_id
                    if nxt == target_node_id:
                        return True
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append((nxt, depth + 1))

        return False

    @staticmethod
    def find_path(
        graph: ResearchGraph,
        source_node_id: str,
        target_node_id: str,
        max_depth: int = 10,
    ) -> list[str] | None:
        """Find the shortest directed path between source and target nodes."""
        if source_node_id not in graph.nodes or target_node_id not in graph.nodes:
            return None
        if source_node_id == target_node_id:
            return [source_node_id]

        visited: set[str] = {source_node_id}
        queue: deque[tuple[str, list[str]]] = deque([(source_node_id, [source_node_id])])

        while queue:
            curr_id, path = queue.popleft()
            if len(path) > max_depth:
                continue

            for edge in graph.edges.values():
                if edge.source_node_id == curr_id:
                    nxt = edge.target_node_id
                    if nxt == target_node_id:
                        return [*path, nxt]
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append((nxt, [*path, nxt]))

        return None
