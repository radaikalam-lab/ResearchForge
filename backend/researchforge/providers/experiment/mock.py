"""Mock experiment provider."""

import hashlib
import uuid

from researchforge.domain.contracts.experiment import ExperimentProvider
from researchforge.domain.models.experiment import (
    ExperimentPlan,
    ExperimentResult,
    ExperimentRun,
    ExperimentType,
)
from researchforge.domain.models.hypothesis import Hypothesis
from researchforge.domain.value_objects.uncertainty import UncertaintyProfile


class MockExperimentProvider(ExperimentProvider):
    """Mock implementation of ExperimentProvider."""

    provider_name: str = "mock-experiment-v1"

    async def design(self, hypothesis: Hypothesis) -> ExperimentPlan:
        """Design an experiment plan to test the hypothesis."""
        plan_id = f"plan_{uuid.uuid4().hex[:8]}"
        return ExperimentPlan(
            id=plan_id,
            hypothesis_id=hypothesis.id,
            experiment_type=ExperimentType.NUMERICAL_EXPERIMENT,
            protocol_description=f"Standard numerical testing suite for hypothesis {hypothesis.id}",
            sample_size=100,
            random_seed=42,
            compute_budget_sec=60,
        )

    async def validate(self, plan: ExperimentPlan) -> bool:
        """Validate experiment plan constraints."""
        return plan.sample_size > 0 and plan.compute_budget_sec <= 300

    async def execute(self, plan: ExperimentPlan) -> ExperimentRun:
        """Execute experiment run."""
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        res_id = f"res_{uuid.uuid4().hex[:8]}"
        out_hash = hashlib.sha256(f"result_{run_id}_seed_{plan.random_seed}".encode()).hexdigest()

        result = ExperimentResult(
            id=res_id,
            run_id=run_id,
            metrics={"effect_size": 0.85, "p_value": 0.001, "sample_variance": 0.12},
            output_hash=out_hash,
            uncertainty=UncertaintyProfile(computational_uncertainty=0.01, sampling_uncertainty=0.03),
            logs=["Run initialized with seed 42", "Computation converged in 12 iterations"],
        )

        return ExperimentRun(
            id=run_id,
            experiment_plan_id=plan.id,
            status="COMPLETED",
            random_seed_used=plan.random_seed,
            environment_snapshot={"python_version": "3.12", "os": "windows"},
            execution_time_sec=0.25,
            result=result,
        )

    async def collect_results(self, run: ExperimentRun) -> ExperimentResult:
        """Collect result from run."""
        if not run.result:
            raise ValueError(f"Run {run.id} has no results.")
        return run.result
