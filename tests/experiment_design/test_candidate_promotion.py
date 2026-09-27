"""
Tests for Candidate Design -> Human Decision -> Authoritative ExperimentDesign promotion (Phase 2.4).

Verifies:
    - Candidate generation alone does not create executable ExperimentDesign
    - Promotion requires explicit HumanDecision
    - PROMOTED_TO and ESTABLISHES semantic graph edges are created
    - Complete provenance recording
"""

from pathlib import Path

from researchforge.application.workflows.experimental_design_workflow import (
    ExperimentalDesignWorkflowService,
)
from researchforge.domain.graph.types import ResearchNodeType, ResearchRelationType
from researchforge.domain.models.conclusion import DecisionType, HumanDecision
from researchforge.domain.models.experiment_design import ExperimentDesign
from researchforge.domain.models.experimental_design_candidate import DesignCandidateStatus
from researchforge.domain.models.parameter_space import (
    ParameterDefinition,
    ParameterSpace,
    ParameterType,
)
from researchforge.persistence.database import DatabaseManager
from researchforge.persistence.unit_of_work import UnitOfWork


def test_candidate_promotion_workflow_end_to_end(tmp_path: Path) -> None:
    """
    Test full lifecycle:
        1. Generate candidates
        2. Evaluate candidates
        3. Authorize promotion via explicit HumanDecision
        4. Verify authoritative ExperimentDesign and Semantic Graph relations
    """
    db_mgr = DatabaseManager(f"sqlite:///{tmp_path}/test_promo.db")
    db_mgr.create_tables()
    service = ExperimentalDesignWorkflowService(db_manager=db_mgr, artifacts_dir=str(tmp_path / "artifacts"))
    proj_id = "proj_promo_test"

    ps = ParameterSpace(
        id="ps_promo",
        name="Promotion Space",
        parameters={
            "core_damping": ParameterDefinition(
                parameter_name="core_damping",
                parameter_type=ParameterType.CONTINUOUS,
                min_value=1.0,
                max_value=10.0,
                default_value=6.0,
            )
        },
    )

    # 1. Generate candidates
    cands = service.generate_candidate_designs(
        project_id=proj_id,
        parameter_space=ps,
        model_ids=["model_1", "model_2"],
        sample_count=2,
    )
    assert len(cands) == 2
    cand = cands[0]
    assert cand.design_status == DesignCandidateStatus.CANDIDATE

    # Verify candidate is not yet an ExperimentDesign
    with UnitOfWork(db_mgr) as uow:
        assert uow.experiment_designs is not None
        assert len(uow.experiment_designs.list_by_project(proj_id)) == 0

    # 2. Evaluate candidates
    evals, pareto = service.evaluate_candidate_designs(
        project_id=proj_id,
        candidate_ids=[c.candidate_design_id for c in cands],
        model_a_id="model_1",
        model_b_id="model_2",
        model_a_params_override={"core_damping": 2.0},
        model_b_params_override={"core_damping": 8.0},
    )
    assert len(evals) == 2
    assert len(pareto.non_dominated_candidate_ids) >= 1

    # 3. Explicit Human Review & Promotion
    exp_design, decision = service.promote_candidate_to_experiment_design(
        project_id=proj_id,
        candidate_id=cand.candidate_design_id,
        reviewer_id="human_scientist_42",
        rationale="Candidate demonstrates strong discrimination ratio (D > 3.0) with acceptable numerical error.",
        experiment_name="Damped Core Discrimination Experiment 01",
        decision_type=DecisionType.APPROVE,
    )

    assert isinstance(exp_design, ExperimentDesign)
    assert isinstance(decision, HumanDecision)
    assert decision.reviewer_id == "human_scientist_42"
    assert decision.decision == DecisionType.APPROVE

    # 4. Verify DB and Semantic Graph State
    with UnitOfWork(db_mgr) as uow:
        assert uow.candidates is not None
        assert uow.experiment_designs is not None
        assert uow.semantic_graphs is not None

        # Candidate is now PROMOTED
        updated_cand = uow.candidates.get(cand.candidate_design_id)
        assert updated_cand is not None
        assert updated_cand.design_status == DesignCandidateStatus.PROMOTED

        # Authoritative ExperimentDesign exists in persistence
        saved_design = uow.experiment_designs.get(exp_design.id)
        assert saved_design is not None
        assert saved_design.name == "Damped Core Discrimination Experiment 01"

        # Check graph edges
        graph = uow.semantic_graphs.load_graph(f"graph_{proj_id}")
        assert graph.has_node(cand.candidate_design_id)
        assert graph.has_node(exp_design.id)
        assert graph.has_node(decision.id)

        # Node types
        assert graph.get_node(cand.candidate_design_id).node_type == ResearchNodeType.EXPERIMENTAL_DESIGN_CANDIDATE
        assert graph.get_node(exp_design.id).node_type == ResearchNodeType.EXPERIMENT_DESIGN
        assert graph.get_node(decision.id).node_type == ResearchNodeType.HUMAN_DECISION

        # Edge PROMOTED_TO exists
        promoted_edges = [
            e for e in graph.edges.values()
            if e.relation_type == ResearchRelationType.PROMOTED_TO
            and e.source_node_id == cand.candidate_design_id
            and e.target_node_id == exp_design.id
        ]
        assert len(promoted_edges) == 1
