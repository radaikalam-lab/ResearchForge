"""Contract test for SimulationProvider implementations."""

import pytest
from researchforge.domain.contracts.simulation import SimulationProvider
from researchforge.domain.models.simulation import Simulation
from researchforge.providers.simulation.mock import MockSimulationProvider


@pytest.mark.asyncio
async def test_simulation_provider_contract_conformance() -> None:
    """Verify provider implements SimulationProvider protocol."""
    provider: SimulationProvider = MockSimulationProvider()
    assert isinstance(provider, SimulationProvider)

    sim = Simulation(
        id="sim_1",
        project_id="proj_1",
        name="LatticeDynamicsSimulation",
        description="Finite element crystal lattice solver",
        engine_name="mock-engine",
    )

    metadata = await provider.prepare(sim, parameters={"pressure_gpa": 5.0, "temp_k": 300.0}, seed=123)
    assert metadata.random_seed == 123
    assert metadata.input_hash != ""

    is_valid = await provider.validate(metadata)
    assert is_valid is True

    run = await provider.run(metadata)
    assert run.metadata.input_hash == metadata.input_hash

    collected = await provider.collect(run)
    assert "metrics" in collected
    assert collected["output_hash"] == metadata.output_hash
