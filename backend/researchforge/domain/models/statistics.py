"""Statistical analysis, hypothesis test results, and sensitivity models."""

from typing import Any

from pydantic import Field

from researchforge.domain.base import DomainModel
from researchforge.domain.value_objects.uncertainty import UncertaintyProfile


class StatisticalTestResult(DomainModel):
    """Result of a formal statistical hypothesis test."""

    test_name: str
    test_statistic: float
    p_value: float = Field(ge=0.0, le=1.0)
    degrees_of_freedom: float | None = None
    effect_size_name: str | None = None
    effect_size_value: float | None = None
    confidence_interval: tuple[float, float] | None = None
    confidence_level: float = 0.95
    power: float | None = Field(default=None, ge=0.0, le=1.0)
    is_statistically_significant: bool = False
    raw_data_refs: list[str] = Field(
        min_length=1,
        description="No statistical conclusion may be generated without underlying numerical references.",
    )


class SensitivityAnalysis(DomainModel):
    """Sensitivity analysis across parameter spaces."""

    parameter_name: str
    variation_range: tuple[float, float]
    sensitivity_indices: dict[str, float] = Field(default_factory=dict)
    summary: str = ""


class StatisticalAnalysis(DomainModel):
    """Composite statistical analysis container for an experiment or dataset."""

    project_id: str
    experiment_id: str | None = None
    dataset_ids: list[str] = Field(default_factory=list)
    tests: list[StatisticalTestResult] = Field(default_factory=list)
    sensitivity_analyses: list[SensitivityAnalysis] = Field(default_factory=list)
    uncertainty_profile: UncertaintyProfile = Field(default_factory=UncertaintyProfile)
    summary_findings: list[str] = Field(default_factory=list)
    numerical_metrics: dict[str, Any] = Field(default_factory=dict)
