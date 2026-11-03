"""Analytical equilibrium and independent pure-strategy enumeration checks."""

import itertools

import numpy as np
import pytest

from poker_ai.toy.analysis import best_response, evaluate
from poker_ai.toy.cfr import CFR, Variant
from poker_ai.toy.games import GameName, ToyState
from poker_ai.toy.tree import FloatArray, Tree


def recursive_value(state: ToyState, lookup: dict[str, dict[int, float]]) -> float:
    if state.terminal:
        return state.payoff
    probabilities = (
        {a: 1 / len(state.actions) for a in state.actions}
        if state.chance
        else lookup[state.information]
    )
    return sum(
        p * recursive_value(state.child(a), lookup) for a, p in probabilities.items()
    )


def test_kuhn_uniform_value_and_br_by_complete_pure_strategy_enumeration() -> None:
    tree = Tree.build("kuhn")
    policy = tree.normalize(tree.legal)
    lookup = {
        key: dict(zip(actions, row[: len(actions)], strict=True))
        for key, actions, row in zip(tree.keys, tree.actions, policy, strict=True)
    }
    assert recursive_value(ToyState("kuhn"), lookup) == pytest.approx(1 / 8)
    assert evaluate(tree, policy).value_player_zero == pytest.approx(1 / 8)
    for player in (0, 1):
        infos = [i for i, owner in enumerate(tree.owners) if owner == player]
        values = []
        for choices in itertools.product(*(tree.actions[i] for i in infos)):
            pure = lookup.copy()
            for info, action in zip(infos, choices, strict=True):
                pure[tree.keys[info]] = {action: 1.0}
            values.append(
                recursive_value(ToyState("kuhn"), pure) * (1 if player == 0 else -1)
            )
        assert best_response(tree, policy, player) == pytest.approx(max(values))
    assert evaluate(tree, policy).exploitability == pytest.approx(11 / 24)


def kuhn_equilibrium(tree: Tree) -> FloatArray:
    weights = np.zeros_like(tree.legal)
    for i, key in enumerate(tree.keys):
        player, rank, _, history = key.split(":")
        card = int(rank)
        if player == "0":
            aggressive = (1 / 3, 0, 1)[card] if history == "" else (0, 2 / 3, 1)[card]
        else:
            aggressive = (1 / 3, 0, 1)[card] if history == "1" else (0, 1 / 3, 1)[card]
        weights[i, :2] = (1 - aggressive, aggressive)
    return weights


def test_known_kuhn_equilibrium_value_and_zero_exploitability() -> None:
    tree = Tree.build("kuhn")
    metrics = evaluate(tree, kuhn_equilibrium(tree))
    assert metrics.value_player_zero == pytest.approx(-1 / 18, abs=1e-14)
    assert metrics.exploitability == pytest.approx(0, abs=1e-14)
    assert metrics.best_response_zero == pytest.approx(-1 / 18, abs=1e-14)


@pytest.mark.parametrize("variant", ["cfr", "cfr_plus", "linear", "discounted"])
def test_cfr_variants_learn_kuhn(variant: Variant) -> None:
    tree = Tree.build("kuhn")
    solver = CFR(tree, variant)
    solver.train(500)
    metrics = evaluate(tree, solver.average_policy)
    assert metrics.exploitability < 0.01
    assert abs(metrics.value_player_zero + 1 / 18) < 0.005
    assert np.all(np.isfinite(solver.regrets))
    if variant == "cfr_plus":
        assert np.all(solver.regrets >= 0)


def test_tree_counts_policy_validation_and_no_rng_dependence() -> None:
    cases: tuple[tuple[GameName, int, int], ...] = (
        ("kuhn", 58, 12),
        ("leduc", 9457, 936),
    )
    for game, count, infos in cases:
        tree = Tree.build(game)
        assert len(tree.states) == count and len(tree.keys) == infos
        policy = tree.normalize(np.zeros_like(tree.legal))
        tree.validate_policy(policy)
        invalid = policy.copy()
        invalid[0] *= 2
        with pytest.raises(ValueError):
            evaluate(tree, invalid)
    a, b = CFR(Tree.build("kuhn")), CFR(Tree.build("kuhn"))
    a.train(3)
    b.train(3)
    np.testing.assert_array_equal(a.average_policy, b.average_policy)
