"""
Tests for Phase 2.3 domain models: ScientificModel, Assumption, ModelValidationStatus,
NumericalVerification, ConvergenceStudy, ReferenceSolution, ModelComparison,
ModelComparisonResult, SensitivityStudy, SensitivitySample.
"""

from __future__ import annotations

import pytest
from researchforge.domain.models.hypothesis import Assumption, AssumptionCategory
from researchforge.domain.models.model_validation import ModelValidationStatus
from researchforge.domain.models.numerical_verification import (
    ErrorCategory,
    ReferenceSolution,
    ReferenceSolutionType,
    VerificationType,
)
from researchforge.domain.models.verification_operators import (
    compare_wave_models,
    run_convergence_study,
    run_sensitivity_study,
    verify_wave_lattice,
)
from researchforge.domain.models.wave_lattice import (
    WaveLatticeParameters,
)

# ---------------------------------------------------------------------------
# Assumption
# ---------------------------------------------------------------------------


class TestAssumption:
    def test_backward_compatible_construction(self) -> None:
        a = Assumption(id="assump_1", statement="Linear medium")
        assert a.statement == "Linear medium"
        assert a.is_testable is True
        assert a.criticality == pytest.approx(0.8)
        assert a.category == AssumptionCategory.OTHER
        assert a.status == "ACTIVE"
        assert a.scope == ""
        assert a.source_ref == ""

    def test_phase_2_3_fields(self) -> None:
        a = Assumption(
            id="assump_2",
            statement="Homogeneous material",
            category=AssumptionCategory.MATERIAL,
            status="ACTIVE",
            scope="Core region",
            source_ref="prov_123",
        )
        assert a.category == AssumptionCategory.MATERIAL
        assert a.status == "ACTIVE"
        assert a.scope == "Core region"
        assert a.source_ref == "prov_123"


# ---------------------------------------------------------------------------
# ScientificModel
# ---------------------------------------------------------------------------


class TestScientificModel:
    def test_backward_compatible_construction(self) -> None:
        from researchforge.domain.models.evidence import ScientificModel

        m = ScientificModel(
            id="model_1",
            name="Wave model",
            equations=["u_tt = c^2 u_xx"],
            parameters={"c": 1.0},
            assumptions=["No damping"],
            domain_of_validity="1-D linear medium",
        )
        assert m.name == "Wave model"
        assert m.version == "1.0.0"
        assert m.equations == ["u_tt = c^2 u_xx"]
        assert m.assumptions == ["No damping"]
        assert m.domain_of_validity == "1-D linear medium"
        assert m.validation_status == ModelValidationStatus.UNVERIFIED

    def test_phase_2_3_fields(self) -> None:
        from researchforge.domain.models.evidence import ScientificModel

        m = ScientificModel(
            id="model_2",
            name="Wave model",
            mathematical_form="rho u_tt + gamma u_t = d/dx[E du/dx]",
            state_variables=["u(x,t)", "v(x,t)"],
            boundary_conditions={"left": "ABSORBING", "right": "ABSORBING"},
            initial_conditions={"u": "0", "v": "0"},
            source_terms={"amplitude": 1.0, "location": 5},
            validity_scope="1-D heterogeneous damped wave",
            validation_status=ModelValidationStatus.NUMERICALLY_VERIFIED,
        )
        assert m.mathematical_form == "rho u_tt + gamma u_t = d/dx[E du/dx]"
        assert m.state_variables == ["u(x,t)", "v(x,t)"]
        assert m.boundary_conditions["left"] == "ABSORBING"
        assert m.validation_status == ModelValidationStatus.NUMERICALLY_VERIFIED


# ---------------------------------------------------------------------------
# ModelValidationStatus
# ---------------------------------------------------------------------------


class TestModelValidationStatus:
    def test_numerically_verified_is_not_physically_validated(self) -> None:
        assert ModelValidationStatus.NUMERICALLY_VERIFIED != ModelValidationStatus.VALIDATED_FOR_SCOPE

    def test_all_statuses_are_strings(self) -> None:
        for status in ModelValidationStatus:
            assert isinstance(status.value, str)
            assert len(status.value) > 0


# ---------------------------------------------------------------------------
# NumericalVerification
# ---------------------------------------------------------------------------


class TestNumericalVerification:
    def test_zero_input_verification(self) -> None:
        params = WaveLatticeParameters(
            id="ver_test",
            nodes=40,
            time_steps=50,
            dx=1.0,
            dt=0.4,
            density=1.0,
            stiffness=1.0,
            damping=0.0,
            core_start=10,
            core_end=20,
            core_density=1.0,
            core_stiffness=1.0,
            core_damping=0.0,
            source_amplitude=0.0,
            source_location=5,
            source_duration=10,
        )
        verification = verify_wave_lattice(params, VerificationType.ZERO_INPUT)
        assert verification.verification_type == VerificationType.ZERO_INPUT
        assert verification.passed is True
        assert verification.metric_name == "max_displacement"
        assert verification.metric_value < 1e-12
        assert verification.error_category == ErrorCategory.IMPLEMENTATION_ERROR

    def test_determinism_verification(self) -> None:
        params = WaveLatticeParameters(
            id="det_test",
            nodes=40,
            time_steps=50,
            dx=1.0,
            dt=0.4,
            density=1.0,
            stiffness=1.0,
            damping=0.0,
            core_start=10,
            core_end=20,
            core_density=1.0,
            core_stiffness=1.0,
            core_damping=0.0,
            source_amplitude=1.0,
            source_location=5,
            source_duration=10,
        )
        verification = verify_wave_lattice(params, VerificationType.DETERMINISM)
        assert verification.passed is True
        assert verification.verification_type == VerificationType.DETERMINISM


# ---------------------------------------------------------------------------
# ConvergenceStudy
# ---------------------------------------------------------------------------


class TestConvergenceStudy:
    def test_convergence_study_runs(self) -> None:
        params = WaveLatticeParameters(
            id="conv_test",
            nodes=40,
            time_steps=60,
            dx=1.0,
            dt=0.4,
            density=1.0,
            stiffness=1.0,
            damping=0.0,
            core_start=10,
            core_end=20,
            core_density=1.0,
            core_stiffness=1.0,
            core_damping=0.0,
            source_amplitude=1.0,
            source_location=5,
            source_duration=10,
        )
        study = run_convergence_study(
            base_params=params,
            refinement_factors=[1.0, 2.0],
            metric_name="max_displacement",
        )
        assert len(study.refinement_levels) == 2
        assert len(study.metric_values) == 2
        assert study.refinement_params == ["dx", "dt"]
        assert study.convergence_order is not None
        assert study.is_convergent is True

    def test_single_level_no_convergence_order(self) -> None:
        params = WaveLatticeParameters(
            id="conv_single",
            nodes=40,
            time_steps=60,
            dx=1.0,
            dt=0.4,
            density=1.0,
            stiffness=1.0,
            damping=0.0,
            core_start=10,
            core_end=20,
            core_density=1.0,
            core_stiffness=1.0,
            core_damping=0.0,
            source_amplitude=1.0,
            source_location=5,
            source_duration=10,
        )
        study = run_convergence_study(
            base_params=params,
            refinement_factors=[1.0],
            metric_name="max_displacement",
        )
        assert study.convergence_order is None
        assert study.is_convergent is None


# ---------------------------------------------------------------------------
# ReferenceSolution
# ---------------------------------------------------------------------------


class TestReferenceSolution:
    def test_creation(self) -> None:
        ref = ReferenceSolution(
            id="ref_1",
            solution_id="ref_1",
            name="High-resolution reference",
            solution_type=ReferenceSolutionType.HIGH_RESOLUTION_NUMERICAL,
            data={"max_displacement": 0.5},
            description="Numerical reference at high resolution",
            validation_status=ModelValidationStatus.NUMERICALLY_VERIFIED,
        )
        assert ref.solution_type == ReferenceSolutionType.HIGH_RESOLUTION_NUMERICAL
        assert ref.validation_status == ModelValidationStatus.NUMERICALLY_VERIFIED
        assert ref.data["max_displacement"] == 0.5


# ---------------------------------------------------------------------------
# SensitivityStudy
# ---------------------------------------------------------------------------


class TestSensitivityStudy:
    def test_sensitivity_study_runs(self) -> None:
        params = WaveLatticeParameters(
            id="sens_test",
            nodes=40,
            time_steps=60,
            dx=1.0,
            dt=0.4,
            density=1.0,
            stiffness=1.0,
            damping=0.0,
            core_start=10,
            core_end=20,
            core_density=1.0,
            core_stiffness=1.0,
            core_damping=0.0,
            source_amplitude=1.0,
            source_location=5,
            source_duration=10,
        )
        study = run_sensitivity_study(
            base_params=params,
            parameter_names=["source_amplitude"],
            perturbations={"source_amplitude": [0.1, -0.1]},
            observable_names=["max_displacement"],
        )
        assert len(study.sample_ids) == 2
        assert any("source_amplitude" in k for k in study.sensitivity_metrics.keys())
        assert study.is_deterministic is True


# ---------------------------------------------------------------------------
# ModelComparison
# ---------------------------------------------------------------------------


class TestModelComparison:
    def test_model_comparison_produces_evidence(self) -> None:
        params_a = WaveLatticeParameters(
            id="comp_a",
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
        )
        params_b = WaveLatticeParameters(
            id="comp_b",
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
        )
        result = compare_wave_models(params_a, params_b)
        assert result.comparison_id == f"comp_{params_a.id}_{params_b.id}"
        assert "max_displacement" in result.observable_differences
        assert "L2_error" in result.error_metrics
        assert result.validation_status == ModelValidationStatus.NUMERICALLY_VERIFIED
        assert result.physical_validation_status == ModelValidationStatus.UNVERIFIED
        assert "No automatic winner" in result.notes

    def test_model_comparison_is_deterministic(self) -> None:
        params_a = WaveLatticeParameters(
            id="det_a",
            nodes=40,
            time_steps=50,
            dx=1.0,
            dt=0.4,
            density=1.0,
            stiffness=1.0,
            damping=0.0,
            core_start=10,
            core_end=20,
            core_density=1.0,
            core_stiffness=1.0,
            core_damping=0.0,
            source_amplitude=1.0,
            source_location=5,
            source_duration=10,
        )
        params_b = WaveLatticeParameters(
            id="det_b",
            nodes=40,
            time_steps=50,
            dx=1.0,
            dt=0.4,
            density=1.0,
            stiffness=1.0,
            damping=0.0,
            core_start=10,
            core_end=20,
            core_density=1.0,
            core_stiffness=1.0,
            core_damping=2.0,
            source_amplitude=1.0,
            source_location=5,
            source_duration=10,
        )
        result1 = compare_wave_models(params_a, params_b)
        result2 = compare_wave_models(params_a, params_b)
        assert result1.observable_differences == result2.observable_differences
        assert result1.error_metrics == result2.error_metrics
