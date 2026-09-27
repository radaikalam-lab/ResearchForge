"""Simulation provider protocol contract."""

from typing import Any, Protocol, runtime_checkable

from researchforge.domain.models.simulation import Simulation, SimulationMetadata, SimulationRun


@runtime_checkable
class SimulationProvider(Protocol):
    """Contract for deterministic numerical and physical simulations."""

    provider_name: str

    async def prepare(self, simulation: Simulation, parameters: dict[str, Any], seed: int = 42) -> SimulationMetadata:
        """Initialize parameters, environment bounds, and compute input hashes."""
        ...

    async def validate(self, metadata: SimulationMetadata) -> bool:
        """Verify deterministic preconditions and resource bounds."""
        ...

    async def run(self, metadata: SimulationMetadata) -> SimulationRun:
        """Run the simulation under deterministic execution constraints."""
        ...

    async def collect(self, run: SimulationRun) -> dict[str, Any]:
        """Extract output arrays, time series, and compute output hashes."""
        ...
