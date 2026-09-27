"""Experiment provider protocol contract."""

from typing import Protocol, runtime_checkable

from researchforge.domain.models.experiment import ExperimentPlan, ExperimentResult, ExperimentRun
from researchforge.domain.models.hypothesis import Hypothesis


@runtime_checkable
class ExperimentProvider(Protocol):
    """Contract for designing, validating, executing, and collecting computational experiments."""

    provider_name: str

    async def design(self, hypothesis: Hypothesis) -> ExperimentPlan:
        """Formulate a computational or statistical experiment plan to test hypothesis."""
        ...

    async def validate(self, plan: ExperimentPlan) -> bool:
        """Validate resource requirements, variable bounds, and protocol completeness."""
        ...

    async def execute(self, plan: ExperimentPlan) -> ExperimentRun:
        """Execute experiment run within sandbox isolation."""
        ...

    async def collect_results(self, run: ExperimentRun) -> ExperimentResult:
        """Extract and structure metrics and datasets from completed run."""
        ...
