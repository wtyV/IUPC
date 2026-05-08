"""Launch-site geometry and first-order launch azimuth relationships."""

from __future__ import annotations

from dataclasses import dataclass
from math import acos, cos, radians, sin

from constants import OMEGA_EARTH, R_EARTH_MEAN, RAD_TO_DEG


@dataclass(frozen=True)
class LaunchGeometryPoint:
    launch_azimuth_deg: float
    approximate_inclination_deg: float
    eastward_rotation_gain_m_s: float


def earth_rotation_speed_at_latitude(latitude_deg: float) -> float:
    """Return surface speed due to Earth rotation at a geodetic latitude."""

    return OMEGA_EARTH * R_EARTH_MEAN * cos(radians(latitude_deg))


def inclination_from_azimuth(latitude_deg: float, launch_azimuth_deg: float) -> float:
    """Approximate orbital inclination from launch azimuth.

    Azimuth is measured clockwise from north. The relation is the common
    spherical-Earth first-order estimate: cos(i) = cos(lat) * sin(A).
    """

    value = cos(radians(latitude_deg)) * sin(radians(launch_azimuth_deg))
    value = max(-1.0, min(1.0, value))
    return acos(value) * RAD_TO_DEG


def rotation_gain_component(latitude_deg: float, launch_azimuth_deg: float) -> float:
    """Eastward component of the launch-site rotation speed along azimuth."""

    return earth_rotation_speed_at_latitude(latitude_deg) * sin(radians(launch_azimuth_deg))


def geometry_point(latitude_deg: float, launch_azimuth_deg: float) -> LaunchGeometryPoint:
    return LaunchGeometryPoint(
        launch_azimuth_deg=launch_azimuth_deg,
        approximate_inclination_deg=inclination_from_azimuth(latitude_deg, launch_azimuth_deg),
        eastward_rotation_gain_m_s=rotation_gain_component(latitude_deg, launch_azimuth_deg),
    )

