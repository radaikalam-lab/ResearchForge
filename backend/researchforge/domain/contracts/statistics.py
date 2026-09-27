"""Statistical provider protocol contract."""

from typing import Protocol, runtime_checkable

from researchforge.domain.models.statistics import StatisticalAnalysis, StatisticalTestResult
from researchforge.domain.value_objects.uncertainty import UncertaintyProfile


@runtime_checkable
class StatisticsProvider(Protocol):
    """Contract for deterministic statistical calculations, hypothesis tests, and uncertainty."""

    provider_name: str

    async def compute_descriptive(self, data: list[float]) -> dict[str, float]:
        """Calculate mean, median, variance, std, IQR, skewness, kurtosis."""
        ...

    async def hypothesis_test(
        self,
        sample_a: list[float],
        sample_b: list[float] | None = None,
        test_type: str = "t_test",
        alpha: float = 0.05,
    ) -> StatisticalTestResult:
        """Perform formal statistical test and return structured result."""
        ...

    async def compute_effect_size(
        self, sample_a: list[float], sample_b: list[float], metric: str = "cohens_d"
    ) -> float:
        """Compute standardized effect size (Cohen's d, Hedges' g, Eta-squared)."""
        ...

    async def uncertainty_propagation(
        self, variables: dict[str, tuple[float, float]], formula: str
    ) -> UncertaintyProfile:
        """Propagate uncertainties through analytical or Monte Carlo calculations."""
        ...

    async def full_analysis(self, project_id: str, datasets: dict[str, list[float]]) -> StatisticalAnalysis:
        """Execute comprehensive statistical workflow returning structured analysis."""
        ...
