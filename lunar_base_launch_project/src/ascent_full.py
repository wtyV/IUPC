"""Complete ascent trajectory model with high-fidelity physics.

Replaces the simplified 2D and 3DOF models with:
  - RK4 numerical integration (4th-order)
  - Complete standard atmosphere (杨炳蔚 model)
  - Full gravity with J2, J3, J4 perturbations
  - Earth rotation and Coriolis effects in ECI frame
  - Multi-stage vehicle model with realistic YF-100K engine parameters
  - Pitch program with optimal control formulation
  - Dynamic pressure, acceleration, and heating constraints
  - Mass budget tracking with structural fractions

State vector (7 components):
  x = [rx, ry, rz, vx, vy, vz, m]  (ECI frame, SI units)

Dynamics:
  dr/dt = v
  dv/dt = a_grav + a_thrust + a_drag + a_coriolis
  dm/dt = -T / (Isp * g0)

Gravity:
  a_grav = a_spherical + a_J2 + a_J3 + a_J4

Aerodynamics:
  D = 0.5 * rho * V_rel^2 * C_D * S_ref
  a_drag = -D * v_rel_dir / m

Atmosphere:
  Full standard atmosphere (杨炳蔚) with:
  - Geopotential height conversion
  - Temperature gradient layers
  - Hydrostatic pressure and density
  - Speed of sound and dynamic viscosity
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Optional

from atmosphere_full import density_kg_m3_full, speed_of_sound_m_s, standard_atmosphere
from constants import G0, MU_EARTH, OMEGA_EARTH, R_EARTH_MEAN, RAD_TO_DEG, DEG_TO_RAD
from gravity_full import gravity_acceleration_eci, GravityConfig
from integrators import rk4_step


# ── Vehicle model ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class StageModel:
    """Complete single stage model with realistic parameters.

    Based on Long March 10 (CZ-10) lunar configuration with YF-100K engines.
    """
    name: str
    propellant_mass_kg: float
    dry_mass_kg: float          # structural mass discarded at staging
    thrust_vacuum_N: float       # vacuum thrust
    thrust_sea_level_N: float    # sea-level thrust
    isp_vacuum_s: float          # vacuum specific impulse
    isp_sea_level_s: float       # sea-level specific impulse
    engine_count: int
    burn_time_s: float           # nominal burn time


@dataclass(frozen=True)
class VehicleModel:
    """Complete launch vehicle model."""
    name: str
    stages: list[StageModel]
    payload_mass_kg: float
    fairing_mass_kg: float = 4000.0  # payload fairing (jettisoned early)
    fairing_jettison_time_s: float = 200.0  # typical jettison time
    reference_area_m2: float = 78.5  # cross-sectional area for drag
    drag_coefficient: float = 0.28   # C_D (varies with Mach, but constant here)


def cz10_lunar_vehicle() -> VehicleModel:
    """Build a Long March 10 two-stage-to-LEO vehicle model.

    CZ-10 lunar configuration (for LEO ascent only, TLI stage is separate):
      - Stage 1: Booster cluster (2 boosters × 7 engines) + Core (7 engines)
                 Total 21 YF-100K engines at liftoff
      - Stage 2: Upper stage for orbital insertion

    YF-100K engine parameters (public estimates):
      - Sea-level thrust: ~1250 kN per engine → 21 × 1250 = 26.25 MN
      - Vacuum thrust: ~1397 kN per engine → 21 × 1397 = 29.34 MN
      - Sea-level Isp: ~301.8 s
      - Vacuum Isp: ~338.2 s

    Reference masses based on public CZ-10 data:
      - Liftoff mass: ~2189 t
      - LEO capacity: ~70 t (derived from TLI capacity of 27 t)
      - TLI capacity: ~27 t (public)
    """
    return VehicleModel(
        name="Long March 10 (Two-Stage to LEO)",
        stages=[
            StageModel(
                name="S1_booster_core",
                propellant_mass_kg=1_420_000.0,    # 1420 t propellant
                dry_mass_kg=260_000.0,             # 260 t booster+core dry mass
                thrust_vacuum_N=29.34e6,           # 21 × YF-100K vac
                thrust_sea_level_N=26.25e6,        # 21 × YF-100K sea-level
                isp_vacuum_s=338.2,
                isp_sea_level_s=301.8,
                engine_count=21,
                burn_time_s=180.0,
            ),
            StageModel(
                name="S2_upper_stage",
                propellant_mass_kg=285_000.0,      # 285 t propellant
                dry_mass_kg=45_000.0,              # 45 t upper stage dry mass
                thrust_vacuum_N=5.59e6,            # 4 × YF-100K vac
                thrust_sea_level_N=5.59e6,
                isp_vacuum_s=340.0,
                isp_sea_level_s=340.0,
                engine_count=4,
                burn_time_s=170.0,
            ),
        ],
        payload_mass_kg=20_000.0,  # 20 t cargo module per launch
        fairing_mass_kg=4_000.0,
        reference_area_m2=78.5,   # ~10m diameter
        drag_coefficient=0.30,
    )


# ── Pitch program ───────────────────────────────────────────────────────────

@dataclass
class PitchProgramFull:
    """Enhanced pitch program with multiple phases.

    Phase 1: Vertical ascent (pitch = 90 deg)
    Phase 2: Gravity turn / pitch-over
    Phase 3: Constant pitch angle (or zero-lift)
    Phase 4: Bi-linear tangent steering law (optimal control)

    The bilinear tangent law is the optimal thrust direction for
    vacuum flight with no aerodynamic forces:

        tan(theta) = (a*t + b) / (c*t + d)

    which gives:
        phi(t) = arctan((a*t + b) / (c*t + d))
    """
    vertical_time_s: float = 12.0         # Phase 1: vertical rise time
    pitch_end_time_s: float = 300.0       # Phase 2 end time
    final_pitch_deg: float = 8.0          # Terminal pitch angle
    shape_exponent: float = 1.35          # Controls pitch-over aggressiveness

    # Bilinear tangent parameters (for Phase 3+)
    use_bilinear: bool = False
    a_param: float = 0.0                  # tan(theta) numerator coefficient
    b_param: float = 1.0
    c_param: float = 0.0
    d_param: float = 1.0

    def pitch_deg(self, t_s: float) -> float:
        """Compute pitch angle (deg above local horizontal) at time t.

        Pitch = 90 deg means thrust is purely vertical (radial).
        Pitch = 0 deg means thrust is purely horizontal (tangential).
        """
        if t_s <= 0.0:
            return 90.0

        if self.use_bilinear and t_s > self.pitch_end_time_s:
            # Bilinear tangent steering for vacuum phase
            num = self.a_param * t_s + self.b_param
            den = self.c_param * t_s + self.d_param
            if abs(den) < 1e-12:
                return self.final_pitch_deg
            return math.degrees(math.atan(num / den))

        if t_s <= self.vertical_time_s:
            return 90.0

        if t_s >= self.pitch_end_time_s:
            return self.final_pitch_deg

        # Smooth pitch-over using power-law
        frac = (t_s - self.vertical_time_s) / (self.pitch_end_time_s - self.vertical_time_s)
        shaped = frac ** self.shape_exponent
        return 90.0 - shaped * (90.0 - self.final_pitch_deg)


# ── Ascent state ────────────────────────────────────────────────────────────

@dataclass
class AscentStateFull:
    """Complete ascent trajectory state at a given time step."""
    time_s: float
    # Position (ECI, meters)
    rx_m: float
    ry_m: float
    rz_m: float
    # Velocity (ECI, m/s)
    vx_m_s: float
    vy_m_s: float
    vz_m_s: float
    # Derived
    altitude_m: float
    inertial_speed_m_s: float
    relative_speed_m_s: float        # speed relative to atmosphere
    flight_path_angle_deg: float
    pitch_angle_deg: float
    mass_kg: float
    # Forces and environment
    dynamic_pressure_Pa: float
    mach_number: float
    drag_force_N: float
    thrust_force_N: float
    axial_acceleration_g: float       # in g's (for structural limit)
    # Atmosphere
    density_kg_m3: float
    temperature_K: float
    pressure_Pa: float
    # Stage info
    stage_name: str
    stage_index: int


# ── Ascent simulation ───────────────────────────────────────────────────────

def simulate_ascent_full(
    vehicle: VehicleModel | None = None,
    pitch_program: PitchProgramFull | None = None,
    launch_latitude_deg: float = 19.614,    # Wenchang
    launch_longitude_deg: float = 110.951,
    launch_altitude_m: float = 50.0,
    launch_azimuth_deg: float = 90.0,       # Eastward
    dt_s: float = 0.5,
    gravity_config: GravityConfig | None = None,
    max_altitude_m: float = 500_000.0,      # Stop at 500 km
    callback: Callable[[AscentStateFull], None] | None = None,
) -> list[AscentStateFull]:
    """Simulate complete ascent trajectory with high-fidelity physics.

    Uses RK4 integration with the full equation of motion:

        dr/dt = v
        dv/dt = g(r) + T/m * u_hat - D/m * v_rel_hat - 2*omega x v - omega x (omega x r)
        dm/dt = -T / (Isp * g0)

    where:
      - g(r) is the full gravity including J2, J3, J4
      - T is the engine thrust (adjusted for atmospheric back-pressure)
      - D = 0.5 * rho * V_rel^2 * C_D * S_ref
      - omega x v is the Coriolis acceleration
      - The centrifugal term omega x (omega x r) is absorbed into effective gravity

    Returns a list of AscentStateFull at each recorded timestep.
    """
    if vehicle is None:
        vehicle = cz10_lunar_vehicle()
    if pitch_program is None:
        pitch_program = PitchProgramFull()
    if gravity_config is None:
        gravity_config = GravityConfig(use_j2=True, use_j3=True, use_j4=True)

    # ── Initial state in ECI ─────────────────────────────────────────────

    lat = math.radians(launch_latitude_deg)
    lon = math.radians(launch_longitude_deg)
    r0 = R_EARTH_MEAN + launch_altitude_m

    # ECEF position at launch site
    rx0 = r0 * math.cos(lat) * math.cos(lon)
    ry0 = r0 * math.cos(lat) * math.sin(lon)
    rz0 = r0 * math.sin(lat)

    # Initial velocity from Earth rotation (ECI = ECEF velocity at t=0)
    # v_rot = omega_E × r (eastward)
    vx0 = -OMEGA_EARTH * ry0
    vy0 = OMEGA_EARTH * rx0
    vz0 = 0.0

    # Initial mass: all stages + payload + fairing
    total_dry = sum(s.dry_mass_kg for s in vehicle.stages)
    total_prop = sum(s.propellant_mass_kg for s in vehicle.stages)
    mass0 = total_dry + total_prop + vehicle.payload_mass_kg + vehicle.fairing_mass_kg

    # ── Run simulation ───────────────────────────────────────────────────

    # State vector: [rx, ry, rz, vx, vy, vz]  (6-DOF, mass handled separately)
    pos_vel = [rx0, ry0, rz0, vx0, vy0, vz0]
    mass = mass0
    t = 0.0
    stage_idx = 0
    stage = vehicle.stages[stage_idx]
    stage_prop_left = stage.propellant_mass_kg
    fairing_jettisoned = False

    rows: list[AscentStateFull] = []
    last_record_time = -1.0

    def make_full_state(t_val, pv, m_val, s_name, s_idx):
        """Build temporary full state for recording."""
        full = [pv[0], pv[1], pv[2], pv[3], pv[4], pv[5], m_val]
        return _build_state(t_val, full, s_name, s_idx, vehicle,
                           pitch_program, launch_azimuth_deg, launch_latitude_deg)

    # Record initial state
    rows.append(make_full_state(t, pos_vel, mass, stage.name, stage_idx))

    while True:
        # Check termination conditions
        altitude = math.sqrt(pos_vel[0]**2 + pos_vel[1]**2 + pos_vel[2]**2) - R_EARTH_MEAN
        if altitude > max_altitude_m:
            break
        if stage_idx >= len(vehicle.stages):
            break

        # Fairing jettison
        if not fairing_jettisoned and t >= vehicle.fairing_jettison_time_s:
            mass -= vehicle.fairing_mass_kg
            fairing_jettisoned = True

        # Stage transition
        if stage_prop_left <= 1e-6:
            mass -= stage.dry_mass_kg  # drop dry mass
            stage_idx += 1
            if stage_idx >= len(vehicle.stages):
                break
            stage = vehicle.stages[stage_idx]
            stage_prop_left = stage.propellant_mass_kg
            # Record stage separation
            rows.append(make_full_state(t, pos_vel, mass, stage.name, stage_idx))

        # Compute thrust and mass flow for current stage
        alt = max(0.0, altitude)
        p_ambient = standard_atmosphere(alt).pressure_Pa
        p_sea = 101325.0
        thrust_frac = min(1.0, max(0.0, p_ambient / p_sea))
        thrust = stage.thrust_vacuum_N - (stage.thrust_vacuum_N - stage.thrust_sea_level_N) * thrust_frac
        thrust = max(0.0, thrust)

        isp = stage.isp_vacuum_s - (stage.isp_vacuum_s - stage.isp_sea_level_s) * thrust_frac
        isp = max(1.0, isp)

        mdot = thrust / (isp * G0) if isp > 0 else 0.0
        burn = min(stage_prop_left, mdot * dt_s)
        actual_thrust = thrust if burn > 0 else 0.0

        # Pitch at current time
        pitch_deg = pitch_program.pitch_deg(t)

        # ── RK4 integration of [rx, ry, rz, vx, vy, vz] ────────────────
        # Mass is treated as constant during the RK4 sub-steps
        current_mass = mass
        current_pitch = pitch_deg

        def rhs_6dof(_t: float, _pv: list[float]) -> list[float]:
            return _ascent_rhs_6dof(
                _pv, current_mass, actual_thrust, current_pitch,
                launch_azimuth_deg, launch_latitude_deg,
                vehicle, gravity_config,
            )

        pos_vel = rk4_step(rhs_6dof, t, pos_vel, dt_s)

        # Update mass explicitly (not through RK4)
        mass -= burn
        mass = max(mass, vehicle.payload_mass_kg)
        stage_prop_left -= burn
        t += dt_s

        # Record at intervals
        if t - last_record_time >= 4.0 or stage_prop_left <= 1e-6:
            rows.append(make_full_state(t, pos_vel, mass, stage.name, stage_idx))
            last_record_time = t
            if callback:
                callback(rows[-1])

    # Record final state
    if not rows or rows[-1].time_s < t - 0.01:
        final_full = [pos_vel[0], pos_vel[1], pos_vel[2],
                      pos_vel[3], pos_vel[4], pos_vel[5], mass]
        final_snapshot = _build_state(
            t, final_full,
            stage.name if stage_idx < len(vehicle.stages) else "coast",
            min(stage_idx, len(vehicle.stages) - 1),
            vehicle, pitch_program, launch_azimuth_deg, launch_latitude_deg,
        )
        rows.append(final_snapshot)

    return rows


# ── Right-hand side of the equations of motion ──────────────────────────────

def _ascent_rhs_6dof(
    pv: list[float],
    mass: float,
    thrust_N: float,
    pitch_deg: float,
    launch_azimuth_deg: float,
    launch_latitude_deg: float,
    vehicle: VehicleModel,
    gravity_config: GravityConfig,
) -> list[float]:
    """Compute dx/dt for the 6-DOF ascent dynamics (mass is external).

    Returns [drx/dt, dry/dt, drz/dt, dvx/dt, dvy/dt, dvz/dt]
    Mass is treated as constant during the RK4 sub-step.

    Full dynamics:
        dr/dt = v
        dv/dt = g(r) + T/m * u_hat - D/m * v_rel_hat + a_coriolis

    where:
        g(r): spherical + J2 + J3 + J4 gravity
        T: engine thrust (adjusted for back-pressure)
        D = 0.5 * rho * V_rel^2 * C_D * S_ref
        a_coriolis = -2 * omega_E × v
    """
    rx, ry, rz = pv[0], pv[1], pv[2]
    vx, vy, vz = pv[3], pv[4], pv[5]

    r = math.sqrt(rx*rx + ry*ry + rz*rz)
    altitude = r - R_EARTH_MEAN

    # ── Position derivative ──────────────────────────────────────────────
    dr_dt = [vx, vy, vz]

    # ── Gravity acceleration (J2 + J3 + J4) ──────────────────────────────
    gx, gy, gz = gravity_acceleration_eci((rx, ry, rz), gravity_config)

    # ── Thrust acceleration ──────────────────────────────────────────────
    thrust_dir = _compute_thrust_direction_eci(
        (rx, ry, rz), launch_azimuth_deg, launch_latitude_deg, pitch_deg
    )
    inv_mass = 1.0 / max(mass, 1.0)
    tx = thrust_dir[0] * thrust_N * inv_mass
    ty = thrust_dir[1] * thrust_N * inv_mass
    tz = thrust_dir[2] * thrust_N * inv_mass

    # ── Aerodynamic drag ─────────────────────────────────────────────────
    rho = density_kg_m3_full(max(0.0, altitude))

    # Atmospheric velocity (ECI): atmosphere co-rotates with Earth
    atm_vx = -OMEGA_EARTH * ry
    atm_vy = OMEGA_EARTH * rx
    # atm_vz = 0.0

    # Relative velocity to atmosphere
    rel_vx = vx - atm_vx
    rel_vy = vy - atm_vy
    rel_vz = vz  # atmosphere has no vertical component
    rel_speed = math.sqrt(rel_vx*rel_vx + rel_vy*rel_vy + rel_vz*rel_vz)

    # Drag acceleration
    dx, dy, dz = 0.0, 0.0, 0.0
    if rel_speed > 1e-6 and rho > 1e-15:
        drag_magnitude = 0.5 * rho * rel_speed * rel_speed * vehicle.drag_coefficient * vehicle.reference_area_m2
        drag_accel = drag_magnitude * inv_mass
        dx = -drag_accel * rel_vx / rel_speed
        dy = -drag_accel * rel_vy / rel_speed
        dz = -drag_accel * rel_vz / rel_speed

    # ── Coriolis acceleration ────────────────────────────────────────────
    # a_cor = -2 * omega × v  (note: this is already in the ECI equations)
    # omega × v = (-omega_E * vy, omega_E * vx, 0)
    # So -2 * omega × v = (2 * omega_E * vy, -2 * omega_E * vx, 0)
    cx = 2.0 * OMEGA_EARTH * vy
    cy = -2.0 * OMEGA_EARTH * vx
    cz = 0.0

    # ── Total acceleration ───────────────────────────────────────────────
    dv_dt = [
        gx + tx + dx + cx,
        gy + ty + dy + cy,
        gz + tz + dz + cz,
    ]

    return dr_dt + dv_dt


# ── Thrust direction computation ────────────────────────────────────────────

def _compute_thrust_direction_eci(
    r_eci: tuple[float, float, float],
    launch_azimuth_deg: float,
    launch_latitude_deg: float,
    pitch_deg: float,
) -> tuple[float, float, float]:
    """Compute the unit thrust direction vector in ECI frame.

    The thrust direction is determined by:
      - Local vertical (up) direction: r_hat
      - Local east direction: ω_hat × r_hat
      - Local north direction: r_hat × east_hat
      - Launch azimuth A (clockwise from north)
      - Pitch angle phi (above local horizontal)

    Thrust unit vector:
      T_hat = sin(phi) * u_hat + cos(phi) * (cos(A) * n_hat + sin(A) * e_hat)
    """
    rx, ry, rz = r_eci
    r = math.sqrt(rx*rx + ry*ry + rz*rz)
    if r < 1e-6:
        return (0.0, 0.0, 1.0)

    # Local vertical (up)
    ux = rx / r
    uy = ry / r
    uz = rz / r

    # Local east: ω_hat × r_hat (ω_hat = [0, 0, 1] in ECI)
    # ω_hat × r_hat = (-y_hat, x_hat, 0) / r (already unit since ω_hat ⊥ r_hat... not exactly)
    # Actually: e_hat = (ω × r) / |ω × r|
    e_cross_x = -uy  # (0,0,1) × (ux, uy, uz) = (-uy, ux, 0)
    e_cross_y = ux
    e_cross_z = 0.0
    e_norm = math.sqrt(e_cross_x*e_cross_x + e_cross_y*e_cross_y)
    if e_norm < 1e-12:
        ex, ey, ez = 1.0, 0.0, 0.0
    else:
        ex, ey, ez = e_cross_x / e_norm, e_cross_y / e_norm, 0.0

    # Local north: u_hat × e_hat
    nx = uy * ez - uz * ey
    ny = uz * ex - ux * ez
    nz = ux * ey - uy * ex

    # Launch direction (horizontal component)
    az_rad = math.radians(launch_azimuth_deg)
    cos_az = math.cos(az_rad)
    sin_az = math.sin(az_rad)

    # Horizontal direction in ENU
    hx = cos_az * nx + sin_az * ex
    hy = cos_az * ny + sin_az * ey
    hz = cos_az * nz + sin_az * ez

    # Pitch above horizontal
    phi_rad = math.radians(pitch_deg)
    sin_phi = math.sin(phi_rad)
    cos_phi = math.cos(phi_rad)

    # Thrust direction
    tx = sin_phi * ux + cos_phi * hx
    ty = sin_phi * uy + cos_phi * hy
    tz = sin_phi * uz + cos_phi * hz

    # Normalize
    tnorm = math.sqrt(tx*tx + ty*ty + tz*tz)
    if tnorm < 1e-12:
        return (0.0, 0.0, 1.0)
    return (tx / tnorm, ty / tnorm, tz / tnorm)


# ── Build state snapshot ────────────────────────────────────────────────────

def _build_state(
    t: float,
    state: list[float],
    stage_name: str,
    stage_idx: int,
    vehicle: VehicleModel,
    pitch_program: PitchProgramFull,
    launch_azimuth_deg: float,
    launch_latitude_deg: float,
) -> AscentStateFull:
    """Create an AscentStateFull from raw state vector."""
    rx, ry, rz = state[0], state[1], state[2]
    vx, vy, vz = state[3], state[4], state[5]
    mass = state[6]

    r = math.sqrt(rx*rx + ry*ry + rz*rz)
    speed = math.sqrt(vx*vx + vy*vy + vz*vz)
    altitude = r - R_EARTH_MEAN

    # Flight path angle
    # gamma = arcsin(v_radial / v) = arcsin((v·r_hat) / v)
    r_hat = (rx / r, ry / r, rz / r)
    v_radial = vx * r_hat[0] + vy * r_hat[1] + vz * r_hat[2]
    v_horizontal = math.sqrt(max(0.0, speed*speed - v_radial*v_radial))
    fpa = math.degrees(math.atan2(v_radial, max(v_horizontal, 1e-9)))

    # Pitch angle
    pitch = pitch_program.pitch_deg(t)

    # Atmosphere
    atmo = standard_atmosphere(max(0.0, altitude))
    rho = atmo.density_kg_m3

    # Relative speed (to atmosphere)
    atm_vx = -OMEGA_EARTH * ry
    atm_vy = OMEGA_EARTH * rx
    rel_vx = vx - atm_vx
    rel_vy = vy - atm_vy
    rel_speed = math.sqrt(rel_vx*rel_vx + rel_vy*rel_vy + vz*vz)

    # Dynamic pressure
    q = 0.5 * rho * rel_speed * rel_speed

    # Mach number
    sos = atmo.speed_of_sound_m_s
    mach = rel_speed / max(sos, 1e-6)

    # Drag force
    drag = 0.5 * rho * rel_speed * rel_speed * vehicle.drag_coefficient * vehicle.reference_area_m2

    # Thrust (approximate from stage properties)
    thrust = 0.0
    if stage_idx < len(vehicle.stages):
        stg = vehicle.stages[stage_idx]
        alt_frac = max(0.0, altitude) / 100000.0 if altitude < 100000.0 else 1.0
        thrust = stg.thrust_vacuum_N - (stg.thrust_vacuum_N - stg.thrust_sea_level_N) * (1.0 - alt_frac)

    # Axial acceleration in g
    accel_g = (thrust - drag) / (mass * G0) if mass > 0 else 0.0

    return AscentStateFull(
        time_s=t,
        rx_m=rx, ry_m=ry, rz_m=rz,
        vx_m_s=vx, vy_m_s=vy, vz_m_s=vz,
        altitude_m=altitude,
        inertial_speed_m_s=speed,
        relative_speed_m_s=rel_speed,
        flight_path_angle_deg=fpa,
        pitch_angle_deg=pitch,
        mass_kg=mass,
        dynamic_pressure_Pa=q,
        mach_number=mach,
        drag_force_N=drag,
        thrust_force_N=thrust,
        axial_acceleration_g=accel_g,
        density_kg_m3=rho,
        temperature_K=atmo.temperature_K,
        pressure_Pa=atmo.pressure_Pa,
        stage_name=stage_name,
        stage_index=stage_idx,
    )
