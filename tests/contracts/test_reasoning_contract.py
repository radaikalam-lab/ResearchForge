"""Contract test for ReasoningProvider implementations."""

import pytest
from researchforge.domain.contracts.reasoning import ReasoningProvider
from researchforge.domain.models.evidence import Claim
from researchforge.domain.models.hypothesis import FalsificationCriterion, Hypothesis
from researchforge.providers.llm.mock import MockReasoningProvider


@pytest.mark.asyncio
async def test_reasoning_provider_contract_conformance() -> None:
    """Verify provider implements ReasoningProvider protocol."""
    provider: ReasoningProvider = MockReasoningProvider()
    assert isinstance(provider, ReasoningProvider)

    crit = FalsificationCriterion(
        id="c1",
        description="Falsification condition",
        condition_expression="p > 0.05",
        metric_name="p",
        refutation_threshold=0.05,
    )
    hyp = Hypothesis(
        id="h1",
        project_id="p1",
        statement="Temperature scales linearly with voltage",
        mechanism="Joule heating",
        falsification_criteria=[crit],
    )

    prop = await provider.propose("thermoelectric materials", ["ref_01"])
    assert "thermoelectric" in prop

    critique = await provider.critique(hyp, [])
    assert len(critique) > 0

    extracted = await provider.extract("Sample text", "ClaimSchema")
    assert "extracted_claim" in extracted

    syn = await provider.synthesize([Claim(id="c1", statement="Claim 1")])
    assert "Synthesized" in syn
