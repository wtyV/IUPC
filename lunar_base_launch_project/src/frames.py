"""Small frame and vector helpers for launch-site calculations."""

from __future__ import annotations

from dataclasses import dataclass
from math import asin, atan2, cos, radians, sin, sqrt

from constants import OMEGA_EARTH, R_EARTH_MEAN, RAD_TO_DEG


@dataclass(frozen=True)
class Vec3:
    x: float
    y: float
    z: float

    def norm(self) -> float:
        return sqrt(self.x * self.x + self.y * self.y + self.z * self.z)


def geodetic_to_ecef_spherical(latitude_deg: float, longitude_deg: float, altitude_m: float = 0.0) -> Vec3:
    """Convert geodetic-like spherical coordinates to ECEF."""

    lat = radians(latitude_deg)
    lon = radians(longitude_deg)
    radius = R_EARTH_MEAN + altitude_m
    return Vec3(
        radius * cos(lat) * cos(lon),
        radius * cos(lat) * sin(lon),
        radius * sin(lat),
    )


def ecef_to_geodetic_spherical(position: Vec3) -> tuple[float, float, float]:
    """Convert ECEF to spherical latitude, longitude and altitude."""

    radius = position.norm()
    latitude = asin(position.z / radius) * RAD_TO_DEG
    longitude = atan2(position.y, position.x) * RAD_TO_DEG
    altitude = radius - R_EARTH_MEAN
    return latitude, longitude, altitude


def eastward_rotation_speed(latitude_deg: float, altitude_m: float = 0.0) -> float:
    """Return local eastward speed due to Earth rotation."""

    return OMEGA_EARTH * (R_EARTH_MEAN + altitude_m) * cos(radians(latitude_deg))

