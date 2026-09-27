"""
Numerical verification, convergence study, and reference solution models (Phase 2.3).

Provides typed representations for:
    - NumericalVerification: result of a verification test
    - ConvergenceStudy: controlled refinement analysis
    - ReferenceSolution: labeled reference for comparison
    - ErrorCategory: taxonomy of error types
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import Field

from researchforge.domain.base import DomainModel
from researchforge.domain.models.model_validation import ModelValidationStatus


class VerificationType(StrEnum):
    """Types of numerical verification."""

    STABILITY = "STABILITY"
    CONVERGENCE = "CONVERGENCE"
    CONSISTENCY = "CONSISTENCY"
    CONSERVATION = "CONSERVATION"
    REFERENCE_AGREEMENT = "REFERENCE_AGREEMENT"
    MANUFACTURED_SOLUTION = "MANUFACTURED_SOLUTION"
    BOUNDARY_BEHAVIOR = "BOUNDARY_BEHAVIOR"
    ZERO_INPUT = "ZERO_INPUT"
    DETERMINISM = "DETERMINISM"


class ReferenceSolutionType(StrEnum):
    """Hierarchy of reference solutions."""

    ANALYTICAL = "ANALYTICAL"
    MANUFACTURED = "MANUFACTURED"
    HIGH_RESOLUTION_NUMERICAL = "HIGH_RESOLUTION_NUMERICAL"
    CROSS_SOLVER = "CROSS_SOLVER"
    EXPERIMENTAL_DATA = "EXPERIMENTAL_DATA"


class ErrorCategory(StrEnum):
    """Explicit error taxonomy.

    These categories must remain distinct.
    """

    NUMERICAL_ERROR = "NUMERICAL_ERROR"
    PARAMETER_UNCERTAINTY = "PARAMETER_UNCERTAINTY"
    MEASUREMENT_ERROR = "MEASUREMENT_ERROR"
    MODEL_FORM_DISCREPANCY = "MODEL_FORM_DISCREPANCY"
    IMPLEMENTATION_ERROR = "IMPLEMENTATION_ERROR"
    BOUNDARY_ARTIFACT = "BOUNDARY_ARTIFACT"
    DISCRETIZATION_ERROR = "DISCRETIZATION_ERROR"
    TRUNCATION_ERROR = "TRUNCATION_ERROR"
    UNKNOWN = "UNKNOWN"


class NumericalVerification(DomainModel):
    """Result of a numerical verification test.

    Asks: Did we correctly solve the mathematical model we specified?
    """

    verification_id: str = Field(description="Unique verification identifier")
    verification_type: VerificationType = Field(description="Type of verification performed")
    model_id: str = Field(description="Model being verified")
    passed: bool = Field(description="Whether the verification passed")
    metric_name: str = Field(description="Name of the verification metric")
    metric_value: float = Field(description="Numerical value of the metric")
    threshold: float | None = Field(default=None, description="Pass/fail threshold if applicable")
    resolution_params: dict[str, Any] = Field(
        default_factory=dict,
        description="Resolution parameters used (dx, dt, nodes, time_steps)",
    )
    error_category: ErrorCategory = Field(
        default=ErrorCategory.NUMERICAL_ERROR,
        description="Primary error category if verification failed",
    )
    notes: str = Field(default="", description="Human-readable notes")
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConvergenceStudy(DomainModel):
    """Controlled refinement study measuring convergence of a numerical solution.

    Supports refinement of:
        - dx (spatial resolution)
        - dt (temporal resolution)
    """

    study_id: str = Field(description="Unique study identifier")
    model_id: str = Field(description="Model under study")
    base_params: dict[str, Any] = Field(
        description="Base parameter set held fixed across refinements"
    )
    refinement_params: list[str] = Field(
        description="Parameters varied (e.g. ['dx', 'dt'])"
    )
    refinement_levels: list[dict[str, Any]] = Field(
        description="Specific parameter values at each refinement level"
    )
    metric_name: str = Field(description="Observable or error metric tracked")
    metric_values: list[float] = Field(description="Metric value at each refinement level")
    convergence_order: float | None = Field(
        default=None,
        description="Estimated convergence order if calculable",
    )
    reference_solution_id: str | None = Field(
        default=None,
        description="Reference solution used for error computation",
    )
    is_convergent: bool | None = Field(
        default=None,
        description="Whether the study demonstrates convergence",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)


class ReferenceSolution(DomainModel):
    """Labeled reference solution for comparison.

    Must NOT be labeled 'ground truth' unless an actual validated ground truth exists.
    """

    solution_id: str = Field(description="Unique reference solution identifier")
    name: str = Field(description="Human-readable name")
    solution_type: ReferenceSolutionType = Field(description="Type of reference solution")
    model_id: str | None = Field(
        default=None,
        description="Model that produced this reference (if numerical)",
    )
    data: dict[str, Any] = Field(
        description="Reference data (displacement field, observables, etc.)"
    )
    description: str = Field(default="", description="How this reference was generated")
    validation_status: ModelValidationStatus = Field(
        default=ModelValidationStatus.UNVERIFIED,
        description="Validation status of the reference itself",
    )
    metadata: dict[str, Any] = Field(default_factory=dict)
