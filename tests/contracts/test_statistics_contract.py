"""Contract test for StatisticsProvider implementations."""

import pytest
from researchforge.domain.contracts.statistics import StatisticsProvider
from researchforge.providers.statistics.mock import MockStatisticsProvider


@pytest.mark.asyncio
async def test_statistics_provider_contract_conformance() -> None:
    """Verify provider implements StatisticsProvider protocol."""
    provider: StatisticsProvider = MockStatisticsProvider()
    assert isinstance(provider, StatisticsProvider)

    data = [1.2, 1.4, 1.5, 1.8, 2.1, 2.2]
    desc = await provider.compute_descriptive(data)
    assert desc["count"] == 6.0
    assert desc["mean"] > 1.0

    sample_a = [10.0, 11.0, 12.0, 10.5, 11.5]
    sample_b = [8.0, 8.5, 9.0, 8.2, 8.8]
    test_res = await provider.hypothesis_test(sample_a, sample_b, test_type="t_test")
    assert test_res.p_value < 0.05
    assert test_res.is_statistically_significant is True
    assert len(test_res.raw_data_refs) > 0

    d = await provider.compute_effect_size(sample_a, sample_b)
    assert d > 0.0

    unc = await provider.uncertainty_propagation({"x": (10.0, 0.5)}, "x**2")
    assert unc.measurement_uncertainty > 0.0

    analysis = await provider.full_analysis("proj_1", {"treatment": sample_a, "control": sample_b})
    assert len(analysis.tests) > 0
    assert len(analysis.summary_findings) > 0
