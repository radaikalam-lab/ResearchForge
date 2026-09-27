"""Hypothesis, assumption, prediction, and falsification criteria entities."""

from enum import StrEnum
from typing import Any

from pydantic import Field, field_validator

from researchforge.domain.base import DomainModel


class AssumptionCategory(StrEnum):
    """Categories of model or hypothesis assumptions."""

    GEOMETRIC = "GEOMETRIC"
    MATERIAL = "MATERIAL"
    BOUNDARY = "BOUNDARY"
    INITIAL_CONDITION = "INITIAL_CONDITION"
    CONSTITUTIVE = "CONSTITUTIVE"
    NUMERICAL = "NUMERICAL"
    STATISTICAL = "STATISTICAL"
    MEASUREMENT = "MEASUREMENT"
    ENVIRONMENTAL = "ENVIRONMENTAL"
    SCALING = "SCALING"
    LINEARITY = "LINEARITY"
    HOMOGENEITY = "HOMOGENEITY"
    OTHER = "OTHER"


class Assumption(DomainModel):
    """Explicit domain, physical, or statistical assumption.

    An assumption is distinguishable from:
        - parameter
        - observation
        - measurement
        - result
        - conclusion
    """

    statement: str
    is_testable: bool = True
    criticality: float = Field(default=0.8, ge=0.0, le=1.0)
    justification: str = ""
    category: AssumptionCategory = Field(
        default=AssumptionCategory.OTHER,
        description="Classification of the assumption type",
    )
    status: str = Field(
        default="ACTIVE",
        description="ACTIVE, RELAXED, VIOLATED, UNKNOWN",
    )
    scope: str = Field(
        default="",
        description="Scope within which the assumption holds",
    )
    source_ref: str = Field(
        default="",
        description="Provenance reference for the assumption",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class Prediction(DomainModel):
    """Empirically testable deductive prediction derived from hypothesis."""

    statement: str
    expected_observable: str
    expected_direction: str = "POSITIVE"  # POSITIVE, NEGATIVE, NULL, NON_LINEAR
    significance_threshold: float = 0.05


class FalsificationCriterion(DomainModel):
    """Explicit observation or threshold that refutes the hypothesis."""

    description: str
    condition_expression: str = Field(
        description="Logical/mathematical condition e.g. 'p_value > 0.05 and effect_size < 0.2'"
    )
    metric_name: str
    refutation_threshold: float
    is_fatal_to_hypothesis: bool = True


class HypothesisAlternative(DomainModel):
    """Alternative or null hypothesis explanation."""

    statement: str
    mechanism: str
    plausibility_score: float = Field(default=0.5, ge=0.0, le=1.0)


class Hypothesis(DomainModel):
    """Scientific hypothesis with explicit falsification conditions."""

    project_id: str
    statement: str
    mechanism: str
    variable_ids: list[str] = Field(default_factory=list)
    assumption_ids: list[str] = Field(default_factory=list)
    prediction_ids: list[str] = Field(default_factory=list)
    alternative_explanations: list[str] = Field(default_factory=list)
    falsification_criteria: list[FalsificationCriterion] = Field(
        min_length=1,
        description="A hypothesis without falsification criteria is incomplete and invalid.",
    )
    required_measurements: list[str] = Field(default_factory=list)
    evidence_basis_ids: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)

    @field_validator("falsification_criteria")
    @classmethod
    def validate_has_falsification_criteria(
        cls, criteria: list[FalsificationCriterion]
    ) -> list[FalsificationCriterion]:
        """Enforce that every hypothesis defines at least one falsification criterion."""
        if not criteria:
            raise ValueError("A hypothesis MUST define at least one explicit falsification criterion.")
        return criteria
