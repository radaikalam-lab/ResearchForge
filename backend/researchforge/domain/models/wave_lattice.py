"""
1-D Heterogeneous Damped-Wave Reference Operator (Phase 2.2).

Numerical contract and reference implementation for the deterministic
1-D finite-difference wave equation on a heterogeneous lattice:

    rho(x) * u_tt + gamma(x) * u_t = d/dx[ E(x) * du/dx ] + source(x, t)

where:
    u(x, t)  : displacement field [m]
    rho(x)   : mass density        [kg/m³]
    E(x)     : elastic stiffness   [Pa]
    gamma(x) : viscous damping     [kg/(m³·s)]
    source   : external forcing    [N/m³]

Local wave speed: c(x) = sqrt(E(x) / rho(x))

Discretisation (explicit central differences):
    Temporal : u_tt ≈ (u[t+1] - 2u[t] + u[t-1]) / dt²
    Temporal : u_t  ≈ (u[t+1] - u[t-1]) / (2·dt)
    Spatial  : d/dx[E du/dx] ≈ (E[i+½]·(u[i+1]-u[i]) - E[i-½]·(u[i]-u[i-1])) / dx²

Stability (CFL):  dt ≤ dx / max(c)   (checked at construction time)

Boundary conditions:
    DIRICHLET : u = 0 at both ends (absorbing / fixed wall)
    ABSORBING : one-way absorbing boundary at x = 0 (default) and x = L

Units are consistent within the normalisation convention of the caller.
All parameters must be supplied explicitly; no hidden defaults affect results.

Determinism guarantee:
    For identical (WaveLatticeParameters, operator version), the output
    dict is byte-for-byte identical across runs on the same CPU architecture.
    The operator is purely functional and contains no mutable state.
"""

from __future__ import annotations

import hashlib
from enum import StrEnum
from typing import Any

import numpy as np
from pydantic import Field, field_validator, model_validator

from researchforge.domain.base import DomainModel, canonical_json_dumps

# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class BoundaryCondition(StrEnum):
    """Supported boundary conditions for the wave lattice."""

    DIRICHLET = "DIRICHLET"  # Fixed-wall: u = 0 at x=0 and x=L
    ABSORBING = "ABSORBING"  # One-way absorbing / transparent (Mur 1st-order)


# ---------------------------------------------------------------------------
# Input contract
# ---------------------------------------------------------------------------


class WaveLatticeParameters(DomainModel):
    """
    Fully explicit input contract for the 1-D heterogeneous damped-wave solver.

    All physical quantities are dimensionless unless the caller establishes
    a consistent unit system.  The operator is unit-agnostic.

    Stability condition (CFL):  dt <= dx / max_wave_speed
    This is checked at construction time; invalid parameters raise ValueError.
    """

    id: str = Field(default="", description="Parameter set identifier")

    # Discretisation
    nodes: int = Field(default=200, ge=4, description="Number of spatial grid points")
    time_steps: int = Field(default=500, ge=2, description="Number of time steps to integrate")
    dx: float = Field(default=1.0, gt=0.0, description="Spatial grid spacing")
    dt: float = Field(default=0.4, gt=0.0, description="Temporal time step")

    # Background (homogeneous) material properties
    density: float = Field(default=1.0, gt=0.0, description="Background mass density rho")
    stiffness: float = Field(default=1.0, gt=0.0, description="Background elastic stiffness E")
    damping: float = Field(default=0.0, ge=0.0, description="Background viscous damping gamma")

    # Heterogeneous core region  (indices: core_start <= i < core_end)
    core_start: int = Field(default=80, ge=0, description="First node index of core region")
    core_end: int = Field(default=120, ge=1, description="One-past-last index of core region")
    core_density: float = Field(default=1.0, gt=0.0, description="Core mass density rho_core")
    core_stiffness: float = Field(default=1.0, gt=0.0, description="Core elastic stiffness E_core")
    core_damping: float = Field(default=5.0, ge=0.0, description="Core viscous damping gamma_core")

    # Source / excitation
    source_amplitude: float = Field(default=1.0, description="Peak amplitude of incident pulse")
    source_location: int = Field(default=10, ge=0, description="Source node index")
    source_duration: int = Field(
        default=20, ge=1, description="Duration of source excitation in time steps"
    )

    # Numerics
    boundary_condition: BoundaryCondition = Field(
        default=BoundaryCondition.ABSORBING,
        description="Boundary condition applied at domain edges",
    )

    # Metadata (not used in computation; carried for provenance)
    experiment_label: str = Field(default="", description="Optional human-readable experiment label")
    computation_version: str = Field(default="1.0.0", description="Operator semantic version")

    @field_validator("core_end")
    @classmethod
    def core_end_gt_core_start(cls, v: int) -> int:
        return v  # cross-field validated below

    @model_validator(mode="after")
    def validate_geometry_and_stability(self) -> WaveLatticeParameters:
        # Core geometry
        if self.core_start >= self.core_end:
            raise ValueError(
                f"core_start ({self.core_start}) must be strictly less than core_end ({self.core_end})"
            )
        if self.core_end > self.nodes:
            raise ValueError(
                f"core_end ({self.core_end}) exceeds number of nodes ({self.nodes})"
            )
        if self.source_location >= self.nodes:
            raise ValueError(
                f"source_location ({self.source_location}) >= nodes ({self.nodes})"
            )
        if self.source_location >= self.core_start:
            pass  # Valid but unusual — caller's responsibility

        # CFL stability check: dt <= dx / max(c)
        c_bg = (self.stiffness / self.density) ** 0.5
        c_core = (self.core_stiffness / self.core_density) ** 0.5
        c_max = max(c_bg, c_core)
        cfl_limit = self.dx / c_max
        if self.dt > cfl_limit + 1e-12:
            raise ValueError(
                f"CFL stability violation: dt={self.dt:.4f} > dx/c_max={cfl_limit:.4f} "
                f"(c_bg={c_bg:.4f}, c_core={c_core:.4f}). "
                "Reduce dt or increase dx to satisfy numerical stability."
            )
        return self


# ---------------------------------------------------------------------------
# Output contract
# ---------------------------------------------------------------------------


class WaveLatticeObservables(DomainModel):
    """
    Deterministic observables produced by the 1-D damped-wave solver.

    Energy quantities are computed from the discrete numerical approximation.
    They are internally consistent within that approximation; they are NOT
    guaranteed to satisfy exact continuum energy conservation beyond the
    discretisation error.

    All displacement/velocity quantities are in the same units as the input;
    energy quantities carry units of [mass·length²/time²] relative to the
    caller's unit system.

    Limitation: attenuation_ratio is defined as
        max_core_displacement / max_incident_displacement
    It is a spatial-peak ratio, not a rigorous energy transmission coefficient.
    A value of 0 means the core was completely undisturbed; a value of 1 means
    no attenuation occurred relative to the incident peak.
    """

    id: str = Field(default="", description="Observables identifier")
    max_displacement: float = Field(description="Maximum absolute displacement across all x, t")
    max_core_displacement: float = Field(
        description="Maximum absolute displacement within the core region [core_start, core_end)"
    )
    max_velocity: float = Field(description="Maximum absolute velocity (finite-difference u_t) across all x, t")
    incident_energy: float = Field(
        description="Approximate energy injected by the source (discrete trapezoidal integral of source work)"
    )
    reflected_energy: float = Field(
        description="Approximate reflected energy at left boundary (kinetic proxy at x=0)"
    )
    transmitted_energy: float = Field(
        description="Approximate transmitted energy at right boundary (kinetic proxy at x=N-1)"
    )
    dissipated_energy: float = Field(
        description="Estimated dissipated energy via damping work (sum of gamma * u_t^2 * dt * dx)"
    )
    core_energy: float = Field(
        description="Total discrete mechanical energy (kinetic + elastic) within core at final time step"
    )
    attenuation_ratio: float = Field(
        description="max_core_displacement / max_incident_displacement; 0 = full attenuation, 1 = no attenuation"
    )
    input_hash: str = Field(description="SHA-256 of canonical parameter JSON (determinism verification)")
    output_hash: str = Field(description="SHA-256 of canonical output JSON (determinism verification)")


# ---------------------------------------------------------------------------
# Solver
# ---------------------------------------------------------------------------

_OPERATOR_VERSION = "1.0.0"


def simulate_1d_damped_wave_lattice(
    params: WaveLatticeParameters,
) -> dict[str, Any]:
    """
    Deterministic explicit finite-difference solver for the 1-D heterogeneous
    damped-wave equation.

    Returns a dict containing:
        "observables"    : WaveLatticeObservables (as dict)
        "final_displacement" : list[float] — spatial displacement at final time step
        "final_velocity"     : list[float] — spatial velocity at final time step
        "params"             : dict — echo of input parameters
        "operator_version"   : str

    The function is pure: it has no side effects, no randomness (unless a
    stochastic source were added in a future version), no I/O, no database
    access, no persistence access, no Cognitia access.
    """
    N = params.nodes
    T = params.time_steps
    dx = params.dx
    dt = params.dt

    # --- Material fields ---
    rho = np.full(N, params.density)
    E = np.full(N, params.stiffness)
    gam = np.full(N, params.damping)

    cs = params.core_start
    ce = params.core_end
    rho[cs:ce] = params.core_density
    E[cs:ce] = params.core_stiffness
    gam[cs:ce] = params.core_damping

    # Half-node stiffness (harmonic mean between adjacent cells)
    # E_half[i] = stiffness at i+½ interface
    E_half = 2.0 * E[:-1] * E[1:] / (E[:-1] + E[1:])  # shape (N-1,)

    # --- Pre-compute update coefficients ---
    # Equation of motion:
    #   rho[i] * (u[t+1,i] - 2u[t,i] + u[t-1,i]) / dt²
    # + gam[i] * (u[t+1,i] - u[t-1,i]) / (2*dt)
    # = [E_half[i]*(u[t,i+1]-u[t,i]) - E_half[i-1]*(u[t,i]-u[t,i-1])] / dx²
    # + source[t,i]
    #
    # Solve for u[t+1,i]:
    #   A[i] = rho[i]/dt² + gam[i]/(2*dt)
    #   B[i] = 2*rho[i]/dt²
    #   C[i] = rho[i]/dt² - gam[i]/(2*dt)
    #   u[t+1,i] = (1/A[i]) * (B[i]*u[t,i] - C[i]*u[t-1,i]
    #              + (E_half[i]*u[t,i+1] - (E_half[i]+E_half[i-1])*u[t,i] + E_half[i-1]*u[t,i-1]) / dx²
    #              + source[t,i])

    A = rho / dt**2 + gam / (2.0 * dt)  # (N,)
    B = 2.0 * rho / dt**2              # (N,)
    C = rho / dt**2 - gam / (2.0 * dt)  # (N,)

    # --- State arrays: u_prev = u[t-1], u_curr = u[t] ---
    u_prev = np.zeros(N)
    u_curr = np.zeros(N)

    # --- Tracking accumulators ---
    max_disp = 0.0
    max_core_disp = 0.0

    # Left-boundary flux accumulator (reflected energy proxy)
    flux_left = 0.0
    # Right-boundary flux accumulator (transmitted energy proxy)
    flux_right = 0.0
    # Damping dissipation accumulator
    dissipated = 0.0
    # Source work (incident energy proxy)
    source_work = 0.0

    # --- Mur absorbing boundary coefficients ---
    c_left = (E[0] / rho[0]) ** 0.5
    c_right = (E[N - 1] / rho[N - 1]) ** 0.5
    mur_left = (c_left * dt - dx) / (c_left * dt + dx)
    mur_right = (c_right * dt - dx) / (c_right * dt + dx)

    # --- Time-stepping ---
    for t in range(T):
        u_next = np.empty(N)

        # Interior nodes  (i = 1 ... N-2)
        i = np.arange(1, N - 1)
        stiffness_term = (
            E_half[i] * (u_curr[i + 1] - u_curr[i])
            - E_half[i - 1] * (u_curr[i] - u_curr[i - 1])
        ) / dx**2

        # Source forcing: Gaussian-smoothed ramp for nodes at source_location
        src_val = 0.0
        if t < params.source_duration:
            phase = (t / params.source_duration) * np.pi
            src_val = params.source_amplitude * np.sin(phase) ** 2

        source_field = np.zeros(N)
        if 0 < params.source_location < N - 1:
            source_field[params.source_location] = src_val
        # If source_location is at a boundary, it will be overwritten by BC below

        # Interior update
        u_next[i] = (
            B[i] * u_curr[i]
            - C[i] * u_prev[i]
            + stiffness_term
            + source_field[i]
        ) / A[i]

        # --- Boundary conditions ---
        if params.boundary_condition == BoundaryCondition.DIRICHLET:
            u_next[0] = 0.0
            u_next[N - 1] = 0.0
        else:  # ABSORBING (Mur 1st-order)
            u_next[0] = u_curr[1] + mur_left * (u_next[1] - u_curr[0])
            u_next[N - 1] = u_curr[N - 2] + mur_right * (u_next[N - 2] - u_curr[N - 1])

        # --- Accumulate observables ---
        abs_curr = np.abs(u_curr)
        max_disp = max(max_disp, float(np.max(abs_curr)))
        max_core_disp = max(max_core_disp, float(np.max(abs_curr[cs:ce])))

        # Velocity proxy: (u_next - u_prev) / (2*dt)
        if t > 0:
            vel = (u_next - u_prev) / (2.0 * dt)
            # Boundary kinetic energy flux (proxy for reflection/transmission)
            flux_left += 0.5 * rho[0] * vel[0] ** 2 * dx * dt
            flux_right += 0.5 * rho[N - 1] * vel[N - 1] ** 2 * dx * dt
            # Viscous dissipation rate: gam * u_t^2
            dissipated += float(np.sum(gam * vel**2) * dx * dt)

        # Source work
        source_work += float(np.sum(source_field * u_curr)) * dx * dt

        # Advance
        u_prev = u_curr.copy()
        u_curr = u_next.copy()

    # --- Final-step velocity and energy ---
    u_final = u_curr
    vel_final = (u_final - u_prev) / dt  # backward difference at last step
    max_vel = float(np.max(np.abs(vel_final)))

    # Core energy at final step (kinetic + elastic)
    kin_core = float(np.sum(0.5 * rho[cs:ce] * vel_final[cs:ce] ** 2)) * dx
    # Elastic energy in core using central stiffness (approximate)
    grad_u = np.diff(u_final) / dx  # shape (N-1,)
    elastic_core = float(np.sum(0.5 * E[cs : ce - 1] * grad_u[cs : ce - 1] ** 2)) * dx
    core_energy = kin_core + elastic_core

    # Attenuation ratio
    if max_disp > 0.0:
        attenuation_ratio = max_core_disp / max_disp
    else:
        attenuation_ratio = 0.0

    # --- Hashing for determinism verification ---
    param_dict = params.model_dump(mode="json")
    input_hash = hashlib.sha256(
        canonical_json_dumps(param_dict).encode("utf-8")
    ).hexdigest()

    output_payload: dict[str, Any] = {
        "max_displacement": max_disp,
        "max_core_displacement": max_core_disp,
        "max_velocity": max_vel,
        "incident_energy": source_work,
        "reflected_energy": flux_left,
        "transmitted_energy": flux_right,
        "dissipated_energy": dissipated,
        "core_energy": core_energy,
        "attenuation_ratio": attenuation_ratio,
    }
    output_hash = hashlib.sha256(
        canonical_json_dumps(output_payload).encode("utf-8")
    ).hexdigest()

    observables = WaveLatticeObservables(
        id=f"obs_{input_hash[:12]}",
        input_hash=input_hash,
        output_hash=output_hash,
        **output_payload,
    )

    return {
        "observables": observables.model_dump(),
        "final_displacement": u_final.tolist(),
        "final_velocity": vel_final.tolist(),
        "params": param_dict,
        "operator_version": _OPERATOR_VERSION,
    }
