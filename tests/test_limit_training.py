"""Fixed-limit wager caps, funding domain and public-only keys."""

from dataclasses import replace
from functools import partial

import pytest
from numpy.random import PCG64, Generator

from poker_ai.cards import Deck
from poker_ai.engine import new_hand
from poker_ai.training.holdem import LimitRules, LimitState, sample_limit
from poker_ai.training.mccfr import MCCFR


def test_limit_wagers_cap_and_change_size_by_street() -> None:
    rules = LimitRules()
    state = LimitState(new_hand(rules.stacks, Deck(), button=1), rules)
    while not state.terminal:
        state = state.child(2 if 2 in state.actions else 1)
    assert state.dealer.total_commitments == (48, 48)
    assert sum(state.dealer.stacks) == 400
    assert rules.bet_sizes == (2, 2, 4, 4)
    assert len(state.dealer.board) == 5


def test_limit_information_hides_opponent_and_future_cards() -> None:
    rules = LimitRules()
    state = LimitState(new_hand(rules.stacks, Deck(), button=1), rules)
    # Swapping the opponent's hole card with a future card preserves the actor's
    # cards and every public field. Training keys must be identical.
    dealer = state.dealer
    holes = list(dealer.hole_cards)
    hidden = holes[0][0]
    holes[0] = (dealer.deck.cards[0], holes[0][1])
    swapped = replace(
        dealer, hole_cards=tuple(holes), deck=Deck((hidden,) + dealer.deck.cards[1:])
    )
    assert state.actor == 1
    assert state.information == LimitState(swapped, rules).information
    assert state.child(1).information != state.information


def test_limit_rejects_short_stack_domain_and_free_folds() -> None:
    with pytest.raises(ValueError, match="cover"):
        LimitRules(stacks=(48, 200))
    state = sample_limit(LimitRules(), Generator(PCG64(7)))
    state = state.child(1)
    assert 0 not in state.actions
    with pytest.raises(ValueError):
        state.child(0)


def test_sampled_trainer_uses_limit_protocol() -> None:
    rules = LimitRules(bet_cap=2)
    solver = MCCFR(partial(sample_limit, rules), Generator(PCG64(11)))
    solver.train(2)
    assert solver.iteration == 2 and solver.rows and solver.nodes_visited > 4
