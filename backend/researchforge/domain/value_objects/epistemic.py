"""Epistemic tier enumeration value object."""

from enum import StrEnum


class EpistemicTier(StrEnum):
    """Authority tiers governing scientific claims and state mutations."""

    TIER_0_PROPOSAL = "TIER_0_PROPOSAL"  # LLMs, heuristic generators (Zero authority)
    TIER_1_CRITIQUE = "TIER_1_CRITIQUE"  # Cognitia epistemic plane (Advisory reasoning only)
    TIER_2_COMPUTATION = "TIER_2_COMPUTATION"  # ResearchForge simulation/numerical engines
    TIER_3_HUMAN_AUTHORITY = "TIER_3_HUMAN_AUTHORITY"  # Human researcher (Ultimate authority)
