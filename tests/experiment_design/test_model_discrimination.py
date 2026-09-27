"""
Tests for multi-model discrimination evaluation, numerical uncertainty accounting,
and formal DiscriminationMetric properties (Phase 2.4).
"""

from researchforge.domain.models.design_exploration_operators import (
    evaluate_candidate_for_model_discrimination,
    generate_candidate_designs,
)
from researchforge.domain.models.experimental_design_candidate import (
    CandidateDesignEvaluation,
    DiscriminationMetric,
)
from researchforge.domain.models.parameter_space import (
    ParameterDefinition,
    ParameterSpace,
    ParameterType,
    SamplingStrategy,
)


def _build_test_candidate() -> ParameterSpace:
    return ParameterSpace(
        id="ps_disc",
        name="Discrimination Space",
        parameters={
            "core_damping": ParameterDefinition(
                parameter_name="core_damping",
                parameter_type=ParameterType.CONTINUOUS,
                min_value=0.0,
                max_value=15.0,
                default_value=8.0,
            )
        },
    )


def test_model_discrimination_evaluation_computes_observable_divergence() -> None:
    """
    Test that evaluating a candidate design simulates both models, computes predicted differences,
    and isolates physical model difference from numerical discretization uncertainty.
    """
    ps = _build_test_candidate()
    cands = generate_candidate_designs(
        project_id="proj_eval",
        parameter_space=ps,
        model_ids=["model_elastic", "model_viscoelastic"],
        sample_count=1,
        sampling_strategy=SamplingStrategy.GRID,
    )
    cand = cands[0]

    # Model A: Purely elastic core (core_damping=0.0)
    # Model B: Viscoelastic core (core_damping=12.0)
    evaluation = evaluate_candidate_for_model_discrimination(
        candidate=cand,
        model_a_id="model_elastic",
        model_b_id="model_viscoelastic",
        model_a_params_override={"core_damping": 0.0},
        model_b_params_override={"core_damping": 12.0},
        estimated_discretization_uncertainty=0.002,
    )

    assert isinstance(evaluation, CandidateDesignEvaluation)
    assert evaluation.candidate_design_id == cand.candidate_design_id
    assert "model_elastic" in evaluation.model_predictions
    assert "model_viscoelastic" in evaluation.model_predictions

    # Transmitted energy should be higher for elastic than viscoelastic
    elastic_te = evaluation.model_predictions["model_elastic"]["transmitted_energy"]
    visco_te = evaluation.model_predictions["model_viscoelastic"]["transmitted_energy"]
    assert elastic_te > visco_te

    # Predicted difference must be strictly positive
    diff = evaluation.predicted_differences["transmitted_energy"]
    assert diff > 0.0
    assert abs(diff - (elastic_te - visco_te)) < 1e-5

    # Numerical uncertainty must be explicit and non-zero
    unc = evaluation.numerical_uncertainties["transmitted_energy"]
    assert unc > 0.0

    # Formal DiscriminationMetric verification
    metric = evaluation.discrimination_metric
    assert isinstance(metric, DiscriminationMetric)
    assert metric.value > 1.0  # Physical signal exceeds numerical error
    assert "numerator" in metric.model_dump()
    assert "denominator" in metric.model_dump()
    assert "limitations" in metric.model_dump()


def test_discrimination_score_drops_when_numerical_error_dominates() -> None:
    """
    Test that candidate evaluation reduces discrimination score when numerical error is large
    relative to model difference.
    """
    ps = _build_test_candidate()
    cands = generate_candidate_designs(
        project_id="proj_eval_err",
        parameter_space=ps,
        model_ids=["model_a", "model_b"],
        sample_count=1,
    )
    cand = cands[0]

    # Clear model parameter difference evaluated under low vs high numerical noise
    eval_clean = evaluate_candidate_for_model_discrimination(
        candidate=cand,
        model_a_id="model_a",
        model_b_id="model_b",
        model_a_params_override={"core_damping": 2.0},
        model_b_params_override={"core_damping": 10.0},
        estimated_discretization_uncertainty=0.001,
    )

    eval_noisy = evaluate_candidate_for_model_discrimination(
        candidate=cand,
        model_a_id="model_a",
        model_b_id="model_b",
        model_a_params_override={"core_damping": 2.0},
        model_b_params_override={"core_damping": 10.0},
        estimated_discretization_uncertainty=0.100,  # 100x larger discretization error
    )

    assert eval_clean.discrimination_score > eval_noisy.discrimination_score
