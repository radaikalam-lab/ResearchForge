"""Tests for graph invariants, type compatibility, referential integrity, and cardinality validation."""

import pytest
from researchforge.domain.graph import (
    DanglingEdgeError,
    ResearchEdge,
    ResearchGraph,
    ResearchNode,
    ResearchNodeType,
    ResearchRelationType,
    validate_graph,
)


def test_valid_graph_passes_validation() -> None:
    """Validate that a well-formed graph conforming to ontology rules passes validation cleanly."""
    graph = ResearchGraph(graph_id="g_valid_01")

    proj = ResearchNode(node_id="proj_01", node_type=ResearchNodeType.PROJECT, entity_id="proj_01")
    q = ResearchNode(node_id="q_01", node_type=ResearchNodeType.QUESTION, entity_id="q_01")
    ev = ResearchNode(node_id="ev_01", node_type=ResearchNodeType.EVIDENCE, entity_id="ev_01")
    claim = ResearchNode(node_id="claim_01", node_type=ResearchNodeType.CLAIM, entity_id="claim_01")

    for n in (proj, q, ev, claim):
        graph.add_node(n)

    graph.add_edge(
        ResearchEdge(
            edge_id="e_asks",
            relation_type=ResearchRelationType.ASKS,
            source_node_id="proj_01",
            target_node_id="q_01",
            provenance_ref="prov_01",
        )
    )
    graph.add_edge(
        ResearchEdge(
            edge_id="e_supp",
            relation_type=ResearchRelationType.SUPPORTS,
            source_node_id="ev_01",
            target_node_id="claim_01",
            provenance_ref="prov_02",
        )
    )

    res = validate_graph(graph, strict_provenance=True)
    assert res.is_valid is True
    assert len(res.errors) == 0


def test_type_incompatibility_detection() -> None:
    """Validate that connecting incompatible source or target node types violates ontology rules."""
    graph = ResearchGraph(graph_id="g_invalid_types_01")

    claim = ResearchNode(node_id="c_01", node_type=ResearchNodeType.CLAIM, entity_id="c_01")
    exp = ResearchNode(node_id="exp_01", node_type=ResearchNodeType.EXPERIMENT, entity_id="exp_01")

    graph.add_node(claim)
    graph.add_node(exp)

    # TESTS relation requires source EXPERIMENT -> target HYPOTHESIS. Connecting CLAIM -> EXPERIMENT is illegal.
    illegal_edge = ResearchEdge(
        edge_id="e_illegal",
        relation_type=ResearchRelationType.TESTS,
        source_node_id="c_01",
        target_node_id="exp_01",
        provenance_ref="prov_01",
    )
    graph.add_edge(illegal_edge)

    res = validate_graph(graph)
    assert res.is_valid is False
    assert any("not in permitted source types" in err for err in res.errors)
    assert any("not in permitted target types" in err for err in res.errors)


def test_dangling_edge_rejection() -> None:
    """Validate that edges referencing missing nodes are rejected during insertion or validation."""
    graph = ResearchGraph(graph_id="g_dangling_01")

    node = ResearchNode(node_id="n_01", node_type=ResearchNodeType.PROJECT, entity_id="p_01")
    graph.add_node(node)

    # Insertion with node validation raises DanglingEdgeError
    dangling_edge = ResearchEdge(
        edge_id="e_dang",
        relation_type=ResearchRelationType.CONTAINS,
        source_node_id="n_01",
        target_node_id="non_existent_node",
    )
    with pytest.raises(DanglingEdgeError):
        graph.add_edge(dangling_edge, validate_nodes=True)

    # If added without node validation, validate_graph flags the dangling reference
    graph.add_edge(dangling_edge, validate_nodes=False)
    res = validate_graph(graph)
    assert res.is_valid is False
    assert any("references non-existent target node" in err for err in res.errors)


def test_cardinality_violation_detection() -> None:
    """Validate that ONE_TO_ONE or MANY_TO_ONE constraints are strictly enforced."""
    graph = ResearchGraph(graph_id="g_cardinality_01")

    dec1 = ResearchNode(node_id="dec_01", node_type=ResearchNodeType.HUMAN_DECISION, entity_id="dec_01")
    concl1 = ResearchNode(node_id="concl_01", node_type=ResearchNodeType.CONCLUSION, entity_id="concl_01")
    concl2 = ResearchNode(node_id="concl_02", node_type=ResearchNodeType.CONCLUSION, entity_id="concl_02")

    for n in (dec1, concl1, concl2):
        graph.add_node(n)

    # ESTABLISHES is ONE_TO_ONE: a decision can establish at most 1 conclusion
    graph.add_edge(
        ResearchEdge(
            edge_id="e_est_1",
            relation_type=ResearchRelationType.ESTABLISHES,
            source_node_id="dec_01",
            target_node_id="concl_01",
            provenance_ref="prov_01",
        )
    )
    graph.add_edge(
        ResearchEdge(
            edge_id="e_est_2",
            relation_type=ResearchRelationType.ESTABLISHES,
            source_node_id="dec_01",
            target_node_id="concl_02",
            provenance_ref="prov_02",
        )
    )

    res = validate_graph(graph)
    assert res.is_valid is False
    assert any("Cardinality violation for relation 'ESTABLISHES'" in err for err in res.errors)
