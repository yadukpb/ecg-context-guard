"""Starfish Optimization Algorithm (SFOA) — generic, reusable by both paper reproductions.

Paper 2 cites SFOA as "a bio-inspired meta-heuristic algorithm" (Zhong et al., 2024) used to
tune both the HGAN-SVM-DT stage and the CNN-classifier stage. The paper itself gives SFOA's
objective functions (Eq. 4, Eq. 5) but not its internal update rules — those live in SFOA's
own publication, which was not uploaded alongside the two target papers for this task.

This is therefore an honest, documented **reimplementation from the algorithm's published
general mechanism** (a starfish's five-arm search: each "arm" explores independently, pulled
toward the best-found point for exploitation, with periodic "regeneration" of the worst
performers to keep exploring) — not a verified line-by-line port of the original paper's
exact operators. It is a real, runnable population-based optimizer that behaves like other
nature-inspired metaheuristics (PSO/GWO/WOA-family): if the official SFOA reference
implementation differs in operator detail, results will differ in degree, not in whether the
optimizer works at all.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

import numpy as np

ObjectiveFn = Callable[[np.ndarray], float]


@dataclass
class SFOAResult:
    best_params: np.ndarray
    best_score: float
    history: list[float]  # best score seen after each iteration, for a convergence plot


def minimize(
    objective_fn: ObjectiveFn,
    bounds: list[tuple[float, float]],
    population: int = 30,
    iterations: int = 50,
    seed: int = 0,
    regeneration_fraction: float = 0.2,
) -> SFOAResult:
    """Minimize ``objective_fn`` over a box-constrained parameter vector.

    ``objective_fn`` should return a score to MINIMIZE (negate accuracy-style objectives
    before passing them in). ``bounds`` is one ``(low, high)`` pair per parameter dimension.
    """
    rng = np.random.default_rng(seed)
    dims = len(bounds)
    low = np.array([b[0] for b in bounds])
    high = np.array([b[1] for b in bounds])

    arms = rng.uniform(low, high, size=(population, dims))
    scores = np.array([objective_fn(arm) for arm in arms])

    best_idx = int(np.argmin(scores))
    best_params = arms[best_idx].copy()
    best_score = float(scores[best_idx])
    history: list[float] = []

    n_regenerate = max(1, int(population * regeneration_fraction))

    for iteration in range(iterations):
        progress = iteration / max(1, iterations - 1)  # 0 -> 1, exploration -> exploitation

        for i in range(population):
            if rng.random() < 0.5:
                # Exploration: each arm takes an independent random step, shrinking over time.
                step = (high - low) * (1 - progress) * rng.uniform(-0.5, 0.5, size=dims)
                candidate = arms[i] + step
            else:
                # Exploitation: pull this arm toward the best-known point found so far.
                pull = rng.uniform(0, 1, size=dims)
                candidate = arms[i] + pull * (best_params - arms[i])

            candidate = np.clip(candidate, low, high)
            candidate_score = objective_fn(candidate)

            if candidate_score < scores[i]:
                arms[i] = candidate
                scores[i] = candidate_score

        # Regeneration: the worst-performing arms are redrawn at random, keeping the search
        # from collapsing entirely onto one local optimum (the starfish-arm-regrowth analogy).
        worst = np.argsort(scores)[-n_regenerate:]
        arms[worst] = rng.uniform(low, high, size=(n_regenerate, dims))
        scores[worst] = [objective_fn(arm) for arm in arms[worst]]

        gen_best_idx = int(np.argmin(scores))
        if scores[gen_best_idx] < best_score:
            best_score = float(scores[gen_best_idx])
            best_params = arms[gen_best_idx].copy()

        history.append(best_score)

    return SFOAResult(best_params=best_params, best_score=best_score, history=history)
