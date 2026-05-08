"""Simple atmosphere models for the v0.2 ascent proxy."""

from __future__ import annotations

from bisect import bisect_right
from math import exp


RHO0 = 1.225  # kg/m^3

# Coarse density table derived from the shape of the standard atmosphere.
# It is intended for first-pass trajectory sensitivity, not precision aero.
_ALTITUDE_M = [
    0.0,
    1_000.0,
    2_000.0,
    5_000.0,
    10_000.0,
    20_000.0,
    30_000.0,
    40_000.0,
    50_000.0,
    60_000.0,
    70_000.0,
    80_000.0,
    90_000.0,
]

_DENSITY_KG_M3 = [
    1.225,
    1.112,
    1.007,
    0.736,
    0.4135,
    0.0889,
    0.0184,
    0.0040,
    0.00103,
    0.00031,
    0.000083,
    0.0000185,
    0.0,
]


def density_kg_m3(altitude_m: float) -> float:
    """Return atmospheric density with log-linear interpolation below 90 km."""

    if altitude_m <= 0.0:
        return RHO0
    if altitude_m >= 90_000.0:
        return 0.0

    idx = bisect_right(_ALTITUDE_M, altitude_m) - 1
    idx = max(0, min(idx, len(_ALTITUDE_M) - 2))
    h0 = _ALTITUDE_M[idx]
    h1 = _ALTITUDE_M[idx + 1]
    rho0 = _DENSITY_KG_M3[idx]
    rho1 = _DENSITY_KG_M3[idx + 1]
    if rho1 <= 0.0:
        return rho0 * max(0.0, (h1 - altitude_m) / (h1 - h0))
    frac = (altitude_m - h0) / (h1 - h0)
    return exp((1.0 - frac) * _safe_log(rho0) + frac * _safe_log(rho1))


def exponential_density_kg_m3(altitude_m: float, scale_height_m: float = 8_500.0) -> float:
    """Return a one-parameter exponential density model."""

    if altitude_m >= 90_000.0:
        return 0.0
    return RHO0 * exp(-max(0.0, altitude_m) / scale_height_m)


def _safe_log(value: float) -> float:
    from math import log

    return log(max(value, 1e-12))

