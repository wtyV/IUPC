"""Objective functions for first-pass mission optimization."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt

from ascent_3dof import PitchProgram, simulate_ascent
from ascent_eci import simulate_ascent_eci
from constants import MU_EARTH, R_EARTH_MEAN
from rendezvous import estimate_rendezvous


@dataclass(frozen=True)
class PitchCandidate:
    pitch_end_time_s: float
    final_pitch_deg: float
    terminal_altitude_km: float
    terminal_speed_m_s: float
    terminal_fpa_deg: float
    max_dynamic_pressure_kpa: float
    score: float


@dataclass(frozen=True)
class RendezvousCandidate:
    target_altitude_km: float
    phasing_altitude_km: float
    wait_time_hours: float
    total_delta_v_m_s: float
    score: float


@dataclass(frozen=True)
class EciPitchCandidate:
    pitch_end_time_s: float
    final_pitch_deg: float
    shape: float
    terminal_altitude_km: float
    terminal_inertial_speed_m_s: float
    terminal_fpa_deg: float
    max_dynamic_pressure_kpa: float
    score: float


def evaluate_pitch_candidate(
    pitch_end_time_s: float,
    final_pitch_deg: float,
    target_altitude_km: float = 300.0,
    target_speed_m_s: float = 7_700.0,
) -> PitchCandidate:
    """Score a pitch program against a rough LEO insertion target."""

    rows = simulate_ascent(
        pitch_program=PitchProgram(
            pitch_end_time_s=pitch_end_time_s,
            final_pitch_deg=final_pitch_deg,
        )
    )
    terminal = rows[-1]
    max_q = max(row.dynamic_pressure_kpa for row in rows)
    altitude_error = (terminal.altitude_km - target_altitude_km) / 100.0
    speed_error = (terminal.speed_m_s - target_speed_m_s) / 500.0
    fpa_error = terminal.flight_path_angle_deg / 5.0
    q_penalty = max(0.0, max_q - 60.0) / 20.0
    score = altitude_error**2 + speed_error**2 + fpa_error**2 + q_penalty**2
    return PitchCandidate(
        pitch_end_time_s=pitch_end_time_s,
        final_pitch_deg=final_pitch_deg,
        terminal_altitude_km=terminal.altitude_km,
        terminal_speed_m_s=terminal.speed_m_s,
        terminal_fpa_deg=terminal.flight_path_angle_deg,
        max_dynamic_pressure_kpa=max_q,
        score=score,
    )


def evaluate_rendezvous_candidate(
    target_altitude_km: float,
    phasing_altitude_km: float,
    phase_angle_deg: float = 40.0,
) -> RendezvousCandidate:
    """Score LEO phasing choices with small delta-v and reasonable wait time."""

    estimate = estimate_rendezvous(
        target_altitude_km=target_altitude_km,
        phasing_altitude_km=phasing_altitude_km,
        phase_angle_deg=phase_angle_deg,
    )
    wait_penalty = estimate.wait_time_hours / 24.0
    dv_penalty = estimate.total_rendezvous_delta_v_m_s / 100.0
    score = dv_penalty + 0.3 * wait_penalty
    return RendezvousCandidate(
        target_altitude_km=target_altitude_km,
        phasing_altitude_km=phasing_altitude_km,
        wait_time_hours=estimate.wait_time_hours,
        total_delta_v_m_s=estimate.total_rendezvous_delta_v_m_s,
        score=score,
    )


def evaluate_eci_pitch_candidate(
    pitch_end_time_s: float,
    final_pitch_deg: float,
    shape: float = 1.35,
    target_altitude_km: float = 300.0,
) -> EciPitchCandidate:
    """Score an ECI pitch program against a target circular parking orbit."""

    rows = simulate_ascent_eci(
        pitch_program=PitchProgram(
            pitch_end_time_s=pitch_end_time_s,
            final_pitch_deg=final_pitch_deg,
            shape=shape,
        )
    )
    terminal = rows[-1]
    target_radius = R_EARTH_MEAN + target_altitude_km * 1000.0
    target_speed = sqrt(MU_EARTH / target_radius)
    max_q = max(row.dynamic_pressure_kpa for row in rows)
    altitude_error = (terminal.altitude_km - target_altitude_km) / 100.0
    speed_error = (terminal.inertial_speed_m_s - target_speed) / 500.0
    fpa_error = terminal.flight_path_angle_deg / 5.0
    q_penalty = max(0.0, max_q - 60.0) / 20.0
    score = altitude_error**2 + speed_error**2 + fpa_error**2 + q_penalty**2
    return EciPitchCandidate(
        pitch_end_time_s=pitch_end_time_s,
        final_pitch_deg=final_pitch_deg,
        shape=shape,
        terminal_altitude_km=terminal.altitude_km,
        terminal_inertial_speed_m_s=terminal.inertial_speed_m_s,
        terminal_fpa_deg=terminal.flight_path_angle_deg,
        max_dynamic_pressure_kpa=max_q,
        score=score,
    )
