"""Generate v0.6 baseline tables, figures and trajectories."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict
from pathlib import Path

from architecture import default_architectures, evaluate_architecture
from ascent_3dof import PitchProgram, simulate_ascent
from ascent_eci import simulate_ascent_eci
from launch_geometry import earth_rotation_speed_at_latitude, geometry_point
from mass_budget import default_mass_budget_sweep
from mission_data import LONG_MARCH_10, STARSHIP_SUPER_HEAVY_ENGINE_COUNT, WENCHANG
from optimize import optimization_summary_rows
from reliability import (
    engine_cluster_reliability,
    three_launch_two_of_three,
    two_launch_all_success,
    two_launch_leo_tli_success,
)
from rendezvous import default_rendezvous_sweep
from svg_charts import write_line_chart
from transfer import hohmann_tli_estimate


ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "results" / "tables"
FIGURES = ROOT / "results" / "figures"
TRAJECTORIES = ROOT / "results" / "trajectories"


def main() -> None:
    TABLES.mkdir(parents=True, exist_ok=True)
    FIGURES.mkdir(parents=True, exist_ok=True)
    TRAJECTORIES.mkdir(parents=True, exist_ok=True)

    architecture_rows = write_architecture_summary()
    reliability_rows = write_reliability_sweep()
    mission_chain_rows = write_mission_chain_reliability()
    mission_chain_sensitivity_rows = write_mission_chain_sensitivity()
    cluster_rows = write_engine_cluster_sweep()
    transfer_rows = write_delta_v_budget()
    mass_budget_rows = write_tli_mass_budget()
    geometry_rows = write_launch_geometry()
    rendezvous_rows = write_rendezvous_plan()
    ascent_rows = write_ascent_baseline()
    ascent_eci_rows = write_ascent_eci_baseline()
    gravity_comparison_rows = write_gravity_comparison()
    optimization_rows = write_optimization_summary()
    write_figures(
        reliability_rows,
        mission_chain_rows,
        mission_chain_sensitivity_rows,
        cluster_rows,
        transfer_rows,
        mass_budget_rows,
        geometry_rows,
        rendezvous_rows,
        ascent_rows,
        ascent_eci_rows,
        gravity_comparison_rows,
        optimization_rows,
    )
    write_summary(
        architecture_rows,
        reliability_rows,
        mission_chain_rows,
        mission_chain_sensitivity_rows,
        transfer_rows,
        mass_budget_rows,
        geometry_rows,
        rendezvous_rows,
        ascent_rows,
        ascent_eci_rows,
        gravity_comparison_rows,
        optimization_rows,
    )

    print(f"Wrote baseline results to {ROOT / 'results'}")


def write_architecture_summary() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for arch in default_architectures(LONG_MARCH_10.tli_capacity_t):
        result = evaluate_architecture(arch)
        rows.append(asdict(result))

    write_csv(TABLES / "architecture_summary.csv", rows)
    return rows


def write_reliability_sweep() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for idx in range(85, 100):
        r = idx / 100.0
        rows.append(
            {
                "single_launch_reliability": r,
                "two_launch_all_success": two_launch_all_success(r),
                "three_launch_two_of_three": three_launch_two_of_three(r),
                "three_minus_two": three_launch_two_of_three(r) - two_launch_all_success(r),
            }
        )
    rows.append(
        {
            "single_launch_reliability": 0.995,
            "two_launch_all_success": two_launch_all_success(0.995),
            "three_launch_two_of_three": three_launch_two_of_three(0.995),
            "three_minus_two": three_launch_two_of_three(0.995) - two_launch_all_success(0.995),
        }
    )
    write_csv(TABLES / "reliability_sweep.csv", rows)
    return rows


def write_mission_chain_reliability() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    rendezvous_reliability = 0.98
    tli_reliability = 0.985
    for idx in range(90, 100):
        r_launch = idx / 100.0
        rows.append(
            {
                "single_launch_reliability": r_launch,
                "rendezvous_reliability": rendezvous_reliability,
                "tli_reliability": tli_reliability,
                "two_launch_only": two_launch_all_success(r_launch),
                "two_launch_leo_rendezvous_tli": two_launch_leo_tli_success(
                    r_launch,
                    rendezvous_reliability,
                    tli_reliability,
                ),
            }
        )
    rows.append(
        {
            "single_launch_reliability": 0.995,
            "rendezvous_reliability": rendezvous_reliability,
            "tli_reliability": tli_reliability,
            "two_launch_only": two_launch_all_success(0.995),
            "two_launch_leo_rendezvous_tli": two_launch_leo_tli_success(
                0.995,
                rendezvous_reliability,
                tli_reliability,
            ),
        }
    )
    write_csv(TABLES / "mission_chain_reliability.csv", rows)
    return rows


def write_mission_chain_sensitivity() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    single_launch_reliability = 0.95
    for rendezvous_reliability in [0.94, 0.96, 0.98, 0.99, 0.995]:
        for tli_reliability in [0.94, 0.96, 0.98, 0.985, 0.995]:
            rows.append(
                {
                    "single_launch_reliability": single_launch_reliability,
                    "rendezvous_reliability": rendezvous_reliability,
                    "tli_reliability": tli_reliability,
                    "mission_reliability": two_launch_leo_tli_success(
                        single_launch_reliability,
                        rendezvous_reliability,
                        tli_reliability,
                    ),
                }
            )
    write_csv(TABLES / "mission_chain_sensitivity.csv", rows)
    return rows


def write_engine_cluster_sweep() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    engine_reliabilities = [0.970, 0.980, 0.990, 0.995, 0.997, 0.999]
    for r in engine_reliabilities:
        rows.append(
            {
                "single_engine_reliability": r,
                "starship_33_no_engine_out": engine_cluster_reliability(
                    r,
                    STARSHIP_SUPER_HEAVY_ENGINE_COUNT,
                    allowed_engine_failures=0,
                ),
                "cz10_21_no_engine_out_assumed": engine_cluster_reliability(
                    r,
                    LONG_MARCH_10.first_stage_engine_count_assumed,
                    allowed_engine_failures=0,
                ),
                "cz10_21_allow_one_engine_out_assumed": engine_cluster_reliability(
                    r,
                    LONG_MARCH_10.first_stage_engine_count_assumed,
                    allowed_engine_failures=1,
                ),
            }
        )
    write_csv(TABLES / "engine_cluster_sweep.csv", rows)
    return rows


def write_delta_v_budget() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for altitude_km in [200, 300, 400, 500, 800, 1000]:
        estimate = hohmann_tli_estimate(float(altitude_km))
        rows.append(
            {
                "leo_altitude_km": estimate.leo_altitude_km,
                "leo_circular_speed_km_s": estimate.circular_speed_m_s / 1000.0,
                "transfer_perigee_speed_km_s": estimate.transfer_perigee_speed_m_s / 1000.0,
                "delta_v_tli_km_s": estimate.delta_v_tli_m_s / 1000.0,
                "time_of_flight_days": estimate.time_of_flight_days,
            }
        )
    write_csv(TABLES / "delta_v_budget.csv", rows)
    return rows


def write_tli_mass_budget() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for budget in default_mass_budget_sweep():
        rows.append(asdict(budget))
    write_csv(TABLES / "tli_mass_budget.csv", rows)
    return rows


def write_launch_geometry() -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for azimuth in range(60, 121, 5):
        point = geometry_point(WENCHANG.latitude_deg, float(azimuth))
        rows.append(
            {
                "launch_azimuth_deg": point.launch_azimuth_deg,
                "approximate_inclination_deg": point.approximate_inclination_deg,
                "eastward_rotation_gain_m_s": point.eastward_rotation_gain_m_s,
            }
        )
    write_csv(TABLES / "launch_geometry.csv", rows)
    return rows


def write_rendezvous_plan() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for estimate in default_rendezvous_sweep():
        rows.append(asdict(estimate))
    write_csv(TABLES / "rendezvous_plan.csv", rows)
    return rows


def write_ascent_baseline() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for state in simulate_ascent():
        rows.append(
            {
                "time_s": state.time_s,
                "downrange_km": state.downrange_km,
                "altitude_km": state.altitude_km,
                "horizontal_velocity_m_s": state.horizontal_velocity_m_s,
                "vertical_velocity_m_s": state.vertical_velocity_m_s,
                "speed_m_s": state.speed_m_s,
                "flight_path_angle_deg": state.flight_path_angle_deg,
                "pitch_deg": state.pitch_deg,
                "mass_t": state.mass_t,
                "dynamic_pressure_kpa": state.dynamic_pressure_kpa,
                "stage": state.stage,
            }
        )
    write_csv(TRAJECTORIES / "ascent_baseline.csv", rows)
    return rows


def write_ascent_eci_baseline() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    tuned_pitch = PitchProgram(pitch_end_time_s=305.0, final_pitch_deg=10.0, shape=1.4)
    for state in simulate_ascent_eci(pitch_program=tuned_pitch):
        rows.append(asdict(state))
    write_csv(TRAJECTORIES / "ascent_eci_baseline.csv", rows)
    return rows


def write_gravity_comparison() -> list[dict[str, object]]:
    tuned_pitch = PitchProgram(pitch_end_time_s=305.0, final_pitch_deg=10.0, shape=1.4)
    rows: list[dict[str, object]] = []
    results: dict[str, dict[str, object]] = {}
    for label, use_j2 in [("spherical", False), ("j2", True)]:
        trajectory = simulate_ascent_eci(pitch_program=tuned_pitch, use_j2=use_j2)
        last = asdict(trajectory[-1])
        max_q = max(state.dynamic_pressure_kpa for state in trajectory)
        row = {
            "gravity_model": label,
            "terminal_altitude_km": last["altitude_km"],
            "terminal_inertial_speed_m_s": last["inertial_speed_m_s"],
            "terminal_fpa_deg": last["flight_path_angle_deg"],
            "terminal_mass_t": last["mass_t"],
            "max_dynamic_pressure_kpa": max_q,
        }
        rows.append(row)
        results[label] = row

    spherical = results["spherical"]
    j2 = results["j2"]
    rows.append(
        {
            "gravity_model": "j2_minus_spherical",
            "terminal_altitude_km": j2["terminal_altitude_km"] - spherical["terminal_altitude_km"],
            "terminal_inertial_speed_m_s": j2["terminal_inertial_speed_m_s"] - spherical["terminal_inertial_speed_m_s"],
            "terminal_fpa_deg": j2["terminal_fpa_deg"] - spherical["terminal_fpa_deg"],
            "terminal_mass_t": j2["terminal_mass_t"] - spherical["terminal_mass_t"],
            "max_dynamic_pressure_kpa": j2["max_dynamic_pressure_kpa"] - spherical["max_dynamic_pressure_kpa"],
        }
    )
    write_csv(TABLES / "gravity_model_comparison.csv", rows)
    return rows


def write_optimization_summary() -> list[dict[str, object]]:
    rows = optimization_summary_rows()
    write_csv(TABLES / "optimization_summary.csv", rows)
    return rows


def write_figures(
    reliability_rows: list[dict[str, float]],
    mission_chain_rows: list[dict[str, float]],
    mission_chain_sensitivity_rows: list[dict[str, float]],
    cluster_rows: list[dict[str, float]],
    transfer_rows: list[dict[str, float]],
    mass_budget_rows: list[dict[str, float]],
    geometry_rows: list[dict[str, float]],
    rendezvous_rows: list[dict[str, object]],
    ascent_rows: list[dict[str, object]],
    ascent_eci_rows: list[dict[str, object]],
    gravity_comparison_rows: list[dict[str, object]],
    optimization_rows: list[dict[str, object]],
) -> None:
    write_line_chart(
        FIGURES / "mission_reliability.svg",
        "Mission reliability for modular CZ-10 architectures",
        "Single-launch reliability",
        "Mission success probability",
        [
            (
                "Two launches, both required",
                [(r["single_launch_reliability"], r["two_launch_all_success"]) for r in reliability_rows],
                "#1f77b4",
            ),
            (
                "Three launches, at least two required",
                [(r["single_launch_reliability"], r["three_launch_two_of_three"]) for r in reliability_rows],
                "#d62728",
            ),
        ],
    )

    write_line_chart(
        FIGURES / "engine_cluster_reliability.svg",
        "Engine-cluster sensitivity",
        "Single-engine critical-phase reliability",
        "Cluster reliability",
        [
            (
                "Starship Super Heavy 33, no engine-out",
                [(r["single_engine_reliability"], r["starship_33_no_engine_out"]) for r in cluster_rows],
                "#9467bd",
            ),
            (
                "CZ-10 assumed 21, no engine-out",
                [(r["single_engine_reliability"], r["cz10_21_no_engine_out_assumed"]) for r in cluster_rows],
                "#2ca02c",
            ),
            (
                "CZ-10 assumed 21, allow 1 engine-out",
                [(r["single_engine_reliability"], r["cz10_21_allow_one_engine_out_assumed"]) for r in cluster_rows],
                "#ff7f0e",
            ),
        ],
    )

    write_line_chart(
        FIGURES / "mission_chain_reliability.svg",
        "Two-launch LEO assembly reliability chain",
        "Single-launch reliability",
        "Mission success probability",
        [
            (
                "Two launches only",
                [(r["single_launch_reliability"], r["two_launch_only"]) for r in mission_chain_rows],
                "#1f77b4",
            ),
            (
                "Launches + rendezvous + TLI",
                [(r["single_launch_reliability"], r["two_launch_leo_rendezvous_tli"]) for r in mission_chain_rows],
                "#d62728",
            ),
        ],
    )

    sensitivity_series = []
    colors = ["#1f77b4", "#2ca02c", "#ff7f0e", "#d62728", "#9467bd"]
    for color, tli_value in zip(colors, [0.94, 0.96, 0.98, 0.985, 0.995]):
        points = [
            (r["rendezvous_reliability"], r["mission_reliability"])
            for r in mission_chain_sensitivity_rows
            if abs(r["tli_reliability"] - tli_value) < 1e-12
        ]
        sensitivity_series.append((f"TLI reliability {tli_value:.3f}", points, color))
    write_line_chart(
        FIGURES / "mission_chain_sensitivity.svg",
        "Rendezvous and TLI reliability sensitivity",
        "Rendezvous reliability",
        "Mission success probability",
        sensitivity_series,
    )

    write_line_chart(
        FIGURES / "tli_delta_v.svg",
        "Hohmann-style TLI estimate",
        "LEO parking altitude (km)",
        "TLI delta-v (km/s)",
        [
            (
                "Delta-v",
                [(r["leo_altitude_km"], r["delta_v_tli_km_s"]) for r in transfer_rows],
                "#1f77b4",
            )
        ],
    )

    write_line_chart(
        FIGURES / "tli_mass_budget.svg",
        "LEO stack mass required for combined TLI",
        "TLI stage Isp (s)",
        "Initial LEO stack mass (t)",
        [
            (
                f"structural fraction {sf:.2f}",
                [
                    (r["tli_stage_isp_s"], r["initial_leo_stack_t"])
                    for r in mass_budget_rows
                    if abs(r["tli_stage_structural_fraction"] - sf) < 1e-12
                ],
                color,
            )
            for sf, color in [(0.06, "#1f77b4"), (0.08, "#d62728"), (0.10, "#2ca02c")]
        ],
    )

    write_line_chart(
        FIGURES / "launch_geometry.svg",
        "Wenchang launch azimuth geometry",
        "Launch azimuth (deg from north)",
        "Inclination (deg) / rotation gain (km/s)",
        [
            (
                "Approx inclination",
                [(r["launch_azimuth_deg"], r["approximate_inclination_deg"]) for r in geometry_rows],
                "#d62728",
            ),
            (
                "Rotation gain km/s",
                [(r["launch_azimuth_deg"], r["eastward_rotation_gain_m_s"] / 1000.0) for r in geometry_rows],
                "#2ca02c",
            ),
        ],
    )

    write_line_chart(
        FIGURES / "rendezvous_plan.svg",
        "LEO rendezvous phasing estimate",
        "Phasing altitude (km)",
        "Wait time (h) / delta-v (m/s)",
        [
            (
                "Wait time h",
                [(float(r["phasing_altitude_km"]), float(r["wait_time_hours"])) for r in rendezvous_rows],
                "#1f77b4",
            ),
            (
                "Total delta-v m/s",
                [(float(r["phasing_altitude_km"]), float(r["total_rendezvous_delta_v_m_s"])) for r in rendezvous_rows],
                "#d62728",
            ),
        ],
    )

    write_line_chart(
        FIGURES / "ascent_altitude_speed.svg",
        "v0.6 ascent proxy: altitude and speed",
        "Time (s)",
        "Altitude (km) / speed (km/s)",
        [
            (
                "Altitude km",
                [(float(r["time_s"]), float(r["altitude_km"])) for r in ascent_rows],
                "#1f77b4",
            ),
            (
                "Speed km/s",
                [(float(r["time_s"]), float(r["speed_m_s"]) / 1000.0) for r in ascent_rows],
                "#d62728",
            ),
        ],
    )

    write_line_chart(
        FIGURES / "ascent_mass_q.svg",
        "v0.6 ascent proxy: mass and dynamic pressure",
        "Time (s)",
        "Mass (t) / q (kPa)",
        [
            (
                "Mass t",
                [(float(r["time_s"]), float(r["mass_t"])) for r in ascent_rows],
                "#2ca02c",
            ),
            (
                "Dynamic pressure kPa",
                [(float(r["time_s"]), float(r["dynamic_pressure_kpa"])) for r in ascent_rows],
                "#ff7f0e",
            ),
        ],
    )

    write_line_chart(
        FIGURES / "ascent_eci_altitude_speed.svg",
        "v0.6 ECI ascent: altitude and inertial speed",
        "Time (s)",
        "Altitude (km) / speed (km/s)",
        [
            (
                "Altitude km",
                [(float(r["time_s"]), float(r["altitude_km"])) for r in ascent_eci_rows],
                "#1f77b4",
            ),
            (
                "Inertial speed km/s",
                [(float(r["time_s"]), float(r["inertial_speed_m_s"]) / 1000.0) for r in ascent_eci_rows],
                "#d62728",
            ),
        ],
    )

    pitch_rows = [r for r in optimization_rows if r["category"] == "ascent_pitch"]
    rendezvous_opt_rows = [r for r in optimization_rows if r["category"] == "leo_rendezvous"]
    eci_pitch_rows = [r for r in optimization_rows if r["category"] == "eci_ascent_pitch"]
    write_line_chart(
        FIGURES / "optimization_scores.svg",
        "v0.6 grid-search objective scores",
        "Candidate rank",
        "Score",
        [
            (
                "Ascent pitch score",
                [(float(r["rank"]), float(r["score"])) for r in pitch_rows],
                "#2ca02c",
            ),
            (
                "LEO rendezvous score",
                [(float(r["rank"]), float(r["score"])) for r in rendezvous_opt_rows],
                "#ff7f0e",
            ),
            (
                "ECI ascent pitch score",
                [(float(r["rank"]), float(r["score"])) for r in eci_pitch_rows],
                "#9467bd",
            ),
        ],
    )


def write_summary(
    architecture_rows: list[dict[str, object]],
    reliability_rows: list[dict[str, float]],
    mission_chain_rows: list[dict[str, float]],
    mission_chain_sensitivity_rows: list[dict[str, float]],
    transfer_rows: list[dict[str, float]],
    mass_budget_rows: list[dict[str, float]],
    geometry_rows: list[dict[str, float]],
    rendezvous_rows: list[dict[str, object]],
    ascent_rows: list[dict[str, object]],
    ascent_eci_rows: list[dict[str, object]],
    gravity_comparison_rows: list[dict[str, object]],
    optimization_rows: list[dict[str, object]],
) -> None:
    recommended = next(row for row in architecture_rows if row["key"] == "B_two_leo_rendezvous")
    tli_300 = next(row for row in transfer_rows if row["leo_altitude_km"] == 300.0)
    east = next(row for row in geometry_rows if row["launch_azimuth_deg"] == 90.0)
    last_ascent = ascent_rows[-1]
    last_ascent_eci = ascent_eci_rows[-1]
    max_q = max(float(row["dynamic_pressure_kpa"]) for row in ascent_rows)
    max_q_eci = max(float(row["dynamic_pressure_kpa"]) for row in ascent_eci_rows)
    best_rendezvous = min(
        rendezvous_rows,
        key=lambda row: float(row["total_rendezvous_delta_v_m_s"]) + float(row["wait_time_hours"]),
    )
    best_pitch = next(row for row in optimization_rows if row["category"] == "ascent_pitch" and int(row["rank"]) == 1)
    best_eci_pitch = next(row for row in optimization_rows if row["category"] == "eci_ascent_pitch" and int(row["rank"]) == 1)
    best_rendezvous_opt = next(row for row in optimization_rows if row["category"] == "leo_rendezvous" and int(row["rank"]) == 1)
    chain_at_095 = next(row for row in mission_chain_rows if row["single_launch_reliability"] == 0.95)
    sensitivity_best = max(mission_chain_sensitivity_rows, key=lambda row: row["mission_reliability"])
    sensitivity_worst = min(mission_chain_sensitivity_rows, key=lambda row: row["mission_reliability"])
    nominal_mass_budget = next(
        row
        for row in mass_budget_rows
        if row["tli_stage_isp_s"] == 450.0 and row["tli_stage_structural_fraction"] == 0.08
    )
    gravity_difference = next(row for row in gravity_comparison_rows if row["gravity_model"] == "j2_minus_spherical")
    summary = {
        "recommended_architecture": recommended,
        "mission_chain_reliability_at_launch_095": chain_at_095,
        "mission_chain_sensitivity_best": sensitivity_best,
        "mission_chain_sensitivity_worst": sensitivity_worst,
        "tli_estimate_at_300_km": tli_300,
        "nominal_tli_mass_budget": nominal_mass_budget,
        "gravity_model_j2_minus_spherical": gravity_difference,
        "leo_rendezvous_recommended": best_rendezvous,
        "wenchang_rotation_speed_m_s": earth_rotation_speed_at_latitude(WENCHANG.latitude_deg),
        "east_launch_geometry": east,
        "ascent_proxy_terminal": last_ascent,
        "ascent_proxy_max_dynamic_pressure_kpa": max_q,
        "ascent_eci_terminal": last_ascent_eci,
        "ascent_eci_max_dynamic_pressure_kpa": max_q_eci,
        "best_ascent_pitch_candidate": best_pitch,
        "best_eci_ascent_pitch_candidate": best_eci_pitch,
        "best_rendezvous_optimization_candidate": best_rendezvous_opt,
        "vehicle": asdict(LONG_MARCH_10),
    }
    (TABLES / "baseline_summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def write_csv(path: Path, rows: list[dict[str, object]]) -> None:
    if not rows:
        raise ValueError("cannot write empty CSV")
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
