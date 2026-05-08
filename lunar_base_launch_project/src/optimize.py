"""Dependency-free grid searches for v0.4."""

from __future__ import annotations

from objectives import (
    EciPitchCandidate,
    PitchCandidate,
    RendezvousCandidate,
    evaluate_eci_pitch_candidate,
    evaluate_pitch_candidate,
    evaluate_rendezvous_candidate,
)


def pitch_grid_search() -> list[PitchCandidate]:
    """Return pitch candidates sorted by objective score."""

    candidates: list[PitchCandidate] = []
    for pitch_end in [400.0, 420.0, 440.0, 460.0, 480.0, 500.0]:
        for final_pitch in [0.0, 2.0, 4.0, 6.0, 8.0]:
            candidates.append(evaluate_pitch_candidate(pitch_end, final_pitch))
    return sorted(candidates, key=lambda item: item.score)


def rendezvous_grid_search() -> list[RendezvousCandidate]:
    """Return phasing-orbit candidates sorted by objective score."""

    candidates: list[RendezvousCandidate] = []
    for target_altitude in [280.0, 300.0, 320.0]:
        for phasing_altitude in [target_altitude - 40.0, target_altitude - 20.0, target_altitude - 10.0, target_altitude + 10.0, target_altitude + 20.0, target_altitude + 40.0]:
            candidates.append(evaluate_rendezvous_candidate(target_altitude, phasing_altitude))
    return sorted(candidates, key=lambda item: item.score)


def eci_pitch_grid_search() -> list[EciPitchCandidate]:
    """Return ECI pitch candidates sorted by objective score."""

    candidates: list[EciPitchCandidate] = []
    for pitch_end in [300.0, 305.0, 310.0, 315.0, 320.0, 325.0, 330.0, 335.0, 340.0]:
        for final_pitch in [6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0]:
            for shape in [1.2, 1.3, 1.35, 1.4, 1.5]:
                candidates.append(evaluate_eci_pitch_candidate(pitch_end, final_pitch, shape=shape))
    return sorted(candidates, key=lambda item: item.score)


def optimization_summary_rows(max_rows: int = 10) -> list[dict[str, object]]:
    """Return combined optimization rows for CSV output."""

    rows: list[dict[str, object]] = []
    for rank, candidate in enumerate(pitch_grid_search()[:max_rows], start=1):
        rows.append(
            {
                "category": "ascent_pitch",
                "rank": rank,
                "parameter_1": "pitch_end_time_s",
                "value_1": candidate.pitch_end_time_s,
                "parameter_2": "final_pitch_deg",
                "value_2": candidate.final_pitch_deg,
                "parameter_3": "",
                "value_3": "",
                "metric_1": "terminal_altitude_km",
                "metric_value_1": candidate.terminal_altitude_km,
                "metric_2": "terminal_speed_m_s",
                "metric_value_2": candidate.terminal_speed_m_s,
                "score": candidate.score,
            }
        )
    for rank, candidate in enumerate(rendezvous_grid_search()[:max_rows], start=1):
        rows.append(
            {
                "category": "leo_rendezvous",
                "rank": rank,
                "parameter_1": "target_altitude_km",
                "value_1": candidate.target_altitude_km,
                "parameter_2": "phasing_altitude_km",
                "value_2": candidate.phasing_altitude_km,
                "parameter_3": "",
                "value_3": "",
                "metric_1": "wait_time_hours",
                "metric_value_1": candidate.wait_time_hours,
                "metric_2": "total_delta_v_m_s",
                "metric_value_2": candidate.total_delta_v_m_s,
                "score": candidate.score,
            }
        )
    for rank, candidate in enumerate(eci_pitch_grid_search()[:max_rows], start=1):
        rows.append(
            {
                "category": "eci_ascent_pitch",
                "rank": rank,
                "parameter_1": "pitch_end_time_s",
                "value_1": candidate.pitch_end_time_s,
                "parameter_2": "final_pitch_deg",
                "value_2": candidate.final_pitch_deg,
                "parameter_3": "shape",
                "value_3": candidate.shape,
                "metric_1": "terminal_altitude_km",
                "metric_value_1": candidate.terminal_altitude_km,
                "metric_2": "terminal_inertial_speed_m_s",
                "metric_value_2": candidate.terminal_inertial_speed_m_s,
                "score": candidate.score,
            }
        )
    return rows
