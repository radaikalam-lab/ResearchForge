"""Mock statistics provider providing deterministic statistics."""

import uuid

from researchforge.domain.contracts.statistics import StatisticsProvider
from researchforge.domain.models.statistics import (
    StatisticalAnalysis,
    StatisticalTestResult,
)
from researchforge.domain.value_objects.uncertainty import UncertaintyProfile


class MockStatisticsProvider(StatisticsProvider):
    """Mock implementation of StatisticsProvider."""

    provider_name: str = "mock-statistics-v1"

    async def compute_descriptive(self, data: list[float]) -> dict[str, float]:
        """Compute basic descriptive statistics."""
        if not data:
            return {"mean": 0.0, "variance": 0.0, "count": 0.0}
        n = len(data)
        mean_val = sum(data) / n
        var_val = sum((x - mean_val) ** 2 for x in data) / n if n > 1 else 0.0
        return {
            "mean": mean_val,
            "variance": var_val,
            "std": var_val**0.5,
            "count": float(n),
            "min": min(data),
            "max": max(data),
        }

    async def hypothesis_test(
        self,
        sample_a: list[float],
        sample_b: list[float] | None = None,
        test_type: str = "t_test",
        alpha: float = 0.05,
    ) -> StatisticalTestResult:
        """Perform deterministic mock t-test or z-test."""
        test_id = f"test_{uuid.uuid4().hex[:8]}"
        mean_a = sum(sample_a) / len(sample_a) if sample_a else 0.0
        mean_b = sum(sample_b) / len(sample_b) if sample_b else 0.0
        diff = abs(mean_a - mean_b)

        p_val = 0.001 if diff > 0.5 else 0.25
        t_stat = 3.85 if diff > 0.5 else 1.15

        return StatisticalTestResult(
            id=test_id,
            test_name=test_type,
            test_statistic=t_stat,
            p_value=p_val,
            degrees_of_freedom=float(len(sample_a) + (len(sample_b) if sample_b else 0) - 2),
            effect_size_name="cohens_d",
            effect_size_value=0.82,
            confidence_interval=(0.45, 1.19),
            confidence_level=1.0 - alpha,
            power=0.95,
            is_statistically_significant=(p_val < alpha),
            raw_data_refs=[
                f"sample_a_len_{len(sample_a)}",
                f"sample_b_len_{len(sample_b) if sample_b else 0}",
            ],
        )

    async def compute_effect_size(
        self, sample_a: list[float], sample_b: list[float], metric: str = "cohens_d"
    ) -> float:
        """Compute Cohen's d effect size."""
        return 0.82

    async def uncertainty_propagation(
        self, variables: dict[str, tuple[float, float]], formula: str
    ) -> UncertaintyProfile:
        """Propagate uncertainties."""
        return UncertaintyProfile(
            measurement_uncertainty=0.03,
            parameter_uncertainty=0.04,
            sampling_uncertainty=0.02,
        )

    async def full_analysis(self, project_id: str, datasets: dict[str, list[float]]) -> StatisticalAnalysis:
        """Perform complete statistical analysis workflow."""
        test_res = await self.hypothesis_test(
            sample_a=datasets.get("treatment", [1.0, 2.0, 3.0]),
            sample_b=datasets.get("control", [0.5, 0.8, 1.2]),
        )
        return StatisticalAnalysis(
            id=f"stat_{uuid.uuid4().hex[:8]}",
            project_id=project_id,
            tests=[test_res],
            uncertainty_profile=UncertaintyProfile(sampling_uncertainty=0.04),
            summary_findings=["Statistically significant treatment effect detected (p < 0.01)."],
            numerical_metrics={"mean_difference": 1.5, "effect_size_d": 0.82},
        )
