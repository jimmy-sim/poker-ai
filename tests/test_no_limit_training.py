"""No-limit adapter legality and explicit aborts for costly sampled traversals."""

from functools import partial

import pytest
from hypothesis import given
from hypothesis import strategies as st
from numpy.random import PCG64, Generator

from poker_ai.cards import Deck
from poker_ai.engine import new_hand
from poker_ai.training.budget import NodeBudgetExceeded, bounded_sample
from poker_ai.training.mccfr import MCCFR
from poker_ai.training.no_limit import NoLimitRules, NoLimitState, sample_no_limit


def test_no_limit_ids_decode_to_sorted_legal_raise_totals() -> None:
    rules = NoLimitRules()
    state = NoLimitState(new_hand(rules.stacks, Deck(), button=1), rules)
    assert state.actions == (0, 1, 2, 3, 4, 5)
    assert state.raise_targets == (4, 6, 10, 200)
    assert state.child(3).dealer.street_commitments == (2, 6)
    with pytest.raises(ValueError):
        state.child(6)


def test_overbet_against_short_stack_returns_uncalled_chips() -> None:
    rules = NoLimitRules(stacks=(3, 200))
    state = NoLimitState(new_hand(rules.stacks, Deck(), button=1), rules)
    state = state.child(state.actions[-1]).child(1)
    assert state.terminal and sum(state.dealer.stacks) == 203
    assert max(state.dealer.uncalled_returns) == 197
    assert sum(state.dealer.net_payoffs) == 0


@given(st.integers(1, 80), st.integers(1, 80), st.integers(0, 1000))
def test_random_abstracted_games_terminate_legally(a: int, b: int, seed: int) -> None:
    rng = Generator(PCG64(seed))
    state = sample_no_limit(NoLimitRules(stacks=(a, b)), rng)
    for _ in range(1000):
        assert sum(state.dealer.stacks) + state.dealer.pot == a + b
        if state.terminal:
            assert sum(state.dealer.net_payoffs) == 0
            return
        action = state.actions[int(rng.integers(len(state.actions)))]
        state = state.child(action)
    pytest.fail("abstracted no-limit hand failed to terminate")


def test_node_budget_aborts_without_returning_a_biased_value() -> None:
    factory = partial(sample_no_limit, NoLimitRules())
    solver = MCCFR(partial(bounded_sample, factory, 1), Generator(PCG64(22)))
    with pytest.raises(NodeBudgetExceeded, match="exceeded 1"):
        solver.step()
    assert solver.iteration == 0
    assert all(not row.regrets.any() for row in solver.rows.values())


def test_both_samplers_can_use_bounded_no_limit_protocol() -> None:
    for method in ("external", "outcome"):
        factory = partial(sample_no_limit, NoLimitRules(stacks=(20, 20)))
        solver = MCCFR(
            partial(bounded_sample, factory, 5000),
            Generator(PCG64(14)),
            method=method,
        )
        solver.train(3)
        assert solver.iteration == 3 and solver.rows
