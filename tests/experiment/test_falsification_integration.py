"""Integration tests connecting Hypotheses, Falsification Criteria,
Experiment Design, and Evaluations in the Semantic Graph.
"""

from researchforge.domain.graph.models import ResearchEdge, ResearchGraph, ResearchNode
from researchforge.domain.graph.query import GraphQueryEngine
from researchforge.domain.graph.types import ResearchNodeType, ResearchRelationType
from researchforge.domain.graph.validator import validate_graph


def test_falsification_graph_trajectory() -> None:
    """Verify semantic graph relationships from hypothesis through falsification evaluation."""
    graph = ResearchGraph(graph_id="falsification_trajectory_graph")

    # 1. Add Nodes
    n_hyp = ResearchNode(
        node_id="hyp_01", node_type=ResearchNodeType.HYPOTHESIS, entity_id="hyp_01", label="Linear scaling of Y with X"
    )
    n_design = ResearchNode(
        node_id="design_01",
        node_type=ResearchNodeType.EXPERIMENT_DESIGN,
        entity_id="design_01",
        label="OLS scaling design",
    )
    n_exp = ResearchNode(
        node_id="exp_01", node_type=ResearchNodeType.EXPERIMENT, entity_id="exp_01", label="OLS experiment protocol"
    )
    n_run = ResearchNode(node_id="run_01", node_type=ResearchNodeType.EXPERIMENT_RUN, entity_id="run_01")
    n_stat = ResearchNode(
        node_id="stat_01",
        node_type=ResearchNodeType.STATISTICAL_ANALYSIS,
        entity_id="stat_01",
        label="OLS Regression p=0.001",
    )
    n_fals = ResearchNode(
        node_id="fals_01", node_type=ResearchNodeType.FALSIFICATION_EVALUATION, entity_id="fals_01", label="SUPPORTED"
    )
    n_dec = ResearchNode(
        node_id="dec_01", node_type=ResearchNodeType.HUMAN_DECISION, entity_id="dec_01", label="Approved Finding"
    )
    n_concl = ResearchNode(
        node_id="concl_01",
        node_type=ResearchNodeType.CONCLUSION,
        entity_id="concl_01",
        label="Scientific finding confirmed",
    )

    for n in [n_hyp, n_design, n_exp, n_run, n_stat, n_fals, n_dec, n_concl]:
        graph.add_node(n)

    # 2. Add Semantic Edges
    # Hypothesis <-> Experiment
    graph.add_edge(
        ResearchEdge(
            edge_id="e_tested",
            relation_type=ResearchRelationType.TESTED_BY,
            source_node_id="hyp_01",
            target_node_id="exp_01",
            provenance_ref="p1",
        )
    )
    graph.add_edge(
        ResearchEdge(
            edge_id="e_tests",
            relation_type=ResearchRelationType.TESTS,
            source_node_id="exp_01",
            target_node_id="hyp_01",
            provenance_ref="p2",
        )
    )
    graph.add_edge(
        ResearchEdge(
            edge_id="e_has_design",
            relation_type=ResearchRelationType.HAS_DESIGN,
            source_node_id="exp_01",
            target_node_id="design_01",
            provenance_ref="p3",
        )
    )

    # Experiment -> Run
    graph.add_edge(
        ResearchEdge(
            edge_id="e_exec",
            relation_type=ResearchRelationType.EXECUTED_AS,
            source_node_id="exp_01",
            target_node_id="run_01",
            provenance_ref="p4",
        )
    )

    # Statistical Analysis -> Falsification Evaluation
    graph.add_edge(
        ResearchEdge(
            edge_id="e_informs_fals",
            relation_type=ResearchRelationType.INFORMS_FALSIFICATION,
            source_node_id="stat_01",
            target_node_id="fals_01",
            provenance_ref="p5",
        )
    )

    # Falsification Evaluation -> Hypothesis
    graph.add_edge(
        ResearchEdge(
            edge_id="e_eval",
            relation_type=ResearchRelationType.EVALUATES,
            source_node_id="fals_01",
            target_node_id="hyp_01",
            provenance_ref="p6",
        )
    )

    # Falsification Evaluation -> Human Decision -> Conclusion
    graph.add_edge(
        ResearchEdge(
            edge_id="e_informs_dec",
            relation_type=ResearchRelationType.INFORMS,
            source_node_id="fals_01",
            target_node_id="dec_01",
            provenance_ref="p7",
        )
    )
    graph.add_edge(
        ResearchEdge(
            edge_id="e_establishes",
            relation_type=ResearchRelationType.ESTABLISHES,
            source_node_id="dec_01",
            target_node_id="concl_01",
            provenance_ref="p8",
        )
    )

    # 3. Verify Validation
    val_res = validate_graph(graph)
    assert val_res.is_valid is True

    # 4. Traversal queries
    assert GraphQueryEngine.path_exists(graph, "stat_01", "hyp_01") is True
    assert GraphQueryEngine.path_exists(graph, "fals_01", "concl_01") is True
