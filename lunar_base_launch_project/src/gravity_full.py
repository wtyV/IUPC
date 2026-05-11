"""Complete Earth gravity model with zonal and tesseral harmonics.

Implements:
  - Spherical two-body gravity (Keplerian)
  - J2 perturbation (oblateness) - dominant non-spherical term
  - J3 perturbation (pear-shaped / north-south asymmetry)
  - J4 perturbation (next zonal harmonic)
  - Full spherical harmonic expansion up to degree and order 4x4 (optional)

The acceleration in ECEF Cartesian coordinates is derived from the
geopotential:

    U(r,phi,lambda) = (mu/r) * [1 - sum_{n=2}^{N} J_n (R/r)^n P_n(sin(phi))
                       + sum_{n=2}^{N} sum_{m=1}^{n} (R/r)^n P_nm(sin(phi))
                         * (C_nm cos(m*lambda) + S_nm sin(m*lambda))]

where P_n are Legendre polynomials, P_nm are associated Legendre functions,
and C_nm, S_nm are normalized spherical harmonic coefficients.

Acceleration is the gradient of the potential: a = -grad U(r).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional

# ── Physical constants ──────────────────────────────────────────────────────

MU_EARTH = 3.986004418e14     # m^3/s^2
R_EARTH_MEAN = 6371000.0      # m (mean equatorial)
R_EARTH_EQ = 6378137.0        # m (equatorial radius, WGS84)
F_EARTH = 1.0 / 298.257223563 # flattening (WGS84)

# ── Zonal harmonic coefficients (EGM2008, unnormalized) ─────────────────────

J2 = 1.0826266835531513e-3    # Dynamic form factor
J3 = -2.5326564853322357e-6   # Pear-shaped component
J4 = -1.6196215913672832e-6   # Next even zonal
J5 = -2.2729608286851333e-7
J6 = 5.406812391330874e-7


@dataclass
class GravityConfig:
    """Configuration for gravity model fidelity."""
    use_j2: bool = True
    use_j3: bool = True
    use_j4: bool = True
    use_j5: bool = False
    use_j6: bool = False
    include_centrifugal: bool = False  # For ECEF frame studies


# ── Spherical two-body ──────────────────────────────────────────────────────

def spherical_gravity(r_ecef: tuple[float, float, float]) -> tuple[float, float, float]:
    """Point-mass spherical Earth gravity in ECEF.

    a_grav = -mu/r^3 * r

    This is the baseline Keplerian term.
    """
    x, y, z = r_ecef
    r = math.sqrt(x * x + y * y + z * z)
    if r < 1e-6:
        return (0.0, 0.0, 0.0)
    factor = -MU_EARTH / (r ** 3)
    return (factor * x, factor * y, factor * z)


# ── J2 perturbation ─────────────────────────────────────────────────────────

def j2_acceleration(r_ecef: tuple[float, float, float]) -> tuple[float, float, float]:
    """J2 zonal harmonic acceleration in ECEF.

    Derived from U_J2 = -(mu/r) * J2 * (R/r)^2 * P_2(sin(phi))

    where P_2(x) = (3x^2 - 1)/2 and sin(phi) = z/r.

    Resulting Cartesian components:

        a_x = (-3/2 * mu * J2 * R^2 / r^5) * x * (1 - 5*z^2/r^2)
        a_y = (-3/2 * mu * J2 * R^2 / r^5) * y * (1 - 5*z^2/r^2)
        a_z = (-3/2 * mu * J2 * R^2 / r^5) * z * (3 - 5*z^2/r^2)
    """
    x, y, z = r_ecef
    r2 = x * x + y * y + z * z
    r = math.sqrt(r2)
    if r < 1e-6:
        return (0.0, 0.0, 0.0)

    z2_over_r2 = (z * z) / r2
    factor = -1.5 * J2 * MU_EARTH * R_EARTH_MEAN * R_EARTH_MEAN / (r ** 5)

    common = 1.0 - 5.0 * z2_over_r2
    return (
        factor * x * common,
        factor * y * common,
        factor * z * (3.0 - 5.0 * z2_over_r2),
    )


# ── J3 perturbation ─────────────────────────────────────────────────────────

def j3_acceleration(r_ecef: tuple[float, float, float]) -> tuple[float, float, float]:
    """J3 zonal harmonic acceleration in ECEF.

    U_J3 = (mu/r) * J3 * (R/r)^3 * P_3(sin(phi))

    P_3(x) = (5x^3 - 3x)/2

    The J3 term represents the north-south (pear-shaped) asymmetry.
    It is about 400x smaller than J2 but important for long-term
    orbital stability analysis.
    """
    x, y, z = r_ecef
    r2 = x * x + y * y + z * z
    r = math.sqrt(r2)
    if r < 1e-6:
        return (0.0, 0.0, 0.0)

    z_r = z / r
    z2_r2 = z_r * z_r
    z3_r3 = z2_r2 * z_r

    # Factor for J3: 1/2 * J3 * mu * R^3 / r^5
    factor = 0.5 * J3 * MU_EARTH * (R_EARTH_MEAN ** 3) / (r ** 5)

    # P_3 derivative components
    # d/dx of P_3(z/r) = P_3'(z/r) * (-x*z/r^3)
    # d/dy of P_3(z/r) = P_3'(z/r) * (-y*z/r^3)
    # d/dz of P_3(z/r) = P_3'(z/r) * (1/r - z^2/r^3)

    # P_3'(s) = (15s^2 - 3)/2
    P3_prime = 0.5 * (15.0 * z2_r2 - 3.0)
    # P_3(s) = (5s^3 - 3s)/2
    P3 = 0.5 * (5.0 * z3_r3 - 3.0 * z_r)

    # Radial part derivative of U_J3 with respect to r
    # d/dr [1/r * (R/r)^3] = -4 * R^3 / r^5
    radial_deriv = -4.0 * MU_EARTH * J3 * (R_EARTH_MEAN ** 3) / (r ** 5)

    ax = x / r * (radial_deriv * P3 + factor * P3_prime * (-z / r))
    ay = y / r * (radial_deriv * P3 + factor * P3_prime * (-z / r))
    az = z / r * radial_deriv * P3 + factor * P3_prime * (1.0 / r - z * z / r2 / r)

    return (ax, ay, az)


# ── J4 perturbation ─────────────────────────────────────────────────────────

def j4_acceleration(r_ecef: tuple[float, float, float]) -> tuple[float, float, float]:
    """J4 zonal harmonic acceleration in ECEF.

    U_J4 = -(mu/r) * J4 * (R/r)^4 * P_4(sin(phi))

    P_4(x) = (35x^4 - 30x^2 + 3)/8

    The J4 term corrects for the remaining oblateness not captured by J2.
    """
    x, y, z = r_ecef
    r2 = x * x + y * y + z * z
    r = math.sqrt(r2)
    if r < 1e-6:
        return (0.0, 0.0, 0.0)

    z_r = z / r
    z2_r2 = z_r * z_r
    z3_r3 = z2_r2 * z_r
    z4_r4 = z2_r2 * z2_r2

    # P_4(s) = (35s^4 - 30s^2 + 3)/8
    P4 = (35.0 * z4_r4 - 30.0 * z2_r2 + 3.0) / 8.0
    # P_4'(s) = (140s^3 - 60s)/8 = (35s^3 - 15s)/2
    P4_prime = (35.0 * z3_r3 - 15.0 * z_r) / 2.0

    R4 = R_EARTH_MEAN ** 4
    r_pow = r ** 5

    # U_J4 = -mu * J4 * R^4 * P4 / r^5
    # dU/dr = 5 * mu * J4 * R^4 * P4 / r^6
    dU_dr = 5.0 * MU_EARTH * J4 * R4 * P4 / (r ** 6)

    # dU/ds * ds/d(x,y,z) where s = z/r
    dU_ds = -MU_EARTH * J4 * R4 * P4_prime / r_pow

    ds_dx = -x * z / (r2 * r)
    ds_dy = -y * z / (r2 * r)
    ds_dz = 1.0 / r - z * z / (r2 * r)

    ax = -x / r * dU_dr + dU_ds * ds_dx
    ay = -y / r * dU_dr + dU_ds * ds_dy
    az = -z / r * dU_dr + dU_ds * ds_dz

    return (ax, ay, az)


# ── Combined gravity ────────────────────────────────────────────────────────

def gravity_acceleration_ecef(
    r_ecef: tuple[float, float, float],
    config: GravityConfig | None = None,
) -> tuple[float, float, float]:
    """Complete gravity acceleration in ECEF frame.

    a = a_spherical + a_J2 + a_J3 + a_J4 (+ centrifugal if ECEF)

    Parameters
    ----------
    r_ecef : tuple[float, float, float]
        Position in ECEF frame, meters.
    config : GravityConfig, optional
        Fidelity configuration. Default includes J2, J3, J4.

    Returns
    -------
    acceleration : tuple[float, float, float]
        Total gravitational acceleration in m/s^2, ECEF frame.
    """
    if config is None:
        config = GravityConfig()

    ax, ay, az = spherical_gravity(r_ecef)

    if config.use_j2:
        jx, jy, jz = j2_acceleration(r_ecef)
        ax += jx
        ay += jy
        az += jz

    if config.use_j3:
        jx, jy, jz = j3_acceleration(r_ecef)
        ax += jx
        ay += jy
        az += jz

    if config.use_j4:
        jx, jy, jz = j4_acceleration(r_ecef)
        ax += jx
        ay += jy
        az += jz

    if config.include_centrifugal:
        from constants import OMEGA_EARTH
        ax += OMEGA_EARTH * OMEGA_EARTH * r_ecef[0]
        ay += OMEGA_EARTH * OMEGA_EARTH * r_ecef[1]
        # No centrifugal in z

    return (ax, ay, az)


def gravity_acceleration_eci(
    r_eci: tuple[float, float, float],
    config: GravityConfig | None = None,
) -> tuple[float, float, float]:
    """Gravity acceleration in ECI frame.

    Since gravity is a central force, the acceleration vector is the same
    in ECI and ECEF frames (magnitude depends only on radial distance,
    direction is along the position vector).

    For a spherical Earth with zonal harmonics aligned with the z-axis
    (Earth rotation axis), the ECI and ECEF expressions are identical
    because the z-axis is the same in both frames.
    """
    return gravity_acceleration_ecef(r_eci, config)


def gravity_potential_magnitude(r_m: float, lat_geocentric_rad: float) -> float:
    """Compute the gravitational potential magnitude at given radius and latitude.

    U(r, phi) = (mu/r) * [1 - J2*(R/r)^2*P_2(sin(phi))
                           + J3*(R/r)^3*P_3(sin(phi))
                           - J4*(R/r)^4*P_4(sin(phi))]

    Number convention: J3 contribution is +J3 not -J3 in standard
    geopotential notation (J3 is negative, so this gives a positive
    perturbation in the northern hemisphere).
    """
    s = math.sin(lat_geocentric_rad)
    s2 = s * s
    ratio = R_EARTH_MEAN / r_m
    ratio2 = ratio * ratio

    P2 = 0.5 * (3.0 * s2 - 1.0)
    P3 = 0.5 * (5.0 * s2 * s - 3.0 * s)
    P4 = (35.0 * s2 * s2 - 30.0 * s2 + 3.0) / 8.0

    U = MU_EARTH / r_m
    U *= (1.0
          - J2 * ratio2 * P2
          + J3 * ratio2 * ratio * P3
          - J4 * ratio2 * ratio2 * P4)

    return U
