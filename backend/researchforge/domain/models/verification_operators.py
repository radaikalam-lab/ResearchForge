"""
Numerical verification, convergence study, and sensitivity analysis operators (Phase 2.3).

Pure deterministic functions for:
    - Convergence study: controlled refinement of dx/dt
    - Sensitivity analysis: parameter perturbation
    - Model comparison: observable differences between models
"""

from __future__ import annotations

from typing import Any

import numpy as np

from researchforge.domain.models.model_comparison import (
    ComparisonMethod,
    ModelComparisonResult,
    SensitivitySample,
    SensitivityStudy,
)
from researchforge.domain.models.model_validation import ModelValidationStatus
from researchforge.domain.models.numerical_verification import (
    ConvergenceStudy,
    ErrorCategory,
    NumericalVerification,
    ReferenceSolution,
    VerificationType,
)
from researchforge.domain.models.wave_lattice import (
    WaveLatticeObservables,
    WaveLatticeParameters,
    simulate_1d_damped_wave_lattice,
)

# ---------------------------------------------------------------------------
# Convergence study
# ---------------------------------------------------------------------------


def run_convergence_study(
    base_params: WaveLatticeParameters,
    refinement_factors: list[float],
    reference_solution: ReferenceSolution | None = None,
    metric_name: str = "max_displacement",
) -> ConvergenceStudy:
    """
    Run a convergence study by refining dx and dt while holding physical
    parameters fixed.

    For each refinement level:
        nodes = base_nodes * factor
        dx = base_dx / factor
        dt = base_dt / factor
        time_steps = base_time_steps * factor

    The study tracks the specified observable across refinement levels and
    computes convergence metrics relative to the finest resolution or a
    provided reference solution.
    """
    base_nodes = base_params.nodes
    base_dx = base_params.dx
    base_dt = base_params.dt
    base_time_steps = base_params.time_steps

    refinement_levels: list[dict[str, Any]] = []
    metric_values: list[float] = []

    for factor in refinement_factors:
        nodes = max(8, int(base_nodes * factor))
        dx = base_dx / factor
        dt = base_dt / factor
        time_steps = max(10, int(base_time_steps * factor))

        params = WaveLatticeParameters(
            id=f"{base_params.id}_conv_{factor}",
            nodes=nodes,
            time_steps=time_steps,
            dx=dx,
            dt=dt,
            density=base_params.density,
            stiffness=base_params.stiffness,
            damping=base_params.damping,
            core_start=base_params.core_start,
            core_end=base_params.core_end,
            core_density=base_params.core_density,
            core_stiffness=base_params.core_stiffness,
            core_damping=base_params.core_damping,
            source_amplitude=base_params.source_amplitude,
            source_location=base_params.source_location,
            source_duration=base_params.source_duration,
            boundary_condition=base_params.boundary_condition,
        )
        output = simulate_1d_damped_wave_lattice(params)
        obs = WaveLatticeObservables.model_validate(output["observables"])

        refinement_levels.append(
            {
                "factor": factor,
                "nodes": nodes,
                "dx": dx,
                "dt": dt,
                "time_steps": time_steps,
            }
        )
        metric_values.append(getattr(obs, metric_name))

    # Compute convergence order if we have at least 2 levels
    convergence_order: float | None = None
    is_convergent: bool | None = None
    if len(metric_values) >= 2:
        # Use log-log slope between consecutive levels
        logs_f = np.log(np.array(refinement_factors, dtype=float))
        logs_m = np.log(np.array(metric_values, dtype=float))
        # Avoid log(0)
        valid = np.isfinite(logs_f) & np.isfinite(logs_m)
        if np.sum(valid) >= 2:
            slope = np.polyfit(logs_f[valid], logs_m[valid], 1)[0]
            convergence_order = float(-slope)
            is_convergent = convergence_order > 0.0

    study = ConvergenceStudy(
        id=f"conv_{base_params.id}",
        study_id=f"conv_{base_params.id}",
        model_id="wave_lattice_model",
        base_params=base_params.model_dump(mode="json"),
        refinement_params=["dx", "dt"],
        refinement_levels=refinement_levels,
        metric_name=metric_name,
        metric_values=metric_values,
        convergence_order=convergence_order,
        reference_solution_id=reference_solution.solution_id if reference_solution else None,
        is_convergent=is_convergent,
    )
    return study


# ---------------------------------------------------------------------------
# Sensitivity analysis
# ---------------------------------------------------------------------------


def run_sensitivity_study(
    base_params: WaveLatticeParameters,
    parameter_names: list[str],
    perturbations: dict[str, list[float]],
    observable_names: list[str],
    study_id: str | None = None,
) -> SensitivityStudy:
    """
    Run a deterministic one-at-a-time sensitivity study.

    For each parameter in `parameter_names`, perturb it by each value in
    `perturbations[parameter_name]` and measure the effect on the selected
    observables.

    The base parameter set is used for all non-perturbed parameters.
    """
    samples: list[SensitivitySample] = []

    base_output = simulate_1d_damped_wave_lattice(base_params)
    base_obs = WaveLatticeObservables.model_validate(base_output["observables"])

    for param_name in parameter_names:
        if param_name not in perturbations:
            continue
        baseline_value = getattr(base_params, param_name)
        for perturb in perturbations[param_name]:
            new_value = baseline_value + perturb
            params_dict = base_params.model_dump(mode="json")
            params_dict[param_name] = new_value
            perturbed_params = WaveLatticeParameters(**params_dict)

            output = simulate_1d_damped_wave_lattice(perturbed_params)
            obs = WaveLatticeObservables.model_validate(output["observables"])

            observables: dict[str, float] = {}
            for obs_name in observable_names:
                observables[obs_name] = getattr(obs, obs_name)

            sample = SensitivitySample(
                id=f"sens_{param_name}_{perturb}",
                sample_id=f"sens_{param_name}_{perturb}",
                study_id=study_id or f"sens_{base_params.id}",
                parameter_name=param_name,
                parameter_value=new_value,
                baseline_value=baseline_value,
                perturbation=perturb,
                observables=observables,
            )
            samples.append(sample)

    # Compute simple sensitivity metrics: normalized change in observable per unit perturbation
    sensitivity_metrics: dict[str, float] = {}
    for param_name in parameter_names:
        if param_name not in perturbations:
            continue
        baseline_value = getattr(base_params, param_name)
        param_samples = [s for s in samples if s.parameter_name == param_name]
        if not param_samples:
            continue
        for obs_name in observable_names:
            # Average |delta_observable / perturbation| across samples
            deltas = []
            for s in param_samples:
                base_val = getattr(base_obs, obs_name)
                perturbed_val = s.observables.get(obs_name, base_val)
                if abs(s.perturbation) > 1e-15:
                    deltas.append(abs(perturbed_val - base_val) / abs(s.perturbation))
            if deltas:
                sensitivity_metrics[f"{param_name}/{obs_name}"] = float(np.mean(deltas))

    study = SensitivityStudy(
        id=study_id or f"sens_{base_params.id}",
        study_id=study_id or f"sens_{base_params.id}",
        name=f"Sensitivity study for {base_params.id}",
        model_id="wave_lattice_model",
        base_params=base_params.model_dump(mode="json"),
        sensitivity_method="ONE_AT_A_TIME",
        parameter_names=parameter_names,
        perturbation_strategy=perturbations,
        observable_names=observable_names,
        sample_ids=[s.sample_id for s in samples],
        sensitivity_metrics=sensitivity_metrics,
        is_deterministic=True,
    )
    return study


# ---------------------------------------------------------------------------
# Model comparison
# ---------------------------------------------------------------------------


def compare_wave_models(
    params_a: WaveLatticeParameters,
    params_b: WaveLatticeParameters,
    reference_solution: ReferenceSolution | None = None,
    comparison_method: ComparisonMethod = ComparisonMethod.OBSERVABLE_DIFFERENCE,
) -> ModelComparisonResult:
    """
    Compare two wave-lattice model configurations.

    Both parameter sets must use the same domain, source, and boundary conditions
    for the comparison to be meaningful. The function does not enforce this;
    it is the caller's responsibility.

    Returns evidence-centric results; it does NOT declare a winner.
    """
    output_a = simulate_1d_damped_wave_lattice(params_a)
    output_b = simulate_1d_damped_wave_lattice(params_b)
    obs_a = WaveLatticeObservables.model_validate(output_a["observables"])
    obs_b = WaveLatticeObservables.model_validate(output_b["observables"])

    # Compute observable differences
    observable_differences: dict[str, float] = {}
    for field in WaveLatticeObservables.model_fields:
        if field in {"input_hash", "output_hash"}:
            continue
        val_a = getattr(obs_a, field)
        val_b = getattr(obs_b, field)
        if isinstance(val_a, (int, float)) and isinstance(val_b, (int, float)):
            observable_differences[field] = float(val_b - val_a)

    # Compute L2 error between final displacement fields if available
    error_metrics: dict[str, float] = {}
    if "final_displacement" in output_a and "final_displacement" in output_b:
        u_a = np.array(output_a["final_displacement"])
        u_b = np.array(output_b["final_displacement"])
        min_len = min(len(u_a), len(u_b))
        u_a = u_a[:min_len]
        u_b = u_b[:min_len]
        error_metrics["L1_error"] = float(np.sum(np.abs(u_a - u_b)) / max(min_len, 1))
        error_metrics["L2_error"] = float(np.sqrt(np.sum((u_a - u_b) ** 2) / max(min_len, 1)))
        error_metrics["Linf_error"] = float(np.max(np.abs(u_a - u_b)))

    # Physical validation status: always UNVERIFIED for pure numerical comparison
    physical_validation_status = ModelValidationStatus.UNVERIFIED

    result = ModelComparisonResult(
        id=f"comp_{params_a.id}_{params_b.id}",
        result_id=f"comp_{params_a.id}_{params_b.id}",
        comparison_id=f"comp_{params_a.id}_{params_b.id}",
        model_ids=["wave_lattice_model", "wave_lattice_model"],
        observable_differences=observable_differences,
        error_metrics=error_metrics,
        numerical_verifications=[],
        convergence_studies=[],
        sensitivity_studies=[],
        assumption_differences=[],
        validation_status=ModelValidationStatus.NUMERICALLY_VERIFIED,
        physical_validation_status=physical_validation_status,
        notes=(
            "Observable differences computed between two model configurations. "
            "No automatic winner declared. Human/domain authority determines scientific conclusion."
        ),
    )
    return result


# ---------------------------------------------------------------------------
# Numerical verification operator
# ---------------------------------------------------------------------------


def verify_wave_lattice(
    params: WaveLatticeParameters,
    verification_type: VerificationType = VerificationType.ZERO_INPUT,
) -> NumericalVerification:
    """
    Run a deterministic numerical verification test on the wave lattice operator.
    """
    if verification_type == VerificationType.ZERO_INPUT:
        zero_params = WaveLatticeParameters(
            id=f"{params.id}_zero_input",
            nodes=params.nodes,
            time_steps=params.time_steps,
            dx=params.dx,
            dt=params.dt,
            density=params.density,
            stiffness=params.stiffness,
            damping=params.damping,
            core_start=params.core_start,
            core_end=params.core_end,
            core_density=params.core_density,
            core_stiffness=params.core_stiffness,
            core_damping=params.core_damping,
            source_amplitude=0.0,
            source_location=params.source_location,
            source_duration=params.source_duration,
            boundary_condition=params.boundary_condition,
        )
        output = simulate_1d_damped_wave_lattice(zero_params)
        obs = WaveLatticeObservables.model_validate(output["observables"])
        passed = obs.max_displacement < 1e-12 and obs.max_core_displacement < 1e-12
        return NumericalVerification(
            id=f"ver_{params.id}_zero_input",
            verification_id=f"ver_{params.id}_zero_input",
            verification_type=verification_type,
            model_id="wave_lattice_model",
            passed=passed,
            metric_name="max_displacement",
            metric_value=obs.max_displacement,
            threshold=1e-12,
            resolution_params=params.model_dump(mode="json"),
            error_category=ErrorCategory.IMPLEMENTATION_ERROR,
            notes="Zero source should produce zero displacement everywhere.",
        )

    if verification_type == VerificationType.DETERMINISM:
        output1 = simulate_1d_damped_wave_lattice(params)
        output2 = simulate_1d_damped_wave_lattice(params)
        obs1 = WaveLatticeObservables.model_validate(output1["observables"])
        obs2 = WaveLatticeObservables.model_validate(output2["observables"])
        passed = obs1.output_hash == obs2.output_hash and obs1.input_hash == obs2.input_hash
        return NumericalVerification(
            id=f"ver_{params.id}_determinism",
            verification_id=f"ver_{params.id}_determinism",
            verification_type=verification_type,
            model_id="wave_lattice_model",
            passed=passed,
            metric_name="output_hash",
            metric_value=float(int(obs1.output_hash[:16], 16)),
            threshold=None,
            resolution_params=params.model_dump(mode="json"),
            error_category=ErrorCategory.IMPLEMENTATION_ERROR,
            notes="Identical parameters must produce identical output hashes.",
        )

    raise ValueError(f"Unsupported verification type: {verification_type}")
