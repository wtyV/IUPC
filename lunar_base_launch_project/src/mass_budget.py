"""Mass budget estimates for the LEO-assembled translunar stack."""

from __future__ import annotations

from dataclasses import dataclass
from math import exp

from constants import G0
from transfer import hohmann_tli_estimate


@dataclass(frozen=True)
class TliMassBudget:
    leo_altitude_km: float
    delivered_cargo_t: float
    adapter_and_docking_t: float
    tli_stage_isp_s: float
    tli_stage_structural_fraction: float
    tli_delta_v_km_s: float
    mass_ratio: float
    tli_propellant_t: float
    tli_stage_dry_t: float
    initial_leo_stack_t: float
    leo_wet_mass_per_launch_t: float
    simulated_terminal_mass_per_launch_t: float
    simulated_margin_per_launch_t: float
    public_direct_tli_capacity_t: float
    direct_tli_margin_for_20t_module_t: float


def solve_tli_mass_budget(
    leo_altitude_km: float = 300.0,
    delivered_cargo_t: float = 40.0,
    adapter_and_docking_t: float = 4.0,
    tli_stage_isp_s: float = 450.0,
    tli_stage_structural_fraction: float = 0.08,
    simulated_terminal_mass_per_launch_t: float = 69.0,
    public_direct_tli_capacity_t: float = 27.0,
    module_payload_t: float = 20.0,
) -> TliMassBudget:
    """Estimate propellant and LEO wet mass needed for combined TLI.

    The structural fraction is dry mass divided by propellant mass. The dry
    stage remains with the stack at TLI cutoff in this simple budget.
    """

    if not (0.0 <= tli_stage_structural_fraction < 1.0):
        raise ValueError("tli_stage_structural_fraction must be in [0, 1)")
    tli = hohmann_tli_estimate(leo_altitude_km)
    mass_ratio = exp(tli.delta_v_tli_m_s / (tli_stage_isp_s * G0))
    final_non_prop_t = delivered_cargo_t + adapter_and_docking_t
    multiplier = mass_ratio - 1.0
    denominator = 1.0 - multiplier * tli_stage_structural_fraction
    if denominator <= 0.0:
        raise ValueError("stage structural fraction too high for requested delta-v")
    propellant_t = multiplier * final_non_prop_t / denominator
    dry_t = tli_stage_structural_fraction * propellant_t
    initial_stack_t = final_non_prop_t + propellant_t + dry_t
    per_launch_t = initial_stack_t / 2.0
    return TliMassBudget(
        leo_altitude_km=leo_altitude_km,
        delivered_cargo_t=delivered_cargo_t,
        adapter_and_docking_t=adapter_and_docking_t,
        tli_stage_isp_s=tli_stage_isp_s,
        tli_stage_structural_fraction=tli_stage_structural_fraction,
        tli_delta_v_km_s=tli.delta_v_tli_m_s / 1000.0,
        mass_ratio=mass_ratio,
        tli_propellant_t=propellant_t,
        tli_stage_dry_t=dry_t,
        initial_leo_stack_t=initial_stack_t,
        leo_wet_mass_per_launch_t=per_launch_t,
        simulated_terminal_mass_per_launch_t=simulated_terminal_mass_per_launch_t,
        simulated_margin_per_launch_t=simulated_terminal_mass_per_launch_t - per_launch_t,
        public_direct_tli_capacity_t=public_direct_tli_capacity_t,
        direct_tli_margin_for_20t_module_t=public_direct_tli_capacity_t - module_payload_t,
    )


def default_mass_budget_sweep() -> list[TliMassBudget]:
    budgets: list[TliMassBudget] = []
    for isp in [440.0, 450.0, 460.0]:
        for structural_fraction in [0.06, 0.08, 0.10]:
            budgets.append(
                solve_tli_mass_budget(
                    tli_stage_isp_s=isp,
                    tli_stage_structural_fraction=structural_fraction,
                )
            )
    return budgets

