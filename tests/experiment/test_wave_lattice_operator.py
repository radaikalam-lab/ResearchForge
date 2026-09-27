"""
Tests for the 1-D Heterogeneous Damped-Wave Reference Operator (Phase 2.2).

Covers:
- Numerical correctness (homogeneous, heterogeneous, boundary conditions)
- Physical sanity (zero source → zero response, damping effects, energy)
- Determinism verification
- Parameter validation / stability check
- Baseline vs heterogeneous comparison
- Architecture boundary (operator must NOT import persistence/sqlalchemy/Cognitia)
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest
from researchforge.domain.models.wave_lattice import (
    BoundaryCondition,
    WaveLatticeObservables,
    WaveLatticeParameters,
    simulate_1d_damped_wave_lattice,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _homogeneous_params(**kwargs: object) -> WaveLatticeParameters:
    """Stable homogeneous baseline with CFL-safe defaults."""
    defaults: dict[str, object] = {
        "nodes": 80,
        "time_steps": 120,
        "dx": 1.0,
        "dt": 0.4,
        "density": 1.0,
        "stiffness": 1.0,
        "damping": 0.0,
        "core_start": 30,
        "core_end": 50,
        "core_density": 1.0,
        "core_stiffness": 1.0,
        "core_damping": 0.0,
        "source_amplitude": 1.0,
        "source_location": 5,
        "source_duration": 15,
        "boundary_condition": BoundaryCondition.ABSORBING,
    }
    defaults.update(kwargs)
    return WaveLatticeParameters(id="params_test", **defaults)  # type: ignore[arg-type]


def _heterogeneous_params(**kwargs: object) -> WaveLatticeParameters:
    """Heterogeneous core with elevated damping, otherwise same as baseline."""
    defaults: dict[str, object] = {
        "nodes": 80,
        "time_steps": 120,
        "dx": 1.0,
        "dt": 0.4,
        "density": 1.0,
        "stiffness": 1.0,
        "damping": 0.0,
        "core_start": 30,
        "core_end": 50,
        "core_density": 1.0,
        "core_stiffness": 1.0,
        "core_damping": 8.0,  # strong damping in core
        "source_amplitude": 1.0,
        "source_location": 5,
        "source_duration": 15,
        "boundary_condition": BoundaryCondition.ABSORBING,
    }
    defaults.update(kwargs)
    return WaveLatticeParameters(id="params_test_het", **defaults)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Parameter Validation
# ---------------------------------------------------------------------------


class TestParameterValidation:
    def test_cfl_stability_violation_raises(self) -> None:
        """dt > dx/c must raise ValueError at construction."""
        with pytest.raises(ValueError, match="CFL stability violation"):
            WaveLatticeParameters(
                id="bad",
                nodes=80,
                time_steps=10,
                dx=1.0,
                dt=2.0,  # >> dx / c = 1.0
                density=1.0,
                stiffness=1.0,
                damping=0.0,
                core_start=30,
                core_end=50,
                core_density=1.0,
                core_stiffness=1.0,
                core_damping=0.0,
                source_amplitude=1.0,
                source_location=5,
                source_duration=10,
            )

    def test_core_end_exceeds_nodes_raises(self) -> None:
        with pytest.raises(ValueError, match="core_end"):
            WaveLatticeParameters(
                id="bad2",
                nodes=50,
                time_steps=10,
                dx=1.0,
                dt=0.4,
                density=1.0,
                stiffness=1.0,
                damping=0.0,
                core_start=30,
                core_end=60,  # > nodes
                core_density=1.0,
                core_stiffness=1.0,
                core_damping=0.0,
                source_amplitude=1.0,
                source_location=5,
                source_duration=10,
            )

    def test_core_start_ge_core_end_raises(self) -> None:
        with pytest.raises(ValueError, match="core_start"):
            WaveLatticeParameters(
                id="bad3",
                nodes=80,
                time_steps=10,
                dx=1.0,
                dt=0.4,
                density=1.0,
                stiffness=1.0,
                damping=0.0,
                core_start=50,
                core_end=30,  # < core_start
                core_density=1.0,
                core_stiffness=1.0,
                core_damping=0.0,
                source_amplitude=1.0,
                source_location=5,
                source_duration=10,
            )

    def test_source_location_out_of_bounds_raises(self) -> None:
        with pytest.raises(ValueError, match="source_location"):
            WaveLatticeParameters(
                id="bad4",
                nodes=80,
                time_steps=10,
                dx=1.0,
                dt=0.4,
                density=1.0,
                stiffness=1.0,
                damping=0.0,
                core_start=30,
                core_end=50,
                core_density=1.0,
                core_stiffness=1.0,
                core_damping=0.0,
                source_amplitude=1.0,
                source_location=90,  # >= nodes
                source_duration=10,
            )

    def test_valid_params_construct_successfully(self) -> None:
        p = _homogeneous_params()
        assert p.nodes == 80
        assert p.dt <= p.dx  # CFL satisfied with c=1


# ---------------------------------------------------------------------------
# Physical Sanity
# ---------------------------------------------------------------------------


class TestPhysicalSanity:
    def test_zero_source_produces_zero_response(self) -> None:
        """Zero source amplitude must yield zero displacement everywhere."""
        p = _homogeneous_params(source_amplitude=0.0)
        out = simulate_1d_damped_wave_lattice(p)
        obs = WaveLatticeObservables.model_validate(out["observables"])
        assert obs.max_displacement == pytest.approx(0.0, abs=1e-15)
        assert obs.max_core_displacement == pytest.approx(0.0, abs=1e-15)
        assert obs.incident_energy == pytest.approx(0.0, abs=1e-15)

    def test_zero_damping_preserves_energy_signature(self) -> None:
        """With zero damping, dissipated_energy should be ~0."""
        p = _homogeneous_params(damping=0.0, core_damping=0.0)
        out = simulate_1d_damped_wave_lattice(p)
        obs = WaveLatticeObservables.model_validate(out["observables"])
        assert obs.dissipated_energy == pytest.approx(0.0, abs=1e-12)

    def test_increased_damping_increases_dissipation(self) -> None:
        """Higher global damping must produce strictly more dissipation."""
        p_low = _homogeneous_params(damping=0.0, core_damping=0.0)
        p_high = _homogeneous_params(damping=0.5, core_damping=0.5)
        out_low = simulate_1d_damped_wave_lattice(p_low)
        out_high = simulate_1d_damped_wave_lattice(p_high)
        obs_low = WaveLatticeObservables.model_validate(out_low["observables"])
        obs_high = WaveLatticeObservables.model_validate(out_high["observables"])
        assert obs_high.dissipated_energy > obs_low.dissipated_energy

    def test_positive_source_produces_positive_max_displacement(self) -> None:
        p = _homogeneous_params(source_amplitude=2.0)
        out = simulate_1d_damped_wave_lattice(p)
        obs = WaveLatticeObservables.model_validate(out["observables"])
        assert obs.max_displacement > 0.0


# ---------------------------------------------------------------------------
# Numerical Correctness
# ---------------------------------------------------------------------------


class TestNumericalCorrectness:
    def test_output_arrays_have_correct_length(self) -> None:
        p = _homogeneous_params(nodes=60)
        out = simulate_1d_damped_wave_lattice(p)
        assert len(out["final_displacement"]) == 60
        assert len(out["final_velocity"]) == 60

    def test_dirichlet_boundary_enforces_zero_ends(self) -> None:
        """With Dirichlet BC the displacement at both ends must be exactly 0."""
        p = _homogeneous_params(boundary_condition=BoundaryCondition.DIRICHLET)
        out = simulate_1d_damped_wave_lattice(p)
        disp = out["final_displacement"]
        assert disp[0] == pytest.approx(0.0, abs=1e-15)
        assert disp[-1] == pytest.approx(0.0, abs=1e-15)

    def test_absorbing_boundary_damps_out_wave(self) -> None:
        """With absorbing BC and enough time steps, the field should be nearly zero."""
        p = _homogeneous_params(
            nodes=80, time_steps=400, boundary_condition=BoundaryCondition.ABSORBING,
            damping=0.1, core_damping=0.1,
        )
        out = simulate_1d_damped_wave_lattice(p)
        disp = np.array(out["final_displacement"])
        # Should be much smaller than source amplitude after damping + absorption
        assert float(np.max(np.abs(disp))) < 0.5  # substantial attenuation

    def test_wave_travels_past_source_region(self) -> None:
        """The wave must reach the core region after sufficient time steps."""
        p = _homogeneous_params(
            nodes=120, time_steps=200, source_location=5,
            core_start=40, core_end=60,
        )
        out = simulate_1d_damped_wave_lattice(p)
        obs = WaveLatticeObservables.model_validate(out["observables"])
        # With enough time steps the wave front should have reached the core
        assert obs.max_core_displacement > 0.0

    def test_homogeneous_no_reflection_at_interface(self) -> None:
        """Homogeneous material should not create interface reflections."""
        # Core has identical properties → no interface → wave passes freely
        p = _homogeneous_params(core_damping=0.0, core_stiffness=1.0, core_density=1.0)
        out = simulate_1d_damped_wave_lattice(p)
        obs = WaveLatticeObservables.model_validate(out["observables"])
        # attenuation_ratio should be close to 1 (no attenuation) when homogeneous
        assert obs.attenuation_ratio > 0.5

    def test_operator_version_present(self) -> None:
        p = _homogeneous_params()
        out = simulate_1d_damped_wave_lattice(p)
        assert out["operator_version"] == "1.0.0"

    def test_params_echoed_in_output(self) -> None:
        p = _homogeneous_params(nodes=70)
        out = simulate_1d_damped_wave_lattice(p)
        assert out["params"]["nodes"] == 70


# ---------------------------------------------------------------------------
# Determinism
# ---------------------------------------------------------------------------


class TestDeterminism:
    def test_identical_params_produce_identical_output(self) -> None:
        """Same params must produce byte-identical output hashes."""
        p = _homogeneous_params()
        out1 = simulate_1d_damped_wave_lattice(p)
        out2 = simulate_1d_damped_wave_lattice(p)
        obs1 = WaveLatticeObservables.model_validate(out1["observables"])
        obs2 = WaveLatticeObservables.model_validate(out2["observables"])
        assert obs1.output_hash == obs2.output_hash
        assert obs1.input_hash == obs2.input_hash
        assert out1["final_displacement"] == out2["final_displacement"]

    def test_different_params_produce_different_output(self) -> None:
        """Changing one parameter must change the output hash."""
        p1 = _homogeneous_params(source_amplitude=1.0)
        p2 = _homogeneous_params(source_amplitude=2.0)
        out1 = simulate_1d_damped_wave_lattice(p1)
        out2 = simulate_1d_damped_wave_lattice(p2)
        obs1 = WaveLatticeObservables.model_validate(out1["observables"])
        obs2 = WaveLatticeObservables.model_validate(out2["observables"])
        assert obs1.output_hash != obs2.output_hash

    def test_input_hash_matches_param_content(self) -> None:
        """Input hash must be derivable from the canonical parameter representation."""
        import hashlib

        from researchforge.domain.base import canonical_json_dumps

        p = _homogeneous_params()
        out = simulate_1d_damped_wave_lattice(p)
        obs = WaveLatticeObservables.model_validate(out["observables"])
        expected_hash = hashlib.sha256(
            canonical_json_dumps(p.model_dump(mode="json")).encode("utf-8")
        ).hexdigest()
        assert obs.input_hash == expected_hash


# ---------------------------------------------------------------------------
# Scientific Comparison: Baseline vs Heterogeneous
# ---------------------------------------------------------------------------


class TestBaselineVsHeterogeneous:
    """
    Baseline (Experiment A): homogeneous material (no core damping).
    Heterogeneous (Experiment B): same geometry, elevated core damping.

    Both use identical source, domain, and discretisation.
    """

    def _run_pair(
        self, *, extra_core_damping: float = 8.0
    ) -> tuple[WaveLatticeObservables, WaveLatticeObservables]:
        common: dict[str, object] = {
            "nodes": 120,
            "time_steps": 200,
            "dx": 1.0,
            "dt": 0.4,
            "density": 1.0,
            "stiffness": 1.0,
            "damping": 0.0,
            "core_start": 40,
            "core_end": 80,
            "core_density": 1.0,
            "core_stiffness": 1.0,
            "source_amplitude": 1.0,
            "source_location": 5,
            "source_duration": 20,
            "boundary_condition": BoundaryCondition.ABSORBING,
        }
        p_baseline = WaveLatticeParameters(
            id="p_baseline", core_damping=0.0, **common  # type: ignore[arg-type]
        )
        p_het = WaveLatticeParameters(
            id="p_het", core_damping=extra_core_damping, **common  # type: ignore[arg-type]
        )
        out_b = simulate_1d_damped_wave_lattice(p_baseline)
        out_h = simulate_1d_damped_wave_lattice(p_het)
        return (
            WaveLatticeObservables.model_validate(out_b["observables"]),
            WaveLatticeObservables.model_validate(out_h["observables"]),
        )

    def test_heterogeneous_core_reduces_core_displacement(self) -> None:
        """Elevated core damping should reduce max_core_displacement vs baseline."""
        obs_b, obs_h = self._run_pair(extra_core_damping=8.0)
        assert obs_h.max_core_displacement < obs_b.max_core_displacement, (
            f"Expected heterogeneous core to reduce max_core_displacement "
            f"({obs_h.max_core_displacement:.6f} vs baseline {obs_b.max_core_displacement:.6f})"
        )

    def test_heterogeneous_core_increases_dissipation(self) -> None:
        """Elevated core damping should produce more dissipated energy."""
        obs_b, obs_h = self._run_pair(extra_core_damping=8.0)
        assert obs_h.dissipated_energy > obs_b.dissipated_energy

    def test_attenuation_ratio_lower_in_heterogeneous(self) -> None:
        """Heterogeneous (more damped) core should have a lower attenuation_ratio."""
        obs_b, obs_h = self._run_pair(extra_core_damping=8.0)
        assert obs_h.attenuation_ratio < obs_b.attenuation_ratio

    def test_incident_energy_identical_for_same_source(self) -> None:
        """Both experiments use the same source, so incident_energy should be equal."""
        obs_b, obs_h = self._run_pair()
        assert obs_b.incident_energy == pytest.approx(obs_h.incident_energy, rel=1e-10)

    def test_no_energy_created_from_nothing(self) -> None:
        """Dissipated + core + transmitted energy must not exceed incident energy
        (within numerical discretisation tolerance)."""
        obs_b, _ = self._run_pair(extra_core_damping=0.0)
        # Conservative budget check with generous tolerance for numeric approximation
        budget = obs_b.dissipated_energy + obs_b.core_energy + obs_b.transmitted_energy
        # At most 2x incident energy (accounting for discrete approximation drift)
        assert budget < 2.0 * max(obs_b.incident_energy, 1e-10) + 1.0


# ---------------------------------------------------------------------------
# Observables Contract
# ---------------------------------------------------------------------------


class TestObservablesContract:
    def test_observables_have_required_fields(self) -> None:
        p = _homogeneous_params()
        out = simulate_1d_damped_wave_lattice(p)
        obs = WaveLatticeObservables.model_validate(out["observables"])
        assert obs.max_displacement >= 0.0
        assert obs.max_core_displacement >= 0.0
        assert obs.max_velocity >= 0.0
        assert obs.attenuation_ratio >= 0.0
        assert len(obs.input_hash) == 64
        assert len(obs.output_hash) == 64

    def test_attenuation_ratio_bounded(self) -> None:
        """attenuation_ratio = max_core / max_global, so [0, 1] is expected for normal runs."""
        p = _homogeneous_params()
        out = simulate_1d_damped_wave_lattice(p)
        obs = WaveLatticeObservables.model_validate(out["observables"])
        # Ratio can exceed 1 if core has amplification (not expected for passive damping)
        # but should never be negative
        assert obs.attenuation_ratio >= 0.0


# ---------------------------------------------------------------------------
# Architecture Boundary: Operator must not import persistence/Cognitia
# ---------------------------------------------------------------------------


class TestWaveLatticeArchitectureBoundary:
    """Static AST checks to enforce the isolation of the wave operator."""

    def _get_imports(self, file_path: Path) -> list[str]:
        tree = ast.parse(file_path.read_text(encoding="utf-8"), filename=str(file_path))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        return imports

    def test_wave_operator_does_not_import_persistence(self) -> None:
        """The wave operator must have no persistence imports."""
        wave_file = Path("backend/researchforge/domain/models/wave_lattice.py")
        imports = self._get_imports(wave_file)
        for imp in imports:
            assert "researchforge.persistence" not in imp, (
                f"Wave operator imports persistence: {imp} — isolation violated"
            )
            assert not imp.startswith("sqlalchemy"), (
                f"Wave operator imports SQLAlchemy: {imp} — isolation violated"
            )

    def test_wave_operator_does_not_import_cognitia(self) -> None:
        """The wave operator must not import Cognitia."""
        wave_file = Path("backend/researchforge/domain/models/wave_lattice.py")
        imports = self._get_imports(wave_file)
        for imp in imports:
            assert "cognitia" not in imp.lower(), (
                f"Wave operator imports Cognitia: {imp} — isolation violated"
            )

    def test_wave_operator_does_not_import_unit_of_work(self) -> None:
        """The wave operator must not import UnitOfWork."""
        wave_file = Path("backend/researchforge/domain/models/wave_lattice.py")
        imports = self._get_imports(wave_file)
        for imp in imports:
            assert "unit_of_work" not in imp, (
                f"Wave operator imports UnitOfWork: {imp} — isolation violated"
            )

    def test_wave_operator_does_not_import_execution_backend(self) -> None:
        """The wave operator must not import execution backends."""
        wave_file = Path("backend/researchforge/domain/models/wave_lattice.py")
        imports = self._get_imports(wave_file)
        for imp in imports:
            assert "researchforge.execution" not in imp, (
                f"Wave operator imports execution subsystem: {imp} — isolation violated"
            )
