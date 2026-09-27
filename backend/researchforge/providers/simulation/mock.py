"""Mock simulation provider."""

import hashlib
import uuid
from typing import Any

from researchforge.domain.contracts.simulation import SimulationProvider
from researchforge.domain.models.simulation import (
    Simulation,
    SimulationMetadata,
    SimulationRun,
)


class MockSimulationProvider(SimulationProvider):
    """Mock implementation of SimulationProvider."""

    provider_name: str = "mock-simulation-v1"

    async def prepare(self, simulation: Simulation, parameters: dict[str, Any], seed: int = 42) -> SimulationMetadata:
        """Prepare simulation metadata and deterministic hashes."""
        in_hash = hashlib.sha256(str(sorted(parameters.items())).encode()).hexdigest()
        out_hash = hashlib.sha256(f"sim_out_{in_hash}_{seed}".encode()).hexdigest()
        meta_id = f"meta_{uuid.uuid4().hex[:8]}"

        return SimulationMetadata(
            id=meta_id,
            model_name=simulation.name,
            model_version="1.0.0",
            parameter_set=parameters,
            software_version="0.1.0",
            environment={"solver": "numpy-rk4", "threads": "1"},
            random_seed=seed,
            input_hash=in_hash,
            output_hash=out_hash,
            execution_time_sec=0.15,
            resource_usage={"cpu_percent": 15.0, "memory_mb": 45.0},
        )

    async def validate(self, metadata: SimulationMetadata) -> bool:
        """Validate simulation metadata."""
        return metadata.random_seed >= 0 and bool(metadata.input_hash)

    async def run(self, metadata: SimulationMetadata) -> SimulationRun:
        """Execute simulation run."""
        run_id = f"simrun_{uuid.uuid4().hex[:8]}"
        return SimulationRun(
            id=run_id,
            simulation_id=f"sim_{uuid.uuid4().hex[:8]}",
            metadata=metadata,
            raw_outputs={"trajectory": [0.0, 0.5, 0.95, 1.25, 1.45], "steady_state": 1.5},
            summary_metrics={"final_value": 1.5, "convergence_steps": 5.0},
        )

    async def collect(self, run: SimulationRun) -> dict[str, Any]:
        """Collect metrics and arrays."""
        return {
            "metrics": run.summary_metrics,
            "output_hash": run.metadata.output_hash,
            "execution_time_sec": run.metadata.execution_time_sec,
        }
