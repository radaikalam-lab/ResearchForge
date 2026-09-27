"""
Model comparison and sensitivity analysis domain models (Phase 2.3).

Provides typed representations for:
    - ModelComparison: formal comparison between two or more models
    - ModelComparisonResult: evidence-centric comparison output
    - SensitivitySample: single parameter perturbation result
    - SensitivityStudy: multi-parameter sensitivity analysis
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field, model_validator

from researchforge.domain.base import DomainModel
from researchforge.domain.models.model_validation import ModelValidationStatus


class ComparisonMethod(StrEnum):
    """Methods for comparing models."""

    OBSERVABLE_DIFFERENCE = "OBSERVABLE_DIFFERENCE"
    ERROR_METRIC = "ERROR_METRIC"
    RESIDUAL_ANALYSIS = "RESIDUAL_ANALYSIS"
    FIT_METRIC = "FIT_METRIC"
    CONVERGENCE_COMPARISON = "CONVERGENCE_COMPARISON"
    SENSITIVITY_COMPARISON = "SENSITIVITY_COMPARISON"


class SensitivityMethod(StrEnum):
    """Sampling strategies for sensitivity analysis."""

    ONE_AT_A_TIME = "ONE_AT_A_TIME"
    FINITE_DIFFERENCE = "FINITE_DIFFERENCE"
    LOCAL = "LOCAL"
    GLOBAL = "GLOBAL"


class ModelComparisonResult(DomainModel):
    """Evidence-centric output of a model comparison.

    Contains observed differences, error metrics, and validation metadata.
    Does NOT automatically declare a winner.
    """

    id: str = Field(default="", description="Identifier")
    result_id: str = Field(default="", description="Unique comparison result identifier")
    comparison_id: str = Field(description="Parent ModelComparison identifier")
    model_ids: list[str] = Field(description="Models included in this comparison")
    observable_differences: dict[str, float] = Field(
        default_factory=dict,
        description="Difference in observables between models",
    )
    error_metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Error metrics relative to reference",
    )
    numerical_verifications: list[str] = Field(
        default_factory=list,
        description="IDs of supporting numerical verifications",
    )
    convergence_studies: list[str] = Field(
        default_factory=list,
        description="IDs of supporting convergence studies",
    )
    sensitivity_studies: list[str] = Field(
        default_factory=list,
        description="IDs of supporting sensitivity analyses",
    )
    assumption_differences: list[str] = Field(
        default_factory=list,
        description="Summary of assumption differences between models",
    )
    validation_status: ModelValidationStatus = Field(
        default=ModelValidationStatus.UNVERIFIED,
        description="Validation status of the comparison",
    )
    physical_validation_status: ModelValidationStatus = Field(
        default=ModelValidationStatus.UNVERIFIED,
        description="Physical validation status (distinct from numerical)",
    )
    notes: str = Field(
        default="",
        description="Interpretation notes - does NOT declare a winner",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def sync_id(self) -> ModelComparisonResult:
        if not self.id and self.result_id:
            self.id = self.result_id
        elif not self.result_id and self.id:
            self.result_id = self.id
        return self


class ModelComparison(DomainModel):
    """Formal comparison between two or more scientific models.

    Produces evidence; does not automatically declare a winner.
    Human/domain authority determines the scientific conclusion.
    """

    id: str = Field(default="", description="Identifier")
    comparison_id: str = Field(default="", description="Unique comparison identifier")
    name: str = Field(description="Human-readable comparison name")
    description: str = Field(default="", description="Purpose and scope of comparison")
    model_ids: list[str] = Field(description="Models being compared")
    comparison_method: ComparisonMethod = Field(description="Primary comparison method")
    experiment_ids: list[str] = Field(
        default_factory=list,
        description="Comparable experiments used for comparison",
    )
    reference_solution_ids: list[str] = Field(
        default_factory=list,
        description="Reference solutions used in comparison",
    )
    convergence_study_ids: list[str] = Field(
        default_factory=list,
        description="Convergence studies supporting the comparison",
    )
    sensitivity_study_ids: list[str] = Field(
        default_factory=list,
        description="Sensitivity studies supporting the comparison",
    )
    numerical_verification_ids: list[str] = Field(
        default_factory=list,
        description="Numerical verifications supporting the comparison",
    )
    result_id: str | None = Field(
        default=None,
        description="ID of the ModelComparisonResult produced by this comparison",
    )
    status: str = Field(default="PENDING", description="PENDING, COMPLETED, FAILED")
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def sync_id(self) -> ModelComparison:
        if not self.id and self.comparison_id:
            self.id = self.comparison_id
        elif not self.comparison_id and self.id:
            self.comparison_id = self.id
        return self


class SensitivitySample(DomainModel):
    """Single parameter perturbation result."""

    id: str = Field(default="", description="Identifier")
    sample_id: str = Field(default="", description="Unique sample identifier")
    study_id: str = Field(description="Parent SensitivityStudy identifier")
    parameter_name: str = Field(description="Parameter perturbed")
    parameter_value: float = Field(description="Value used for this sample")
    baseline_value: float = Field(description="Baseline parameter value")
    perturbation: float = Field(description="Perturbation applied (value - baseline)")
    observables: dict[str, float] = Field(
        default_factory=dict,
        description="Observable values for this sample",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def sync_id(self) -> SensitivitySample:
        if not self.id and self.sample_id:
            self.id = self.sample_id
        elif not self.sample_id and self.id:
            self.sample_id = self.id
        return self


class SensitivityStudy(DomainModel):
    """Deterministic sensitivity analysis over selected model parameters.

    Distinguishes sensitivity analysis from uncertainty quantification.
    Sensitivity analysis varies parameters; it does not model probability distributions.
    """

    id: str = Field(default="", description="Identifier")
    study_id: str = Field(default="", description="Unique study identifier")
    name: str = Field(description="Human-readable study name")
    model_id: str = Field(description="Model under sensitivity study")
    base_params: dict[str, Any] = Field(
        description="Base parameter values for the model"
    )
    sensitivity_method: SensitivityMethod = Field(
        default=SensitivityMethod.ONE_AT_A_TIME,
        description="Sampling strategy used",
    )
    parameter_names: list[str] = Field(
        description="Parameters included in the sensitivity study"
    )
    perturbation_strategy: dict[str, Any] = Field(
        default_factory=dict,
        description="Perturbation magnitudes and directions for each parameter",
    )
    observable_names: list[str] = Field(
        description="Observables tracked for sensitivity"
    )
    sample_ids: list[str] = Field(
        default_factory=list,
        description="IDs of SensitivitySample results",
    )
    sensitivity_metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Computed sensitivity metrics per parameter",
    )
    is_deterministic: bool = Field(
        default=True,
        description="Whether the study is deterministic for given inputs",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def sync_id(self) -> SensitivityStudy:
        if not self.id and self.study_id:
            self.id = self.study_id
        elif not self.study_id and self.id:
            self.study_id = self.id
        return self
