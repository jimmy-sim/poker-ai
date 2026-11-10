"""Exhaustive rational-bin checks on raw updates of a nonuniform Kuhn fixture.

Enumerate downstream adaptive tapes conditional on each joint private deal.
Compare every raw component mean with the independent full frozen expectation.
The rational interval intersections do not call the production CDF/stratifier.
No learner, real poker context or native reference is constructed here.
"""

import itertools
from fractions import Fraction
from typing import Any

import numpy as np

from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.controlled_training import ArrayState, expected_pass
from poker_ai.postflop.training_isolation import (
    NextChoice,
    dense_updates,
    sentinel_policy,
    sentinel_tree,
)
from poker_ai.training.mccfr import Updates, external_updates


def conditional_tapes(
    tree: ArrayTree, policy: FloatArray, target: int, first: int, second: int
) -> list[tuple[float, Updates]]:
    """Independent enumeration after two specified prefix choices, including
    separate opponent draws in all enumerated own-action subtrees.
    """
    lookup = {key: i for i, key in enumerate(tree.keys)}
    result: list[tuple[float, Updates]] = []

    def frozen(key: str, actions: tuple[int, ...]) -> FloatArray:
        info = lookup[key]
        if actions != tree.actions[info]:
            raise ArithmeticError("fixture action menu changed")
        return policy[info, : len(actions)].copy()

    def walk(tape: tuple[int, ...], mass: float) -> None:
        consumed = 0

        def select(probabilities: FloatArray) -> int:
            nonlocal consumed
            if consumed == len(tape):
                raise NextChoice(probabilities)
            index = tape[consumed]
            consumed += 1
            if probabilities[index] <= 0:
                raise ArithmeticError("fixture enumerated zero mass")
            return index

        try:
            update = external_updates(ArrayState(tree), target, frozen, select)
        except NextChoice as choice:
            for i, p in enumerate(choice.probabilities):
                if p > 0:
                    walk(tape + (i,), mass * float(p))
        else:
            if len(result) >= 10000:
                raise ArithmeticError("fixture adaptive enumeration cap")
            result.append((mass, update))

    walk((first, second), 1.0)
    return result


def bin_law(probabilities: list[Fraction], count: int) -> list[list[Fraction]]:
    """Exact half-open interval overlaps, conditional probability per bin."""
    if (
        type(count) is not int
        or count <= 0
        or not probabilities
        or any(p < 0 for p in probabilities)
        or sum(probabilities) != 1
    ):
        raise ValueError("invalid exact bin law")
    ends = list(itertools.accumulate(probabilities, initial=Fraction(0)))
    return [
        [
            count
            * max(
                Fraction(0),
                min(ends[j + 1], Fraction(i + 1, count))
                - max(ends[j], Fraction(i, count)),
            )
            for j in range(len(probabilities))
        ]
        for i in range(count)
    ]


def proofs() -> list[dict[str, Any]]:
    tree = sentinel_tree()
    paths = [(i, j) for i in range(3) for j in range(2)]
    # Deliberately independent rational description of the software fixture.
    joint = [
        p / 2
        for p in (Fraction(1, 10), Fraction(3, 10), Fraction(3, 5))
        for _ in range(2)
    ]
    rows: list[dict[str, Any]] = []
    for name, target in itertools.product(("positive", "zero_support"), (0, 1)):
        policy = sentinel_policy(tree, name)
        conditional = [conditional_tapes(tree, policy, target, i, j) for i, j in paths]

        def vector(update: Updates) -> FloatArray:
            return np.concatenate(
                (
                    dense_updates(tree, update.regrets).ravel(),
                    dense_updates(tree, update.averages).ravel(),
                )
            )

        expected = vector(expected_pass(tree, policy, target))
        by_deal = [[(p, vector(u)) for p, u in tapes] for tapes in conditional]
        mean = sum(
            (
                float(pj) * p * v
                for pj, tapes in zip(joint, by_deal, strict=True)
                for p, v in tapes
            ),
            np.zeros_like(expected),
        )
        variance = sum(
            (
                float(pj) * p * (v - mean) ** 2
                for pj, tapes in zip(joint, by_deal, strict=True)
                for p, v in tapes
            ),
            np.zeros_like(expected),
        )
        for batch in (2, 4, 16):
            law = bin_law(joint, batch)
            means, variances = [], []
            for bin_prob in law:
                m = sum(
                    (
                        float(pj) * p * v
                        for pj, tapes in zip(bin_prob, by_deal, strict=True)
                        for p, v in tapes
                    ),
                    np.zeros_like(expected),
                )
                v = sum(
                    (
                        float(pj) * p * (v - m) ** 2
                        for pj, tapes in zip(bin_prob, by_deal, strict=True)
                        for p, v in tapes
                    ),
                    np.zeros_like(expected),
                )
                means.append(m)
                variances.append(v)
            mean_strat = sum(means, np.zeros_like(expected)) / batch
            var_strat = sum(variances, np.zeros_like(expected)) / batch**2
            between = (
                sum(((m - mean) ** 2 for m in means), np.zeros_like(expected))
                / batch**2
            )
            errors = dict(
                conditional_mass=max(
                    abs(sum(p for p, _ in tapes) - 1) for tapes in conditional
                ),
                mean=float(np.max(np.abs(mean_strat - expected))),
                iid_mean=float(np.max(np.abs(mean - expected))),
                variance_decomposition=float(
                    np.max(np.abs(variance / batch - var_strat - between))
                ),
                variance_excess=float(
                    np.max(np.maximum(var_strat - variance / batch, 0))
                ),
            )
            if any(not np.isfinite(x) or x > 1e-12 for x in errors.values()):
                raise ArithmeticError("private-prefix raw moment identity failed")
            rows.append(
                dict(
                    scope="NONUNIFORM_KUHN_RAW_MOMENTS_NOT_POKER_STRENGTH",
                    policy=name,
                    target=target,
                    batch_size=batch,
                    conditional_tapes=sum(map(len, conditional)),
                    maximum_iid_batch_variance=float((variance / batch).max()),
                    maximum_stratified_batch_variance=float(var_strat.max()),
                    maximum_variance_reduction=float(between.max()),
                    errors=errors,
                )
            )
    if not any(row["maximum_variance_reduction"] > 1e-12 for row in rows):
        raise ArithmeticError("fixture missed a nontrivial stratification effect")
    return rows
