"""Prespecified balanced binary-factor contrasts; no arm selection or inference."""

import itertools
import math
from collections.abc import Mapping
from typing import Any

FACTORS = {
    "traversal": ("full", "external"),
    "regret_rule": ("signed", "clipped"),
    "regret_weight": ("uniform", "linear"),
    "average_weight": ("uniform", "linear"),
}
LEVELS = tuple(itertools.product(*FACTORS.values()))


def contrasts(values: Mapping[tuple[str, ...], float]) -> dict[str, Any]:
    """Second minus first levels, holding others fixed and averaged interactions.

    A k-factor averaged difference is 2**k * mean(y * product(signs)),
    where first-listed levels have sign -1. This equals an average of paired
    k-way differences, not a fitted coefficient or a statistical significance.
    """
    if set(values) != set(LEVELS) or any(
        type(v) not in (int, float) or not math.isfinite(v) for v in values.values()
    ):
        raise ValueError("need all sixteen finite binary-factor means")
    names = list(FACTORS)
    conditional = []
    for index, name in enumerate(names):
        for levels in LEVELS:
            if levels[index] != FACTORS[name][0]:
                continue
            second = list(levels)
            second[index] = FACTORS[name][1]
            conditional.append(
                dict(
                    factor=name,
                    held={k: levels[i] for i, k in enumerate(names) if i != index},
                    difference=values[tuple(second)] - values[levels],
                )
            )
    factorial = []
    for order in range(1, 5):
        for indices in itertools.combinations(range(4), order):
            signed = []
            for levels, value in values.items():
                sign = math.prod(
                    -1 if levels[i] == FACTORS[names[i]][0] else 1 for i in indices
                )
                signed.append(sign * value)
            factorial.append(
                dict(
                    factors=[names[i] for i in indices],
                    order=order,
                    difference=2**order * math.fsum(signed) / 16,
                )
            )
    return dict(conditional=conditional, factorial=factorial)
