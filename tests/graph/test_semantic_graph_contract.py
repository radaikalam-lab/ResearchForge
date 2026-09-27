"""Tests for semantic graph models, vocabulary, query engine, and deterministic serialization."""

import pytest
from researchforge.domain.graph import (
    GraphQueryEngine,
    ResearchEdge,
    ResearchGraph,
    ResearchNode,
    ResearchNodeType,
    ResearchRelationType,
    compute_graph_content_hash,
    deserialize_graph,
    get_relation_rule,
    serialize_graph,
)


def test_ontology_relation_rules_completeness() -> None:
    """Validate all ResearchRelationType values have defined ontology rules with valid sources/targets."""
    for rel_type in ResearchRelationType:
        rule = get_relation_rule(rel_type)
        assert rule.relation_type == rel_type
        assert len(rule.valid_source_types) > 0
        assert len(rule.valid_target_types) > 0
        assert rule.description != ""

    with pytest.raises(KeyError):
        get_relation_rule("UNKNOWN_RELATION")  # type: ignore


def test_graph_node_and_edge_mutation() -> None:
    """Validate adding, retrieving, and removing nodes and edges in ResearchGraph."""
    graph = ResearchGraph(graph_id="g_test_01")

    n_proj = ResearchNode(
        node_id="proj_01",
        node_type=ResearchNodeType.PROJECT,
        entity_id="proj_01",
        label="Test Project",
    )
    n_q = ResearchNode(
        node_id="q_01",
        node_type=ResearchNodeType.QUESTION,
        entity_id="q_01",
        label="Test Question",
    )

    graph.add_node(n_proj)
    graph.add_node(n_q)

    assert graph.node_count == 2
    assert graph.has_node("proj_01") is True
    assert graph.get_node("proj_01") == n_proj

    edge = ResearchEdge(
        edge_id="e_asks_01",
        relation_type=ResearchRelationType.ASKS,
        source_node_id="proj_01",
        target_node_id="q_01",
        provenance_ref="prov_01",
    )
    graph.add_edge(edge)

    assert graph.edge_count == 1
    assert graph.has_edge("e_asks_01") is True

    # Test node removal also cleans incident edges
    removed_proj = graph.remove_node("proj_01")
    assert removed_proj == n_proj
    assert graph.has_node("proj_01") is False
    assert graph.has_edge("e_asks_01") is False
    assert graph.edge_count == 0


def test_graph_query_engine_traversal() -> None:
    """Validate query engine primitives: outgoing, incoming, neighbors, related, find_nodes, path_exists."""
    graph = ResearchGraph(graph_id="g_query_01")

    n1 = ResearchNode(node_id="q_01", node_type=ResearchNodeType.QUESTION, entity_id="q_01")
    n2 = ResearchNode(node_id="src_01", node_type=ResearchNodeType.SOURCE, entity_id="src_01")
    n3 = ResearchNode(node_id="ev_01", node_type=ResearchNodeType.EVIDENCE, entity_id="ev_01")
    n4 = ResearchNode(node_id="claim_01", node_type=ResearchNodeType.CLAIM, entity_id="claim_01")

    for n in (n1, n2, n3, n4):
        graph.add_node(n)

    e1 = ResearchEdge(
        edge_id="e1",
        relation_type=ResearchRelationType.SOURCED_FROM,
        source_node_id="ev_01",
        target_node_id="src_01",
    )
    e2 = ResearchEdge(
        edge_id="e2",
        relation_type=ResearchRelationType.SUPPORTS,
        source_node_id="ev_01",
        target_node_id="claim_01",
    )
    graph.add_edge(e1)
    graph.add_edge(e2)

    # 1. Outgoing and Incoming
    out_edges = GraphQueryEngine.outgoing(graph, "ev_01")
    assert len(out_edges) == 2
    in_edges = GraphQueryEngine.incoming(graph, "claim_01")
    assert len(in_edges) == 1
    assert in_edges[0].edge_id == "e2"

    # 2. Neighbors and Related
    neighbors = GraphQueryEngine.neighbors(graph, "ev_01")
    assert {n.node_id for n in neighbors} == {"src_01", "claim_01"}

    supporting = GraphQueryEngine.related(graph, "ev_01", ResearchRelationType.SUPPORTS)
    assert len(supporting) == 1
    assert supporting[0].node_id == "claim_01"

    # 3. Find by type
    claims = GraphQueryEngine.find_nodes(graph, ResearchNodeType.CLAIM)
    assert len(claims) == 1
    assert claims[0].node_id == "claim_01"

    # 4. Path existence
    assert GraphQueryEngine.path_exists(graph, "ev_01", "claim_01") is True
    assert GraphQueryEngine.path_exists(graph, "claim_01", "src_01") is False


def test_deterministic_graph_serialization_roundtrip() -> None:
    """Validate canonical serialization, deserialization, and deterministic SHA-256 hash reproducibility."""
    graph = ResearchGraph(graph_id="g_serial_01")

    n1 = ResearchNode(node_id="n_b", node_type=ResearchNodeType.CLAIM, entity_id="c_02", label="Claim B")
    n2 = ResearchNode(node_id="n_a", node_type=ResearchNodeType.EVIDENCE, entity_id="ev_01", label="Evidence A")
    graph.add_node(n1)
    graph.add_node(n2)

    e1 = ResearchEdge(
        edge_id="e_01",
        relation_type=ResearchRelationType.SUPPORTS,
        source_node_id="n_a",
        target_node_id="n_b",
        confidence=0.95,
    )
    graph.add_edge(e1)

    hash1 = compute_graph_content_hash(graph)
    serialized = serialize_graph(graph)

    # Roundtrip deserialization
    reconstructed = deserialize_graph(serialized)
    hash2 = compute_graph_content_hash(reconstructed)

    assert hash1 == hash2
    assert reconstructed.node_count == graph.node_count
    assert reconstructed.edge_count == graph.edge_count
    assert reconstructed.has_edge("e_01") is True
