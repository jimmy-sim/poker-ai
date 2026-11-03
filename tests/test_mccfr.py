"""Exact sampling expectations from enumerated Kuhn cases and seeded learning."""

import itertools
from collections.abc import Iterator

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.toy.analysis import evaluate
from poker_ai.toy.games import ToyState
from poker_ai.toy.tree import FloatArray, Tree
from poker_ai.training.mccfr import (
    MCCFR,
    Method,
    Policy,
    external_updates,
    outcome_updates,
)


def uniform(key: str, actions: tuple[int, ...]) -> FloatArray:
    return np.full(len(actions), 1 / len(actions))


def biased(key: str, actions: tuple[int, ...]) -> FloatArray:
    if key == "0:1:None:":
        return np.array([0.2, 0.8])
    if key == "0:1:None:12":
        return np.array([0.75, 0.25])
    return uniform(key, actions)


class Tape:
    def __init__(self, slots: tuple[int, ...]) -> None:
        self.slots = iter(slots)

    def __call__(self, probabilities: FloatArray) -> int:
        slot = next(self.slots)
        assert probabilities[slot] > 0
        return slot


def terminal_paths(
    state: ToyState,
    slots: tuple[int, ...] = (),
    probability: float = 1,
    policy: Policy = uniform,
) -> Iterator[tuple[tuple[int, ...], float]]:
    if state.terminal:
        yield slots, probability
        return
    if state.chance:
        behavior = np.full(len(state.actions), 1 / len(state.actions))
    else:
        sigma = policy(state.information, state.actions)
        behavior = 0.4 * sigma + 0.6 / len(sigma) if state.actor == 0 else sigma
    for slot, action in enumerate(state.actions):
        yield from terminal_paths(
            state.child(action),
            slots + (slot,),
            probability * float(behavior[slot]),
            policy,
        )


def test_external_expected_regret_on_queen_is_analytical_one_eighth() -> None:
    # For player-0 Q, conditional check value=-1/4, bet value=1/2.
    # Average value=1/8, and P(Q)=1/3: regrets=(-1/8,+1/8).
    expected = np.zeros(2)
    for slots in itertools.product(range(3), range(2), range(2), range(2)):
        updates = external_updates(ToyState("kuhn"), 0, uniform, Tape(slots))
        expected += updates.regrets.get("0:1:None:", np.zeros(2)) / 24
    np.testing.assert_allclose(expected, (-1 / 8, 1 / 8), atol=1e-14)


def test_outcome_expected_regret_and_average_by_all_terminal_paths() -> None:
    expected_regret = np.zeros(2)
    expected_average = np.zeros(2)
    total = 0.0
    for slots, probability in terminal_paths(ToyState("kuhn")):
        updates = outcome_updates(ToyState("kuhn"), 0, uniform, Tape(slots), 0.6)
        expected_regret += probability * updates.regrets.get("0:1:None:", np.zeros(2))
        expected_average += probability * updates.averages.get("0:1:None:", np.zeros(2))
        total += probability
    assert total == pytest.approx(1)
    np.testing.assert_allclose(expected_regret, (-1 / 8, 1 / 8), atol=1e-14)
    # Two possible opponent cards contribute own reach=1 and uniform strategy.
    np.testing.assert_allclose(expected_average, (1, 1), atol=1e-14)


@pytest.mark.parametrize("method", ["external", "outcome"])
def test_explicit_rng_reproduces_sampled_training(method: Method) -> None:
    a = MCCFR(lambda rng: ToyState("kuhn"), Generator(PCG64(43)), method=method)
    b = MCCFR(lambda rng: ToyState("kuhn"), Generator(PCG64(43)), method=method)
    a.train(50)
    b.train(50)
    assert a.iteration == b.iteration == 50
    assert a.nodes_visited == b.nodes_visited
    assert set(a.rows) == set(b.rows)
    for key in a.rows:
        np.testing.assert_array_equal(a.rows[key].regrets, b.rows[key].regrets)
        np.testing.assert_array_equal(
            a.rows[key].strategy_sum, b.rows[key].strategy_sum
        )


def test_invalid_exploration_and_information_set_actions() -> None:
    for epsilon in (0.0, -1.0, 1.1, float("nan")):
        with pytest.raises(ValueError):
            MCCFR(lambda rng: ToyState("kuhn"), Generator(PCG64(4)), epsilon=epsilon)
    solver = MCCFR(lambda rng: ToyState("kuhn"), Generator(PCG64(4)))
    solver.policy("test", (1, 2))
    with pytest.raises(ValueError):
        solver.policy("test", (0, 1, 2))


def test_sampled_algorithms_learn_beyond_uniform_in_a_small_budget() -> None:
    tree = Tree.build("kuhn")
    for method in ("external", "outcome"):
        solver = MCCFR(
            lambda rng: ToyState("kuhn"), Generator(PCG64(20261113)), method=method
        )
        solver.train(2000)
        policy = np.zeros_like(tree.legal)
        for info, (key, actions) in enumerate(
            zip(tree.keys, tree.actions, strict=True)
        ):
            policy[info, : len(actions)] = solver.policy(key, actions, average=True)
        assert evaluate(tree, policy).exploitability < 0.15


def test_nonuniform_outcome_importance_weights_and_zero_own_reach_in_regret() -> None:
    expected: dict[str, FloatArray] = {}
    averages: dict[str, FloatArray] = {}
    for slots, probability in terminal_paths(ToyState("kuhn"), policy=biased):
        updates = outcome_updates(ToyState("kuhn"), 0, biased, Tape(slots), 0.6)
        for key, value in updates.regrets.items():
            expected.setdefault(key, np.zeros(2))[:] += probability * value
        for key, value in updates.averages.items():
            averages.setdefault(key, np.zeros(2))[:] += probability * value
    # Root Q: check=-3/8, bet=1/2, sigma=(.2,.8), value=13/40.
    np.testing.assert_allclose(expected["0:1:None:"], (-7 / 30, 7 / 120), atol=1e-14)
    # After check/bet, fold=-1, call=0, value=-3/4. Counterfactual
    # reach is P(Q)*P(opponent bets)=1/6; own earlier check .2 is excluded.
    np.testing.assert_allclose(expected["0:1:None:12"], (-1 / 24, 1 / 8), atol=1e-14)
    np.testing.assert_allclose(averages["0:1:None:"], (0.4, 1.6), atol=1e-14)
    np.testing.assert_allclose(averages["0:1:None:12"], (0.3, 0.1), atol=1e-14)


def test_nonuniform_external_expected_regret_enumerates_own_actions() -> None:
    root, response = np.zeros(2), np.zeros(2)
    for slots in itertools.product(range(3), range(2), range(2), range(2)):
        updates = external_updates(ToyState("kuhn"), 0, biased, Tape(slots))
        root += updates.regrets.get("0:1:None:", np.zeros(2)) / 24
        response += updates.regrets.get("0:1:None:12", np.zeros(2)) / 24
    np.testing.assert_allclose(root, (-7 / 30, 7 / 120), atol=1e-14)
    np.testing.assert_allclose(response, (-1 / 24, 1 / 8), atol=1e-14)
