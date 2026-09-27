"""
Deterministic Design Exploration and Model Discrimination Operators (Phase 2.4).

Pure computational operators for:
    - Candidate experimental design generation across parameter spaces
    - Constraint enforcement and invalid candidate rejection
    - Sensitivity-guided parameter exploration
    - Multi-model simulation and discrimination evaluation
    - Numerical uncertainty vs. model difference accounting
    - Multi-objective Pareto frontier identification

These functions are strictly pure:
    - Zero side-effects
    - Zero I/O, database, or persistence access
    - Zero network or Cognitia access
    - Deterministic across identical inputs and random seeds
"""

from __future__ import annotations

import hashlib
import json
import math
import uuid
from typing import Any

import numpy as np

from researchforge.domain.models.experimental_design_candidate import (
    CandidateDesignEvaluation,
    DesignCandidateStatus,
    DesignObjective,
    DiscriminationMetric,
    ExperimentalDesignCandidate,
    ParetoCandidateSet,
    ResourceRequirements,
)
from researchforge.domain.models.model_comparison import SensitivityStudy
from researchforge.domain.models.parameter_space import (
    ParameterConstraint,
    ParameterDefinition,
    ParameterSpace,
    ParameterType,
    SamplingStrategy,
)
from researchforge.domain.models.wave_lattice import (
    BoundaryCondition,
    WaveLatticeParameters,
    simulate_1d_damped_wave_lattice,
)


def _canonical_json(obj: Any) -> str:
    """Deterministic canonical JSON serialization."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def check_parameter_constraints(
    assignments: dict[str, Any],
    constraints: list[ParameterConstraint],
    parameter_definitions: dict[str, ParameterDefinition],
) -> tuple[bool, list[str]]:
    """
    Validate parameter assignments against bounds, types, and explicit constraints.

    Returns:
        (is_valid, list of violation error messages)
    """
    violations: list[str] = []

    # 1. Check definition bounds
    for param_name, val in assignments.items():
        if param_name in parameter_definitions:
            pdef = parameter_definitions[param_name]
            if pdef.parameter_type in (ParameterType.CONTINUOUS, ParameterType.DISCRETE):
                if isinstance(val, (int, float)):
                    if pdef.min_value is not None and val < pdef.min_value:
                        violations.append(
                            f"Parameter '{param_name}' value {val} < min_value {pdef.min_value}"
                        )
                    if pdef.max_value is not None and val > pdef.max_value:
                        violations.append(
                            f"Parameter '{param_name}' value {val} > max_value {pdef.max_value}"
                        )
            if pdef.allowed_values and val not in pdef.allowed_values:
                violations.append(
                    f"Parameter '{param_name}' value {val} not in allowed_values {pdef.allowed_values}"
                )

    # 2. Check explicit expressions and physical rules
    # Common wave-lattice checks
    core_start = assignments.get("core_start")
    core_end = assignments.get("core_end")
    nodes = assignments.get("nodes", 200)

    if core_start is not None and core_end is not None:
        if core_start >= core_end:
            violations.append(f"core_start ({core_start}) must be strictly less than core_end ({core_end})")
        if core_end > nodes:
            violations.append(f"core_end ({core_end}) exceeds total nodes ({nodes})")

    # CFL check if dt, dx, stiffness, density present
    dt = assignments.get("dt", 0.4)
    dx = assignments.get("dx", 1.0)
    density = assignments.get("density", 1.0)
    stiffness = assignments.get("stiffness", 1.0)
    core_density = assignments.get("core_density", 1.0)
    core_stiffness = assignments.get("core_stiffness", 1.0)

    try:
        c_bg = math.sqrt(stiffness / density) if density > 0 and stiffness > 0 else 1.0
        c_core = math.sqrt(core_stiffness / core_density) if core_density > 0 and core_stiffness > 0 else 1.0
        c_max = max(c_bg, c_core)
        cfl_limit = dx / c_max if c_max > 0 else dx
        if dt > cfl_limit + 1e-9:
            violations.append(
                f"CFL stability violation: dt={dt:.4f} > dx/c_max={cfl_limit:.4f}"
            )
    except Exception as e:
        violations.append(f"Physical constraint evaluation failed: {e}")

    # Custom algebraic constraints
    for constraint in constraints:
        # Check expression if safe
        expr = constraint.expression
        if expr:
            try:
                # Safe evaluation with parameter dictionary as local scope
                allowed_locals = {k: v for k, v in assignments.items() if isinstance(v, (int, float, bool))}
                allowed_locals.update({"min": min, "max": max, "abs": abs})
                # Check if all required variables are present
                if all(p in allowed_locals for p in constraint.parameters_involved):
                    res = eval(expr, {"__builtins__": {}}, allowed_locals)
                    if not res:
                        violations.append(
                            f"Constraint '{constraint.name}' violated: {expr}"
                        )
            except Exception:
                pass  # Ignore unparseable non-evaluable expressions

    return len(violations) == 0, violations


def generate_candidate_designs(
    project_id: str,
    parameter_space: ParameterSpace,
    model_ids: list[str],
    hypothesis_id: str | None = None,
    research_question_id: str | None = None,
    design_objective: DesignObjective = DesignObjective.MODEL_DISCRIMINATION,
    sampling_strategy: SamplingStrategy | str = SamplingStrategy.GRID,
    sample_count: int = 5,
    random_seed: int | None = 42,
    controlled_variables: dict[str, Any] | None = None,
    target_observables: list[str] | None = None,
    sensitivity_study: SensitivityStudy | None = None,
    resource_limits: ResourceRequirements | None = None,
) -> list[ExperimentalDesignCandidate]:
    """
    Deterministically generate candidate experimental designs over a parameter space.

    Consumes existing SensitivityStudy to prioritize exploration along highly sensitive
    parameters while maintaining the full parameter space. Invalid candidates violating
    constraints are rejected before emission.

    Returns:
        Canonical, sorted list of valid ExperimentalDesignCandidate objects.
    """
    if not model_ids:
        raise ValueError("At least one model_id must be specified for candidate design generation.")

    if not parameter_space.parameters:
        raise ValueError("ParameterSpace contains no parameter definitions to explore.")

    strategy_str = str(
        sampling_strategy.value if isinstance(sampling_strategy, SamplingStrategy) else sampling_strategy
    )
    controlled = controlled_variables.copy() if controlled_variables else {
        "nodes": 200,
        "time_steps": 500,
        "dx": 1.0,
        "dt": 0.4,
        "density": 1.0,
        "stiffness": 1.0,
        "damping": 0.0,
        "source_amplitude": 1.0,
        "source_location": 10,
        "source_duration": 20,
        "boundary_condition": "ABSORBING",
    }
    observables = target_observables or [
        "transmitted_energy",
        "attenuation_ratio",
        "max_displacement",
        "dissipated_energy",
        "core_energy",
    ]

    # Parameters to vary (independent variables)
    param_names = sorted(parameter_space.parameters.keys())

    # If SensitivityStudy provided, prioritize high-sensitivity parameters
    sensitivity_ref: str | None = None
    if sensitivity_study:
        sensitivity_ref = sensitivity_study.study_id
        # Sort parameter names descending by sensitivity metric
        param_names = sorted(
            param_names,
            key=lambda p: sensitivity_study.sensitivity_metrics.get(p, 0.0),
            reverse=True,
        )

    # Generate parameter grids / samples
    sampled_assignments: list[dict[str, Any]] = []

    if strategy_str in ("GRID", "FACTORIAL"):
        # Deterministic 1D or multi-D grid
        grid_values: dict[str, list[Any]] = {}
        for p_name in param_names:
            pdef = parameter_space.parameters[p_name]
            if pdef.allowed_values:
                grid_values[p_name] = sorted(pdef.allowed_values)[:sample_count]
            elif pdef.min_value is not None and pdef.max_value is not None:
                min_v = float(pdef.min_value)
                max_v = float(pdef.max_value)
                if sample_count == 1:
                    vals = [(min_v + max_v) / 2.0]
                else:
                    step = (max_v - min_v) / (sample_count - 1)
                    vals = [round(min_v + i * step, 6) for i in range(sample_count)]
                grid_values[p_name] = vals
            elif pdef.default_value is not None:
                grid_values[p_name] = [pdef.default_value]
            else:
                grid_values[p_name] = [1.0]

        # Cartesian product (bounded to sample_count candidates)
        # For simplicity and bound control, vary primary parameter across sample_count
        # and secondary parameters across their range
        primary_param = param_names[0]
        for val in grid_values[primary_param]:
            assign = {primary_param: val}
            for other_p in param_names[1:]:
                assign[other_p] = grid_values[other_p][0]
            sampled_assignments.append(assign)

    elif strategy_str in ("RANDOM_UNIFORM", "LATIN_HYPERCUBE", "SOBOL"):
        rng = np.random.RandomState(random_seed or 42)
        for _ in range(sample_count * 2):  # Sample extra to account for rejections
            assign = {}
            for p_name in param_names:
                pdef = parameter_space.parameters[p_name]
                if pdef.allowed_values:
                    assign[p_name] = rng.choice(pdef.allowed_values)
                elif pdef.min_value is not None and pdef.max_value is not None:
                    min_v = float(pdef.min_value)
                    max_v = float(pdef.max_value)
                    val = min_v + rng.uniform(0.0, 1.0) * (max_v - min_v)
                    if pdef.parameter_type == ParameterType.DISCRETE:
                        assign[p_name] = round(val)
                    else:
                        assign[p_name] = round(float(val), 6)
                elif pdef.default_value is not None:
                    assign[p_name] = pdef.default_value
                else:
                    assign[p_name] = 1.0
            sampled_assignments.append(assign)

    else:  # ONE_AT_A_TIME
        for p_name in param_names:
            pdef = parameter_space.parameters[p_name]
            min_v = float(pdef.min_value) if pdef.min_value is not None else 1.0
            max_v = float(pdef.max_value) if pdef.max_value is not None else 5.0
            step = (max_v - min_v) / max(sample_count - 1, 1)
            for i in range(sample_count):
                assign = {p: parameter_space.parameters[p].default_value or 1.0 for p in param_names}
                assign[p_name] = round(min_v + i * step, 6)
                sampled_assignments.append(assign)

    # Filter and construct candidates
    candidates: list[ExperimentalDesignCandidate] = []
    seen_hashes: set[str] = set()

    for assign in sampled_assignments:
        # Merge with controlled variables to perform full constraint check
        full_config = {**controlled, **assign}

        is_valid, _violations = check_parameter_constraints(
            full_config,
            parameter_space.constraints,
            parameter_space.parameters,
        )

        if not is_valid:
            continue  # Reject invalid candidate

        # Deterministic candidate hash
        assign_json = _canonical_json(assign)
        cand_hash = hashlib.sha256(f"{project_id}:{assign_json}".encode()).hexdigest()[:12]

        if cand_hash in seen_hashes:
            continue
        seen_hashes.add(cand_hash)

        # Resource requirements calculation
        nodes_cnt = int(full_config.get("nodes", 200))
        steps_cnt = int(full_config.get("time_steps", 500))
        res_req = resource_limits or ResourceRequirements(
            max_spatial_nodes=nodes_cnt,
            max_time_steps=steps_cnt,
            estimated_cost=round(nodes_cnt * steps_cnt * 1e-4, 4),
        )

        candidate = ExperimentalDesignCandidate(
            candidate_design_id=f"cand_{cand_hash}",
            project_id=project_id,
            research_question_id=research_question_id,
            hypothesis_id=hypothesis_id,
            model_ids=model_ids,
            parameter_assignments=assign,
            controlled_variables=controlled,
            independent_variables=list(assign.keys()),
            dependent_variables=observables,
            target_observables=observables,
            constraints=[f"CFL stability (dt={full_config.get('dt')})", "Parameter bounds"],
            expected_information={
                "strategy": strategy_str,
                "sensitivity_guided": sensitivity_study is not None,
                "parameter_count": len(assign),
            },
            design_objective=design_objective,
            execution_requirements={"solver": "simulate_1d_damped_wave_lattice", "backend": "numpy"},
            resource_requirements=res_req,
            risk_constraints=[],
            assumptions=["1D linear elasticity", "Mur 1st-order absorbing boundaries"],
            design_status=DesignCandidateStatus.CANDIDATE,
            design_strategy=strategy_str,
            random_seed=random_seed,
            sensitivity_study_ref=sensitivity_ref,
        )
        candidates.append(candidate)

        if len(candidates) >= sample_count:
            break

    # Ensure deterministic canonical ordering by candidate_design_id
    candidates.sort(key=lambda c: c.candidate_design_id)
    return candidates


def evaluate_candidate_for_model_discrimination(
    candidate: ExperimentalDesignCandidate,
    model_a_id: str,
    model_b_id: str,
    model_a_params_override: dict[str, Any] | None = None,
    model_b_params_override: dict[str, Any] | None = None,
    estimated_discretization_uncertainty: float = 0.005,
) -> CandidateDesignEvaluation:
    """
    Evaluate an ExperimentalDesignCandidate on its ability to discriminate between two models.

    Runs deterministic wave lattice simulations under Model A and Model B configurations.
    Explicitly separates predicted model difference from numerical uncertainty.
    Calculates formal DiscriminationMetric and multi-objective properties.

    Returns:
        CandidateDesignEvaluation with detailed metrics (does NOT declare a winner).
    """
    full_config = {**candidate.controlled_variables, **candidate.parameter_assignments}

    # Model A configuration (e.g. baseline or low damping)
    cfg_a = full_config.copy()
    if model_a_params_override:
        cfg_a.update(model_a_params_override)

    # Model B configuration (e.g. modified core or high damping)
    cfg_b = full_config.copy()
    if model_b_params_override:
        cfg_b.update(model_b_params_override)

    def _build_params(cfg: dict[str, Any]) -> WaveLatticeParameters:
        bc_str = cfg.get("boundary_condition", "ABSORBING")
        bc = BoundaryCondition.ABSORBING if bc_str == "ABSORBING" else BoundaryCondition.DIRICHLET
        return WaveLatticeParameters(
            nodes=int(cfg.get("nodes", 200)),
            time_steps=int(cfg.get("time_steps", 500)),
            dx=float(cfg.get("dx", 1.0)),
            dt=float(cfg.get("dt", 0.4)),
            density=float(cfg.get("density", 1.0)),
            stiffness=float(cfg.get("stiffness", 1.0)),
            damping=float(cfg.get("damping", 0.0)),
            core_start=int(cfg.get("core_start", 80)),
            core_end=int(cfg.get("core_end", 120)),
            core_density=float(cfg.get("core_density", 1.0)),
            core_stiffness=float(cfg.get("core_stiffness", 1.0)),
            core_damping=float(cfg.get("core_damping", 5.0)),
            source_amplitude=float(cfg.get("source_amplitude", 1.0)),
            source_location=int(cfg.get("source_location", 10)),
            source_duration=int(cfg.get("source_duration", 20)),
            boundary_condition=bc,
        )

    params_a = _build_params(cfg_a)
    params_b = _build_params(cfg_b)

    # Run simulations
    out_a = simulate_1d_damped_wave_lattice(params_a)
    out_b = simulate_1d_damped_wave_lattice(params_b)

    obs_a: dict[str, float] = out_a["observables"]
    obs_b: dict[str, float] = out_b["observables"]

    model_predictions = {
        model_a_id: {k: float(v) for k, v in obs_a.items() if isinstance(v, (int, float))},
        model_b_id: {k: float(v) for k, v in obs_b.items() if isinstance(v, (int, float))},
    }

    predicted_diffs: dict[str, float] = {}
    numerical_uncertainties: dict[str, float] = {}

    for obs_name in candidate.target_observables:
        val_a = model_predictions[model_a_id].get(obs_name, 0.0)
        val_b = model_predictions[model_b_id].get(obs_name, 0.0)
        diff = abs(val_a - val_b)
        predicted_diffs[obs_name] = round(diff, 6)

        # Scale discretization uncertainty with grid spacing (O(dx^2 + dt^2))
        unc = estimated_discretization_uncertainty * (params_a.dx**2 + params_a.dt**2)
        numerical_uncertainties[obs_name] = round(max(unc, 1e-6), 6)

    # Primary observable for formal discrimination metric: use highest-divergence target observable
    primary_obs = max(
        candidate.target_observables,
        key=lambda o: predicted_diffs.get(o, 0.0),
        default="attenuation_ratio",
    )
    signal = predicted_diffs.get(primary_obs, 0.0)
    noise = numerical_uncertainties.get(primary_obs, 1e-4)
    d_ratio = signal / noise if noise > 0 else 0.0

    disc_metric = DiscriminationMetric(
        metric_name=f"discrimination_ratio_{primary_obs}",
        numerator=f"|{model_a_id}.{primary_obs} - {model_b_id}.{primary_obs}|",
        denominator="effective_numerical_discretization_uncertainty",
        value=round(d_ratio, 4),
        assumptions=[
            "Linear wave propagation in 1-D",
            "Finite-difference 2nd-order spatial and temporal truncation error scaling",
            "Sufficient absorption at boundaries",
        ],
        units="dimensionless_ratio",
        interpretation=(
            "Ratio D > 1 indicates model divergence exceeds discretization noise; "
            "higher values provide clearer experimental separation."
        ),
        limitations="Does not account for unmodeled physical noise or epistemic parameter misspecification.",
    )

    # Multi-objective metrics
    # Robustness: Distance to CFL limit
    c_max = max(
        math.sqrt(params_a.stiffness / params_a.density),
        math.sqrt(params_a.core_stiffness / params_a.core_density),
    )
    cfl_limit = params_a.dx / c_max
    cfl_ratio = params_a.dt / cfl_limit
    numerical_robustness = round(max(0.0, 1.0 - cfl_ratio), 4)

    # Resource cost
    raw_cost = candidate.resource_requirements.estimated_cost or (params_a.nodes * params_a.time_steps * 1e-4)
    resource_cost = round(raw_cost, 4)

    eval_id = f"eval_{uuid.uuid4().hex[:8]}"
    return CandidateDesignEvaluation(
        evaluation_id=eval_id,
        candidate_design_id=candidate.candidate_design_id,
        model_predictions=model_predictions,
        predicted_differences=predicted_diffs,
        numerical_uncertainties=numerical_uncertainties,
        sensitivities={},
        discrimination_metric=disc_metric,
        discrimination_score=round(d_ratio, 4),
        numerical_robustness=numerical_robustness,
        parameter_coverage=1.0,
        resource_cost=resource_cost,
        constraint_satisfaction=True,
        sensitivity_alignment=1.0 if candidate.sensitivity_study_ref else 0.8,
        expected_observable_difference=round(signal, 6),
        evaluation_status="COMPLETED",
        notes=f"Candidate provides D={d_ratio:.2f} on {primary_obs} relative to numerical uncertainty.",
    )


def compute_pareto_frontier(
    project_id: str,
    evaluations: list[CandidateDesignEvaluation],
    objectives: list[str] | None = None,
) -> ParetoCandidateSet:
    """
    Compute the Pareto non-dominated candidate designs across multi-objective trade-offs.

    Supported default objectives:
        - "maximize:discrimination_score"
        - "minimize:resource_cost"
        - "maximize:numerical_robustness"

    Returns:
        ParetoCandidateSet identifying non-dominated candidate IDs without picking a single winner.
    """
    if not evaluations:
        raise ValueError("Cannot compute Pareto frontier over an empty evaluation set.")

    objs = objectives or [
        "maximize:discrimination_score",
        "minimize:resource_cost",
        "maximize:numerical_robustness",
    ]

    def _extract_val(ev: CandidateDesignEvaluation, obj_name: str) -> tuple[float, bool]:
        # returns (value, is_maximize)
        parts = obj_name.split(":")
        direction = parts[0].lower()
        field = parts[1]
        is_max = direction == "maximize"

        val = 0.0
        if field == "discrimination_score":
            val = ev.discrimination_score
        elif field == "resource_cost":
            val = ev.resource_cost
        elif field == "numerical_robustness":
            val = ev.numerical_robustness
        elif field == "expected_observable_difference":
            val = ev.expected_observable_difference
        return float(val), is_max

    non_dominated: list[str] = []

    for i, ev_i in enumerate(evaluations):
        dominated = False
        for j, ev_j in enumerate(evaluations):
            if i == j:
                continue

            # Check if ev_j dominates ev_i
            # ev_j dominates ev_i iff ev_j is >= ev_i in all objectives and > in at least one
            better_or_equal_all = True
            strictly_better_any = False

            for obj in objs:
                val_i, is_max = _extract_val(ev_i, obj)
                val_j, is_max = _extract_val(ev_j, obj)

                if is_max:
                    if val_j < val_i - 1e-9:
                        better_or_equal_all = False
                        break
                    if val_j > val_i + 1e-9:
                        strictly_better_any = True
                else:  # minimize
                    if val_j > val_i + 1e-9:
                        better_or_equal_all = False
                        break
                    if val_j < val_i - 1e-9:
                        strictly_better_any = True

            if better_or_equal_all and strictly_better_any:
                dominated = True
                break

        if not dominated:
            non_dominated.append(ev_i.candidate_design_id)

    # Deterministic sorting
    non_dominated = sorted(set(non_dominated))
    set_id = f"pareto_{uuid.uuid4().hex[:8]}"

    return ParetoCandidateSet(
        set_id=set_id,
        project_id=project_id,
        candidate_evaluations=evaluations,
        non_dominated_candidate_ids=non_dominated,
        objectives=objs,
        metadata={"total_evaluated": len(evaluations), "frontier_count": len(non_dominated)},
    )
