"""Independent explicit path sums/pure replies for tiny SOFTWARE fixtures only."""

import itertools

import numpy as np

from poker_ai.finite import ArrayTree, FloatArray


def terminal_sum(
    tree: ArrayTree, first: FloatArray, second: FloatArray, target: int
) -> float:
    total = 0.0
    pending = [(0, 1.0)]
    while pending:
        node, reach = pending.pop()
        actor = int(tree.player[node])
        if actor == -2:
            total += (
                reach * float(tree.terminal_values[node]) * (1 if target == 0 else -1)
            )
        else:
            for col in np.flatnonzero(tree.valid[node]):
                probability = (
                    float(tree.chance_edges[node, col])
                    if actor == -1
                    else float(
                        (first if actor == 0 else second)[tree.information[node], col]
                    )
                )
                pending.append((int(tree.children[node, col]), reach * probability))
    return total


def pure_root(tree: ArrayTree, opponent: FloatArray, target: int) -> float:
    owned = np.flatnonzero(tree.owners == target)
    best = -float("inf")
    for actions in itertools.product(*(range(len(tree.actions[i])) for i in owned)):
        own = opponent.copy()
        own[owned] = 0
        own[owned, np.asarray(actions)] = 1
        best = max(
            best,
            terminal_sum(
                tree,
                own if target == 0 else opponent,
                opponent if target == 0 else own,
                target,
            ),
        )
    return best


def metrics(tree: ArrayTree, policy: FloatArray) -> dict[str, float]:
    tree.validate_policy(policy)
    return dict(
        value_player_zero_chips=terminal_sum(tree, policy, policy, 0),
        exact_exploitability_chips=(
            pure_root(tree, policy, 0) + pure_root(tree, policy, 1)
        )
        / 2,
    )
