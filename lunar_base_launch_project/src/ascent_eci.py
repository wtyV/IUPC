"""ECI 3D point-mass ascent model with optional J2.

This is a v0.3 bridge between the earlier 2D proxy and a full launch-vehicle
trajectory optimizer. It keeps the same rough stage model but propagates
position and velocity in an inertial frame, includes Earth rotation in the
initial velocity and aerodynamic relative velocity, and can switch J2 on/off.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, radians, sin, sqrt

from ascent_3dof import PitchProgram, default_stage_segments
from atmosphere import density_kg_m3
from constants import G0, J2_EARTH, MU_EARTH, OMEGA_EARTH, R_EARTH_MEAN, RAD_TO_DEG
from frames import geodetic_to_ecef_spherical
from mission_data import WENCHANG


Vector = tuple[float, float, float]


@dataclass(frozen=True)
class EciAscentState:
    time_s: float
    x_km: float
    y_km: float
    z_km: float
    vx_m_s: float
    vy_m_s: float
    vz_m_s: float
    altitude_km: float
    speed_m_s: float
    inertial_speed_m_s: float
    flight_path_angle_deg: float
    pitch_deg: float
    mass_t: float
    dynamic_pressure_kpa: float
    stage: str


def simulate_ascent_eci(
    dt_s: float = 1.0,
    initial_mass_kg: float = 2_189_000.0,
    pitch_program: PitchProgram | None = None,
    launch_azimuth_deg: float = 90.0,
    use_j2: bool = True,
) -> list[EciAscentState]:
    """Simulate an eastward Wenchang launch in ECI coordinates."""

    if dt_s <= 0.0:
        raise ValueError("dt_s must be positive")

    pitch_program = pitch_program or PitchProgram()
    stages = default_stage_segments()

    site = geodetic_to_ecef_spherical(WENCHANG.latitude_deg, WENCHANG.longitude_deg, WENCHANG.altitude_m)
    r: Vector = (site.x, site.y, site.z)
    v: Vector = _omega_cross_r(r)
    mass = initial_mass_kg
    t = 0.0
    stage_index = 0
    stage_prop_left = stages[stage_index].propellant_mass_kg
    rows: list[EciAscentState] = []

    while stage_index < len(stages):
        stage = stages[stage_index]
        pitch_deg = pitch_program.pitch_deg(t)
        pitch_rad = radians(pitch_deg)
        thrust_dir = _thrust_direction(r, launch_azimuth_deg, pitch_rad)

        mdot = stage.thrust_n / (stage.isp_s * G0)
        burn = min(stage_prop_left, mdot * dt_s)
        active_dt = burn / mdot if mdot > 0.0 else dt_s
        thrust = stage.thrust_n if burn > 0.0 else 0.0

        altitude_m = _norm(r) - R_EARTH_MEAN
        rho = density_kg_m3(altitude_m)
        v_atm = _omega_cross_r(r)
        v_rel = _sub(v, v_atm)
        rel_speed = _norm(v_rel)
        cd = 0.28
        area_m2 = 78.5
        drag_n = 0.5 * rho * rel_speed * rel_speed * cd * area_m2

        a_gravity = _gravity_acceleration(r, use_j2=use_j2)
        a_thrust = _scale(thrust_dir, thrust / mass)
        a_drag = (0.0, 0.0, 0.0) if rel_speed < 1e-9 else _scale(v_rel, -drag_n / (rel_speed * mass))
        acceleration = _add(_add(a_gravity, a_thrust), a_drag)

        v = _add(v, _scale(acceleration, active_dt))
        r = _add(r, _scale(v, active_dt))
        mass -= burn
        stage_prop_left -= burn

        if int(t) % 5 == 0 or stage_prop_left <= 1e-6:
            rows.append(_state_row(t, r, v, mass, pitch_deg, stage.name, rho, v_rel))

        t += active_dt

        if stage_prop_left <= 1e-6:
            mass -= stage.dry_mass_drop_kg
            stage_index += 1
            if stage_index < len(stages):
                stage_prop_left = stages[stage_index].propellant_mass_kg
            else:
                break

    return rows


def _state_row(
    time_s: float,
    r: Vector,
    v: Vector,
    mass_kg: float,
    pitch_deg: float,
    stage: str,
    rho: float,
    v_rel: Vector,
) -> EciAscentState:
    radius = _norm(r)
    altitude = radius - R_EARTH_MEAN
    up = _scale(r, 1.0 / radius)
    radial_speed = _dot(v, up)
    inertial_speed = _norm(v)
    rel_speed = _norm(v_rel)
    horizontal_speed = sqrt(max(0.0, inertial_speed * inertial_speed - radial_speed * radial_speed))
    fpa = atan2(radial_speed, max(horizontal_speed, 1e-9)) * RAD_TO_DEG
    q_kpa = 0.5 * rho * rel_speed * rel_speed / 1000.0
    return EciAscentState(
        time_s=time_s,
        x_km=r[0] / 1000.0,
        y_km=r[1] / 1000.0,
        z_km=r[2] / 1000.0,
        vx_m_s=v[0],
        vy_m_s=v[1],
        vz_m_s=v[2],
        altitude_km=altitude / 1000.0,
        speed_m_s=rel_speed,
        inertial_speed_m_s=inertial_speed,
        flight_path_angle_deg=fpa,
        pitch_deg=pitch_deg,
        mass_t=mass_kg / 1000.0,
        dynamic_pressure_kpa=q_kpa,
        stage=stage,
    )


def _gravity_acceleration(r: Vector, use_j2: bool) -> Vector:
    x, y, z = r
    radius = _norm(r)
    base = _scale(r, -MU_EARTH / radius**3)
    if not use_j2:
        return base

    z2 = z * z
    r2 = radius * radius
    factor = 1.5 * J2_EARTH * MU_EARTH * R_EARTH_MEAN**2 / radius**5
    common = 5.0 * z2 / r2
    return (
        base[0] + factor * x * (common - 1.0),
        base[1] + factor * y * (common - 1.0),
        base[2] + factor * z * (common - 3.0),
    )


def _thrust_direction(r: Vector, launch_azimuth_deg: float, pitch_rad: float) -> Vector:
    up = _unit(r)
    east = _unit(_omega_cross_r(r))
    north = _unit(_cross(up, east))
    az = radians(launch_azimuth_deg)
    horizontal = _unit(_add(_scale(north, cos(az)), _scale(east, sin(az))))
    return _unit(_add(_scale(up, sin(pitch_rad)), _scale(horizontal, cos(pitch_rad))))


def _omega_cross_r(r: Vector) -> Vector:
    return (-OMEGA_EARTH * r[1], OMEGA_EARTH * r[0], 0.0)


def _norm(v: Vector) -> float:
    return sqrt(_dot(v, v))


def _unit(v: Vector) -> Vector:
    n = _norm(v)
    if n < 1e-12:
        return (0.0, 0.0, 0.0)
    return _scale(v, 1.0 / n)


def _dot(a: Vector, b: Vector) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a: Vector, b: Vector) -> Vector:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _add(a: Vector, b: Vector) -> Vector:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a: Vector, b: Vector) -> Vector:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _scale(v: Vector, scalar: float) -> Vector:
    return (v[0] * scalar, v[1] * scalar, v[2] * scalar)

