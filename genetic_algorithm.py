# -*- coding: utf-8 -*-
"""
Простий генетичний алгоритм для безперервної оптимізації (real-coded GA).

Реалізація класичного підходу до real-coded ГА: популяція векторів у межах bounds,
турнірний відбір, арифметичний кросовер, гаусова мутація з відсіканням,
елітизм, історія «найкращої придатності» по поколіннях.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from variants import VariantSpec, fitness_cost


@dataclass
class GAResult:
    best_phenotype: np.ndarray
    best_objective_value: float
    best_internal_cost: float
    generations: int
    history_best_cost: List[float]
    history_mean_cost: List[float]
    population_final: np.ndarray


def _clip_to_bounds(x: np.ndarray, low: np.ndarray, high: np.ndarray) -> np.ndarray:
    return np.minimum(np.maximum(x, low), high)


def _init_population(
    rng: np.random.Generator,
    pop_size: int,
    low: np.ndarray,
    high: np.ndarray,
) -> np.ndarray:
    u = rng.uniform(0.0, 1.0, size=(pop_size, low.size))
    return low + u * (high - low)


def _tournament(
    rng: np.random.Generator,
    population: np.ndarray,
    costs: np.ndarray,
    k: int,
) -> np.ndarray:
    """Повертає одного батька (мінімальний cost у турі)."""
    idx = rng.integers(0, population.shape[0], size=k)
    best = idx[0]
    for j in idx[1:]:
        if costs[j] < costs[best]:
            best = j
    return population[best].copy()


def _crossover_arithmetic(
    rng: np.random.Generator,
    p1: np.ndarray,
    p2: np.ndarray,
    pc: float,
) -> Tuple[np.ndarray, np.ndarray]:
    if rng.random() > pc:
        return p1.copy(), p2.copy()
    alpha = rng.random()
    c1 = alpha * p1 + (1.0 - alpha) * p2
    c2 = (1.0 - alpha) * p1 + alpha * p2
    return c1, c2


def _mutate_gaussian(
    rng: np.random.Generator,
    child: np.ndarray,
    low: np.ndarray,
    high: np.ndarray,
    pm: float,
    sigma_scale: float,
) -> np.ndarray:
    span = high - low
    sigma = np.maximum(sigma_scale * span, 1e-12 * (np.abs(high) + np.abs(low) + 1.0))
    out = child.copy()
    for i in range(out.size):
        if rng.random() < pm:
            out[i] += rng.normal(0.0, float(sigma[i]))
    return _clip_to_bounds(out, low, high)


def run_ga(
    spec: VariantSpec,
    *,
    population_size: int = 40,
    generations: int = 120,
    tournament_size: int = 3,
    crossover_prob: float = 0.85,
    mutation_prob: float = 0.15,
    mutation_sigma_scale: float = 0.05,
    elitism: int = 1,
    seed: Optional[int] = None,
) -> GAResult:
    """
    Запускає ГА для заданого варіанта.

    Усі задачі зводяться до мінімізації скаляра ``fitness_cost``.
    """
    if population_size < 2:
        raise ValueError("population_size має бути не менше 2 (потрібен турнірний відбір).")
    if generations < 1:
        raise ValueError("generations має бути >= 1.")
    if elitism < 0 or elitism >= population_size:
        raise ValueError("elitism має бути в діапазоні [0; population_size).")
    rng = np.random.default_rng(seed)
    low = np.array([b[0] for b in spec.bounds], dtype=float)
    high = np.array([b[1] for b in spec.bounds], dtype=float)
    if not np.all(np.isfinite(low)) or not np.all(np.isfinite(high)):
        raise ValueError("Межі bounds мають бути скінченними числами.")
    if not np.all(high > low):
        raise ValueError("У кожній парі bounds має бути left < right.")
    tsize = int(tournament_size)
    tsize = max(2, min(tsize, population_size))

    pop = _init_population(rng, population_size, low, high)
    hist_best: List[float] = []
    hist_mean: List[float] = []

    def eval_pop(p: np.ndarray) -> np.ndarray:
        return np.array([fitness_cost(spec, p[i]) for i in range(p.shape[0])], dtype=float)

    costs = eval_pop(pop)
    best_idx = int(np.argmin(costs))
    best = pop[best_idx].copy()
    best_cost = float(costs[best_idx])

    for _ in range(generations):
        hist_best.append(best_cost)
        hist_mean.append(float(np.mean(costs)))

        new_pop: List[np.ndarray] = []
        # елітизм
        elite_indices = np.argsort(costs)[:elitism]
        for ei in elite_indices:
            new_pop.append(pop[int(ei)].copy())

        while len(new_pop) < population_size:
            pa = _tournament(rng, pop, costs, tsize)
            pb = _tournament(rng, pop, costs, tsize)
            ca, cb = _crossover_arithmetic(rng, pa, pb, crossover_prob)
            ca = _mutate_gaussian(rng, ca, low, high, mutation_prob, mutation_sigma_scale)
            cb = _mutate_gaussian(rng, cb, low, high, mutation_prob, mutation_sigma_scale)
            new_pop.append(ca)
            if len(new_pop) < population_size:
                new_pop.append(cb)

        pop = np.stack(new_pop[:population_size], axis=0)
        costs = eval_pop(pop)
        gen_best_idx = int(np.argmin(costs))
        gen_best_cost = float(costs[gen_best_idx])
        if gen_best_cost < best_cost:
            best_cost = gen_best_cost
            best = pop[gen_best_idx].copy()

    hist_best.append(best_cost)
    hist_mean.append(float(np.mean(costs)))

    fval = spec.objective(best)
    return GAResult(
        best_phenotype=best,
        best_objective_value=float(fval),
        best_internal_cost=best_cost,
        generations=generations,
        history_best_cost=hist_best,
        history_mean_cost=hist_mean,
        population_final=pop,
    )
