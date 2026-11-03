"""Own no-limit Hold'em transitions, rule edge cases, and conservation properties."""

from dataclasses import fields

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from numpy.random import PCG64, Generator

from poker_ai.cards import Deck, cards_to_mask, parse_card
from poker_ai.engine import (
    Action,
    ActionKind,
    HoldemState,
    Street,
    build_pots,
    new_hand,
)


def hand(text: str) -> tuple[int, ...]:
    return tuple(map(parse_card, text.split()))


def arranged(holes: tuple[tuple[int, ...], ...], board: tuple[int, ...]) -> Deck:
    """Canonical button-last deal: one card per seat per pass, then burns/board."""
    prefix = tuple(cards[index] for index in range(2) for cards in holes)
    used = set(prefix + board)
    rest = [card for card in range(52) if card not in used]
    burns = rest[:3]
    order = prefix + (burns[0],) + board[:3] + (burns[1], board[3], burns[2], board[4])
    return Deck(order + tuple(card for card in range(52) if card not in order))


def passive_to_flop(stacks: tuple[int, ...]) -> HoldemState:
    state = new_hand(stacks, Deck(), button=len(stacks) - 1)
    while state.street == Street.PREFLOP and not state.terminal:
        state = state.apply(
            Action(
                ActionKind.CHECK if state.legal_actions.can_check else ActionKind.CALL
            )
        )
    return state


def assert_invariants(state: HoldemState) -> None:
    assert all(stack >= 0 for stack in state.stacks)
    assert sum(state.stacks) + state.pot == sum(state.starting_stacks)
    all_cards = tuple(card for cards in state.hole_cards for card in cards)
    all_cards += state.board + state.burned + state.deck.cards
    assert len(all_cards) == cards_to_mask(all_cards).bit_count() == 52
    if not state.terminal:
        assert state.actor is not None
        assert not state.folded[state.actor] and state.stacks[state.actor] > 0
    else:
        assert state.actor is None and sum(state.net_payoffs) == 0


def test_initial_blinds_turn_and_heads_up_order() -> None:
    state = new_hand((100, 100, 100), Deck(), button=2)
    assert state.street_commitments == (1, 2, 0)
    assert state.actor == 2 and state.legal_actions.call_amount == 2
    assert state.legal_actions.min_raise_to == 4
    state = new_hand((100, 100), Deck(), button=1)
    assert state.street_commitments == (2, 1) and state.actor == 1
    state = state.apply(Action(ActionKind.CALL))
    assert state.actor == 0 and state.legal_actions.can_check
    assert state.legal_actions.min_raise_to == 4  # The big blind retains its option.
    state = state.apply(Action(ActionKind.CHECK))
    assert state.street == Street.FLOP and state.actor == 0 and len(state.board) == 3


def test_fold_settlement_and_uncalled_refund() -> None:
    state = new_hand((100, 100, 100), Deck(), button=2)
    state = state.apply(Action(ActionKind.FOLD)).apply(Action(ActionKind.FOLD))
    assert state.terminal and state.board == ()
    assert state.stacks == (99, 101, 100)
    assert state.uncalled_returns == (0, 1, 0)
    assert_invariants(state)


def test_single_short_raise_does_not_reopen_but_full_raise_does() -> None:
    state = passive_to_flop((100, 17, 100))
    state = state.apply(Action(ActionKind.RAISE_TO, 10))
    state = state.apply(Action(ActionKind.RAISE_TO, 15))
    state = state.apply(Action(ActionKind.CALL))
    assert state.actor == 0 and state.legal_actions.call_amount == 5
    assert state.legal_actions.min_raise_to is None
    with pytest.raises(ValueError, match="raise"):
        state.apply(Action(ActionKind.RAISE_TO, 25))


def test_cumulative_short_all_ins_reopen_the_betting() -> None:
    state = passive_to_flop((100, 17, 22, 100))
    for amount in (10, 15, 20):
        state = state.apply(Action(ActionKind.RAISE_TO, amount))
    state = state.apply(Action(ActionKind.CALL))
    assert state.actor == 0 and state.legal_actions.min_raise_to == 30
    state = state.apply(Action(ActionKind.RAISE_TO, 30))
    assert state.actor == 3 and state.legal_actions.min_raise_to == 40


def test_prior_check_can_raise_after_a_short_opening_all_in() -> None:
    state = passive_to_flop((100, 3, 100))
    state = state.apply(Action(ActionKind.CHECK))
    state = state.apply(Action(ActionKind.RAISE_TO, 1))
    state = state.apply(Action(ActionKind.CALL))
    assert state.actor == 0 and state.legal_actions.min_raise_to == 3
    with pytest.raises(ValueError):
        state.apply(Action(ActionKind.RAISE_TO, 2))


def test_short_big_blind_preserves_nominal_bring_in_with_multiple_funded_players() -> (
    None
):
    state = new_hand((100, 1, 100), Deck(), button=2)
    assert state.street_commitments == (1, 1, 0)
    assert state.actor == 2 and state.legal_actions.call_amount == 2
    assert state.legal_actions.min_raise_to == 4


def test_all_in_side_pots_and_uncalled_money() -> None:
    deck = arranged(
        (hand("Ah Ad"), hand("Kh Kc"), hand("Qd Qc")), hand("As Kd Qh 2c 3d")
    )
    state = new_hand((5, 10, 20), deck, button=2)
    state = state.apply(Action(ActionKind.RAISE_TO, 20))
    state = state.apply(Action(ActionKind.CALL)).apply(Action(ActionKind.CALL))
    assert state.terminal and state.stacks == (15, 10, 10)
    assert [pot.amount for pot in state.pots] == [15, 10, 10]
    assert state.uncalled_returns == (0, 0, 10)
    assert len(state.board) == 5 and len(state.burned) == 3
    assert_invariants(state)


def test_identical_eligibility_layers_merge_before_odd_chip_distribution() -> None:
    pots = build_pots((1, 2, 5, 8, 8), (True, True, True, False, False))
    assert len(pots) == 1 and pots[0].amount == 24 and pots[0].eligible == (3, 4)


def test_odd_chip_goes_to_first_winner_left_of_button() -> None:
    deck = arranged(
        (hand("2d 3h"), hand("4d 5h"), hand("6d 7h")), hand("Tc Jc Qc Kc Ac")
    )
    state = new_hand((100, 100, 100), deck, button=2)
    state = state.apply(Action(ActionKind.CALL)).apply(Action(ActionKind.FOLD))
    while not state.terminal:
        state = state.apply(
            Action(
                ActionKind.CHECK if state.legal_actions.can_check else ActionKind.CALL
            )
        )
    assert state.stacks == (99, 101, 100)
    assert_invariants(state)


def test_short_heads_up_blind_does_not_create_meaningless_extra_action() -> None:
    state = new_hand((1, 100), Deck(), button=1)
    assert state.terminal and len(state.board) == 5
    assert_invariants(state)


def test_player_observation_excludes_deck_other_holes_and_burns() -> None:
    state = new_hand((100, 100, 100), Deck(), button=2)
    observation = state.observe(2)
    assert observation.hole_cards == state.hole_cards[2]
    names = {field.name for field in fields(observation)}
    assert not names & {"deck", "burned", "all_hole_cards", "state"}
    assert len(observation.hole_cards) == 2
    assert state.observe(0).legal_actions is None


def test_illegal_action_does_not_modify_original_state() -> None:
    state = new_hand((100, 100), Deck(), button=1)
    with pytest.raises(ValueError):
        state.apply(Action(ActionKind.CHECK))
    with pytest.raises(ValueError):
        state.apply(Action(ActionKind.RAISE_TO, 3))
    assert state.history == () and state.stacks == (98, 99)


@settings(max_examples=100)
@given(
    stacks=st.lists(st.integers(1, 80), min_size=2, max_size=6),
    seed=st.integers(0, 2**32 - 1),
)
def test_legal_random_games_terminate_and_conserve_chips_and_cards(
    stacks: list[int], seed: int
) -> None:
    rng = Generator(PCG64(seed))
    state = new_hand(stacks, Deck.shuffled(rng), button=len(stacks) - 1)
    for _ in range(1000):
        assert_invariants(state)
        if state.terminal:
            break
        legal = state.legal_actions
        actions = [Action(ActionKind.FOLD)]
        actions.append(Action(ActionKind.CHECK if legal.can_check else ActionKind.CALL))
        if legal.min_raise_to is not None:
            actions += [
                Action(ActionKind.RAISE_TO, legal.min_raise_to),
                Action(ActionKind.RAISE_TO, legal.max_raise_to),
            ]
        state = state.apply(actions[int(rng.integers(len(actions)))])
    else:
        pytest.fail("legal game failed to terminate within a generous action bound")


def test_no_raise_when_other_funded_player_cannot_cover_current_wager() -> None:
    state = passive_to_flop((100, 17, 42))
    state = state.apply(Action(ActionKind.CHECK))
    state = state.apply(Action(ActionKind.RAISE_TO, 2))
    state = state.apply(Action(ActionKind.RAISE_TO, 40))
    assert state.actor == 0 and state.legal_actions.call_amount == 40
    assert state.legal_actions.min_raise_to is None
    with pytest.raises(ValueError, match="raise"):
        state.apply(Action(ActionKind.RAISE_TO, 80))


def test_free_fold_preserves_last_unacted_check_or_fold_choice() -> None:
    state = passive_to_flop((100, 5, 100))
    state = state.apply(Action(ActionKind.CHECK))
    state = state.apply(Action(ActionKind.RAISE_TO, 3))
    state = state.apply(Action(ActionKind.CALL)).apply(Action(ActionKind.CALL))
    assert state.street == Street.TURN and state.actor == 0
    state = state.apply(Action(ActionKind.FOLD))
    assert not state.terminal and state.actor == 2 and state.legal_actions.can_check
    assert state.legal_actions.min_raise_to is None
    state = state.apply(Action(ActionKind.CHECK))
    assert state.terminal and len(state.board) == 5


def test_reachable_dead_money_layers_do_not_bias_a_tied_pot() -> None:
    holes = tuple(hand(text) for text in ("2d 3h", "4d 5h", "6d 7h", "8d 9h", "Td Jh"))
    state = new_hand((100,) * 5, arranged(holes, hand("Tc Jc Qc Kc Ac")), button=4)
    for action in (
        Action(ActionKind.RAISE_TO, 5),
        Action(ActionKind.RAISE_TO, 8),
        Action(ActionKind.CALL),
        Action(ActionKind.FOLD),
        Action(ActionKind.FOLD),
        Action(ActionKind.FOLD),
    ):
        state = state.apply(action)
    while not state.terminal:
        state = state.apply(
            Action(
                ActionKind.CHECK if state.legal_actions.can_check else ActionKind.CALL
            )
        )
    assert len(state.pots) == 1 and state.pots[0].amount == 24
    assert state.stacks == (99, 98, 95, 104, 104)
    assert_invariants(state)


def test_folded_nuts_cannot_win_at_showdown() -> None:
    holes = (hand("Ah Ad"), hand("Kh Kc"), hand("Qd Qc"))
    state = new_hand((100,) * 3, arranged(holes, hand("As Kd Qh 2c 3d")), button=2)
    for action in (
        Action(ActionKind.CALL),
        Action(ActionKind.CALL),
        Action(ActionKind.CHECK),
        Action(ActionKind.FOLD),
    ):
        state = state.apply(action)
    while not state.terminal:
        state = state.apply(Action(ActionKind.CHECK))
    assert state.stacks == (98, 104, 98)


@pytest.mark.parametrize("stacks", [(), (100,), (100,) * 7, (0, 100), (-1, 100)])
def test_invalid_starting_table(stacks: tuple[int, ...]) -> None:
    with pytest.raises(ValueError):
        new_hand(stacks, Deck())


def test_invalid_blinds_button_deck_and_actions() -> None:
    for kwargs in ({"button": 2}, {"small_blind": 3, "big_blind": 2}, {"big_blind": 0}):
        with pytest.raises(ValueError):
            new_hand((100, 100), Deck(), **kwargs)
    with pytest.raises(ValueError):
        new_hand((100, 100), Deck((0, 1)))
    with pytest.raises(TypeError):
        Action(ActionKind.RAISE_TO, True)
    with pytest.raises(ValueError):
        Action(ActionKind.CALL, 1)


def test_folding_main_pot_keeps_an_already_secured_side_pot() -> None:
    state = new_hand((5, 100, 100), Deck(), button=2)
    state = state.apply(Action(ActionKind.RAISE_TO, 10))
    state = state.apply(Action(ActionKind.CALL)).apply(Action(ActionKind.CALL))
    assert state.street == Street.FLOP and state.actor == 1
    state = state.apply(Action(ActionKind.FOLD))
    assert state.actor == 2 and state.legal_actions.can_check
    state = state.apply(Action(ActionKind.FOLD))
    assert state.terminal and state.stacks == (15, 90, 100)
    assert state.pot_winners == ((0,), (2,))
    assert_invariants(state)


def test_prior_preflop_caller_cannot_reraise_a_short_all_in() -> None:
    state = new_hand((28, 3, 15, 48), Deck(), button=1)
    for action in (
        Action(ActionKind.CALL),
        Action(ActionKind.RAISE_TO, 3),
        Action(ActionKind.CALL),
        Action(ActionKind.CALL),
    ):
        state = state.apply(action)
    assert state.actor == 0 and state.legal_actions.call_amount == 1
    assert state.legal_actions.min_raise_to is None


def test_multiple_odd_chips_are_spread_one_each_clockwise() -> None:
    holes = tuple(hand(text) for text in ("2d 3h", "4d 5h", "6d 7h", "8d 9h"))
    state = new_hand(
        (100, 100, 3, 100), arranged(holes, hand("Tc Jc Qc Kc Ac")), button=3
    )
    for action in (
        Action(ActionKind.RAISE_TO, 3),
        Action(ActionKind.CALL),
        Action(ActionKind.CALL),
        Action(ActionKind.FOLD),
    ):
        state = state.apply(action)
    while not state.terminal:
        state = state.apply(Action(ActionKind.CHECK))
    assert len(state.pots) == 1 and state.pots[0].amount == 11
    assert state.stacks == (101, 98, 4, 100)
    assert_invariants(state)
