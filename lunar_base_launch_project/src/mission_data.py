"""Baseline vehicle and mission data.

The values are intentionally separated into public data and assumptions so the
paper can avoid treating uncertain open-source details as official facts.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LaunchVehicle:
    name: str
    height_m: float
    liftoff_mass_t: float
    liftoff_thrust_tf: float
    tli_capacity_t: float
    first_stage_engine_count_assumed: int


@dataclass(frozen=True)
class EngineFamily:
    name: str
    thrust_sea_level_kn: float
    thrust_vacuum_kn: float
    isp_sea_level_s: float
    isp_vacuum_s: float
    notes: str


@dataclass(frozen=True)
class LaunchSite:
    name: str
    latitude_deg: float
    longitude_deg: float
    altitude_m: float


LONG_MARCH_10 = LaunchVehicle(
    name="Long March 10 lunar configuration",
    height_m=92.5,
    liftoff_mass_t=2189.0,
    liftoff_thrust_tf=2678.0,
    tli_capacity_t=27.0,
    # Modeling assumption for the full lunar configuration:
    # 7 engines on the center core plus two 7-engine boosters.
    first_stage_engine_count_assumed=21,
)

YF_100K_ASSUMED = EngineFamily(
    name="YF-100K assumed open-source model",
    thrust_sea_level_kn=1250.0,
    thrust_vacuum_kn=1397.0,
    isp_sea_level_s=301.84,
    isp_vacuum_s=338.2,
    notes=(
        "Use as a sensitivity parameter, not as an official complete engine "
        "datasheet. Public official tests establish the 130 tf class."
    ),
)

STARSHIP_SUPER_HEAVY_ENGINE_COUNT = 33

WENCHANG = LaunchSite(
    name="Wenchang Space Launch Site",
    latitude_deg=19.614,
    longitude_deg=110.951,
    altitude_m=50.0,
)

