"""Reliability formulas for engine clusters and multi-launch architectures."""

from __future__ import annotations

from math import comb


def engine_cluster_reliability(
    single_engine_reliability: float,
    engine_count: int,
    allowed_engine_failures: int = 0,
) -> float:
    """Return probability that an engine cluster remains acceptable.

    The model assumes independent engine outcomes during the critical phase.
    It is a sensitivity model, not a complete launch vehicle reliability model.
    """

    r = _clamp_probability(single_engine_reliability)
    if engine_count < 0:
        raise ValueError("engine_count must be non-negative")
    if allowed_engine_failures < 0:
        raise ValueError("allowed_engine_failures must be non-negative")

    max_failures = min(allowed_engine_failures, engine_count)
    total = 0.0
    for failures in range(max_failures + 1):
        successes = engine_count - failures
        total += comb(engine_count, failures) * ((1.0 - r) ** failures) * (r**successes)
    return total


def at_least_k_successes(single_launch_reliability: float, launches: int, required: int) -> float:
    """Return probability that at least ``required`` launches succeed."""

    r = _clamp_probability(single_launch_reliability)
    if launches < 0:
        raise ValueError("launches must be non-negative")
    if required < 0:
        raise ValueError("required must be non-negative")
    if required > launches:
        return 0.0

    total = 0.0
    for successes in range(required, launches + 1):
        failures = launches - successes
        total += comb(launches, successes) * (r**successes) * ((1.0 - r) ** failures)
    return total


def two_launch_all_success(single_launch_reliability: float) -> float:
    return at_least_k_successes(single_launch_reliability, launches=2, required=2)


def three_launch_two_of_three(single_launch_reliability: float) -> float:
    return at_least_k_successes(single_launch_reliability, launches=3, required=2)


def two_launch_leo_tli_success(
    single_launch_reliability: float,
    rendezvous_reliability: float,
    tli_reliability: float,
) -> float:
    """Return total reliability for the baseline two-launch LEO assembly mission."""

    return (
        two_launch_all_success(single_launch_reliability)
        * _clamp_probability(rendezvous_reliability)
        * _clamp_probability(tli_reliability)
    )


def _clamp_probability(value: float) -> float:
    if value < 0.0 or value > 1.0:
        raise ValueError("probability must be in [0, 1]")
    return value


# ── Asymmetric Launch Reliability (Payload-Fuel Split) ─────────────────────

def payload_fuel_split_reliability(
    launch_reliability: float,
    rendezvous_reliability: float,
    tli_reliability: float,
    fuel_relaunch_feasible: bool = False,
    fuel_relaunch_reliability: float = 0.95,
) -> float:
    """Reliability for the asymmetric payload+fuel split architecture.

    Launch A (payload): must succeed — mission-critical hardware.
    Launch B (fuel):    carries only propellant.

    If Launch B fails:
      - If fuel_relaunch_feasible: the payload can wait in LEO for a
        second fuel launch attempt. The mission succeeds if the relaunch
        succeeds.
      - If not feasible: mission fails (no fuel for TLI).

    Parameters
    ----------
    launch_reliability : float
        Single-launch success probability (assumed equal for both launches).
    rendezvous_reliability : float
        Probability that the LEO rendezvous and docking succeeds.
    tli_reliability : float
        Probability that the TLI burn succeeds.
    fuel_relaunch_feasible : bool
        Whether a failed fuel launch can be re-attempted.
    fuel_relaunch_reliability : float
        Reliability of the fuel re-launch attempt.

    Returns
    -------
    mission_reliability : float
    """
    r = _clamp_probability(launch_reliability)
    r_rend = _clamp_probability(rendezvous_reliability)
    r_tli = _clamp_probability(tli_reliability)

    # Probability both launches succeed on first attempt
    both_succeed = r * r

    if fuel_relaunch_feasible:
        # Launch A succeeds AND (Launch B succeeds OR Launch B fails but relaunch succeeds)
        r_relaunch = _clamp_probability(fuel_relaunch_reliability)
        launch_phase_success = r * (r + (1.0 - r) * r_relaunch)
    else:
        # Both must succeed
        launch_phase_success = both_succeed

    return launch_phase_success * r_rend * r_tli


def asymmetric_launch_sensitivity(
    launch_reliability: float = 0.95,
    rendezvous_reliability: float = 0.98,
    tli_reliability: float = 0.985,
) -> dict[str, float]:
    """Compare symmetric vs asymmetric launch reliability.

    Returns a dict comparing the payload-fuel split against the
    symmetric two-launch architecture.
    """
    symmetric = two_launch_leo_tli_success(
        launch_reliability, rendezvous_reliability, tli_reliability
    )

    asymmetric_no_relaunch = payload_fuel_split_reliability(
        launch_reliability, rendezvous_reliability, tli_reliability,
        fuel_relaunch_feasible=False,
    )

    asymmetric_with_relaunch = payload_fuel_split_reliability(
        launch_reliability, rendezvous_reliability, tli_reliability,
        fuel_relaunch_feasible=True,
        fuel_relaunch_reliability=launch_reliability,
    )

    return {
        "launch_reliability": launch_reliability,
        "rendezvous_reliability": rendezvous_reliability,
        "tli_reliability": tli_reliability,
        "symmetric_two_launch": symmetric,
        "asymmetric_no_relaunch": asymmetric_no_relaunch,
        "asymmetric_with_relaunch": asymmetric_with_relaunch,
    }
