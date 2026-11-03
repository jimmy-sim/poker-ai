"""Documented public Slumbot action strings replayed through own cash rules.

Only monetary/public history is reconstructed with synthetic dealer cards. An
acting observation receives the real own hole cards and currently public board.
Synthetic showdown payouts are never used as observed benchmark results.
"""

import re
from dataclasses import dataclass, replace
from typing import cast

from poker_ai.cards import Deck, cards_to_mask
from poker_ai.engine import Action, ActionKind, ActionRecord, Observation, new_hand

TOKEN = re.compile(r"b([0-9]+)|([fck/])")


class ProtocolError(ValueError):
    pass


@dataclass(frozen=True)
class PublicReplay:
    terminal: bool
    observation: Observation | None
    history: tuple[ActionRecord, ...]
    fold_payoff: int | None


def replay_public(
    text: str,
    *,
    client_seat: int,
    hole: tuple[int, ...],
    board: tuple[int, ...],
    stacks: tuple[int, int] = (20000, 20000),
    small_blind: int = 50,
    big_blind: int = 100,
    button: int = 1,
) -> PublicReplay:
    if type(client_seat) is not int or client_seat not in (0, 1):
        raise ProtocolError("unknown public client position")
    if not isinstance(text, str) or len(hole) != 2 or len(board) not in (0, 3, 4, 5):
        raise ProtocolError("invalid public action/own-card/board fields")
    cards_to_mask(hole + board)
    state = new_hand(
        stacks, Deck(), button=button, small_blind=small_blind, big_blind=big_blind
    )
    cursor = street = actions = 0
    while cursor < len(text):
        token = TOKEN.match(text, cursor)
        if token is None:
            raise ProtocolError("unknown public action token")
        cursor = token.end()
        if token.group(2) == "/":
            street += 1
            if street > 3 or (state.terminal and any(state.folded)):
                raise ProtocolError("unexpected street delimiter")
            continue
        if state.terminal or int(state.street) != street or actions >= 512:
            raise ProtocolError("action after terminal or on inconsistent street")
        if token.group(1) is not None:
            move = Action(ActionKind.RAISE_TO, int(token.group(1)))
        else:
            move = Action(
                {"f": ActionKind.FOLD, "c": ActionKind.CALL, "k": ActionKind.CHECK}[
                    token.group(2)
                ]
            )
        try:
            state = state.apply(move)
        except (ValueError, TypeError) as error:
            raise ProtocolError(
                "public action violates the configured cash rules"
            ) from error
        actions += 1
    if state.terminal:
        return PublicReplay(
            True,
            None,
            state.history,
            state.net_payoffs[client_seat] if any(state.folded) else None,
        )
    if len(board) != len(state.board) or state.actor != client_seat:
        raise ProtocolError("public board/client turn inconsistent with action history")
    observation = replace(state.observe(client_seat), hole_cards=hole, board=board)
    return PublicReplay(False, observation, state.history, None)


def encode_action(action: Action) -> str:
    if action.kind == ActionKind.RAISE_TO:
        if action.amount is None:
            raise ProtocolError("raise requires a street total")
        return f"b{action.amount}"
    return {ActionKind.FOLD: "f", ActionKind.CHECK: "k", ActionKind.CALL: "c"}[
        action.kind
    ]


def verify_result(replay: PublicReplay, winnings: object, maximum_loss: int) -> int:
    if not replay.terminal:
        raise ProtocolError("server settlement before the public hand ends")
    if type(winnings) not in (int, float):
        raise ProtocolError("server winnings must be integer-valued net chips")
    # Use a checked conversion; never round fractional or non-finite outcomes.
    try:
        integer = int(cast(int | float, winnings))
    except (ValueError, OverflowError) as error:
        raise ProtocolError("non-finite server winnings") from error
    if integer != winnings or abs(integer) > maximum_loss:
        raise ProtocolError("server winnings outside declared chip support")
    if replay.fold_payoff is not None and integer != replay.fold_payoff:
        raise ProtocolError("server/own fold settlement mismatch")
    return integer
