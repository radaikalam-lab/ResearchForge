"""Integration tests for Phase 2 Experiment Planning Workflow and Semantic Graph generation."""

from pathlib import Path

import pytest
from researchforge.application.workflows.experiment_trajectory import ExperimentPlanningWorkflowService
from researchforge.application.workflows.literature_trajectory import LiteratureEvidenceWorkflowService
from researchforge.domain.graph.query import GraphQueryEngine
from researchforge.domain.graph.types import ResearchNodeType, ResearchRelationType
from researchforge.domain.graph.validator import validate_graph
from researchforge.domain.models.computation_plan import (
    AnalysisSpecification,
    DatasetSpecification,
    ExecutionSpecification,
)
from researchforge.domain.models.parameter_space import (
    ParameterConstraint,
    ParameterDefinition,
    ParameterType,
    SamplingStrategy,
)
from researchforge.persistence.database import DatabaseManager
from researchforge.persistence.unit_of_work import UnitOfWork
from researchforge.provenance.replay import ProvenanceReplayEngine


@pytest.mark.asyncio
async def test_experiment_planning_workflow_creates_valid_semantic_graph(tmp_path: Path) -> None:
    """Validate that planning an experiment creates domain models,
    records provenance, and builds a valid SemanticGraph.
    """
    db_file = tmp_path / "exp_plan.db"
    db_mgr = DatabaseManager(f"sqlite:///{db_file}")
    db_mgr.create_tables()

    # 1. Execute Phase 1 Literature Trajectory to establish Question, Evidence, Gap, and Hypothesis
    lit_service = LiteratureEvidenceWorkflowService(
        db_manager=db_mgr,
        artifacts_dir=tmp_path / "artifacts",
    )
    lit_res = await lit_service.execute_literature_trajectory(
        question_text="What is the scaling response of Parameter X on Yield Y?",
        primary_variable="Parameter X",
        target_phenomenon="Yield Y",
    )

    project_id = lit_res.project.id
    hypothesis_id = lit_res.hypotheses[0].id

    # 2. Execute Phase 2 Experiment Planning
    plan_service = ExperimentPlanningWorkflowService(
        db_manager=db_mgr,
        artifacts_dir=tmp_path / "artifacts",
    )

    p1 = ParameterDefinition(
        id="param_x",
        parameter_name="Parameter X",
        parameter_type=ParameterType.CONTINUOUS,
        unit="Concentration (mM)",
        min_value=0.0,
        max_value=5.0,
        default_value=1.0,
    )
    con = ParameterConstraint(
        id="con_x",
        name="max_solubility",
        expression="Parameter X <= 5.0",
        parameters_involved=["Parameter X"],
    )

    exec_spec = ExecutionSpecification(
        id="exec_spec_01",
        timeout_seconds=120,
        reproducibility_seed=42,
    )
    ds_spec = DatasetSpecification(
        id="ds_spec_01",
        name="experiment_runs.csv",
        expected_columns=["param_x", "yield_y"],
    )
    an_spec = AnalysisSpecification(
        id="an_spec_01",
        name="Linear vs Quadratic Response OLS",
        target_variables=["yield_y"],
    )

    design = await plan_service.plan_experiment_trajectory(
        project_id=project_id,
        hypothesis_id=hypothesis_id,
        experiment_name="Scaling Response Assay",
        parameter_definitions=[p1],
        constraints=[con],
        sampling_strategy=SamplingStrategy.GRID,
        sample_count=25,
        execution_spec=exec_spec,
        dataset_specs=[ds_spec],
        analysis_specs=[an_spec],
    )

    assert design.hypothesis_id == hypothesis_id
    assert design.parameter_space.sample_count == 25

    # 3. Verify Persistence and Semantic Graph Invariants
    with UnitOfWork(db_mgr) as uow:
        assert uow.semantic_graphs is not None
        assert uow.experiment_designs is not None
        assert uow.experiments is not None

        # Verify domain entity persistence
        persisted_design = uow.experiment_designs.get(design.id)
        assert persisted_design is not None
        assert persisted_design.name == "Scaling Response Assay Design"

        # Load persisted SemanticGraph
        graph = uow.semantic_graphs.load_graph(f"graph_{project_id}")
        assert graph.node_count >= 6
        assert graph.edge_count >= 5

        # Check Node Types
        assert len(GraphQueryEngine.find_nodes(graph, ResearchNodeType.EXPERIMENT)) >= 1
        assert len(GraphQueryEngine.find_nodes(graph, ResearchNodeType.EXPERIMENT_DESIGN)) >= 1
        assert len(GraphQueryEngine.find_nodes(graph, ResearchNodeType.PARAMETER_SPACE)) >= 1
        assert len(GraphQueryEngine.find_nodes(graph, ResearchNodeType.COMPUTATION_PLAN)) >= 1

        # Check Relationships
        assert len(GraphQueryEngine.find_edges(graph, ResearchRelationType.TESTS)) >= 1
        assert len(GraphQueryEngine.find_edges(graph, ResearchRelationType.TESTED_BY)) >= 1
        assert len(GraphQueryEngine.find_edges(graph, ResearchRelationType.HAS_DESIGN)) >= 1
        assert len(GraphQueryEngine.find_edges(graph, ResearchRelationType.HAS_PARAMETER_SPACE)) >= 1
        assert len(GraphQueryEngine.find_edges(graph, ResearchRelationType.HAS_COMPUTATION_PLAN)) >= 1
        assert len(GraphQueryEngine.find_edges(graph, ResearchRelationType.SPECIFIES_EXECUTION)) >= 1

        # Validate Graph Contract Invariants
        val_res = validate_graph(graph)
        assert val_res.is_valid is True

    # 4. Verify Provenance Replay of Complete Sequence
    with UnitOfWork(db_mgr) as uow:
        assert uow.provenance_repo is not None
        all_events = uow.provenance_repo.list_all()

    replayed = ProvenanceReplayEngine.replay(all_events)
    replayed_graph = replayed.semantic_graph
    assert replayed_graph.node_count >= 6
    assert len(replayed.experiments) >= 1
    assert len(replayed.experiment_designs) >= 1
