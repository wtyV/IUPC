"""Mission architecture definitions and metrics."""

from __future__ import annotations

from dataclasses import dataclass

from reliability import at_least_k_successes


@dataclass(frozen=True)
class Architecture:
    key: str
    description: str
    launches: int
    payload_each_t: float
    required_successes: int
    tli_capacity_each_t: float
    rendezvous_location: str
    transfer_strategy: str
    single_body_required: bool = False


@dataclass(frozen=True)
class ArchitectureResult:
    key: str
    feasible_by_mass: bool
    launches: int
    payload_each_t: float
    required_successes: int
    required_delivered_t: float
    delivered_if_required_successes_t: float
    delivered_if_all_success_t: float
    margin_each_t: float
    mission_reliability_at_095: float
    rendezvous_location: str
    transfer_strategy: str
    note: str


def default_architectures(tli_capacity_each_t: float = 27.0) -> list[Architecture]:
    return [
        Architecture(
            key="A_single_direct",
            description="One Long March 10 attempts to inject a 40 t payload to TLI.",
            launches=1,
            payload_each_t=40.0,
            required_successes=1,
            tli_capacity_each_t=tli_capacity_each_t,
            rendezvous_location="none",
            transfer_strategy="direct TLI attempt",
        ),
        Architecture(
            key="B_two_leo_rendezvous",
            description="Two 20 t cargo modules rendezvous and dock in LEO, then the combined stack performs TLI.",
            launches=2,
            payload_each_t=20.0,
            required_successes=2,
            tli_capacity_each_t=tli_capacity_each_t,
            rendezvous_location="LEO",
            transfer_strategy="LEO docking followed by combined TLI",
        ),
        Architecture(
            key="C_three_2of3_reliability_extension",
            description="Three 20 t cargo modules; any two successful launches satisfy 40 t.",
            launches=3,
            payload_each_t=20.0,
            required_successes=2,
            tli_capacity_each_t=tli_capacity_each_t,
            rendezvous_location="LEO or separate TLI",
            transfer_strategy="reliability extension only",
        ),
        Architecture(
            key="D_single_body_leo_assembly",
            description="Keep 40 t as one non-divisible payload and assemble it with a TLI stage in LEO.",
            launches=3,
            payload_each_t=0.0,
            required_successes=3,
            tli_capacity_each_t=tli_capacity_each_t,
            rendezvous_location="LEO",
            transfer_strategy="single-body payload plus external TLI propulsion",
            single_body_required=True,
        ),
    ]


def evaluate_architecture(
    architecture: Architecture,
    required_total_t: float = 40.0,
    single_launch_reliability: float = 0.95,
) -> ArchitectureResult:
    if architecture.single_body_required:
        return ArchitectureResult(
            key=architecture.key,
            feasible_by_mass=True,
            launches=architecture.launches,
            payload_each_t=architecture.payload_each_t,
            required_successes=architecture.required_successes,
            required_delivered_t=required_total_t,
            delivered_if_required_successes_t=required_total_t,
            delivered_if_all_success_t=required_total_t,
            margin_each_t=0.0,
            mission_reliability_at_095=at_least_k_successes(
                single_launch_reliability,
                architecture.launches,
                architecture.required_successes,
            ),
            rendezvous_location=architecture.rendezvous_location,
            transfer_strategy=architecture.transfer_strategy,
            note="Backup only: needed if the 40 t payload cannot be split into modules.",
        )

    margin_each = architecture.tli_capacity_each_t - architecture.payload_each_t
    feasible_by_mass = margin_each >= 0.0
    delivered_required = architecture.payload_each_t * architecture.required_successes
    delivered_all = architecture.payload_each_t * architecture.launches
    feasible = feasible_by_mass and delivered_required >= required_total_t
    note = "Recommended baseline architecture." if architecture.key == "B_two_leo_rendezvous" else ""
    if architecture.key == "C_three_2of3_reliability_extension":
        note = "Reliability extension, not the baseline because it adds a third launch."
    if not feasible_by_mass:
        note = "Rejected: payload exceeds public TLI capacity per launch."
    elif not feasible:
        note = "Rejected: required successful launches do not deliver 40 t."

    return ArchitectureResult(
        key=architecture.key,
        feasible_by_mass=feasible,
        launches=architecture.launches,
        payload_each_t=architecture.payload_each_t,
        required_successes=architecture.required_successes,
        required_delivered_t=required_total_t,
        delivered_if_required_successes_t=delivered_required,
        delivered_if_all_success_t=delivered_all,
        margin_each_t=margin_each,
        mission_reliability_at_095=at_least_k_successes(
            single_launch_reliability,
            architecture.launches,
            architecture.required_successes,
        ),
        rendezvous_location=architecture.rendezvous_location,
        transfer_strategy=architecture.transfer_strategy,
        note=note,
    )
