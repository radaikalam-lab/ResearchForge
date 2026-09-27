"""
Integration test: Wave Lattice Experiment through the full ResearchForge
semantic graph, persistence, and provenance pipeline (Phase 2.2).

Tests:
- Full experiment lifecycle (plan + run) through the workflow service
- Semantic graph representation with correct relationships
- Graph invariant validation
- Provenance recording
- Deterministic replay (same params → same observables → same output_hash)
- Falsification evaluation correctness
- Baseline vs heterogeneous experiment comparability
"""

from __future__ import annotations

from pathlib import Path

import pytest
from researchforge.application.workflows.literature_trajectory import LiteratureEvidenceWorkflowService
from researchforge.application.workflows.wave_lattice_workflow import WaveLatticeWorkflowService
from researchforge.domain.models.falsification import FalsificationStatus
from researchforge.domain.models.wave_lattice import (
    BoundaryCondition,
    WaveLatticeParameters,
    simulate_1d_damped_wave_lattice,
)
from researchforge.persistence.database import DatabaseManager
from researchforge.persistence.unit_of_work import UnitOfWork

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _setup_project(db_mgr: DatabaseManager, tmp_path: Path) -> tuple[str, str]:
    """Run the literature trajectory to get a project + hypothesis."""
    svc = LiteratureEvidenceWorkflowService(
        db_manager=db_mgr,
        artifacts_dir=tmp_path / "artifacts",
    )
    res = await svc.execute_literature_trajectory()
    return res.project.id, res.hypotheses[0].id


def _make_db(tmp_path: Path, name: str = "test_wave.db") -> DatabaseManager:
    db_mgr = DatabaseManager(f"sqlite:///{tmp_path}/{name}")
    db_mgr.create_tables()
    return db_mgr


def _base_params(label: str = "baseline") -> WaveLatticeParameters:
    return WaveLatticeParameters(
        id=f"params_{label}",
        nodes=80,
        time_steps=100,
        dx=1.0,
        dt=0.4,
        density=1.0,
        stiffness=1.0,
        damping=0.0,
        core_start=30,
        core_end=50,
        core_density=1.0,
        core_stiffness=1.0,
        core_damping=0.0,
        source_amplitude=1.0,
        source_location=5,
        source_duration=15,
        boundary_condition=BoundaryCondition.ABSORBING,
        experiment_label=label,
    )


def _het_params(label: str = "heterogeneous") -> WaveLatticeParameters:
    return WaveLatticeParameters(
        id=f"params_{label}",
        nodes=80,
        time_steps=100,
        dx=1.0,
        dt=0.4,
        density=1.0,
        stiffness=1.0,
        damping=0.0,
        core_start=30,
        core_end=50,
        core_density=1.0,
        core_stiffness=1.0,
        core_damping=10.0,
        source_amplitude=1.0,
        source_location=5,
        source_duration=15,
        boundary_condition=BoundaryCondition.ABSORBING,
        experiment_label=label,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_wave_experiment_full_lifecycle(tmp_path: Path) -> None:
    """
    End-to-end test: plan + run a wave lattice experiment via the workflow service,
    verify graph, provenance, run, and falsification are all recorded.
    """
    db_mgr = _make_db(tmp_path)
    project_id, hyp_id = await _setup_project(db_mgr, tmp_path)

    svc = WaveLatticeWorkflowService(
        artifacts_dir=tmp_path / "wave_artifacts",
        db_manager=db_mgr,
    )
    params = _base_params()

    # 1. Plan the experiment (registers design in semantic graph)
    design_dict = await svc.plan_wave_experiment(
        project_id=project_id,
        hypothesis_id=hyp_id,
        params=params,
        experiment_name="Wave Baseline Plan",
    )
    assert "id" in design_dict
    assert "wave_params" in design_dict

    # 2. Run the experiment
    wave_result = await svc.run_wave_experiment(
        project_id=project_id,
        hypothesis_id=hyp_id,
        params=params,
        db_manager=db_mgr,
        attenuation_threshold=0.9,
        experiment_name="Wave Baseline Run",
    )

    # 3. Verify result contract
    assert wave_result.run.status == "COMPLETED"
    assert wave_result.run.output_hash != ""
    assert wave_result.observables.max_displacement >= 0.0
    assert wave_result.observables.attenuation_ratio >= 0.0
    assert wave_result.provenance_event_id != ""

    # 4. Verify falsification
    assert wave_result.falsification.hypothesis_id == hyp_id
    assert wave_result.falsification.status in {
        FalsificationStatus.SUPPORTED,
        FalsificationStatus.CONTRADICTED,
    }

    # 5. Verify semantic graph was updated
    with UnitOfWork(db_mgr) as uow:
        assert uow.semantic_graphs is not None
        graph = uow.semantic_graphs.load_graph(f"graph_{project_id}")
        node_types = {n.node_type for n in graph.nodes.values()}
        assert "EXPERIMENT" in node_types
        assert "EXPERIMENT_RUN" in node_types

    # 6. Graph invariant check
    from researchforge.domain.graph.validator import validate_graph
    with UnitOfWork(db_mgr) as uow:
        assert uow.semantic_graphs is not None
        graph = uow.semantic_graphs.load_graph(f"graph_{project_id}")
        val = validate_graph(graph)
        assert val.is_valid, f"Graph invariant violation: {val.errors}"


@pytest.mark.asyncio
async def test_wave_experiment_deterministic_replay(tmp_path: Path) -> None:
    """
    Running the same parameters twice must produce the same output_hash.
    This validates the determinism guarantee.
    Replay uses only the pure operator - no Cognitia, no LLM, no network.
    """
    db_mgr = _make_db(tmp_path, "replay.db")
    project_id, hyp_id = await _setup_project(db_mgr, tmp_path)
    svc = WaveLatticeWorkflowService(
        artifacts_dir=tmp_path / "wave_artifacts",
        db_manager=db_mgr,
    )
    params = _base_params()

    result1 = await svc.run_wave_experiment(
        project_id=project_id,
        hypothesis_id=hyp_id,
        params=params,
        db_manager=db_mgr,
        experiment_name="Wave Determinism Run 1",
    )
    result2 = await svc.run_wave_experiment(
        project_id=project_id,
        hypothesis_id=hyp_id,
        params=params,
        db_manager=db_mgr,
        experiment_name="Wave Determinism Run 2",
    )

    assert result1.observables.output_hash == result2.observables.output_hash
    assert result1.observables.input_hash == result2.observables.input_hash
    assert result1.observables.attenuation_ratio == result2.observables.attenuation_ratio


@pytest.mark.asyncio
async def test_wave_experiment_baseline_vs_heterogeneous(tmp_path: Path) -> None:
    """
    Experiment A (baseline) and Experiment B (heterogeneous core) must produce
    different results; the heterogeneous core must show measurable attenuation.
    """
    db_mgr = _make_db(tmp_path, "compare.db")
    project_id, hyp_id = await _setup_project(db_mgr, tmp_path)
    svc = WaveLatticeWorkflowService(
        artifacts_dir=tmp_path / "wave_artifacts",
        db_manager=db_mgr,
    )

    params_b = _base_params("baseline")
    params_h = _het_params("heterogeneous")

    result_b = await svc.run_wave_experiment(
        project_id=project_id,
        hypothesis_id=hyp_id,
        params=params_b,
        db_manager=db_mgr,
        experiment_name="Wave Experiment A (Baseline)",
    )
    result_h = await svc.run_wave_experiment(
        project_id=project_id,
        hypothesis_id=hyp_id,
        params=params_h,
        db_manager=db_mgr,
        experiment_name="Wave Experiment B (Heterogeneous)",
    )

    # Different params → different output hashes
    assert result_b.observables.output_hash != result_h.observables.output_hash

    # Heterogeneous core with high damping should show lower core displacement
    assert result_h.observables.max_core_displacement < result_b.observables.max_core_displacement

    # Heterogeneous experiment should dissipate more energy
    assert result_h.observables.dissipated_energy > result_b.observables.dissipated_energy

    # Both should share the same incident energy (identical source)
    assert result_b.observables.incident_energy == pytest.approx(
        result_h.observables.incident_energy, rel=1e-9
    )


@pytest.mark.asyncio
async def test_wave_experiment_falsification_with_strict_threshold(tmp_path: Path) -> None:
    """
    With threshold=0.0, any positive attenuation_ratio → CONTRADICTED.
    With threshold=1.0, all passive-material experiments → SUPPORTED.
    """
    db_mgr = _make_db(tmp_path, "fals.db")
    project_id, hyp_id = await _setup_project(db_mgr, tmp_path)
    svc = WaveLatticeWorkflowService(
        artifacts_dir=tmp_path / "wave_artifacts",
        db_manager=db_mgr,
    )
    params = _het_params()

    # Threshold = 0.0 → CONTRADICTED (ratio > 0 since core is still reached by wave)
    result_strict = await svc.run_wave_experiment(
        project_id=project_id,
        hypothesis_id=hyp_id,
        params=params,
        db_manager=db_mgr,
        attenuation_threshold=0.0,
        experiment_name="Strict Threshold Test",
    )
    assert result_strict.falsification.status == FalsificationStatus.CONTRADICTED

    # Threshold = 1.0 → SUPPORTED (attenuation_ratio <= 1.0 for passive material)
    result_lenient = await svc.run_wave_experiment(
        project_id=project_id,
        hypothesis_id=hyp_id,
        params=params,
        db_manager=db_mgr,
        attenuation_threshold=1.0,
        experiment_name="Lenient Threshold Test",
    )
    assert result_lenient.falsification.status == FalsificationStatus.SUPPORTED


@pytest.mark.asyncio
async def test_wave_experiment_graph_relationships(tmp_path: Path) -> None:
    """
    Verify that the required semantic graph relationships are established:
    Hypothesis → TESTED_BY → Experiment → EXECUTED_AS → ExperimentRun
    Analysis → INFORMS_FALSIFICATION → FalsificationEvaluation → EVALUATES → run
    """
    db_mgr = _make_db(tmp_path, "graph_rel.db")
    project_id, hyp_id = await _setup_project(db_mgr, tmp_path)
    svc = WaveLatticeWorkflowService(
        artifacts_dir=tmp_path / "wave_artifacts",
        db_manager=db_mgr,
    )
    params = _base_params()

    result = await svc.run_wave_experiment(
        project_id=project_id,
        hypothesis_id=hyp_id,
        params=params,
        db_manager=db_mgr,
        experiment_name="Graph Relationship Test",
    )

    exp_id = result.experiment.id
    run_id = result.run.id
    fals_id = result.falsification.id

    with UnitOfWork(db_mgr) as uow:
        assert uow.semantic_graphs is not None
        graph = uow.semantic_graphs.load_graph(f"graph_{project_id}")

        # Verify node existence
        assert graph.has_node(exp_id), f"EXPERIMENT node {exp_id} missing from graph"
        assert graph.has_node(run_id), f"EXPERIMENT_RUN node {run_id} missing from graph"
        assert graph.has_node(fals_id), f"FALSIFICATION_EVALUATION node {fals_id} missing"

        # Verify relationships
        edge_types = {e.relation_type for e in graph.edges.values()}
        assert "EXECUTED_AS" in edge_types, "EXECUTED_AS relationship missing"
        assert "INFORMS_FALSIFICATION" in edge_types, "INFORMS_FALSIFICATION relationship missing"
        assert "EVALUATES" in edge_types, "EVALUATES relationship missing"


@pytest.mark.asyncio
async def test_wave_experiment_provenance_recorded(tmp_path: Path) -> None:
    """Provenance event ID must be non-empty and start with 'prov_'."""
    db_mgr = _make_db(tmp_path, "prov.db")
    project_id, hyp_id = await _setup_project(db_mgr, tmp_path)
    svc = WaveLatticeWorkflowService(
        artifacts_dir=tmp_path / "wave_artifacts",
        db_manager=db_mgr,
    )
    params = _base_params()

    result = await svc.run_wave_experiment(
        project_id=project_id,
        hypothesis_id=hyp_id,
        params=params,
        db_manager=db_mgr,
        experiment_name="Provenance Test",
    )
    assert result.provenance_event_id != ""
    assert result.provenance_event_id.startswith("prov_")


def test_wave_replay_without_cognitia_or_network() -> None:
    """
    Replay (re-running the pure operator) must be independent of Cognitia,
    network, database, or LLM.  Verified by calling the operator standalone.
    """
    p = WaveLatticeParameters(
        id="replay_test",
        nodes=60,
        time_steps=80,
        dx=1.0,
        dt=0.4,
        density=1.0,
        stiffness=1.0,
        damping=0.0,
        core_start=20,
        core_end=40,
        core_density=1.0,
        core_stiffness=1.0,
        core_damping=5.0,
        source_amplitude=1.0,
        source_location=3,
        source_duration=10,
        boundary_condition=BoundaryCondition.ABSORBING,
    )
    out1 = simulate_1d_damped_wave_lattice(p)
    out2 = simulate_1d_damped_wave_lattice(p)
    assert out1["observables"]["output_hash"] == out2["observables"]["output_hash"]
