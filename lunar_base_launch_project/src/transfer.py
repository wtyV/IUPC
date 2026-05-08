"""First-order Earth-Moon transfer calculations."""

from __future__ import annotations

from dataclasses import dataclass
from math import pi, sqrt

from constants import MOON_MEAN_DISTANCE, MU_EARTH, R_EARTH_MEAN, SECONDS_PER_DAY


@dataclass(frozen=True)
class TliEstimate:
    leo_altitude_km: float
    leo_radius_m: float
    circular_speed_m_s: float
    transfer_perigee_speed_m_s: float
    delta_v_tli_m_s: float
    time_of_flight_days: float


def hohmann_tli_estimate(leo_altitude_km: float, target_radius_m: float = MOON_MEAN_DISTANCE) -> TliEstimate:
    """Estimate TLI delta-v with a patched-conic/Hohmann-style ellipse."""

    if leo_altitude_km <= 0:
        raise ValueError("leo_altitude_km must be positive")
    r1 = R_EARTH_MEAN + leo_altitude_km * 1000.0
    r2 = target_radius_m
    a = 0.5 * (r1 + r2)

    circular_speed = sqrt(MU_EARTH / r1)
    transfer_perigee_speed = sqrt(MU_EARTH * (2.0 / r1 - 1.0 / a))
    delta_v = transfer_perigee_speed - circular_speed
    tof_days = (pi * sqrt((a**3) / MU_EARTH)) / SECONDS_PER_DAY

    return TliEstimate(
        leo_altitude_km=leo_altitude_km,
        leo_radius_m=r1,
        circular_speed_m_s=circular_speed,
        transfer_perigee_speed_m_s=transfer_perigee_speed,
        delta_v_tli_m_s=delta_v,
        time_of_flight_days=tof_days,
    )

