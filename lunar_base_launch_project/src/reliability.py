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
