"""
Tests for deterministic candidate generation and evaluation replay (Phase 2.4).

Verifies that design candidate generation and evaluation can be replayed offline
without network, LLM, or Cognitia access, yielding bitwise identical results.
"""

from researchforge.domain.models.design_exploration_operators import (
    evaluate_candidate_for_model_discrimination,
    generate_candidate_designs,
)
from researchforge.domain.models.parameter_space import (
    ParameterDefinition,
    ParameterSpace,
    ParameterType,
    SamplingStrategy,
)


def test_offline_candidate_replay_without_external_dependencies() -> None:
    """Verify that candidate generation produces bitwise identical candidates across re-runs."""
    ps = ParameterSpace(
        id="ps_replay",
        name="Replay Parameter Space",
        parameters={
            "core_damping": ParameterDefinition(
                parameter_name="core_damping",
                parameter_type=ParameterType.CONTINUOUS,
                min_value=0.0,
                max_value=10.0,
            ),
            "core_stiffness": ParameterDefinition(
                parameter_name="core_stiffness",
                parameter_type=ParameterType.CONTINUOUS,
                min_value=0.5,
                max_value=1.5,
            ),
        },
    )

    # Run 1: Grid
    cands_1 = generate_candidate_designs(
        project_id="proj_replay",
        parameter_space=ps,
        model_ids=["m1", "m2"],
        sampling_strategy=SamplingStrategy.GRID,
        sample_count=3,
    )

    # Run 2: Replay
    cands_2 = generate_candidate_designs(
        project_id="proj_replay",
        parameter_space=ps,
        model_ids=["m1", "m2"],
        sampling_strategy=SamplingStrategy.GRID,
        sample_count=3,
    )

    assert len(cands_1) == len(cands_2)
    for c1, c2 in zip(cands_1, cands_2, strict=True):
        assert c1.candidate_design_id == c2.candidate_design_id
        assert c1.parameter_assignments == c2.parameter_assignments

        # Evaluate both
        ev1 = evaluate_candidate_for_model_discrimination(
            candidate=c1,
            model_a_id="m1",
            model_b_id="m2",
            model_a_params_override={"core_damping": 1.0},
            model_b_params_override={"core_damping": 8.0},
        )
        ev2 = evaluate_candidate_for_model_discrimination(
            candidate=c2,
            model_a_id="m1",
            model_b_id="m2",
            model_a_params_override={"core_damping": 1.0},
            model_b_params_override={"core_damping": 8.0},
        )

        assert ev1.discrimination_score == ev2.discrimination_score
        assert ev1.predicted_differences == ev2.predicted_differences
        assert ev1.numerical_uncertainties == ev2.numerical_uncertainties
