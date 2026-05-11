"""Earth-Moon transfer orbit injection (TLI) model.

This module computes the delta-v required to inject a spacecraft from
a circular LEO parking orbit into an Earth-Moon transfer orbit.

The task only requires reaching the transfer orbit — lunar arrival,
lunar SOI, and LOI are out of scope.

Core formulas:
  - Vis-viva:           v^2 = mu * (2/r - 1/a)
  - Hohmann TLI dv:     dv_TLI = v_p - v_c
  - Transfer ellipse:   a = (r1 + r2) / 2,  r1=LEO, r2=lunar distance
  - C3 energy:          C3 = v_inf^2
  - Time of flight:     TOF = pi * sqrt(a^3 / mu)
  - Rocket equation:    MR = exp(dv / (Isp * g0))

Reference:
  Bate, Mueller, White (1971) "Fundamentals of Astrodynamics"
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from constants import G0, MU_EARTH, R_EARTH_MEAN, MOON_MEAN_DISTANCE, SECONDS_PER_DAY


@dataclass(frozen=True)
class TliInjection:
    """TLI injection result — Earth departure only, no lunar arrival."""

    # ── Inputs ──────────────────────────────────────────────────────────
    leo_altitude_km: float
    leo_radius_m: float
    target_radius_m: float            # apogee, typically lunar distance

    # ── Parking orbit ───────────────────────────────────────────────────
    leo_circular_speed_m_s: float     # v_c = sqrt(mu / r1)

    # ── Transfer ellipse ────────────────────────────────────────────────
    transfer_semi_major_axis_m: float # a = (r1 + r2) / 2
    transfer_eccentricity: float      # e = 1 - r1/a
    transfer_perigee_speed_m_s: float # v_p via vis-viva
    transfer_apogee_speed_m_s: float  # v_a via vis-viva

    # ── TLI burn ────────────────────────────────────────────────────────
    delta_v_tli_m_s: float            # impulsive dv at perigee
    delta_v_ideal_m_s: float          # dv = v_p - v_c

    # ── Departure energy ────────────────────────────────────────────────
    v_infinity_m_s: float             # hyperbolic excess (0 for elliptic)
    c3_energy_km2_s2: float           # C3 = v_inf^2 / 1e6

    # ── Time of flight ──────────────────────────────────────────────────
    time_of_flight_days: float
    time_of_flight_seconds: float

    # ── Mass budget (TLI stage only) ────────────────────────────────────
    tli_isp_s: float
    mass_ratio: float                 # MR = exp(dv / (Isp * g0))

    note: str


def tli_injection(
    leo_altitude_km: float = 300.0,
    target_radius_m: float = MOON_MEAN_DISTANCE,
    tli_isp_s: float = 450.0,
) -> TliInjection:
    """Compute TLI injection from a circular LEO parking orbit.

    Parameters
    ----------
    leo_altitude_km : float
        Circular parking orbit altitude above Earth surface.
    target_radius_m : float
        Target apogee radius (default: Earth-Moon mean distance).
    tli_isp_s : float
        Specific impulse of the TLI stage (vacuum).

    Returns
    -------
    TliInjection

    Mathematical formulation
    ------------------------
    Given parking orbit radius r1 and target apogee r2:

    Transfer ellipse semi-major axis:
        a = (r1 + r2) / 2

    Circular parking orbit speed:
        v_c = sqrt(mu_E / r1)

    Perigee speed on transfer ellipse (vis-viva):
        v_p = sqrt(mu_E * (2/r1 - 1/a))

    TLI delta-v:
        dv_TLI = v_p - v_c

    Apogee speed:
        v_a = sqrt(mu_E * (2/r2 - 1/a))

    Orbital energy:
        E = v^2/2 - mu/r  = -mu/(2a)   (constant along ellipse)

    Hyperbolic excess speed:
        If E > 0 (hyperbolic):  v_inf = sqrt(2E)
        If E <= 0 (elliptic):   v_inf = 0

    C3 energy parameter:
        C3 = v_inf^2   (km^2/s^2, launch vehicle performance metric)

    Time of flight (half-period for elliptic):
        TOF = pi * sqrt(a^3 / mu_E)

    Rocket equation for TLI stage mass ratio:
        MR = m0/mf = exp(dv_TLI / (Isp * g0))
    """
    r1 = R_EARTH_MEAN + leo_altitude_km * 1000.0
    r2 = target_radius_m

    if r2 <= r1:
        raise ValueError("Target radius must be greater than parking orbit radius")

    # ── Transfer ellipse ────────────────────────────────────────────────
    a_transfer = 0.5 * (r1 + r2)
    e_transfer = 1.0 - r1 / a_transfer

    # ── Velocities via vis-viva ─────────────────────────────────────────
    v_circular = math.sqrt(MU_EARTH / r1)
    v_perigee  = math.sqrt(MU_EARTH * (2.0 / r1 - 1.0 / a_transfer))
    v_apogee   = math.sqrt(MU_EARTH * (2.0 / r2 - 1.0 / a_transfer))

    # ── TLI delta-v ─────────────────────────────────────────────────────
    dv_tli = v_perigee - v_circular

    # ── Departure energy ────────────────────────────────────────────────
    # Specific orbital energy: E = v^2/2 - mu/r = -mu/(2a)
    energy = 0.5 * v_perigee * v_perigee - MU_EARTH / r1
    if energy > 0.0:
        v_inf = math.sqrt(2.0 * energy)
    else:
        v_inf = 0.0  # elliptical transfer, v_inf = 0

    c3 = v_inf * v_inf / 1e6

    # ── Time of flight (half ellipse period) ────────────────────────────
    tof_seconds = math.pi * math.sqrt(a_transfer ** 3 / MU_EARTH)
    tof_days = tof_seconds / SECONDS_PER_DAY

    # ── TLI stage mass ratio (rocket equation) ──────────────────────────
    mr = math.exp(dv_tli / (tli_isp_s * G0))

    # ── Summary note ────────────────────────────────────────────────────
    departure_type = "hyperbolic" if energy > 0 else "elliptic"
    note = (
        f"TLI from {leo_altitude_km} km LEO to r_apogee = {r2/1000:.0f} km. "
        f"Transfer: {departure_type}, e = {e_transfer:.4f}. "
        f"dv = {dv_tli/1000:.3f} km/s, TOF = {tof_days:.2f} d, "
        f"C3 = {c3:.4f} km^2/s^2, MR = {mr:.4f}."
    )

    return TliInjection(
        leo_altitude_km=leo_altitude_km,
        leo_radius_m=r1,
        target_radius_m=r2,
        leo_circular_speed_m_s=v_circular,
        transfer_semi_major_axis_m=a_transfer,
        transfer_eccentricity=e_transfer,
        transfer_perigee_speed_m_s=v_perigee,
        transfer_apogee_speed_m_s=v_apogee,
        delta_v_tli_m_s=dv_tli,
        delta_v_ideal_m_s=dv_tli,
        v_infinity_m_s=v_inf,
        c3_energy_km2_s2=c3,
        time_of_flight_days=tof_days,
        time_of_flight_seconds=tof_seconds,
        tli_isp_s=tli_isp_s,
        mass_ratio=mr,
        note=note,
    )


def tli_sensitivity_sweep(
    leo_altitudes_km: list[float] | None = None,
    tli_isp_s: float = 450.0,
) -> list[TliInjection]:
    """Generate TLI results for a range of LEO parking altitudes."""
    if leo_altitudes_km is None:
        leo_altitudes_km = [200.0, 250.0, 300.0, 350.0, 400.0, 500.0]
    return [tli_injection(leo_altitude_km=h, tli_isp_s=tli_isp_s) for h in leo_altitudes_km]


def compute_c3(
    leo_altitude_km: float,
    target_radius_m: float = MOON_MEAN_DISTANCE,
) -> float:
    """Compute C3 (km^2/s^2) for a given LEO altitude.

    C3 = v_inf^2 is the launch vehicle energy performance metric.
    For elliptical lunar transfers: C3 ≈ -1.5 to -2.0 km^2/s^2.
    Negative C3 means the transfer ellipse does not escape Earth.
    """
    return tli_injection(leo_altitude_km, target_radius_m).c3_energy_km2_s2


def tli_delta_v_budget(
    leo_altitude_km: float = 300.0,
    tcm_m_s: float = 15.0,
    tli_isp_s: float = 450.0,
) -> dict[str, float]:
    """Return the TLI delta-v budget: injection burn + small margin.

    The task only requires reaching the transfer orbit, so the budget
    consists of the TLI burn itself plus a small injection accuracy margin.

    Parameters
    ----------
    leo_altitude_km : float
    tcm_m_s : float
        Injection accuracy / dispersions margin (m/s).
    tli_isp_s : float

    Returns
    -------
    dict with keys: tli_injection_m_s, injection_margin_m_s, total_m_s
    """
    tli = tli_injection(leo_altitude_km, tli_isp_s=tli_isp_s)
    return {
        "leo_altitude_km": leo_altitude_km,
        "tli_injection_m_s": tli.delta_v_tli_m_s,
        "injection_margin_m_s": tcm_m_s,
        "total_m_s": tli.delta_v_tli_m_s + tcm_m_s,
        "time_of_flight_days": tli.time_of_flight_days,
        "c3_km2_s2": tli.c3_energy_km2_s2,
        "transfer_eccentricity": tli.transfer_eccentricity,
    }
