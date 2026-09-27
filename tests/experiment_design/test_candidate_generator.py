"""
Tests for deterministic candidate design generator, parameter space sampling,
constraint enforcement, and sensitivity study integration (Phase 2.4).
"""

from researchforge.domain.models.design_exploration_operators import (
    check_parameter_constraints,
    generate_candidate_designs,
)
from researchforge.domain.models.experimental_design_candidate import (
    DesignCandidateStatus,
    DesignObjective,
    ExperimentalDesignCandidate,
)
from researchforge.domain.models.model_comparison import SensitivityStudy
from researchforge.domain.models.parameter_space import (
    ParameterConstraint,
    ParameterDefinition,
    ParameterSpace,
    ParameterType,
    SamplingStrategy,
)


def _create_sample_parameter_space() -> ParameterSpace:
    """Create a sample 2-parameter space for wave lattice tests."""
    return ParameterSpace(
        id="ps_test_1",
        name="Wave Core Parameter Space",
        parameters={
            "core_damping": ParameterDefinition(
                parameter_name="core_damping",
                parameter_type=ParameterType.CONTINUOUS,
                min_value=0.0,
                max_value=20.0,
                default_value=5.0,
            ),
            "core_stiffness": ParameterDefinition(
                parameter_name="core_stiffness",
                parameter_type=ParameterType.CONTINUOUS,
                min_value=0.5,
                max_value=2.0,
                default_value=1.0,
            ),
        },
        constraints=[
            ParameterConstraint(
                name="cfl_bound",
                expression="dt <= dx / ((core_stiffness/1.0)**0.5)",
                parameters_involved=["core_stiffness", "dt", "dx"],
            )
        ],
    )


def test_grid_candidate_generation_is_deterministic() -> None:
    """Test that GRID sampling generates a canonical, deterministic set of valid candidates."""
    ps = _create_sample_parameter_space()
    cands1 = generate_candidate_designs(
        project_id="proj_1",
        parameter_space=ps,
        model_ids=["model_a", "model_b"],
        sample_count=5,
        sampling_strategy=SamplingStrategy.GRID,
    )
    cands2 = generate_candidate_designs(
        project_id="proj_1",
        parameter_space=ps,
        model_ids=["model_a", "model_b"],
        sample_count=5,
        sampling_strategy=SamplingStrategy.GRID,
    )

    assert len(cands1) == 5
    assert len(cands2) == 5
    assert [c.candidate_design_id for c in cands1] == [c.candidate_design_id for c in cands2]
    for c1, c2 in zip(cands1, cands2, strict=True):
        assert c1.parameter_assignments == c2.parameter_assignments
        assert c1.design_status == DesignCandidateStatus.CANDIDATE
        assert c1.design_objective == DesignObjective.MODEL_DISCRIMINATION


def test_stochastic_sampling_seed_reproducibility() -> None:
    """Test that RANDOM_UNIFORM and LATIN_HYPERCUBE are strictly seed-reproducible."""
    ps = _create_sample_parameter_space()
    cands_a = generate_candidate_designs(
        project_id="proj_stochastic",
        parameter_space=ps,
        model_ids=["model_a", "model_b"],
        sample_count=4,
        sampling_strategy=SamplingStrategy.LATIN_HYPERCUBE,
        random_seed=12345,
    )
    cands_b = generate_candidate_designs(
        project_id="proj_stochastic",
        parameter_space=ps,
        model_ids=["model_a", "model_b"],
        sample_count=4,
        sampling_strategy=SamplingStrategy.LATIN_HYPERCUBE,
        random_seed=12345,
    )
    cands_c = generate_candidate_designs(
        project_id="proj_stochastic",
        parameter_space=ps,
        model_ids=["model_a", "model_b"],
        sample_count=4,
        sampling_strategy=SamplingStrategy.LATIN_HYPERCUBE,
        random_seed=99999,
    )

    assert len(cands_a) == 4
    assert [c.parameter_assignments for c in cands_a] == [c.parameter_assignments for c in cands_b]
    assert [c.parameter_assignments for c in cands_a] != [c.parameter_assignments for c in cands_c]


def test_constraint_checking_and_candidate_rejection() -> None:
    """Test that candidates violating CFL stability or parameter bounds are rejected."""
    ps = _create_sample_parameter_space()

    # Valid assignment
    valid, violations = check_parameter_constraints(
        {"core_damping": 5.0, "core_stiffness": 1.0, "dt": 0.4, "dx": 1.0},
        ps.constraints,
        ps.parameters,
    )
    assert valid
    assert len(violations) == 0

    # Out of bounds
    invalid_bounds, v_bounds = check_parameter_constraints(
        {"core_damping": 50.0, "core_stiffness": 1.0, "dt": 0.4, "dx": 1.0},
        ps.constraints,
        ps.parameters,
    )
    assert not invalid_bounds
    assert any("max_value" in v for v in v_bounds)

    # CFL violation: dt=1.5 > dx/c (1.0/1.0)
    invalid_cfl, v_cfl = check_parameter_constraints(
        {"core_damping": 5.0, "core_stiffness": 1.0, "dt": 1.5, "dx": 1.0},
        ps.constraints,
        ps.parameters,
    )
    assert not invalid_cfl
    assert any("CFL" in v for v in v_cfl)


def test_sensitivity_study_prioritization() -> None:
    """Test that existing SensitivityStudy metrics prioritize exploration along high-sensitivity parameters."""
    ps = ParameterSpace(
        id="ps_sens_test",
        name="Multi-param Space",
        parameters={
            "core_damping": ParameterDefinition(
                parameter_name="core_damping",
                min_value=0.0,
                max_value=10.0,
            ),
            "density": ParameterDefinition(
                parameter_name="density",
                min_value=0.8,
                max_value=1.2,
            ),
        },
    )

    # Sensitivity study showing core_damping has high sensitivity (0.9) while density has low (0.01)
    study = SensitivityStudy(
        study_id="sens_study_01",
        name="Damping vs Density Sensitivity",
        model_id="model_a",
        base_params={},
        parameter_names=["core_damping", "density"],
        observable_names=["transmitted_energy"],
        sensitivity_metrics={"core_damping": 0.95, "density": 0.05},
    )

    cands = generate_candidate_designs(
        project_id="proj_sens",
        parameter_space=ps,
        model_ids=["model_a", "model_b"],
        sample_count=4,
        sampling_strategy=SamplingStrategy.GRID,
        sensitivity_study=study,
    )

    assert len(cands) == 4
    # The primary varied parameter should be core_damping because of higher sensitivity
    damping_values = [c.parameter_assignments["core_damping"] for c in cands]
    assert len(set(damping_values)) == 4
    for c in cands:
        assert c.sensitivity_study_ref == "sens_study_01"


def test_candidate_preserves_explicit_variables() -> None:
    """Test that candidates cleanly separate independent, dependent, and controlled variables."""
    ps = _create_sample_parameter_space()
    cands = generate_candidate_designs(
        project_id="proj_vars",
        parameter_space=ps,
        model_ids=["model_a", "model_b"],
        sample_count=3,
        controlled_variables={"dx": 1.0, "dt": 0.3, "nodes": 200, "boundary_condition": "ABSORBING"},
        target_observables=["transmitted_energy", "attenuation_ratio"],
    )

    c = cands[0]
    assert isinstance(c, ExperimentalDesignCandidate)
    assert set(c.independent_variables) == {"core_damping", "core_stiffness"}
    assert c.controlled_variables["boundary_condition"] == "ABSORBING"
    assert c.dependent_variables == ["transmitted_energy", "attenuation_ratio"]
    assert c.resource_requirements.max_spatial_nodes == 200
