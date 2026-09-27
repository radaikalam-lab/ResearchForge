"""Unit and integration tests for GraphPersistenceAdapter, graph hashing, deltas, and transactional boundaries."""

from pathlib import Path

import pytest
from researchforge.domain.graph.delta import GraphDelta, GraphDeltaItem, GraphDeltaOp
from researchforge.domain.graph.models import ResearchEdge, ResearchGraph, ResearchNode
from researchforge.domain.graph.serialization import compute_graph_content_hash
from researchforge.domain.graph.types import (
    GraphValidationError,
    ResearchNodeType,
    ResearchRelationType,
)
from researchforge.persistence.database import DatabaseManager
from researchforge.persistence.unit_of_work import UnitOfWork


def test_graph_persistence_adapter_roundtrip_preserves_content_hash(tmp_path: Path) -> None:
    """Verify that persisting and loading a graph preserves identical canonical content hash."""
    db_file = tmp_path / "graph_store.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    # 1. Build a valid SemanticGraph
    graph = ResearchGraph(graph_id="graph_test_roundtrip")
    n1 = ResearchNode(node_id="proj_01", node_type=ResearchNodeType.PROJECT, entity_id="proj_01", label="Project Alpha")
    n2 = ResearchNode(node_id="q_01", node_type=ResearchNodeType.QUESTION, entity_id="q_01", label="Question 1")
    n3 = ResearchNode(node_id="hyp_01", node_type=ResearchNodeType.HYPOTHESIS, entity_id="hyp_01", label="Hypothesis 1")
    n4 = ResearchNode(node_id="exp_01", node_type=ResearchNodeType.EXPERIMENT, entity_id="exp_01", label="Experiment 1")

    graph.add_node(n1)
    graph.add_node(n2)
    graph.add_node(n3)
    graph.add_node(n4)

    e1 = ResearchEdge(
        edge_id="e1",
        relation_type=ResearchRelationType.ASKS,
        source_node_id="proj_01",
        target_node_id="q_01",
        provenance_ref="p1",
    )
    e2 = ResearchEdge(
        edge_id="e2",
        relation_type=ResearchRelationType.TESTS,
        source_node_id="exp_01",
        target_node_id="hyp_01",
        provenance_ref="p2",
    )
    graph.add_edge(e1)
    graph.add_edge(e2)

    initial_hash = compute_graph_content_hash(graph)

    # 2. Persist graph via UnitOfWork
    with UnitOfWork(db_mgr) as uow:
        assert uow.semantic_graphs is not None
        persisted_hash = uow.semantic_graphs.persist_graph(graph)
        assert persisted_hash == initial_hash

    # 3. Load graph in a new session and compare hash
    with UnitOfWork(db_mgr) as uow:
        assert uow.semantic_graphs is not None
        assert uow.semantic_graphs.graph_exists("graph_test_roundtrip") is True
        loaded_graph = uow.semantic_graphs.load_graph("graph_test_roundtrip")
        loaded_hash = compute_graph_content_hash(loaded_graph)

        assert loaded_hash == initial_hash
        assert loaded_graph.node_count == 4
        assert loaded_graph.edge_count == 2
        assert loaded_graph.get_node("proj_01").label == "Project Alpha"


def test_graph_delta_application_and_persistence(tmp_path: Path) -> None:
    """Verify applying a GraphDelta sequence onto a persisted graph."""
    db_file = tmp_path / "graph_delta.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    # Initial graph
    graph = ResearchGraph(graph_id="graph_delta_target")
    n1 = ResearchNode(node_id="hyp_base", node_type=ResearchNodeType.HYPOTHESIS, entity_id="hyp_base", label="Base Hyp")
    graph.add_node(n1)

    with UnitOfWork(db_mgr) as uow:
        assert uow.semantic_graphs is not None
        uow.semantic_graphs.persist_graph(graph)

    # Prepare Delta: Add Experiment node and TESTS edge
    n_exp = ResearchNode(
        node_id="exp_delta", node_type=ResearchNodeType.EXPERIMENT, entity_id="exp_delta", label="Delta Exp"
    )
    e_tests = ResearchEdge(
        edge_id="e_tests_delta",
        relation_type=ResearchRelationType.TESTS,
        source_node_id="exp_delta",
        target_node_id="hyp_base",
        provenance_ref="prov_delta_01",
    )

    delta = GraphDelta(
        delta_id="delta_01",
        graph_id="graph_delta_target",
        operations=[
            GraphDeltaItem(op=GraphDeltaOp.ADD_NODE, node=n_exp),
            GraphDeltaItem(op=GraphDeltaOp.ADD_EDGE, edge=e_tests),
        ],
        provenance_ref="prov_delta_batch",
    )

    with UnitOfWork(db_mgr) as uow:
        assert uow.semantic_graphs is not None
        updated_graph = uow.semantic_graphs.append_graph_delta("graph_delta_target", delta)
        assert updated_graph.node_count == 2
        assert updated_graph.edge_count == 1

    # Reload and verify
    with UnitOfWork(db_mgr) as uow:
        assert uow.semantic_graphs is not None
        reloaded = uow.semantic_graphs.load_graph("graph_delta_target")
        assert reloaded.has_node("exp_delta")
        assert reloaded.has_edge("e_tests_delta")


def test_invalid_graph_persistence_fails_closed(tmp_path: Path) -> None:
    """Verify that attempting to persist an invalid graph raises GraphValidationError."""
    db_file = tmp_path / "invalid_graph.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    invalid_graph = ResearchGraph(graph_id="invalid_graph")
    n1 = ResearchNode(node_id="hyp_1", node_type=ResearchNodeType.HYPOTHESIS, entity_id="hyp_1")
    invalid_graph.add_node(n1)

    # Incompatible relation: HYPOTHESIS cannot ASKS HYPOTHESIS
    e_invalid = ResearchEdge(
        edge_id="e_bad",
        relation_type=ResearchRelationType.ASKS,
        source_node_id="hyp_1",
        target_node_id="hyp_1",
        provenance_ref="p1",
    )
    invalid_graph.add_edge(e_invalid, validate_nodes=False)

    with UnitOfWork(db_mgr) as uow:
        assert uow.semantic_graphs is not None
        with pytest.raises(GraphValidationError):
            uow.semantic_graphs.persist_graph(invalid_graph)


def test_transaction_rollback_preserves_graph_state(tmp_path: Path) -> None:
    """Verify that transaction rollback properly discards uncommitted graph mutations."""
    db_file = tmp_path / "rollback_test.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    graph = ResearchGraph(graph_id="graph_rollback")
    n1 = ResearchNode(node_id="proj_init", node_type=ResearchNodeType.PROJECT, entity_id="proj_init")
    graph.add_node(n1)

    with UnitOfWork(db_mgr) as uow:
        assert uow.semantic_graphs is not None
        uow.semantic_graphs.persist_graph(graph)

    # Attempt mutation that raises an exception inside UnitOfWork
    try:
        with UnitOfWork(db_mgr) as uow:
            assert uow.semantic_graphs is not None
            delta = GraphDelta(
                delta_id="delta_fail",
                graph_id="graph_rollback",
                operations=[
                    GraphDeltaItem(
                        op=GraphDeltaOp.ADD_NODE,
                        node=ResearchNode(
                            node_id="node_temp", node_type=ResearchNodeType.QUESTION, entity_id="node_temp"
                        ),
                    )
                ],
            )
            uow.semantic_graphs.append_graph_delta("graph_rollback", delta)
            raise RuntimeError("Simulated failure during transaction")
    except RuntimeError:
        pass

    # Verify original graph state remained unchanged
    with UnitOfWork(db_mgr) as uow:
        assert uow.semantic_graphs is not None
        graph_curr = uow.semantic_graphs.load_graph("graph_rollback")
        assert graph_curr.node_count == 1
        assert not graph_curr.has_node("node_temp")
