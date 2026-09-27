"""Tests for Cognitia Adapter and provider isolation."""

import pytest
from researchforge.domain.models.hypothesis import Hypothesis
from researchforge.providers.cognitia.adapter import CognitiaAdapter


@pytest.mark.asyncio
async def test_cognitia_adapter_epistemic_critique(sample_hypothesis: Hypothesis) -> None:
    """Verify Cognitia adapter produces structured epistemic critique without physical authority."""
    adapter = CognitiaAdapter()
    assessment = await adapter.evaluate_hypothesis(sample_hypothesis)

    assert assessment.target_id == sample_hypothesis.id
    assert assessment.tier.value == "TIER_1_CRITIQUE"
    assert len(assessment.identified_assumptions) > 0
    assert len(assessment.vulnerabilities) > 0
