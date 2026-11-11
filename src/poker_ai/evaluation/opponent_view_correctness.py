"""Closed-form signal-game fixtures for own opponent-information controls.

Policies are analytic examples, never outputs of a learner or reference solver.
Independent terminal sums and exhaustive pure replies live in the tests.
"""

from dataclasses import replace
from typing import Any

import numpy as np

from poker_ai.finite import ArrayTree, IntArray
from poker_ai.postflop.opponent_views import bind_policy, build_view, compose
from poker_ai.toy.analysis import evaluate


def signal_game(risk_target: int = 0) -> tuple[ArrayTree, ArrayTree, IntArray]:
    if type(risk_target) is not int or risk_target not in (0, 1):
        raise ValueError("risk target must be zero or one")
    children = np.zeros((11, 2), dtype=np.int64)
    children[0], children[1], children[2] = (1, 2), (3, 5), (4, 6)
    children[5], children[6] = (7, 8), (9, 10)
    valid = np.zeros((11, 2), dtype=np.bool_)
    valid[[0, 1, 2, 5, 6]] = True
    chance = np.zeros((11, 2))
    chance[0] = [0.5, 0.5]
    sign = 1 if risk_target == 0 else -1
    fine = ArrayTree(
        children,
        valid,
        np.array(
            [
                -1,
                risk_target,
                risk_target,
                -2,
                -2,
                1 - risk_target,
                1 - risk_target,
                -2,
                -2,
                -2,
                -2,
            ]
        ),
        np.array([-1, 0, 1, -1, -1, 2, 3, -1, -1, -1, -1]),
        ("risk/signal0", "risk/signal1", "reply/signal0", "reply/signal1"),
        ((0, 1),) * 4,
        np.array([risk_target] * 2 + [1 - risk_target] * 2),
        np.ones((4, 2)),
        chance,
        np.array([1.0] + [0.5] * 10),
        sign * np.array([0.0, 0, 0, 0, 0, 0, 0, 1, -1, -1, 1]),
        (np.array([0]), np.array([1, 2]), np.array([5, 6])),
    )
    mapping = np.array([0, 0, 1, 1], dtype=np.int64)
    information = fine.information.copy()
    decision = fine.player >= 0
    information[decision] = mapping[information[decision]]
    coarse = replace(
        fine,
        information=information,
        keys=("risk/shared", "reply/shared"),
        actions=((0, 1),) * 2,
        owners=np.array([risk_target, 1 - risk_target]),
        legal=np.ones((2, 2)),
    )
    return fine, coarse, mapping


def analytic_proof() -> list[dict[str, Any]]:
    results = []
    for risk_target in (0, 1):
        fine, coarse, mapping = signal_game(risk_target)
        unsafe = np.array([[0.0, 1.0], [0.5, 0.5]])
        safe = np.array([[1.0, 0.0], [0.5, 0.5]])
        bundles = []
        for target in (0, 1):
            view = build_view(fine, coarse, mapping, target)
            policy = view.tree.normalize(view.tree.legal)
            owned = coarse.owners == target
            policy[view.coarse_own_to_view[owned]] = safe[owned]
            bundles.append((view, bind_policy(view, policy)))
        combined = compose(coarse, bundles[0], bundles[1])
        before_coarse = evaluate(coarse, unsafe)
        before_fine = evaluate(fine, unsafe[mapping])
        after_fine = evaluate(fine, combined[mapping])
        if (
            before_coarse.exploitability != 0
            or before_fine.exploitability != 0.5
            or after_fine.exploitability != 0
            or not np.array_equal(combined, safe)
        ):
            raise ArithmeticError("closed-form signal-game control failed")
        results.append(
            dict(
                risk_target=risk_target,
                coarse_unsafe_exploitability=before_coarse.exploitability,
                fine_unsafe_exploitability=before_fine.exploitability,
                fine_analytic_safe_exploitability=after_fine.exploitability,
                units="fictional payoff units",
                policies="analytic fixture, not trained or reference outputs",
                mixed_views=[v.sha256 for v, _ in bundles],
                long_run_admitted=False,
            )
        )
    return results
