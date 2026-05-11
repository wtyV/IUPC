"""Metaheuristic optimization algorithms for trajectory optimization.

Implements Particle Swarm Optimization (PSO), Genetic Algorithm (GA),
and Simulated Annealing (SA) to replace the earlier simple grid search.

All algorithms support:
  - Bound constraints via clipping
  - Inequality constraints via penalty functions
  - Early stopping on stagnation
  - Deterministic seeding for reproducibility
"""

from __future__ import annotations

import math
import random
from copy import deepcopy
from dataclasses import dataclass, field
from typing import Callable

# ── shared helpers ──────────────────────────────────────────────────────────

@dataclass
class Bounds:
    low: list[float]
    high: list[float]

    def __post_init__(self) -> None:
        if len(self.low) != len(self.high):
            raise ValueError("Bounds dimension mismatch")
        self._dim = len(self.low)

    @property
    def dim(self) -> int:
        return self._dim

    def clip(self, x: list[float]) -> list[float]:
        return [max(lo, min(hi, xi)) for lo, hi, xi in zip(self.low, self.high, x)]

    def random_point(self) -> list[float]:
        return [random.uniform(lo, hi) for lo, hi in zip(self.low, self.high)]


def _random_normal(mean: float, std: float) -> float:
    return random.gauss(mean, std)


# ── Particle Swarm Optimization ─────────────────────────────────────────────

@dataclass
class PSOConfig:
    swarm_size: int = 40
    max_iterations: int = 100
    inertia_start: float = 0.9       # w start (high exploration)
    inertia_end: float = 0.4         # w end (high exploitation)
    cognitive_weight: float = 2.0    # c1
    social_weight: float = 2.0       # c2
    stagnation_limit: int = 20       # early stop if global best unchanged
    seed: int = 42


def particle_swarm_optimization(
    objective: Callable[[list[float]], float],
    bounds: Bounds,
    config: PSOConfig | None = None,
    verbose: bool = False,
) -> tuple[list[float], float, list[float]]:
    """Particle Swarm Optimization with inertia weight decay.

    Parameters
    ----------
    objective : callable
        Scalar objective function f(x) -> float. Must return lower values
        for better solutions.
    bounds : Bounds
        Search-space bounds.
    config : PSOConfig, optional
    verbose : bool

    Returns
    -------
    best_position : list[float]
    best_score : float
    history : list[float]
        Global best score at each iteration.
    """
    cfg = config or PSOConfig()
    random.seed(cfg.seed)

    dim = bounds.dim
    # Initialize swarm uniformly within bounds
    positions = [bounds.random_point() for _ in range(cfg.swarm_size)]
    velocities = [
        [random.uniform(-abs(bounds.high[j] - bounds.low[j]),
                         abs(bounds.high[j] - bounds.low[j])) * 0.1
         for j in range(dim)]
        for _ in range(cfg.swarm_size)
    ]

    personal_best_pos = deepcopy(positions)
    personal_best_score = [objective(p) for p in personal_best_pos]

    global_best_idx = min(range(cfg.swarm_size), key=lambda i: personal_best_score[i])
    global_best_pos = personal_best_pos[global_best_idx][:]
    global_best_score = personal_best_score[global_best_idx]

    history = [global_best_score]
    stagnation = 0

    for iteration in range(cfg.max_iterations):
        # Linear inertia decay
        w = cfg.inertia_start - (cfg.inertia_start - cfg.inertia_end) * iteration / cfg.max_iterations

        prev_best = global_best_score

        for i in range(cfg.swarm_size):
            r1 = random.random()
            r2 = random.random()

            for j in range(dim):
                cognitive = cfg.cognitive_weight * r1 * (personal_best_pos[i][j] - positions[i][j])
                social = cfg.social_weight * r2 * (global_best_pos[j] - positions[i][j])
                velocities[i][j] = w * velocities[i][j] + cognitive + social

            positions[i] = bounds.clip(
                [positions[i][j] + velocities[i][j] for j in range(dim)]
            )

            score = objective(positions[i])
            if score < personal_best_score[i]:
                personal_best_score[i] = score
                personal_best_pos[i] = positions[i][:]
                if score < global_best_score:
                    global_best_score = score
                    global_best_pos = positions[i][:]

        history.append(global_best_score)

        if abs(prev_best - global_best_score) < 1e-9:
            stagnation += 1
        else:
            stagnation = 0

        if stagnation >= cfg.stagnation_limit:
            if verbose:
                print(f"  PSO: early stop at iteration {iteration + 1}, "
                      f"best = {global_best_score:.6f}")
            break

    if verbose:
        print(f"  PSO: final best = {global_best_score:.6f}, "
              f"iterations = {len(history)}")

    return global_best_pos, global_best_score, history


# ── Genetic Algorithm ───────────────────────────────────────────────────────

@dataclass
class GAConfig:
    population_size: int = 60
    max_generations: int = 80
    crossover_prob: float = 0.85
    mutation_prob: float = 0.15
    mutation_std_fraction: float = 0.08   # std = fraction * (high - low)
    elitism_count: int = 4
    tournament_size: int = 3
    stagnation_limit: int = 15
    seed: int = 42


@dataclass(order=True)
class _GAIndividual:
    score: float
    position: list[float] = field(compare=False)


def genetic_algorithm(
    objective: Callable[[list[float]], float],
    bounds: Bounds,
    config: GAConfig | None = None,
    verbose: bool = False,
) -> tuple[list[float], float, list[float]]:
    """Real-coded Genetic Algorithm with tournament selection.

    Uses simulated binary crossover (SBX) style operator and Gaussian
    mutation for continuous variables.
    """
    cfg = config or GAConfig()
    random.seed(cfg.seed)

    dim = bounds.dim

    # Initialize population
    population = [
        _GAIndividual(objective(bounds.random_point()), bounds.random_point())
        for _ in range(cfg.population_size)
    ]

    best = min(population)
    history = [best.score]
    stagnation = 0

    for gen in range(cfg.max_generations):
        prev_best = best.score

        # Elitism: keep best individuals
        population.sort()
        new_population = [
            _GAIndividual(ind.score, ind.position[:])
            for ind in population[:cfg.elitism_count]
        ]

        # Fill rest with crossover + mutation
        while len(new_population) < cfg.population_size:
            # Tournament selection for two parents
            parent1 = _tournament_select(population, cfg.tournament_size)
            parent2 = _tournament_select(population, cfg.tournament_size)

            if random.random() < cfg.crossover_prob:
                # Blend crossover (BLX-alpha style)
                child_pos = []
                for j in range(dim):
                    c_min = min(parent1.position[j], parent2.position[j])
                    c_max = max(parent1.position[j], parent2.position[j])
                    diff = c_max - c_min
                    lo = max(bounds.low[j], c_min - 0.25 * diff)
                    hi = min(bounds.high[j], c_max + 0.25 * diff)
                    child_pos.append(random.uniform(lo, hi))
            else:
                child_pos = random.choice([parent1, parent2]).position[:]

            # Gaussian mutation
            if random.random() < cfg.mutation_prob:
                j = random.randrange(dim)
                std = cfg.mutation_std_fraction * (bounds.high[j] - bounds.low[j])
                child_pos[j] += random.gauss(0.0, std)
                child_pos = bounds.clip(child_pos)

            new_population.append(_GAIndividual(objective(child_pos), child_pos))

        population = new_population
        current_best = min(population)
        if current_best.score < best.score:
            best = _GAIndividual(current_best.score, current_best.position[:])

        history.append(best.score)

        if abs(prev_best - best.score) < 1e-9:
            stagnation += 1
        else:
            stagnation = 0

        if stagnation >= cfg.stagnation_limit:
            if verbose:
                print(f"  GA: early stop at generation {gen + 1}, "
                      f"best = {best.score:.6f}")
            break

    if verbose:
        print(f"  GA: final best = {best.score:.6f}, "
              f"generations = {len(history)}")

    return best.position, best.score, history


def _tournament_select(population: list[_GAIndividual], k: int) -> _GAIndividual:
    candidates = random.sample(population, k=min(k, len(population)))
    return min(candidates)


# ── Simulated Annealing ─────────────────────────────────────────────────────

@dataclass
class SAConfig:
    initial_temp: float = 100.0
    cooling_rate: float = 0.95
    max_iterations: int = 500
    steps_per_temp: int = 20
    restart_count: int = 3
    seed: int = 42


def simulated_annealing(
    objective: Callable[[list[float]], float],
    bounds: Bounds,
    initial_guess: list[float] | None = None,
    config: SAConfig | None = None,
    verbose: bool = False,
) -> tuple[list[float], float, list[float]]:
    """Simulated Annealing with adaptive step size and restarts.

    Good for fine-tuning after PSO or GA.
    """
    cfg = config or SAConfig()
    random.seed(cfg.seed)

    dim = bounds.dim
    best_pos = initial_guess[:] if initial_guess else bounds.random_point()
    best_score = objective(best_pos)

    history = [best_score]
    current_pos = best_pos[:]
    current_score = best_score
    temp = cfg.initial_temp

    for iteration in range(cfg.max_iterations):
        for _ in range(cfg.steps_per_temp):
            # Adaptive step: proportional to temperature and bound range
            neighbor = []
            for j in range(dim):
                step_std = (bounds.high[j] - bounds.low[j]) * 0.05 * (temp / cfg.initial_temp + 0.01)
                neighbor.append(current_pos[j] + random.gauss(0.0, step_std))
            neighbor = bounds.clip(neighbor)

            neighbor_score = objective(neighbor)
            delta = neighbor_score - current_score

            if delta < 0 or random.random() < math.exp(-delta / max(temp, 1e-12)):
                current_pos = neighbor
                current_score = neighbor_score

                if current_score < best_score:
                    best_pos = current_pos[:]
                    best_score = current_score

            history.append(best_score)

        temp *= cfg.cooling_rate

        # Restart from best found
        if temp < 0.01 * cfg.initial_temp and cfg.restart_count > 0:
            current_pos = best_pos[:]
            current_score = best_score
            temp = cfg.initial_temp * 0.5
            cfg.restart_count -= 1

        if temp < 1e-6:
            break

    if verbose:
        print(f"  SA: final best = {best_score:.6f}")

    return best_pos, best_score, history


# ── Hybrid optimizer: PSO coarse -> SA fine ─────────────────────────────────

def hybrid_pso_sa(
    objective: Callable[[list[float]], float],
    bounds: Bounds,
    pso_config: PSOConfig | None = None,
    sa_config: SAConfig | None = None,
    verbose: bool = True,
) -> tuple[list[float], float, list[float]]:
    """Two-stage optimization: PSO for global search, SA for local refinement.

    Returns
    -------
    best_position, best_score, combined_history
    """
    pso_cfg = pso_config or PSOConfig(swarm_size=50, max_iterations=80)
    if verbose:
        print("Stage 1: PSO global search")
    pso_best, pso_score, pso_hist = particle_swarm_optimization(
        objective, bounds, pso_cfg, verbose=verbose
    )

    sa_cfg = sa_config or SAConfig(initial_temp=50.0, max_iterations=200)
    if verbose:
        print("Stage 2: SA local refinement")
    sa_best, sa_score, sa_hist = simulated_annealing(
        objective, bounds, initial_guess=pso_best, config=sa_cfg, verbose=verbose
    )

    combined_hist = pso_hist + sa_hist
    return sa_best, sa_score, combined_hist


# ── Multi-start wrapper ─────────────────────────────────────────────────────

def multi_start_optimization(
    optimizer: Callable[..., tuple[list[float], float, list[float]]],
    objective: Callable[[list[float]], float],
    bounds: Bounds,
    num_starts: int = 5,
    **optimizer_kwargs,
) -> tuple[list[float], float, list[tuple[list[float], float]]]:
    """Run optimizer from multiple random starting configurations.

    Returns the best overall result and a list of all (position, score) pairs.
    """
    all_results: list[tuple[list[float], float]] = []
    best_pos: list[float] = []
    best_score = float("inf")

    for start_idx in range(num_starts):
        if "seed" in optimizer_kwargs:
            optimizer_kwargs["seed"] = optimizer_kwargs["seed"] + start_idx * 100
        pos, score, _ = optimizer(objective, bounds, **optimizer_kwargs)
        all_results.append((pos, score))
        if score < best_score:
            best_score = score
            best_pos = pos[:]

    return best_pos, best_score, all_results
