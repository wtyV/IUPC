"""Complete multi-objective optimization formulation.

Defines the full objective function for ascent trajectory optimization,
combining:
  - Terminal state accuracy (altitude, speed, flight path angle)
  - Path constraints (max dynamic pressure, max acceleration, max heating)
  - Control effort (minimize pitch rate, smoothness)
  - Mass optimization (maximize payload to orbit)

The full multi-objective cost function:

  J = w1 * J_orbit + w2 * J_q + w3 * J_accel + w4 * J_control + w5 * J_mass

where:
  J_orbit  = (h_f - h*)^2 / sigma_h^2 + (v_f - v*)^2 / sigma_v^2 + gamma_f^2 / sigma_gamma^2
  J_q      = max(0, q_max - q_limit)^2 / sigma_q^2
  J_accel  = max(0, n_max - n_limit)^2 / sigma_n^2
  J_control = integral(dphi/dt)^2 dt  (control smoothness)
  J_mass   = -mass_final / mass_initial  (maximize final mass)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

from ascent_full import (
    AscentStateFull,
    PitchProgramFull,
    VehicleModel,
    cz10_lunar_vehicle,
    simulate_ascent_full,
)
from constants import MU_EARTH, R_EARTH_MEAN
from gravity_full import GravityConfig


@dataclass
class OptimizationResult:
    """Complete optimization result for one candidate."""
    # Design variables
    pitch_end_time_s: float
    final_pitch_deg: float
    shape_exponent: float
    vertical_time_s: float

    # Terminal state
    terminal_altitude_km: float
    terminal_inertial_speed_m_s: float
    terminal_fpa_deg: float
    terminal_mass_kg: float
    payload_fraction: float

    # Path constraints
    max_dynamic_pressure_kPa: float
    max_mach_number: float
    max_acceleration_g: float
    max_heating_rate_kW_m2: float

    # Stage performance
    stage_separation_times: list[float]
    burnout_time_s: float

    # Objective components
    orbit_error_score: float
    q_penalty: float
    accel_penalty: float
    heating_penalty: float
    mass_score: float

    # Total score (lower is better)
    total_score: float

    # Feasibility
    is_feasible: bool


@dataclass
class OptimizationConfig:
    """Configuration for the ascent optimization problem."""
    # Target orbit
    target_altitude_km: float = 300.0
    target_eccentricity: float = 0.0  # circular

    # Constraint limits
    max_q_kPa: float = 60.0           # maximum dynamic pressure
    max_accel_g: float = 6.0          # maximum axial acceleration
    max_mach: float = 25.0            # maximum Mach number
    max_heating_kW_m2: float = 500.0  # stagnation point heating rate

    # Objective weights
    w_orbit: float = 10.0
    w_q: float = 5.0
    w_accel: float = 3.0
    w_heating: float = 2.0
    w_mass: float = 1.0
    w_control: float = 0.1

    # Scoring normalization
    sigma_altitude_km: float = 5.0      # 1-sigma altitude error
    sigma_speed_m_s: float = 50.0       # 1-sigma speed error
    sigma_fpa_deg: float = 0.5          # 1-sigma FPA error
    sigma_q_kPa: float = 20.0           # q penalty scaling
    sigma_accel_g: float = 1.0          # acceleration penalty scaling
    sigma_heating_kW_m2: float = 100.0  # heating penalty scaling


def evaluate_ascent_objective(
    design_vars: list[float],
    config: OptimizationConfig | None = None,
    vehicle: VehicleModel | None = None,
    gravity_config: GravityConfig | None = None,
    verbose: bool = False,
) -> OptimizationResult:
    """Evaluate the full ascent objective function for a candidate design.

    Parameters
    ----------
    design_vars : list[float]
        [pitch_end_time_s, final_pitch_deg, shape_exponent, vertical_time_s]
        Respective bounds: [200, 400], [2, 20], [0.8, 2.0], [5, 20]

    Returns
    -------
    OptimizationResult
    """
    if config is None:
        config = OptimizationConfig()
    if vehicle is None:
        vehicle = cz10_lunar_vehicle()
    if gravity_config is None:
        gravity_config = GravityConfig(use_j2=True, use_j3=True, use_j4=True)

    # Unpack design variables
    pitch_end = max(200.0, min(400.0, design_vars[0]))
    final_pitch = max(2.0, min(20.0, design_vars[1]))
    shape = max(0.8, min(2.0, design_vars[2]))
    vertical_t = max(5.0, min(20.0, design_vars[3])) if len(design_vars) > 3 else 12.0

    # Build pitch program
    pitch_prog = PitchProgramFull(
        vertical_time_s=vertical_t,
        pitch_end_time_s=pitch_end,
        final_pitch_deg=final_pitch,
        shape_exponent=shape,
    )

    # Run simulation
    try:
        trajectory = simulate_ascent_full(
            vehicle=vehicle,
            pitch_program=pitch_prog,
            dt_s=0.25,
            gravity_config=gravity_config,
            max_altitude_m=config.target_altitude_km * 1000.0 + 50000.0,
        )
    except Exception as e:
        if verbose:
            print(f"  Simulation failed: {e}")
        # Return a bad score
        return OptimizationResult(
            pitch_end_time_s=pitch_end,
            final_pitch_deg=final_pitch,
            shape_exponent=shape,
            vertical_time_s=vertical_t,
            terminal_altitude_km=0.0,
            terminal_inertial_speed_m_s=0.0,
            terminal_fpa_deg=90.0,
            terminal_mass_kg=0.0,
            payload_fraction=0.0,
            max_dynamic_pressure_kPa=999.0,
            max_mach_number=99.0,
            max_acceleration_g=99.0,
            max_heating_rate_kW_m2=999.0,
            stage_separation_times=[],
            burnout_time_s=0.0,
            orbit_error_score=1e9,
            q_penalty=1e9,
            accel_penalty=1e9,
            heating_penalty=1e9,
            mass_score=1e9,
            total_score=1e12,
            is_feasible=False,
        )

    if not trajectory:
        return _bad_result(pitch_end, final_pitch, shape, vertical_t)

    # ── Find injection point ─────────────────────────────────────────────
    # Strategy: find the point where the vehicle first reaches the target
    # altitude with velocity close to circular. This is the natural
    # orbit injection point.
    target_alt_m = config.target_altitude_km * 1000.0
    r_target = R_EARTH_MEAN + target_alt_m
    v_target = math.sqrt(MU_EARTH / r_target)

    injection_point = None
    # First preference: point where altitude >= target and speed >= 95% of circular
    for s in trajectory:
        if s.altitude_m >= target_alt_m and s.inertial_speed_m_s >= 0.95 * v_target:
            injection_point = s
            break

    # Second preference: first point above target altitude
    if injection_point is None:
        for s in trajectory:
            if s.altitude_m >= target_alt_m:
                injection_point = s
                break

    # Fallback: terminal state
    if injection_point is None:
        injection_point = trajectory[-1]

    terminal = injection_point

    # ── Terminal state computation ───────────────────────────────────────

    alt_km = terminal.altitude_m / 1000.0
    speed = terminal.inertial_speed_m_s
    fpa = terminal.flight_path_angle_deg
    mass = terminal.mass_kg

    # Target orbit quantities
    h_star = config.target_altitude_km
    r_target = R_EARTH_MEAN + h_star * 1000.0
    v_star = math.sqrt(MU_EARTH / r_target)

    # ── Orbit injection error ────────────────────────────────────────────

    alt_error = (alt_km - h_star) / config.sigma_altitude_km
    speed_error = (speed - v_star) / config.sigma_speed_m_s
    fpa_error = fpa / config.sigma_fpa_deg

    J_orbit = alt_error**2 + speed_error**2 + fpa_error**2

    # ── Path constraints ─────────────────────────────────────────────────

    max_q = max(s.dynamic_pressure_Pa / 1000.0 for s in trajectory)  # kPa
    max_mach = max(s.mach_number for s in trajectory)
    max_accel = max(s.axial_acceleration_g for s in trajectory)

    # Stagnation point heating rate (Sutton-Graves correlation)
    # q_dot = k * sqrt(rho / R_n) * V^3
    # where k ≈ 1.83e-4 (SI), R_n ≈ 1.0 m (nose radius)
    # Simplified: q_dot_est = 1.83e-4 * sqrt(rho) * V^3 (kW/m^2)
    max_heating = 0.0
    for s in trajectory:
        if s.density_kg_m3 > 0 and s.relative_speed_m_s > 1000:
            heating = 1.83e-4 * math.sqrt(s.density_kg_m3 / 1.0) * (s.relative_speed_m_s ** 3)
            max_heating = max(max_heating, heating)

    # Penalty values (zero if within limits)
    q_excess = max(0.0, max_q - config.max_q_kPa)
    accel_excess = max(0.0, max_accel - config.max_accel_g)
    heating_excess = max(0.0, max_heating - config.max_heating_kW_m2)

    J_q = (q_excess / config.sigma_q_kPa) ** 2
    J_accel = (accel_excess / config.sigma_accel_g) ** 2
    J_heating = (heating_excess / config.sigma_heating_kW_m2) ** 2

    # ── Control smoothness ───────────────────────────────────────────────
    # Approximate integral of (dphi/dt)^2
    control_effort = 0.0
    for i in range(1, len(trajectory)):
        dpitch = trajectory[i].pitch_angle_deg - trajectory[i-1].pitch_angle_deg
        dt = trajectory[i].time_s - trajectory[i-1].time_s
        if dt > 0:
            control_effort += (dpitch / dt) ** 2 * dt
    J_control = control_effort / 1000.0

    # ── Mass score (negative final mass to reward higher payload) ────────
    payload_fraction = (mass - sum(s.dry_mass_kg for s in vehicle.stages)) / (
        sum(s.propellant_mass_kg + s.dry_mass_kg for s in vehicle.stages) + vehicle.payload_mass_kg
    )
    J_mass = -payload_fraction

    # ── Total weighted score ─────────────────────────────────────────────

    total = (
        config.w_orbit * J_orbit
        + config.w_q * J_q
        + config.w_accel * J_accel
        + config.w_heating * J_heating
        + config.w_mass * J_mass
        + config.w_control * J_control
    )

    # ── Feasibility ──────────────────────────────────────────────────────

    feasible = (
        abs(alt_km - h_star) < 20.0
        and abs(speed - v_star) < 200.0
        and abs(fpa) < 5.0
        and max_q <= config.max_q_kPa
        and max_accel <= config.max_accel_g
        and max_heating <= config.max_heating_kW_m2
    )

    # ── Stage separation times ───────────────────────────────────────────
    stage_times: list[float] = []
    current_stage = ""
    for s in trajectory:
        if s.stage_name != current_stage:
            stage_times.append(s.time_s)
            current_stage = s.stage_name

    return OptimizationResult(
        pitch_end_time_s=pitch_end,
        final_pitch_deg=final_pitch,
        shape_exponent=shape,
        vertical_time_s=vertical_t,
        terminal_altitude_km=alt_km,
        terminal_inertial_speed_m_s=speed,
        terminal_fpa_deg=fpa,
        terminal_mass_kg=mass,
        payload_fraction=payload_fraction,
        max_dynamic_pressure_kPa=max_q,
        max_mach_number=max_mach,
        max_acceleration_g=max_accel,
        max_heating_rate_kW_m2=max_heating,
        stage_separation_times=stage_times,
        burnout_time_s=trajectory[-1].time_s,
        orbit_error_score=J_orbit,
        q_penalty=J_q,
        accel_penalty=J_accel,
        heating_penalty=J_heating,
        mass_score=J_mass,
        total_score=total,
        is_feasible=feasible,
    )


def make_ascent_objective(
    config: OptimizationConfig | None = None,
    gravity_config: GravityConfig | None = None,
    verbose: bool = False,
):
    """Create an objective function for use with optimizers.

    Returns a callable f(design_vars: list[float]) -> float suitable
    for PSO, GA, and SA optimizers.
    """
    if config is None:
        config = OptimizationConfig()
    if gravity_config is None:
        gravity_config = GravityConfig(use_j2=True, use_j3=True, use_j4=True)

    def objective(design_vars: list[float]) -> float:
        result = evaluate_ascent_objective(
            design_vars, config=config,
            gravity_config=gravity_config, verbose=verbose,
        )
        return result.total_score

    return objective


def _bad_result(pitch_end, final_pitch, shape, vertical_t) -> OptimizationResult:
    """Return a worst-case result for failed simulations."""
    return OptimizationResult(
        pitch_end_time_s=pitch_end,
        final_pitch_deg=final_pitch,
        shape_exponent=shape,
        vertical_time_s=vertical_t,
        terminal_altitude_km=0.0, terminal_inertial_speed_m_s=0.0,
        terminal_fpa_deg=90.0, terminal_mass_kg=0.0, payload_fraction=0.0,
        max_dynamic_pressure_kPa=999.0, max_mach_number=99.0,
        max_acceleration_g=99.0, max_heating_rate_kW_m2=999.0,
        stage_separation_times=[], burnout_time_s=0.0,
        orbit_error_score=1e9, q_penalty=1e9, accel_penalty=1e9,
        heating_penalty=1e9, mass_score=1e9, total_score=1e12,
        is_feasible=False,
    )


def compare_gravity_models(
    design_vars: list[float] | None = None,
) -> dict[str, OptimizationResult]:
    """Compare ascent results with different gravity model fidelities.

    Uses the same pitch program and compares the injection state
    at the first altitude crossing of the target.
    """
    if design_vars is None:
        design_vars = [305.0, 10.0, 1.4, 12.0]  # baseline

    results = {}
    configs = {
        "spherical": GravityConfig(use_j2=False, use_j3=False, use_j4=False),
        "J2_only": GravityConfig(use_j2=True, use_j3=False, use_j4=False),
        "J2_J3_J4": GravityConfig(use_j2=True, use_j3=True, use_j4=True),
    }

    # Use fixed config for consistent injection detection
    opt_config = OptimizationConfig(target_altitude_km=300.0)

    for name, gc in configs.items():
        result = evaluate_ascent_objective(design_vars, config=opt_config, gravity_config=gc)
        results[name] = result

    return results
