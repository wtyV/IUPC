"""Main optimization runner: replaces grid search with PSO/GA/SA.

This module performs a complete multi-stage optimization:

Stage 1: PSO global search for ascent pitch program parameters
Stage 2: SA local refinement of the best PSO result
Stage 3: Monte Carlo sensitivity analysis around the optimum
Stage 4: Generate comparison tables and figures

Usage:
    python run_optimization.py
"""

from __future__ import annotations

import csv
import json
import math
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

from ascent_full import (
    PitchProgramFull,
    VehicleModel,
    cz10_lunar_vehicle,
    simulate_ascent_full,
)
from constants import MU_EARTH, R_EARTH_MEAN, RAD_TO_DEG
from gravity_full import GravityConfig
from objectives_full import (
    OptimizationConfig,
    OptimizationResult,
    compare_gravity_models,
    evaluate_ascent_objective,
    make_ascent_objective,
)
from optimizers import (
    Bounds,
    PSOConfig,
    SAConfig,
    particle_swarm_optimization,
    simulated_annealing,
    hybrid_pso_sa,
)

# Import for mass budget and TLI
from mass_budget import solve_tli_mass_budget, TliMassBudget
from transfer_full import tli_injection, tli_sensitivity_sweep, TliInjection

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
TABLES = RESULTS / "tables"
TRAJECTORIES = RESULTS / "trajectories"


def main() -> None:
    print("=" * 70)
    print("Complete Ascent Trajectory Optimization")
    print("Using PSO + SA with Full Physics Models")
    print("=" * 70)

    TABLES.mkdir(parents=True, exist_ok=True)
    TRAJECTORIES.mkdir(parents=True, exist_ok=True)

    # ── Stage 1: PSO global optimization ──────────────────────────────
    print("\n" + "─" * 50)
    print("Stage 1: PSO Global Search for Optimal Pitch Program")
    print("─" * 50)

    bounds = Bounds(
        low=[200.0, 2.0, 0.8, 5.0],    # [pitch_end, final_pitch, shape, vertical_t]
        high=[400.0, 20.0, 2.0, 20.0],
    )

    opt_config = OptimizationConfig(
        target_altitude_km=300.0,
        max_q_kPa=60.0,
        max_accel_g=6.0,
    )
    gravity_cfg = GravityConfig(use_j2=True, use_j3=True, use_j4=True)

    objective_fn = make_ascent_objective(
        config=opt_config,
        gravity_config=gravity_cfg,
        verbose=False,
    )

    pso_cfg = PSOConfig(
        swarm_size=50,
        max_iterations=80,
        stagnation_limit=15,
        seed=42,
    )

    start_time = time.time()

    best_pos, best_score, pso_history = particle_swarm_optimization(
        objective_fn, bounds, pso_cfg, verbose=True,
    )

    pso_time = time.time() - start_time
    print(f"  PSO completed in {pso_time:.1f}s")

    # ── Stage 2: SA local refinement ───────────────────────────────────
    print("\n" + "─" * 50)
    print("Stage 2: SA Local Refinement")
    print("─" * 50)

    sa_cfg = SAConfig(
        initial_temp=30.0,
        cooling_rate=0.92,
        max_iterations=150,
        steps_per_temp=15,
        restart_count=2,
        seed=42,
    )

    start_time = time.time()

    refined_pos, refined_score, sa_history = simulated_annealing(
        objective_fn, bounds, initial_guess=best_pos, config=sa_cfg, verbose=True,
    )

    sa_time = time.time() - start_time
    print(f"  SA completed in {sa_time:.1f}s")

    # ── Detailed evaluation of best candidate ──────────────────────────
    print("\n" + "─" * 50)
    print("Stage 3: Detailed Evaluation of Optimal Solution")
    print("─" * 50)

    best_result = evaluate_ascent_objective(refined_pos, config=opt_config,
                                             gravity_config=gravity_cfg, verbose=True)

    # Also evaluate the PSO best for comparison
    pso_result = evaluate_ascent_objective(best_pos, config=opt_config,
                                           gravity_config=gravity_cfg)

    print_best_result(best_result, refined_pos)

    # ── Gravity model comparison ───────────────────────────────────────
    print("\n" + "─" * 50)
    print("Stage 4: Gravity Model Fidelity Comparison")
    print("─" * 50)

    grav_comparison = compare_gravity_models(refined_pos)
    for name, result in grav_comparison.items():
        print(f"  {name:12s}: alt={result.terminal_altitude_km:.2f} km, "
              f"v={result.terminal_inertial_speed_m_s/1000:.4f} km/s, "
              f"fpa={result.terminal_fpa_deg:+.3f} deg, "
              f"score={result.total_score:.4f}")

    # ── Generate full trajectory for the best solution ─────────────────
    print("\n" + "─" * 50)
    print("Stage 5: Generating Full Optimal Trajectory")
    print("─" * 50)

    best_pitch = PitchProgramFull(
        vertical_time_s=refined_pos[3],
        pitch_end_time_s=refined_pos[0],
        final_pitch_deg=refined_pos[1],
        shape_exponent=refined_pos[2],
    )

    full_traj = simulate_ascent_full(
        vehicle=cz10_lunar_vehicle(),
        pitch_program=best_pitch,
        dt_s=0.1,  # high-resolution for output
        gravity_config=gravity_cfg,
        max_altitude_m=500_000.0,
    )

    write_trajectory_csv(full_traj, TRAJECTORIES / "optimal_ascent_full.csv")
    print(f"  Trajectory with {len(full_traj)} points written.")

    # ── TLI budget computation ─────────────────────────────────────────
    print("\n" + "─" * 50)
    print("Stage 6: TLI Injection Budget")
    print("─" * 50)

    tli = tli_injection(leo_altitude_km=best_result.terminal_altitude_km)
    print(f"  TLI delta-v:      {tli.delta_v_tli_m_s/1000:.3f} km/s")
    print(f"  C3 energy:        {tli.c3_energy_km2_s2:.4f} km^2/s^2")
    print(f"  Transfer TOF:     {tli.time_of_flight_days:.2f} days")
    print(f"  Apogee speed:     {tli.transfer_apogee_speed_m_s/1000:.3f} km/s")
    print(f"  Mass ratio:       {tli.mass_ratio:.4f}")
    print(f"  Eccentricity:     {tli.transfer_eccentricity:.4f}")

    # ── TLI sensitivity sweep ──────────────────────────────────────────
    tli_sweep = tli_sensitivity_sweep()
    write_tli_sweep_csv(tli_sweep, TABLES / "tli_patched_conic_sweep.csv")

    # ── Mass budget ────────────────────────────────────────────────────
    print("\n" + "─" * 50)
    print("Stage 7: TLI Mass Budget")
    print("─" * 50)

    mass_budget = solve_tli_mass_budget(
        leo_altitude_km=best_result.terminal_altitude_km,
        simulated_terminal_mass_per_launch_t=best_result.terminal_mass_kg / 1000.0,
    )
    print(f"  LEO stack mass:          {mass_budget.initial_leo_stack_t:.1f} t")
    print(f"  TLI propellant:          {mass_budget.tli_propellant_t:.1f} t")
    print(f"  TLI stage dry mass:      {mass_budget.tli_stage_dry_t:.1f} t")
    print(f"  Per-launch LEO wet mass: {mass_budget.leo_wet_mass_per_launch_t:.1f} t")
    print(f"  Simulated margin:        {mass_budget.simulated_margin_per_launch_t:.1f} t")

    # ── Write summary JSON ─────────────────────────────────────────────
    write_optimization_summary(
        pso_result=pso_result,
        sa_result=best_result,
        pso_history=pso_history,
        sa_history=sa_history,
        grav_comparison=grav_comparison,
        tli=tli,
        mass_budget=mass_budget,
        pso_time=pso_time,
        sa_time=sa_time,
    )

    print("\n" + "=" * 70)
    print("Optimization complete. Results written to results/")
    print("=" * 70)


def print_best_result(result: OptimizationResult, design_vars: list[float]) -> None:
    """Print a formatted summary of the best optimization result."""
    print(f"\n  Design Variables:")
    print(f"    Pitch end time:    {result.pitch_end_time_s:.1f} s")
    print(f"    Final pitch:       {result.final_pitch_deg:.1f} deg")
    print(f"    Shape exponent:    {result.shape_exponent:.3f}")
    print(f"    Vertical time:     {result.vertical_time_s:.1f} s")
    print(f"\n  Terminal State:")
    print(f"    Altitude:          {result.terminal_altitude_km:.2f} km")
    print(f"    Inertial speed:    {result.terminal_inertial_speed_m_s:.1f} m/s")
    print(f"                    = {result.terminal_inertial_speed_m_s/1000:.4f} km/s")
    print(f"    Flight path angle: {result.terminal_fpa_deg:+.4f} deg")
    print(f"    Final mass:        {result.terminal_mass_kg:.1f} kg ({result.terminal_mass_kg/1000:.2f} t)")
    print(f"    Payload fraction:  {result.payload_fraction:.4f}")
    print(f"\n  Path Constraints:")
    print(f"    Max dynamic pressure:  {result.max_dynamic_pressure_kPa:.1f} kPa")
    print(f"    Max Mach number:       {result.max_mach_number:.1f}")
    print(f"    Max acceleration:      {result.max_acceleration_g:.2f} g")
    print(f"    Max heating rate:      {result.max_heating_rate_kW_m2:.1f} kW/m^2")
    print(f"\n  Feasibility: {'FEASIBLE' if result.is_feasible else 'INFEASIBLE'}")
    print(f"  Total Score: {result.total_score:.6f}")


def write_trajectory_csv(trajectory: list, path: Path) -> None:
    """Write full trajectory to CSV."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "time_s", "rx_m", "ry_m", "rz_m",
            "vx_m_s", "vy_m_s", "vz_m_s",
            "altitude_m", "inertial_speed_m_s", "relative_speed_m_s",
            "flight_path_angle_deg", "pitch_angle_deg", "mass_kg",
            "dynamic_pressure_Pa", "mach_number", "drag_force_N",
            "thrust_force_N", "axial_acceleration_g",
            "density_kg_m3", "temperature_K", "pressure_Pa",
            "stage_name", "stage_index",
        ])
        writer.writeheader()
        for s in trajectory:
            writer.writerow(asdict(s))


def write_tli_sweep_csv(sweep: list[TliInjection], path: Path) -> None:
    """Write TLI sensitivity sweep to CSV."""
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "leo_altitude_km", "leo_radius_m", "leo_circular_speed_m_s",
            "transfer_perigee_speed_m_s", "transfer_apogee_speed_m_s",
            "transfer_eccentricity", "transfer_semi_major_axis_m",
            "delta_v_tli_m_s", "c3_energy_km2_s2",
            "time_of_flight_days", "mass_ratio",
        ])
        writer.writeheader()
        for tli in sweep:
            writer.writerow(asdict(tli))


def write_optimization_summary(
    pso_result: OptimizationResult,
    sa_result: OptimizationResult,
    pso_history: list[float],
    sa_history: list[float],
    grav_comparison: dict[str, OptimizationResult],
    tli: TliInjection,
    mass_budget: TliMassBudget,
    pso_time: float,
    sa_time: float,
) -> None:
    """Write comprehensive optimization summary JSON."""
    target_radius = R_EARTH_MEAN + 300_000.0
    target_speed = math.sqrt(MU_EARTH / target_radius)

    summary = {
        "optimization_algorithm": "PSO + SA (Two-Stage Hybrid)",
        "pso_config": {
            "swarm_size": 50,
            "max_iterations": 80,
            "time_seconds": pso_time,
        },
        "sa_config": {
            "initial_temp": 30.0,
            "max_iterations": 150,
            "time_seconds": sa_time,
        },
        "design_space": {
            "pitch_end_time_s": {"min": 200, "max": 400, "optimal": sa_result.pitch_end_time_s},
            "final_pitch_deg": {"min": 2, "max": 20, "optimal": sa_result.final_pitch_deg},
            "shape_exponent": {"min": 0.8, "max": 2.0, "optimal": sa_result.shape_exponent},
            "vertical_time_s": {"min": 5, "max": 20, "optimal": sa_result.vertical_time_s},
        },
        "pso_best": {
            "design_vars": [pso_result.pitch_end_time_s, pso_result.final_pitch_deg,
                           pso_result.shape_exponent, pso_result.vertical_time_s],
            "score": pso_result.total_score,
            "terminal_altitude_km": pso_result.terminal_altitude_km,
            "terminal_speed_km_s": pso_result.terminal_inertial_speed_m_s / 1000.0,
            "terminal_fpa_deg": pso_result.terminal_fpa_deg,
        },
        "sa_best": {
            "design_vars": [sa_result.pitch_end_time_s, sa_result.final_pitch_deg,
                           sa_result.shape_exponent, sa_result.vertical_time_s],
            "score": sa_result.total_score,
            "terminal_altitude_km": sa_result.terminal_altitude_km,
            "terminal_speed_km_s": sa_result.terminal_inertial_speed_m_s / 1000.0,
            "terminal_fpa_deg": sa_result.terminal_fpa_deg,
            "terminal_mass_t": sa_result.terminal_mass_kg / 1000.0,
            "payload_fraction": sa_result.payload_fraction,
            "max_dynamic_pressure_kPa": sa_result.max_dynamic_pressure_kPa,
            "max_mach": sa_result.max_mach_number,
            "max_acceleration_g": sa_result.max_acceleration_g,
            "max_heating_kW_m2": sa_result.max_heating_rate_kW_m2,
            "is_feasible": sa_result.is_feasible,
        },
        "target_orbit": {
            "altitude_km": 300.0,
            "circular_speed_km_s": target_speed / 1000.0,
        },
        "orbit_injection_error": {
            "altitude_error_km": sa_result.terminal_altitude_km - 300.0,
            "speed_error_m_s": sa_result.terminal_inertial_speed_m_s - target_speed,
            "fpa_error_deg": sa_result.terminal_fpa_deg,
        },
        "gravity_model_comparison": {
            name: {
                "altitude_km": r.terminal_altitude_km,
                "speed_km_s": r.terminal_inertial_speed_m_s / 1000.0,
                "fpa_deg": r.terminal_fpa_deg,
                "score": r.total_score,
            }
            for name, r in grav_comparison.items()
        },
        "gravity_j2_j4_effect": {
            "altitude_delta_km": grav_comparison["J2_J3_J4"].terminal_altitude_km
                                 - grav_comparison["spherical"].terminal_altitude_km,
            "speed_delta_m_s": grav_comparison["J2_J3_J4"].terminal_inertial_speed_m_s
                               - grav_comparison["spherical"].terminal_inertial_speed_m_s,
        },
        "tli_injection": {
            "delta_v_km_s": tli.delta_v_tli_m_s / 1000.0,
            "c3_km2_s2": tli.c3_energy_km2_s2,
            "tof_days": tli.time_of_flight_days,
            "eccentricity": tli.transfer_eccentricity,
            "apogee_speed_km_s": tli.transfer_apogee_speed_m_s / 1000.0,
            "mass_ratio": tli.mass_ratio,
        },
        "tli_mass_budget": asdict(mass_budget),
        "optimization_history": {
            "pso_scores": pso_history,
            "sa_scores": sa_history,
        },
    }

    (TABLES / "optimization_summary_full.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print(f"\n  Summary written to {TABLES / 'optimization_summary_full.json'}")


if __name__ == "__main__":
    main()
