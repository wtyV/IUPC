"""First-order LEO rendezvous and docking estimates.

The baseline mission launches two 20 t cargo modules into nearby LEO parking
orbits. This module estimates a simple phasing strategy: one module waits in
the target orbit, while the second uses a lower or higher phasing orbit to
build the required phase angle before a Hohmann transfer to the target orbit.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt

from constants import MU_EARTH, R_EARTH_MEAN, SECONDS_PER_DAY


@dataclass(frozen=True)
class RendezvousEstimate:
    target_altitude_km: float
    phasing_altitude_km: float
    phase_angle_deg: float
    relative_drift_deg_per_hour: float
    wait_time_hours: float
    transfer_delta_v_m_s: float
    total_rendezvous_delta_v_m_s: float
    note: str


def circular_mean_motion(altitude_km: float) -> float:
    """Return circular-orbit mean motion in rad/s."""

    radius = R_EARTH_MEAN + altitude_km * 1000.0
    return sqrt(MU_EARTH / radius**3)


def hohmann_delta_v_between_circular_orbits(from_altitude_km: float, to_altitude_km: float) -> float:
    """Return total Hohmann transfer delta-v between two circular LEO orbits."""

    r1 = R_EARTH_MEAN + from_altitude_km * 1000.0
    r2 = R_EARTH_MEAN + to_altitude_km * 1000.0
    if abs(r2 - r1) < 1e-9:
        return 0.0

    a = 0.5 * (r1 + r2)
    v1 = sqrt(MU_EARTH / r1)
    v2 = sqrt(MU_EARTH / r2)
    v_transfer_1 = sqrt(MU_EARTH * (2.0 / r1 - 1.0 / a))
    v_transfer_2 = sqrt(MU_EARTH * (2.0 / r2 - 1.0 / a))
    return abs(v_transfer_1 - v1) + abs(v2 - v_transfer_2)


def estimate_rendezvous(
    target_altitude_km: float = 300.0,
    phasing_altitude_km: float = 280.0,
    phase_angle_deg: float = 40.0,
    docking_and_margin_m_s: float = 20.0,
) -> RendezvousEstimate:
    """Estimate phasing wait time and delta-v for a two-module LEO rendezvous."""

    target_n = circular_mean_motion(target_altitude_km)
    phasing_n = circular_mean_motion(phasing_altitude_km)
    relative_rate = phasing_n - target_n
    relative_rate_deg_hour = relative_rate * 180.0 / pi * 3600.0

    if abs(relative_rate_deg_hour) < 1e-9:
        wait_hours = 0.0
        note = "Same-altitude phasing needs launch timing, not orbital drift."
    else:
        phase = phase_angle_deg % 360.0
        wait_hours = phase / abs(relative_rate_deg_hour)
        note = "Lower phasing orbit catches up." if relative_rate > 0.0 else "Higher phasing orbit falls back."

    transfer_dv = hohmann_delta_v_between_circular_orbits(phasing_altitude_km, target_altitude_km)
    return RendezvousEstimate(
        target_altitude_km=target_altitude_km,
        phasing_altitude_km=phasing_altitude_km,
        phase_angle_deg=phase_angle_deg,
        relative_drift_deg_per_hour=relative_rate_deg_hour,
        wait_time_hours=wait_hours,
        transfer_delta_v_m_s=transfer_dv,
        total_rendezvous_delta_v_m_s=transfer_dv + docking_and_margin_m_s,
        note=note,
    )


def default_rendezvous_sweep() -> list[RendezvousEstimate]:
    """Return a small sweep suitable for the first report tables."""

    estimates: list[RendezvousEstimate] = []
    for phasing_altitude in [260.0, 280.0, 290.0, 310.0, 320.0, 340.0]:
        estimates.append(
            estimate_rendezvous(
                target_altitude_km=300.0,
                phasing_altitude_km=phasing_altitude,
                phase_angle_deg=40.0,
            )
        )
    return estimates


def orbital_period_minutes(altitude_km: float) -> float:
    return 2.0 * pi / circular_mean_motion(altitude_km) / 60.0
