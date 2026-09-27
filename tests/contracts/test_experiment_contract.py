"""Contract test for ExperimentProvider implementations."""

import pytest
from researchforge.domain.contracts.experiment import ExperimentProvider
from researchforge.domain.models.experiment import ExperimentType
from researchforge.domain.models.hypothesis import FalsificationCriterion, Hypothesis
from researchforge.providers.experiment.mock import MockExperimentProvider


@pytest.mark.asyncio
async def test_experiment_provider_contract_conformance() -> None:
    """Verify provider implements ExperimentProvider protocol."""
    provider: ExperimentProvider = MockExperimentProvider()
    assert isinstance(provider, ExperimentProvider)

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
        statement="Increased stress alters conductivity",
        mechanism="Piezoelectric coupling",
        falsification_criteria=[crit],
    )

    plan = await provider.design(hyp)
    assert plan.hypothesis_id == hyp.id
    assert plan.experiment_type == ExperimentType.NUMERICAL_EXPERIMENT

    is_valid = await provider.validate(plan)
    assert is_valid is True

    run = await provider.execute(plan)
    assert run.status == "COMPLETED"
    assert run.random_seed_used == plan.random_seed

    result = await provider.collect_results(run)
    assert result.output_hash != ""
    assert "effect_size" in result.metrics
