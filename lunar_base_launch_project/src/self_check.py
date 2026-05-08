"""Lightweight formula checks for the v0.1 baseline model."""

from __future__ import annotations

from launch_geometry import earth_rotation_speed_at_latitude, inclination_from_azimuth
from mass_budget import solve_tli_mass_budget
from mission_data import WENCHANG
from optimize import optimization_summary_rows
from reliability import engine_cluster_reliability, three_launch_two_of_three, two_launch_all_success, two_launch_leo_tli_success
from ascent_3dof import PitchProgram, simulate_ascent
from ascent_eci import simulate_ascent_eci
from rendezvous import estimate_rendezvous
from transfer import hohmann_tli_estimate


def approx_equal(value: float, expected: float, tolerance: float) -> None:
    if abs(value - expected) > tolerance:
        raise AssertionError(f"{value} differs from {expected} by more than {tolerance}")


def main() -> None:
    approx_equal(two_launch_all_success(0.95), 0.9025, 1e-12)
    approx_equal(three_launch_two_of_three(0.95), 0.99275, 1e-12)
    approx_equal(two_launch_leo_tli_success(0.95, 0.98, 0.985), 0.87118325, 1e-12)
    approx_equal(engine_cluster_reliability(0.99, 2, 0), 0.9801, 1e-12)
    approx_equal(engine_cluster_reliability(0.99, 2, 1), 0.9999, 1e-12)

    tli_300 = hohmann_tli_estimate(300.0)
    if not (3100.0 < tli_300.delta_v_tli_m_s < 3300.0):
        raise AssertionError("300 km TLI delta-v is outside expected first-order range")

    rotation_speed = earth_rotation_speed_at_latitude(WENCHANG.latitude_deg)
    if not (430.0 < rotation_speed < 445.0):
        raise AssertionError("Wenchang rotation speed is outside expected range")

    east_inclination = inclination_from_azimuth(WENCHANG.latitude_deg, 90.0)
    approx_equal(east_inclination, WENCHANG.latitude_deg, 0.2)

    ascent = simulate_ascent()
    if len(ascent) < 20:
        raise AssertionError("ascent proxy did not produce enough samples")
    terminal = ascent[-1]
    if terminal.speed_m_s < 6000.0:
        raise AssertionError("ascent proxy terminal speed is too low for an LEO-class ascent")
    if max(row.dynamic_pressure_kpa for row in ascent) <= 1.0:
        raise AssertionError("ascent proxy dynamic pressure did not become positive")

    eci_ascent = simulate_ascent_eci()
    if len(eci_ascent) < 20:
        raise AssertionError("ECI ascent did not produce enough samples")
    if eci_ascent[-1].inertial_speed_m_s < 6000.0:
        raise AssertionError("ECI ascent terminal speed is too low for an LEO-class ascent")

    rendezvous = estimate_rendezvous()
    if rendezvous.total_rendezvous_delta_v_m_s <= 0.0:
        raise AssertionError("rendezvous delta-v should be positive for different phasing altitude")
    if rendezvous.wait_time_hours <= 0.0:
        raise AssertionError("rendezvous phasing wait time should be positive")

    optimization_rows = optimization_summary_rows(max_rows=3)
    if len(optimization_rows) != 9:
        raise AssertionError("optimization summary should include 2D ascent, ECI ascent and rendezvous rows")

    mass_budget = solve_tli_mass_budget()
    if mass_budget.initial_leo_stack_t <= 80.0 or mass_budget.initial_leo_stack_t >= 120.0:
        raise AssertionError("nominal TLI mass budget is outside the expected first-order range")
    if mass_budget.simulated_margin_per_launch_t <= 0.0:
        raise AssertionError("simulated LEO terminal mass should exceed the nominal per-launch wet mass need")

    tuned_pitch = PitchProgram(pitch_end_time_s=305.0, final_pitch_deg=10.0, shape=1.4)
    spherical = simulate_ascent_eci(pitch_program=tuned_pitch, use_j2=False)[-1]
    j2 = simulate_ascent_eci(pitch_program=tuned_pitch, use_j2=True)[-1]
    if abs(j2.altitude_km - spherical.altitude_km) > 10.0:
        raise AssertionError("J2 altitude difference is unexpectedly large for this ascent proxy")

    print("self_check passed")


if __name__ == "__main__":
    main()
