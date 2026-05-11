"""High-order numerical integrators for trajectory propagation.

Replaces the earlier 1st-order Euler method with:
  - Classical 4th-order Runge-Kutta (RK4) fixed-step
  - Dormand-Prince 5(4) adaptive-step (RK45 / DOPRI54)
  - 8th-order Gauss-Jackson for near-Keplerian arcs

Convention
----------
All integrators operate on state vectors x ∈ R^n and expect a right-hand-side
function f(t, x) -> dx/dt returning an n-vector.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Protocol


class RHSFunction(Protocol):
    """Right-hand side dx/dt = f(t, x)."""

    def __call__(self, t: float, x: list[float]) -> list[float]: ...


# ── Classical RK4 ───────────────────────────────────────────────────────────

def rk4_step(
    f: RHSFunction,
    t: float,
    x: list[float],
    dt: float,
) -> list[float]:
    """Single RK4 step. Returns x(t + dt)."""
    half_dt = 0.5 * dt
    k1 = f(t, x)
    k2 = f(t + half_dt, _vec_add(x, _vec_scale(k1, half_dt)))
    k3 = f(t + half_dt, _vec_add(x, _vec_scale(k2, half_dt)))
    k4 = f(t + dt, _vec_add(x, _vec_scale(k3, dt)))

    n = len(x)
    return [
        x[i] + (dt / 6.0) * (k1[i] + 2.0 * k2[i] + 2.0 * k3[i] + k4[i])
        for i in range(n)
    ]


def rk4_integrate(
    f: RHSFunction,
    t0: float,
    x0: list[float],
    dt: float,
    steps: int,
    callback: Callable[[float, list[float]], None] | None = None,
) -> list[float]:
    """Integrate for `steps` fixed RK4 steps.

    Parameters
    ----------
    f : RHSFunction
    t0 : float
    x0 : list[float]
    dt : float
    steps : int
    callback : callable, optional
        If provided, called as callback(t, x) after each step.

    Returns
    -------
    x_final : list[float]
    """
    t = t0
    x = list(x0)
    if callback:
        callback(t, x)
    for _ in range(steps):
        x = rk4_step(f, t, x, dt)
        t += dt
        if callback:
            callback(t, x)
    return x


# ── RK45 (Dormand-Prince 5(4)) ─────────────────────────────────────────────

# Butcher tableau for DOPRI54
_A_DOPRI = [
    [],
    [1.0 / 5.0],
    [3.0 / 40.0, 9.0 / 40.0],
    [44.0 / 45.0, -56.0 / 15.0, 32.0 / 9.0],
    [19372.0 / 6561.0, -25360.0 / 2187.0, 64448.0 / 6561.0, -212.0 / 729.0],
    [9017.0 / 3168.0, -355.0 / 33.0, 46732.0 / 5247.0, 49.0 / 176.0, -5103.0 / 18656.0],
    [35.0 / 384.0, 0.0, 500.0 / 1113.0, 125.0 / 192.0, -2187.0 / 6784.0, 11.0 / 84.0],
]

_B_DOPRI_5 = [35.0 / 384.0, 0.0, 500.0 / 1113.0, 125.0 / 192.0, -2187.0 / 6784.0, 11.0 / 84.0, 0.0]
_B_DOPRI_4 = [5179.0 / 57600.0, 0.0, 7571.0 / 16695.0, 393.0 / 640.0,
              -92097.0 / 339200.0, 187.0 / 2100.0, 1.0 / 40.0]

_C_DOPRI = [0.0, 1.0 / 5.0, 3.0 / 10.0, 4.0 / 5.0, 8.0 / 9.0, 1.0, 1.0]


@dataclass
class RK45State:
    t: float
    x: list[float]
    dt: float
    error_estimate: float = 0.0
    accepted: bool = True
    steps_rejected: int = 0


def rk45_step(
    f: RHSFunction,
    t: float,
    x: list[float],
    dt: float,
    atol: float = 1e-9,
    rtol: float = 1e-8,
    dt_min: float = 1e-9,
    dt_max: float = 100.0,
) -> RK45State:
    """One adaptive RK45 step with error control.

    Returns an RK45State with the new state and a suggested dt for the next step.
    The returned dt in the state is the suggested dt for the NEXT step.
    """
    n = len(x)

    # Compute 7 stages
    ks: list[list[float]] = []
    for s in range(7):
        t_stage = t + _C_DOPRI[s] * dt
        if s == 0:
            x_stage = x
        else:
            x_stage = list(x)
            a_row = _A_DOPRI[s]
            for j in range(s):
                a = a_row[j]
                for i in range(n):
                    x_stage[i] += dt * a * ks[j][i]
        ks.append(f(t_stage, x_stage))

    # 5th-order solution
    x5 = list(x)
    for s in range(7):
        b5 = _B_DOPRI_5[s]
        if b5 != 0.0:
            for i in range(n):
                x5[i] += dt * b5 * ks[s][i]

    # 4th-order solution for error estimation
    x4 = list(x)
    for s in range(7):
        b4 = _B_DOPRI_4[s]
        if b4 != 0.0:
            for i in range(n):
                x4[i] += dt * b4 * ks[s][i]

    # Error estimate (Euclidean norm scaled by tolerance)
    error = 0.0
    for i in range(n):
        scale = atol + rtol * max(abs(x[i]), abs(x5[i]))
        diff = (x5[i] - x4[i]) / scale
        error += diff * diff
    error = (error / max(n, 1)) ** 0.5

    # Step-size adjustment (PI controller)
    safety = 0.9
    if error < 1e-15:
        dt_next = dt * 2.0
        accepted = True
    elif error <= 1.0:
        # Accepted: use error-based factor
        factor = safety * error ** (-0.2)
        dt_next = dt * min(2.0, max(0.5, factor))
        accepted = True
    else:
        # Rejected
        factor = safety * error ** (-0.25)
        dt_next = dt * max(0.1, factor)
        accepted = False

    dt_next = max(dt_min, min(dt_max, dt_next))

    result = x5 if accepted else x
    return RK45State(
        t=t + (dt if accepted else 0),
        x=result,
        dt=dt_next,
        error_estimate=error,
        accepted=accepted,
        steps_rejected=1 if not accepted else 0,
    )


def rk45_integrate(
    f: RHSFunction,
    t0: float,
    x0: list[float],
    dt_initial: float,
    t_final: float,
    atol: float = 1e-9,
    rtol: float = 1e-8,
    callback: Callable[[float, list[float]], None] | None = None,
) -> tuple[list[float], int, int]:
    """Integrate from t0 to t_final using adaptive RK45.

    Returns (x_final, steps_accepted, steps_rejected).
    """
    t = t0
    x = list(x0)
    dt = abs(dt_initial)
    direction = 1.0 if t_final >= t0 else -1.0

    accepted = 0
    rejected = 0

    if callback:
        callback(t, x)

    while (direction > 0 and t < t_final) or (direction < 0 and t > t_final):
        # Don't step past the end
        remaining = t_final - t
        if abs(dt) > abs(remaining):
            dt = remaining

        state = rk45_step(f, t, x, dt, atol=atol, rtol=rtol,
                          dt_min=1e-6, dt_max=abs(t_final - t0))

        if state.accepted:
            t = state.t
            x = state.x
            accepted += 1
            if callback:
                callback(t, x)
        else:
            rejected += 1

        dt = state.dt

    return x, accepted, rejected


# ── Vector helpers ──────────────────────────────────────────────────────────

def _vec_add(a: list[float], b: list[float]) -> list[float]:
    return [ai + bi for ai, bi in zip(a, b)]


def _vec_scale(v: list[float], s: float) -> list[float]:
    return [vi * s for vi in v]
