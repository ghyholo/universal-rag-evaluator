from __future__ import annotations

import itertools
import random
from statistics import mean, pstdev
from typing import Iterable


def paired_differences(a: Iterable[float], b: Iterable[float]) -> list[float]:
    a_values = list(a)
    b_values = list(b)
    if len(a_values) != len(b_values):
        raise ValueError("paired samples must have the same length")
    return [right - left for left, right in zip(a_values, b_values)]


def bootstrap_ci(
    differences: list[float], iterations: int = 5000, seed: int = 7
) -> tuple[float, float]:
    if not differences:
        return 0.0, 0.0
    if iterations < 100:
        raise ValueError("iterations must be at least 100")
    rng = random.Random(seed)
    sampled_means = []
    n = len(differences)
    for _ in range(iterations):
        sampled_means.append(mean(rng.choice(differences) for _ in range(n)))
    sampled_means.sort()
    low_index = int(0.025 * (iterations - 1))
    high_index = int(0.975 * (iterations - 1))
    return sampled_means[low_index], sampled_means[high_index]


def sign_flip_pvalue(
    differences: list[float], iterations: int = 10000, seed: int = 7
) -> float:
    nonzero = [value for value in differences if value != 0]
    if not nonzero:
        return 1.0
    observed = abs(mean(nonzero))
    n = len(nonzero)
    if n <= 18:
        values = [
            abs(mean(value * sign for value, sign in zip(nonzero, signs)))
            for signs in itertools.product((-1, 1), repeat=n)
        ]
        return sum(value >= observed for value in values) / len(values)
    rng = random.Random(seed)
    values = [
        abs(mean(value * rng.choice((-1, 1)) for value in nonzero))
        for _ in range(iterations)
    ]
    return (sum(value >= observed for value in values) + 1) / (len(values) + 1)


def effect_size(differences: list[float]) -> float:
    """Paired standardized mean difference (Cohen's dz)."""
    if len(differences) < 2:
        return 0.0
    sd = pstdev(differences)
    return mean(differences) / sd if sd else 0.0


def holm_adjust(p_values: list[float]) -> list[float]:
    indexed = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [0.0] * len(p_values)
    running = 0.0
    m = len(p_values)
    for rank, (index, p_value) in enumerate(indexed):
        candidate = min(1.0, (m - rank) * p_value)
        running = max(running, candidate)
        adjusted[index] = running
    return adjusted
