"""Multi-dimensional uncertainty value objects."""

from pydantic import BaseModel, Field


class UncertaintyProfile(BaseModel):
    """Explicit multi-dimensional uncertainty representation."""

    measurement_uncertainty: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Uncertainty from physical/sensor measurement noise",
    )
    model_uncertainty: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Uncertainty arising from model structural assumptions",
    )
    parameter_uncertainty: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Uncertainty in estimated input parameters"
    )
    sampling_uncertainty: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Uncertainty from sample size and population coverage",
    )
    computational_uncertainty: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Uncertainty from numerical tolerances and floating point precision",
    )
    epistemic_uncertainty: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Uncertainty stemming from fundamental lack of domain knowledge",
    )
    rationale: str = Field(default="", description="Detailed qualitative justification for uncertainty bounds")

    @property
    def total_aggregate_uncertainty(self) -> float:
        """Conservative aggregate bound without collapsing individual dimensions."""
        dimensions = [
            self.measurement_uncertainty,
            self.model_uncertainty,
            self.parameter_uncertainty,
            self.sampling_uncertainty,
            self.computational_uncertainty,
            self.epistemic_uncertainty,
        ]
        return min(1.0, sum(d**2 for d in dimensions) ** 0.5)
