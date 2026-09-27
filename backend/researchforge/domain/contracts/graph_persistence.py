"""Semantic Graph Persistence Contract Port (Phase 2)."""

from typing import Protocol

from researchforge.domain.graph.delta import GraphDelta
from researchforge.domain.graph.models import ResearchGraph
from researchforge.domain.graph.validator import GraphValidationResult


class GraphPersistencePort(Protocol):
    """Authoritative persistence boundary contract for semantic graphs."""

    def persist_graph(self, graph: ResearchGraph) -> str:
        """Persist or overwrite a complete ResearchGraph state, returning the graph content hash."""
        ...

    def load_graph(self, graph_id: str) -> ResearchGraph:
        """Reconstruct and validate a complete ResearchGraph from persistent storage."""
        ...

    def append_graph_delta(self, graph_id: str, delta: GraphDelta) -> ResearchGraph:
        """Atomically apply and persist a validated GraphDelta sequence onto an existing graph."""
        ...

    def load_subgraph(
        self,
        graph_id: str,
        root_node_ids: list[str],
        max_depth: int = 2,
    ) -> ResearchGraph:
        """Extract a topologically bounded subgraph starting from root nodes up to max_depth."""
        ...

    def graph_exists(self, graph_id: str) -> bool:
        """Check whether a graph exists in persistent storage."""
        ...

    def get_graph_version(self, graph_id: str) -> str:
        """Retrieve the schema version or content hash of a persisted graph."""
        ...

    def verify_graph_integrity(self, graph_id: str) -> GraphValidationResult:
        """Inspect and validate the structural and ontological invariants of a persisted graph."""
        ...
