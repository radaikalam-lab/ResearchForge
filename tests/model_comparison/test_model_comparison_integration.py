"""
Integration tests for Phase 2.3 model comparison workflow.

Tests:
- Scientific model registration in semantic graph
- Numerical verification
- Convergence study
- Sensitivity study
- Model comparison
- Graph relationships
- Provenance recording
"""

from __future__ import annotations

from pathlib import Path

import pytest
from researchforge.application.workflows.literature_trajectory import LiteratureEvidenceWorkflowService
from researchforge.application.workflows.model_comparison_workflow import ModelComparisonWorkflowService
from researchforge.domain.graph.types import ResearchNodeType
from researchforge.domain.models.hypothesis import Assumption, AssumptionCategory
from researchforge.domain.models.model_comparison import (
    ModelComparisonResult,
)
from researchforge.domain.models.numerical_verification import (
    ModelValidationStatus,
    VerificationType,
)
from researchforge.domain.models.wave_lattice import (
    BoundaryCondition,
    WaveLatticeParameters,
)
from researchforge.persistence.database import DatabaseManager
from researchforge.persistence.unit_of_work import UnitOfWork

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _setup_project(db_mgr: DatabaseManager, tmp_path: Path) -> tuple[str, str]:
    svc = LiteratureEvidenceWorkflowService(
        db_manager=db_mgr,
        artifacts_dir=tmp_path / "artifacts",
    )
    res = await svc.execute_literature_trajectory()
    return res.project.id, res.hypotheses[0].id


def _make_db(tmp_path: Path, name: str = "test_model.db") -> DatabaseManager:
    db_mgr = DatabaseManager(f"sqlite:///{tmp_path}/{name}")
    db_mgr.create_tables()
    return db_mgr


def _base_params(label: str = "baseline") -> WaveLatticeParameters:
    return WaveLatticeParameters(
        id=f"params_{label}",
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
        source_location=5,
        source_duration=15,
        boundary_condition=BoundaryCondition.ABSORBING,
        experiment_label=label,
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_register_scientific_model(tmp_path: Path) -> None:
    db_mgr = _make_db(tmp_path)
    project_id, _ = await _setup_project(db_mgr, tmp_path)
    svc = ModelComparisonWorkflowService(
        artifacts_dir=tmp_path / "model_artifacts",
        db_manager=db_mgr,
    )
    assumption = Assumption(
        id="assump_test",
        statement="Linear elastic material",
        category=AssumptionCategory.CONSTITUTIVE,
        status="ACTIVE",
        scope="Global",
    )
    model = svc.register_scientific_model(
        project_id=project_id,
        name="1-D Damped Wave Model",
        version="1.0.0",
        mathematical_form="rho u_tt + gamma u_t = d/dx[E du/dx] + source",
        state_variables=["u(x,t)", "v(x,t)"],
        assumptions=[assumption],
        boundary_conditions={"left": "ABSORBING", "right": "ABSORBING"},
        validation_status=ModelValidationStatus.NUMERICALLY_VERIFIED.value,
    )
    assert model.name == "1-D Damped Wave Model"
    assert model.validation_status == ModelValidationStatus.NUMERICALLY_VERIFIED

    with UnitOfWork(db_mgr) as uow:
        graph = uow.semantic_graphs.load_graph(f"graph_{project_id}")
        assert graph.has_node(model.id)
        node = graph.get_node(model.id)
        assert node is not None
        assert node.node_type == ResearchNodeType.SCIENTIFIC_MODEL


@pytest.mark.asyncio
async def test_numerical_verification_integration(tmp_path: Path) -> None:
    db_mgr = _make_db(tmp_path)
    project_id, _ = await _setup_project(db_mgr, tmp_path)
    svc = ModelComparisonWorkflowService(
        artifacts_dir=tmp_path / "model_artifacts",
        db_manager=db_mgr,
    )
    params = _base_params()
    verification = svc.run_numerical_verification(
        project_id=project_id,
        params=params,
        verification_type=VerificationType.ZERO_INPUT,
    )
    assert verification.passed is True
    assert verification.verification_type == VerificationType.ZERO_INPUT


@pytest.mark.asyncio
async def test_convergence_study_integration(tmp_path: Path) -> None:
    db_mgr = _make_db(tmp_path)
    project_id, _ = await _setup_project(db_mgr, tmp_path)
    svc = ModelComparisonWorkflowService(
        artifacts_dir=tmp_path / "model_artifacts",
        db_manager=db_mgr,
    )
    params = _base_params()
    study = svc.run_convergence_study(
        project_id=project_id,
        base_params=params,
        refinement_factors=[1.0, 2.0],
        metric_name="max_displacement",
    )
    assert len(study.refinement_levels) == 2
    assert study.is_convergent is True


@pytest.mark.asyncio
async def test_sensitivity_study_integration(tmp_path: Path) -> None:
    db_mgr = _make_db(tmp_path)
    project_id, _ = await _setup_project(db_mgr, tmp_path)
    svc = ModelComparisonWorkflowService(
        artifacts_dir=tmp_path / "model_artifacts",
        db_manager=db_mgr,
    )
    params = _base_params()
    study = svc.run_sensitivity_study(
        project_id=project_id,
        base_params=params,
        parameter_names=["source_amplitude"],
        perturbations={"source_amplitude": [0.1, -0.1]},
        observable_names=["max_displacement"],
    )
    assert len(study.sample_ids) == 2
    assert study.is_deterministic is True


@pytest.mark.asyncio
async def test_model_comparison_integration(tmp_path: Path) -> None:
    db_mgr = _make_db(tmp_path)
    project_id, hyp_id = await _setup_project(db_mgr, tmp_path)
    svc = ModelComparisonWorkflowService(
        artifacts_dir=tmp_path / "model_artifacts",
        db_manager=db_mgr,
    )
    model_a = svc.register_scientific_model(
        project_id=project_id,
        name="Homogeneous Wave Model",
        validation_status=ModelValidationStatus.NUMERICALLY_VERIFIED.value,
    )
    model_b = svc.register_scientific_model(
        project_id=project_id,
        name="Heterogeneous Wave Model",
        validation_status=ModelValidationStatus.NUMERICALLY_VERIFIED.value,
    )

    result = svc.compare_models(
        project_id=project_id,
        params_a=_base_params("baseline"),
        params_b=_het_params("heterogeneous"),
        hypothesis_id=hyp_id,
        model_a_id=model_a.id,
        model_b_id=model_b.id,
        attenuation_threshold=0.9,
    )
    assert isinstance(result, ModelComparisonResult)
    assert result.validation_status == ModelValidationStatus.NUMERICALLY_VERIFIED
    assert result.physical_validation_status == ModelValidationStatus.UNVERIFIED
    assert "No automatic winner" in result.notes
