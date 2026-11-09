"""Exact adaptive-tape product checks of conditional raw batch mean/variance.

All numbers describe a nonuniform-chance Kuhn SOFTWARE fixture, not poker
learning outcomes. This independently checks the sampled traversal primitive
against the full frozen expectation; no learner or reference solver is trained.
"""

import itertools
import math
from typing import Any

import numpy as np

from poker_ai.postflop.controlled_training import expected_pass
from poker_ai.postflop.training_isolation import (
    dense_updates,
    enumerate_pass,
    sentinel_policy,
    sentinel_tree,
)


def proofs() -> list[dict[str, Any]]:
    tree = sentinel_tree()
    rows: list[dict[str, Any]] = []
    for name, target in itertools.product(("positive", "zero_support"), (0, 1)):
        policy = sentinel_policy(tree, name)
        tapes = enumerate_pass(tree, policy, target, maximum_paths=10000)
        expected = expected_pass(tree, policy, target)
        samples = [
            (
                p,
                np.concatenate(
                    (
                        dense_updates(tree, u.regrets).ravel(),
                        dense_updates(tree, u.averages).ravel(),
                    )
                ),
            )
            for p, u in tapes
        ]
        full = np.concatenate(
            (
                dense_updates(tree, expected.regrets).ravel(),
                dense_updates(tree, expected.averages).ravel(),
            )
        )
        mean = sum((p * x for p, x in samples), np.zeros_like(full))
        variance = sum((p * (x - mean) ** 2 for p, x in samples), np.zeros_like(full))
        pair_mean, pair_var, clip_mean = (np.zeros_like(full) for _ in range(3))
        pair_count = 0
        for (pa, a), (pb, b) in itertools.product(samples, repeat=2):
            mass, average = pa * pb, (a + b) / 2
            pair_mean += mass * average
            pair_var += mass * (average - mean) ** 2
            clip_mean += mass * np.maximum(average, 0)
            pair_count += 1
        # Only the first half stores regret increments. Average probabilities
        # are nonnegative, so their clipping difference is trivially zero.
        width = len(full) // 2
        errors = dict(
            probability_mass_error=abs(math.fsum(p for p, _ in samples) - 1),
            single_mean_error=float(np.max(np.abs(mean - full))),
            pair_mean_error=float(np.max(np.abs(pair_mean - full))),
            variance_halving_error=float(np.max(np.abs(pair_var - variance / 2))),
        )
        if any(not math.isfinite(x) or x > 1e-12 for x in errors.values()):
            raise ArithmeticError("exact frozen-batch expectation/variance failed")
        rows.append(
            dict(
                scope="NONUNIFORM_KUHN_SOFTWARE_FIXTURE_NOT_HOLDEM_STRENGTH",
                policy=name,
                target=target,
                single_tapes=len(samples),
                independent_pair_tapes=pair_count,
                **errors,
                maximum_single_variance=float(variance.max()),
                maximum_pair_variance=float(pair_var.max()),
                maximum_expected_clip_vs_clip_expected=float(
                    np.max(np.abs(clip_mean[:width] - np.maximum(full[:width], 0)))
                ),
            )
        )
    if not any(r["maximum_expected_clip_vs_clip_expected"] > 1e-12 for r in rows):
        raise ArithmeticError("batch fixture missed clipping nonlinearity")
    return rows
