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


# ── Fast Rendezvous for Payload-Fuel Split ──────────────────────────────────

@dataclass(frozen=True)
class FastRendezvousEstimate:
    """Rendezvous plan for fuel tanker (Launch B) chasing payload (Launch A).

    Launch A is in a 300 km parking orbit. Launch B targets the same orbital
    plane but enters a lower phasing orbit to catch up rapidly.
    """
    target_altitude_km: float          # A's parking orbit
    phasing_altitude_km: float         # B's initial phasing orbit
    target_mean_motion_rad_s: float
    phasing_mean_motion_rad_s: float
    relative_drift_deg_per_hour: float
    # Phase angle scenarios
    initial_phase_deg: float           # worst-case phase angle at B's arrival
    worst_case_wait_hours: float
    best_case_wait_hours: float        # launch-on-time, near-zero phase
    # Hohmann transfer from phasing to target
    hohmann_dv_m_s: float
    docking_margin_m_s: float
    total_rendezvous_dv_m_s: float
    # Launch window
    launch_window_minutes: float       # daily launch window to hit orbital plane
    note: str


def estimate_fast_rendezvous(
    target_altitude_km: float = 300.0,
    phasing_altitude_km: float = 280.0,
    worst_case_phase_deg: float = 120.0,   # worst-case when B arrives
    docking_margin_m_s: float = 15.0,
) -> FastRendezvousEstimate:
    """Estimate fast rendezvous for fuel tanker chasing payload.

    Strategy
    --------
    Launch A (payload) is in a 300 km circular parking orbit.
    Launch B (fuel) launches into a ~280 km phasing orbit in the same plane.

    Since B is lower, its angular velocity is higher (n = √(μ/r³)),
    so it catches up to A over time. The lower the phasing orbit, the
    faster the catch-up — at the cost of a slightly larger Hohmann Δv
    to transfer up to 300 km for docking.

    Launch window: B must launch when the Wenchang launch site passes
    through A's orbital plane. For a 19.6° inclination orbit, this
    occurs twice per day, each window lasting ~5-10 minutes.

    The wait time after B's arrival depends on the initial phase angle:
      t_wait = Δθ_initial / (n_phase − n_target)
    """
    n_target = circular_mean_motion(target_altitude_km)
    n_phase = circular_mean_motion(phasing_altitude_km)
    relative_rate_rad_s = n_phase - n_target  # positive if phasing is lower

    if relative_rate_rad_s <= 0:
        raise ValueError("Phasing orbit must be lower than target for catch-up")

    relative_rate_deg_h = relative_rate_rad_s * 180.0 / pi * 3600.0

    # Wait time as a function of initial phase angle
    worst_case_wait = worst_case_phase_deg / relative_rate_deg_h
    # Best case: B arrives with near-zero phase angle (well-timed launch)
    best_case_wait = 5.0 / relative_rate_deg_h   # ~5° residual

    # Hohmann transfer Δv from phasing to target
    dv_hohmann = hohmann_delta_v_between_circular_orbits(phasing_altitude_km, target_altitude_km)

    total_dv = dv_hohmann + docking_margin_m_s

    # Launch window: twice per day when launch site passes through orbit plane
    # For 19.6° inclination from Wenchang, the launch site latitude ≈ inclination
    # so the site passes through the orbit plane twice daily
    launch_window_minutes_val = 8.0  # typical plane window for LEO

    note = (
        f"Fuel tanker at {phasing_altitude_km} km catches up to payload at "
        f"{target_altitude_km} km at {relative_rate_deg_h:.2f} deg/h. "
        f"Worst-case wait: {worst_case_wait:.1f} h (Δθ = {worst_case_phase_deg}°). "
        f"Hohmann Δv to transfer up: {dv_hohmann:.1f} m/s. "
        f"Total rendezvous Δv budget: {total_dv:.1f} m/s."
    )

    return FastRendezvousEstimate(
        target_altitude_km=target_altitude_km,
        phasing_altitude_km=phasing_altitude_km,
        target_mean_motion_rad_s=n_target,
        phasing_mean_motion_rad_s=n_phase,
        relative_drift_deg_per_hour=relative_rate_deg_h,
        initial_phase_deg=worst_case_phase_deg,
        worst_case_wait_hours=worst_case_wait,
        best_case_wait_hours=best_case_wait,
        hohmann_dv_m_s=dv_hohmann,
        docking_margin_m_s=docking_margin_m_s,
        total_rendezvous_dv_m_s=total_dv,
        launch_window_minutes=launch_window_minutes_val,
        note=note,
    )


def fast_rendezvous_sweep() -> list[FastRendezvousEstimate]:
    """Sweep phasing altitudes for the payload-fuel fast rendezvous.

    Lower phasing orbit → faster catch-up but higher Hohmann Δv.
    Higher phasing orbit → slower catch-up but less propellant.
    """
    estimates: list[FastRendezvousEstimate] = []
    for phasing_alt in [250.0, 260.0, 270.0, 280.0, 290.0, 295.0]:
        estimates.append(
            estimate_fast_rendezvous(
                target_altitude_km=300.0,
                phasing_altitude_km=phasing_alt,
            )
        )
    return estimates
