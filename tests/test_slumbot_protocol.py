"""Public protocol tests use synthetic packets and make no network requests."""

import pytest

from poker_ai.cards import parse_card
from poker_ai.engine import Action, ActionKind
from poker_ai.evaluation.slumbot_protocol import (
    ProtocolError,
    encode_action,
    replay_public,
    verify_result,
)

HOLE = tuple(map(parse_card, ("As", "Ad")))
BOARD = tuple(map(parse_card, ("2c", "7d", "Jh", "Tc", "3s")))


def test_public_preflop_raise_uses_street_total_and_correct_position() -> None:
    state = replay_public("b200", client_seat=0, hole=HOLE, board=())
    observation = state.observation
    assert observation is not None
    assert observation.pot == 300
    assert observation.stacks == (19900, 19800)
    assert observation.legal_actions is not None
    assert observation.legal_actions.call_amount == 100
    assert observation.hole_cards == HOLE


def test_later_bet_is_street_total_not_cumulative_hand_total() -> None:
    state = replay_public("cb300c/kk/kk/kb200", client_seat=0, hole=HOLE, board=BOARD)
    observation = state.observation
    assert observation is not None
    assert observation.pot == 800
    assert observation.total_commitments == (300, 500)
    assert observation.history[-1].action == Action(ActionKind.RAISE_TO, 200)
    assert observation.board == BOARD


def test_all_in_trailing_empty_streets_and_unknown_showdown() -> None:
    for text in ("b20000c", "b20000c///"):
        state = replay_public(text, client_seat=1, hole=HOLE, board=BOARD)
        assert state.terminal and state.observation is None
        assert state.fold_payoff is None
        assert verify_result(state, -20000, 20000) == -20000


def test_fold_payout_is_card_independent_and_verified() -> None:
    state = replay_public("f", client_seat=1, hole=HOLE, board=())
    assert state.fold_payoff == -50
    assert verify_result(state, -50, 20000) == -50
    with pytest.raises(ProtocolError, match="fold settlement"):
        verify_result(state, 50, 20000)


@pytest.mark.parametrize("text", ["x", "b10", "/k", "f///", "b20000cf"])
def test_malformed_or_illegal_public_history_fails(text: str) -> None:
    with pytest.raises((ProtocolError, ValueError)):
        replay_public(text, client_seat=0, hole=HOLE, board=())


def test_action_encoding_and_censored_settlement_failures() -> None:
    assert encode_action(Action(ActionKind.RAISE_TO, 350)) == "b350"
    assert encode_action(Action(ActionKind.CHECK)) == "k"
    state = replay_public("b200", client_seat=0, hole=HOLE, board=())
    with pytest.raises(ProtocolError, match="before"):
        verify_result(state, 0, 20000)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), True, 1.5, 20001])
def test_noninteger_nonfinite_or_out_of_support_settlements_fail(bad: object) -> None:
    state = replay_public("b20000c", client_seat=1, hole=HOLE, board=BOARD)
    with pytest.raises(ProtocolError):
        verify_result(state, bad, 20000)
