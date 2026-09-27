"""Tests for Epistemic Boundary and authority validation."""

import pytest
from researchforge.domain.models.epistemic import EpistemicTier
from researchforge.epistemic.boundary import (
    EpistemicAuthorityViolationError,
    EpistemicBoundaryValidator,
)


def test_llm_cannot_perform_authoritative_action() -> None:
    """Verify Tier 0 proposal engines cannot perform authoritative declarations."""
    with pytest.raises(EpistemicAuthorityViolationError):
        EpistemicBoundaryValidator.assert_llm_cannot_validate(
            actor_tier=EpistemicTier.TIER_0_PROPOSAL,
            target_action="VALIDATE_SCIENTIFIC_CLAIM",
        )


def test_cognitia_cannot_execute_experiments() -> None:
    """Verify Cognitia (Tier 1) cannot execute physical or system operations."""
    with pytest.raises(EpistemicAuthorityViolationError):
        EpistemicBoundaryValidator.assert_cognitia_cannot_execute(
            actor_tier=EpistemicTier.TIER_1_CRITIQUE,
            action_type="EXECUTE_EXPERIMENT",
        )
