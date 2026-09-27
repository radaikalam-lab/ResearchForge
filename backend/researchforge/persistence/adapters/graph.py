"""Semantic Graph Persistence Adapter implementing GraphPersistencePort."""

import json
from collections import deque

from sqlalchemy.orm import Session

from researchforge.domain.contracts.graph_persistence import GraphPersistencePort
from researchforge.domain.graph.delta import GraphDelta, apply_delta
from researchforge.domain.graph.models import ResearchEdge, ResearchGraph, ResearchNode
from researchforge.domain.graph.serialization import compute_graph_content_hash
from researchforge.domain.graph.types import (
    GraphValidationError,
    ResearchNodeType,
    ResearchRelationType,
)
from researchforge.domain.graph.validator import GraphValidationResult, validate_graph
from researchforge.persistence.models import (
    GraphDeltaRecord,
    GraphEdgeRecord,
    GraphMetadataRecord,
    GraphNodeRecord,
)


class GraphPersistenceAdapter(GraphPersistencePort):
    """Relational SQL adapter for persisting and querying contract-governed Semantic Graphs."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def persist_graph(self, graph: ResearchGraph) -> str:
        """Persist or overwrite a complete ResearchGraph state, returning the graph content hash."""
        # 1. Enforce strict invariant validation before persistence (fail-closed)
        val_res = validate_graph(graph)
        if not val_res.is_valid:
            raise GraphValidationError(f"Cannot persist invalid graph '{graph.graph_id}': {'; '.join(val_res.errors)}")

        content_hash = compute_graph_content_hash(graph)

        # 2. Delete existing node and edge records for this graph_id
        self.session.query(GraphEdgeRecord).filter(GraphEdgeRecord.graph_id == graph.graph_id).delete()
        self.session.query(GraphNodeRecord).filter(GraphNodeRecord.graph_id == graph.graph_id).delete()

        # 3. Insert Node Records
        for node in graph.nodes.values():
            node_rec = GraphNodeRecord(
                graph_id=graph.graph_id,
                node_id=node.node_id,
                node_type=str(node.node_type),
                entity_id=node.entity_id,
                label=node.label,
                entity_version=node.entity_version,
                provenance_ref=node.provenance_ref,
                metadata_json=json.dumps(node.metadata),
            )
            self.session.add(node_rec)

        # 4. Insert Edge Records
        for edge in graph.edges.values():
            edge_rec = GraphEdgeRecord(
                graph_id=graph.graph_id,
                edge_id=edge.edge_id,
                relation_type=str(edge.relation_type),
                source_node_id=edge.source_node_id,
                target_node_id=edge.target_node_id,
                provenance_ref=edge.provenance_ref,
                confidence=edge.confidence,
                metadata_json=json.dumps(edge.metadata),
            )
            self.session.add(edge_rec)

        # 5. Upsert Graph Metadata Record
        meta_rec = (
            self.session.query(GraphMetadataRecord).filter(GraphMetadataRecord.graph_id == graph.graph_id).first()
        )

        if meta_rec is None:
            meta_rec = GraphMetadataRecord(
                graph_id=graph.graph_id,
                schema_version=graph.schema_version,
                content_hash=content_hash,
                node_count=graph.node_count,
                edge_count=graph.edge_count,
            )
            self.session.add(meta_rec)
        else:
            meta_rec.schema_version = graph.schema_version
            meta_rec.content_hash = content_hash
            meta_rec.node_count = graph.node_count
            meta_rec.edge_count = graph.edge_count

        self.session.flush()
        return content_hash

    def load_graph(self, graph_id: str) -> ResearchGraph:
        """Reconstruct and validate a complete ResearchGraph from persistent storage."""
        meta_rec = self.session.query(GraphMetadataRecord).filter(GraphMetadataRecord.graph_id == graph_id).first()

        if meta_rec is None:
            raise KeyError(f"Graph '{graph_id}' not found in persistent storage.")

        graph = ResearchGraph(
            graph_id=graph_id,
            schema_version=meta_rec.schema_version,
        )

        # Load Nodes
        node_recs = self.session.query(GraphNodeRecord).filter(GraphNodeRecord.graph_id == graph_id).all()

        for nr in node_recs:
            try:
                meta = json.loads(nr.metadata_json) if nr.metadata_json else {}
            except Exception:
                meta = {}
            node = ResearchNode(
                node_id=nr.node_id,
                node_type=ResearchNodeType(nr.node_type),
                entity_id=nr.entity_id,
                entity_version=nr.entity_version,
                label=nr.label,
                provenance_ref=nr.provenance_ref,
                metadata=meta,
            )
            graph.add_node(node)

        # Load Edges
        edge_recs = self.session.query(GraphEdgeRecord).filter(GraphEdgeRecord.graph_id == graph_id).all()

        for er in edge_recs:
            try:
                meta = json.loads(er.metadata_json) if er.metadata_json else {}
            except Exception:
                meta = {}
            edge = ResearchEdge(
                edge_id=er.edge_id,
                relation_type=ResearchRelationType(er.relation_type),
                source_node_id=er.source_node_id,
                target_node_id=er.target_node_id,
                provenance_ref=er.provenance_ref,
                confidence=er.confidence,
                metadata=meta,
            )
            graph.add_edge(edge, validate_nodes=False)

        # Validate loaded graph (fail closed)
        val_res = validate_graph(graph)
        if not val_res.is_valid:
            raise GraphValidationError(
                f"Persisted graph '{graph_id}' failed contract validation: {'; '.join(val_res.errors)}"
            )

        return graph

    def append_graph_delta(self, graph_id: str, delta: GraphDelta) -> ResearchGraph:
        """Atomically apply and persist a validated GraphDelta sequence onto an existing graph."""
        graph = self.load_graph(graph_id)
        updated_graph = apply_delta(graph, delta, validate_after=True)
        self.persist_graph(updated_graph)

        # Record delta log
        delta_count = self.session.query(GraphDeltaRecord).filter(GraphDeltaRecord.graph_id == graph_id).count()

        ops_data = [
            {
                "op": str(op.op),
                "node": op.node.model_dump() if op.node else None,
                "edge": op.edge.model_dump() if op.edge else None,
                "target_id": op.target_id,
            }
            for op in delta.operations
        ]

        delta_rec = GraphDeltaRecord(
            id=f"{graph_id}_{delta.delta_id}_{delta_count}",
            graph_id=graph_id,
            delta_id=delta.delta_id,
            delta_index=delta_count,
            operations_json=json.dumps(ops_data),
            provenance_ref=delta.provenance_ref,
        )
        self.session.add(delta_rec)
        self.session.flush()

        return updated_graph

    def load_subgraph(
        self,
        graph_id: str,
        root_node_ids: list[str],
        max_depth: int = 2,
    ) -> ResearchGraph:
        """Extract a topologically bounded subgraph starting from root nodes up to max_depth."""
        full_graph = self.load_graph(graph_id)
        visited_nodes: set[str] = set()
        queue: deque[tuple[str, int]] = deque((nid, 0) for nid in root_node_ids if full_graph.has_node(nid))

        while queue:
            curr_id, depth = queue.popleft()
            if curr_id in visited_nodes or depth > max_depth:
                continue
            visited_nodes.add(curr_id)

            if depth < max_depth:
                # Find outgoing and incoming neighbors
                for edge in full_graph.edges.values():
                    if edge.source_node_id == curr_id and edge.target_node_id not in visited_nodes:
                        queue.append((edge.target_node_id, depth + 1))
                    elif edge.target_node_id == curr_id and edge.source_node_id not in visited_nodes:
                        queue.append((edge.source_node_id, depth + 1))

        subgraph = ResearchGraph(
            graph_id=f"{graph_id}_subgraph",
            schema_version=full_graph.schema_version,
        )
        for nid in visited_nodes:
            subgraph.add_node(full_graph.get_node(nid))

        for edge in full_graph.edges.values():
            if edge.source_node_id in visited_nodes and edge.target_node_id in visited_nodes:
                subgraph.add_edge(edge, validate_nodes=False)

        return subgraph

    def graph_exists(self, graph_id: str) -> bool:
        """Check whether a graph exists in persistent storage."""
        return self.session.query(GraphMetadataRecord).filter(GraphMetadataRecord.graph_id == graph_id).count() > 0

    def get_graph_version(self, graph_id: str) -> str:
        """Retrieve the content hash of a persisted graph."""
        meta = self.session.query(GraphMetadataRecord).filter(GraphMetadataRecord.graph_id == graph_id).first()
        if not meta:
            raise KeyError(f"Graph '{graph_id}' not found.")
        return meta.content_hash

    def verify_graph_integrity(self, graph_id: str) -> GraphValidationResult:
        """Inspect and validate the structural and ontological invariants of a persisted graph."""
        try:
            graph = self.load_graph(graph_id)
            return validate_graph(graph)
        except Exception as e:
            return GraphValidationResult(is_valid=False, errors=[str(e)], warnings=[])
