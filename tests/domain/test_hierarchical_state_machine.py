"""Unit tests for hierarchical state machines and TransitionEngine."""

import pytest
from researchforge.domain.models.epistemic import EpistemicTier
from researchforge.domain.state_machine import (
    GuardViolationError,
    HypothesisLifecycleState,
    MissingArtifactError,
    Transition,
    TransitionEngine,
)


def test_transition_engine_valid_flow() -> None:
    """Verify TransitionEngine processes valid state progression."""
    engine = TransitionEngine()
    engine.register_transition(
        Transition(
            source_state=HypothesisLifecycleState.DRAFT,
            target_state=HypothesisLifecycleState.FORMED,
            trigger="formulate_hypothesis",
            required_actor_tier=EpistemicTier.TIER_0_PROPOSAL,
            required_artifacts=["Hypothesis"],
        )
    )

    result = engine.execute_transition(
        current_state=HypothesisLifecycleState.DRAFT,
        target_state=HypothesisLifecycleState.FORMED,
        actor_tier=EpistemicTier.TIER_2_COMPUTATION,
        available_artifacts=["Hypothesis"],
    )
    assert result == HypothesisLifecycleState.FORMED


def test_transition_engine_missing_artifact() -> None:
    """Verify TransitionEngine rejects transition when required artifacts are missing."""
    engine = TransitionEngine()
    engine.register_transition(
        Transition(
            source_state=HypothesisLifecycleState.FORMED,
            target_state=HypothesisLifecycleState.CRITIQUE_PENDING,
            trigger="submit_critique",
            required_artifacts=["FalsificationCriterion"],
        )
    )

    with pytest.raises(MissingArtifactError):
        engine.execute_transition(
            current_state=HypothesisLifecycleState.FORMED,
            target_state=HypothesisLifecycleState.CRITIQUE_PENDING,
            available_artifacts=[],  # Missing FalsificationCriterion
        )


def test_transition_engine_guard_violation() -> None:
    """Verify TransitionEngine enforces guard conditions."""
    engine = TransitionEngine()
    engine.register_transition(
        Transition(
            source_state=HypothesisLifecycleState.EXPERIMENT_READY,
            target_state=HypothesisLifecycleState.UNDER_TEST,
            trigger="start_run",
            guard_description="Resource budget must be positive",
        ),
        guard_fn=lambda compute_budget: compute_budget > 0,
    )

    # Budget <= 0 triggers GuardViolationError
    with pytest.raises(GuardViolationError):
        engine.execute_transition(
            current_state=HypothesisLifecycleState.EXPERIMENT_READY,
            target_state=HypothesisLifecycleState.UNDER_TEST,
            context={"compute_budget": 0},
        )

    # Budget > 0 succeeds
    res = engine.execute_transition(
        current_state=HypothesisLifecycleState.EXPERIMENT_READY,
        target_state=HypothesisLifecycleState.UNDER_TEST,
        context={"compute_budget": 60},
    )
    assert res == HypothesisLifecycleState.UNDER_TEST
