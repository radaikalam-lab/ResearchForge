"""Epistemic assessment entities and authority tiers."""

from typing import Any

from pydantic import Field

from researchforge.domain.base import DomainModel
from researchforge.domain.value_objects.epistemic import EpistemicTier
from researchforge.domain.value_objects.uncertainty import UncertaintyProfile


class EpistemicAssessment(DomainModel):
    """Formal assessment produced by epistemic evaluation (e.g. Cognitia)."""

    target_id: str
    target_type: str  # Claim, Hypothesis, Model, Gap
    tier: EpistemicTier = EpistemicTier.TIER_1_CRITIQUE
    epistemic_soundness: float = Field(default=0.8, ge=0.0, le=1.0)
    coherence_score: float = Field(default=0.8, ge=0.0, le=1.0)
    identified_assumptions: list[str] = Field(default_factory=list)
    hidden_assumptions: list[str] = Field(default_factory=list)
    vulnerabilities: list[str] = Field(default_factory=list)
    falsifiability_assessment: str = ""
    uncertainty: UncertaintyProfile = Field(default_factory=UncertaintyProfile)
    details: dict[str, Any] = Field(default_factory=dict)
