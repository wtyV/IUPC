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


# ── Payload-Fuel Split Mass Budget ─────────────────────────────────────────

@dataclass(frozen=True)
class SplitMassBudget:
    """Mass budget for the asymmetric payload+fuel split architecture.

    Launch A (payload first): cargo + adapter + TLI stage dry mass → LEO
    Launch B (fuel second):   TLI propellant only → LEO, fast rendezvous

    After docking, the combined stack performs TLI as a single stage.
    """
    leo_altitude_km: float
    # Mission payload
    cargo_mass_t: float               # lunar base construction materials
    adapter_and_docking_t: float      # docking mechanism + payload adapter
    # TLI stage
    tli_stage_dry_t: float            # TLI engine + structure + avionics
    tli_propellant_t: float           # TLI propellant (carried by Launch B)
    tli_isp_s: float
    tli_delta_v_km_s: float
    mass_ratio: float
    # LEO assembly
    launch_a_leo_mass_t: float        # Launch A wet mass to LEO
    launch_b_leo_mass_t: float        # Launch B wet mass to LEO
    combined_leo_stack_t: float       # Total stack before TLI
    post_tli_mass_t: float            # Mass after TLI burn (on transfer orbit)
    # Launch vehicle capacity check
    cz10_leo_capacity_t: float        # CZ-10 estimated LEO capacity
    launch_a_margin_t: float          # margin for Launch A
    launch_b_margin_t: float          # margin for Launch B


def solve_split_mass_budget(
    leo_altitude_km: float = 300.0,
    cargo_mass_t: float = 40.0,
    adapter_and_docking_t: float = 4.0,
    tli_stage_isp_s: float = 450.0,
    tli_stage_structural_fraction: float = 0.08,
    cz10_leo_capacity_t: float = 70.0,
) -> SplitMassBudget:
    """Compute mass budget for the payload+fuel split architecture.

    Architecture
    ------------
    Launch A (payload, launched first):
      - 40 t lunar base cargo (non-separable, stays with TLI stage)
      -  4 t docking adapter + mechanism
      -  m_dry (TLI stage engine/structure)
      Total to LEO: 40 + 4 + m_dry

    Launch B (fuel tanker, launched second):
      - m_prop (TLI propellant only)
      Total to LEO: m_prop

    Combined TLI stack:
      m0 = 40 + 4 + m_dry + m_prop  (before TLI burn)
      mf = 40 + 4 + m_dry            (after TLI burn, on lunar transfer)

    The TLI burn parameters are identical to the symmetric case:
      Δv = Isp · g0 · ln(m0/mf)
      The only difference is how mass is distributed between the two launches.
    """
    from transfer import hohmann_tli_estimate

    tli = hohmann_tli_estimate(leo_altitude_km)
    dv = tli.delta_v_tli_m_s

    # Fixed mass that must go to the Moon
    fixed_mass_t = cargo_mass_t + adapter_and_docking_t

    # Mass ratio: MR = m0/mf = exp(Δv / (Isp · g0))
    mass_ratio = exp(dv / (tli_stage_isp_s * G0))

    # Propellant mass from rocket equation with structural fraction
    # m0 = m_fixed + m_dry + m_prop = m_fixed + (1 + ε) · m_prop
    # mf = m_fixed + m_dry = m_fixed + ε · m_prop
    # MR = m0/mf = (m_fixed + (1+ε)·m_prop) / (m_fixed + ε·m_prop)
    # Solve for m_prop:
    multiplier = mass_ratio - 1.0
    denominator = 1.0 - multiplier * tli_stage_structural_fraction
    if denominator <= 0.0:
        raise ValueError("Structural fraction too high for requested Δv")
    propellant_t = multiplier * fixed_mass_t / denominator
    dry_t = tli_stage_structural_fraction * propellant_t

    # Launch A mass to LEO: cargo + adapter + TLI stage dry mass
    launch_a_mass_t = fixed_mass_t + dry_t

    # Launch B mass to LEO: TLI propellant only
    launch_b_mass_t = propellant_t

    # Combined stack
    combined_t = launch_a_mass_t + launch_b_mass_t
    post_tli_t = fixed_mass_t + dry_t

    return SplitMassBudget(
        leo_altitude_km=leo_altitude_km,
        cargo_mass_t=cargo_mass_t,
        adapter_and_docking_t=adapter_and_docking_t,
        tli_stage_dry_t=dry_t,
        tli_propellant_t=propellant_t,
        tli_isp_s=tli_stage_isp_s,
        tli_delta_v_km_s=dv / 1000.0,
        mass_ratio=mass_ratio,
        launch_a_leo_mass_t=launch_a_mass_t,
        launch_b_leo_mass_t=launch_b_mass_t,
        combined_leo_stack_t=combined_t,
        post_tli_mass_t=post_tli_t,
        cz10_leo_capacity_t=cz10_leo_capacity_t,
        launch_a_margin_t=cz10_leo_capacity_t - launch_a_mass_t,
        launch_b_margin_t=cz10_leo_capacity_t - launch_b_mass_t,
    )


def split_mass_budget_sweep() -> list[SplitMassBudget]:
    """Sensitivity sweep over Isp and structural fraction."""
    budgets: list[SplitMassBudget] = []
    for isp in [440.0, 450.0, 460.0]:
        for sf in [0.06, 0.08, 0.10]:
            budgets.append(
                solve_split_mass_budget(
                    tli_stage_isp_s=isp,
                    tli_stage_structural_fraction=sf,
                )
            )
    return budgets

