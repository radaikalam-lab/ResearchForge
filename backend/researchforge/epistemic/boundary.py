"""Epistemic boundary validator and invariant assertions."""

from researchforge.domain.models.conclusion import Conclusion, HumanDecision
from researchforge.domain.models.epistemic import EpistemicTier
from researchforge.domain.state_machine import ResearchLifecycleState


class EpistemicAuthorityViolationError(Exception):
    """Raised when an unauthorized tier attempts an epistemic assertion or state promotion."""


class EpistemicBoundaryValidator:
    """Enforces the Research Authority Law across actors and tiers."""

    @staticmethod
    def assert_llm_cannot_validate(actor_tier: EpistemicTier, target_action: str) -> None:
        """Rule: LLM/Heuristics (Tier 0) cannot declare scientific truth or advance authority states."""
        if actor_tier == EpistemicTier.TIER_0_PROPOSAL:
            raise EpistemicAuthorityViolationError(
                f"Tier 0 (LLM/Proposal) is strictly advisory and cannot perform authoritative action '{target_action}'."
            )

    @staticmethod
    def assert_cognitia_cannot_execute(actor_tier: EpistemicTier, action_type: str) -> None:
        """Rule: Cognitia (Tier 1) cannot execute physical/computational experiments."""
        if actor_tier == EpistemicTier.TIER_1_CRITIQUE and action_type in {
            "EXECUTE_EXPERIMENT",
            "RUN_PHYSICAL_BENCH",
            "PUBLISH_MANUSCRIPT",
        }:
            raise EpistemicAuthorityViolationError(
                f"Cognitia (Tier 1 Critique) is prohibited from physical execution or publication: '{action_type}'."
            )

    @staticmethod
    def assert_conclusion_has_human_authority(conclusion: Conclusion, decision: HumanDecision | None) -> None:
        """Rule: A scientific claim cannot enter CONCLUSION_ACCEPTED without explicit human authority."""
        if not decision or decision.decision.value != "APPROVE":
            raise EpistemicAuthorityViolationError(
                f"Conclusion '{conclusion.id}' cannot be accepted without explicit Human Approval."
            )

    @staticmethod
    def assert_state_transition_authorized(
        current_state: ResearchLifecycleState,
        target_state: ResearchLifecycleState,
        actor_tier: EpistemicTier,
    ) -> None:
        """Enforce tier authority on state machine transitions."""
        if target_state in {
            ResearchLifecycleState.CONCLUSION_ACCEPTED,
            ResearchLifecycleState.PUBLISHABLE_ARTIFACT,
        }:
            if actor_tier != EpistemicTier.TIER_3_HUMAN_AUTHORITY:
                raise EpistemicAuthorityViolationError(
                    f"Transition to {target_state.value} requires Tier 3 Human Authority. Provided: {actor_tier.value}."
                )
