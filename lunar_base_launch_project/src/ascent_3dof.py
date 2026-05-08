"""v0.2 ascent proxy for a Long March 10 class launch.

This module is intentionally modest: it is a 2D vertical-plane point-mass model
with staging, drag, gravity and a pitch program. It generates physically shaped
curves for the first report draft. The next version should replace it with a
full ECI 3DOF integrator and tune the guidance variables against a target LEO.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import atan2, cos, radians, sin, sqrt

from atmosphere import density_kg_m3
from constants import G0, MU_EARTH, R_EARTH_MEAN, RAD_TO_DEG
from frames import eastward_rotation_speed
from mission_data import WENCHANG


@dataclass(frozen=True)
class StageSegment:
    name: str
    propellant_mass_kg: float
    dry_mass_drop_kg: float
    thrust_n: float
    isp_s: float


@dataclass(frozen=True)
class PitchProgram:
    vertical_time_s: float = 10.0
    pitch_end_time_s: float = 440.0
    final_pitch_deg: float = 0.0
    shape: float = 1.35

    def pitch_deg(self, t_s: float) -> float:
        """Pitch angle above local horizontal, 90 deg means vertical."""

        if t_s <= self.vertical_time_s:
            return 90.0
        if t_s >= self.pitch_end_time_s:
            return self.final_pitch_deg
        frac = (t_s - self.vertical_time_s) / (self.pitch_end_time_s - self.vertical_time_s)
        shaped = frac**self.shape
        return 90.0 - shaped * (90.0 - self.final_pitch_deg)


@dataclass(frozen=True)
class AscentState:
    time_s: float
    downrange_km: float
    altitude_km: float
    horizontal_velocity_m_s: float
    vertical_velocity_m_s: float
    speed_m_s: float
    flight_path_angle_deg: float
    pitch_deg: float
    mass_t: float
    dynamic_pressure_kpa: float
    stage: str


def default_stage_segments() -> list[StageSegment]:
    """Return a rough Long March 10 class staging model.

    The numbers are engineering placeholders constrained by the public liftoff
    mass and thrust scale. They are suitable for v0.2 trend plots only.
    """

    return [
        StageSegment(
            name="booster_core_cluster",
            propellant_mass_kg=1_420_000.0,
            dry_mass_drop_kg=260_000.0,
            thrust_n=26.27e6,
            isp_s=305.0,
        ),
        StageSegment(
            name="second_stage",
            propellant_mass_kg=285_000.0,
            dry_mass_drop_kg=45_000.0,
            thrust_n=4.20e6,
            isp_s=340.0,
        ),
        StageSegment(
            name="third_stage_proxy",
            propellant_mass_kg=110_000.0,
            dry_mass_drop_kg=0.0,
            thrust_n=1.80e6,
            isp_s=450.0,
        ),
    ]


def simulate_ascent(
    dt_s: float = 1.0,
    initial_mass_kg: float = 2_189_000.0,
    payload_to_leo_kg: float = 20_000.0,
    pitch_program: PitchProgram | None = None,
) -> list[AscentState]:
    """Simulate one baseline launch to the LEO phasing/insertion region."""

    if dt_s <= 0.0:
        raise ValueError("dt_s must be positive")

    pitch_program = pitch_program or PitchProgram()
    stages = default_stage_segments()

    t = 0.0
    downrange_m = 0.0
    altitude_m = WENCHANG.altitude_m
    vx = eastward_rotation_speed(WENCHANG.latitude_deg, WENCHANG.altitude_m)
    vz = 0.0
    mass = initial_mass_kg
    stage_index = 0
    stage_prop_left = stages[stage_index].propellant_mass_kg
    rows: list[AscentState] = []

    while stage_index < len(stages) and altitude_m >= -1.0:
        stage = stages[stage_index]
        pitch_deg = pitch_program.pitch_deg(t)
        pitch_rad = radians(pitch_deg)

        mdot = stage.thrust_n / (stage.isp_s * G0)
        burn = min(stage_prop_left, mdot * dt_s)
        active_dt = burn / mdot if mdot > 0.0 else dt_s
        thrust = stage.thrust_n if burn > 0.0 else 0.0

        rho = density_kg_m3(altitude_m)
        rel_vx = vx - eastward_rotation_speed(WENCHANG.latitude_deg, altitude_m)
        rel_vz = vz
        rel_speed = sqrt(rel_vx * rel_vx + rel_vz * rel_vz)
        cd = 0.28
        area_m2 = 78.5
        drag_n = 0.5 * rho * rel_speed * rel_speed * cd * area_m2
        if rel_speed > 1e-6:
            drag_ax = -drag_n * rel_vx / rel_speed / mass
            drag_az = -drag_n * rel_vz / rel_speed / mass
        else:
            drag_ax = 0.0
            drag_az = 0.0

        gravity = MU_EARTH / ((R_EARTH_MEAN + max(0.0, altitude_m)) ** 2)
        thrust_ax = thrust * cos(pitch_rad) / mass
        thrust_az = thrust * sin(pitch_rad) / mass
        ax = thrust_ax + drag_ax
        az = thrust_az + drag_az - gravity

        vx += ax * active_dt
        vz += az * active_dt
        downrange_m += vx * active_dt
        altitude_m += vz * active_dt
        mass -= burn
        stage_prop_left -= burn

        if int(t) % 5 == 0 or stage_prop_left <= 1e-6:
            speed = sqrt(vx * vx + vz * vz)
            fpa = atan2(vz, max(vx, 1e-6)) * RAD_TO_DEG
            q_kpa = 0.5 * rho * rel_speed * rel_speed / 1000.0
            rows.append(
                AscentState(
                    time_s=t,
                    downrange_km=downrange_m / 1000.0,
                    altitude_km=altitude_m / 1000.0,
                    horizontal_velocity_m_s=vx,
                    vertical_velocity_m_s=vz,
                    speed_m_s=speed,
                    flight_path_angle_deg=fpa,
                    pitch_deg=pitch_deg,
                    mass_t=mass / 1000.0,
                    dynamic_pressure_kpa=q_kpa,
                    stage=stage.name,
                )
            )

        t += active_dt

        if stage_prop_left <= 1e-6:
            mass -= stage.dry_mass_drop_kg
            stage_index += 1
            if stage_index < len(stages):
                stage_prop_left = stages[stage_index].propellant_mass_kg
                # Guard against an impossible placeholder vehicle model.
                if mass <= payload_to_leo_kg:
                    break
            else:
                break

    return rows
