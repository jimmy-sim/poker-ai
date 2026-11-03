"""Validation-only shared full-world traces against native ACPC mechanics."""

from typing import Any

from numpy.random import PCG64, Generator

from poker_ai.cards import Deck
from poker_ai.engine import new_hand
from poker_ai.evaluation.openspiel import OpenSpielBaseline
from poker_ai.training.no_limit import NoLimitRules, NoLimitState


def validate_native_traces(
    rules: NoLimitRules, *, seed: int, hands: int
) -> dict[str, Any]:
    if type(hands) is not int or hands < 1 or type(seed) is not int or seed < 0:
        raise ValueError("explicit positive trace budget and nonnegative seed required")
    adapter = OpenSpielBaseline(rules)
    rng = Generator(PCG64(seed))
    actions = showdowns = 0
    error = 0.0
    for _ in range(hands):
        own = new_hand(
            rules.stacks,
            Deck.shuffled(rng),
            button=rules.button,
            small_blind=rules.small_blind,
            big_blind=rules.big_blind,
        )
        native = adapter.game.new_initial_state()
        # Ground truth is allowed only in this isolated mechanics validator.
        # The baseline's search() constructs a NEW root from Observation instead.
        for hole in own.hole_cards:
            for card in hole:
                native.apply_action(adapter.cards[card])
        board_index = 0
        while True:
            while native.is_chance_node():
                if board_index >= len(own.board):
                    raise ArithmeticError("native requests a card before own reveal")
                native.apply_action(adapter.cards[own.board[board_index]])
                board_index += 1
            if own.terminal:
                if not native.is_terminal():
                    raise ArithmeticError("native/own terminal mismatch")
                gap = max(
                    abs(p - q)
                    for p, q in zip(own.net_payoffs, native.returns(), strict=True)
                )
                error = max(error, gap)
                if gap > 1e-9:
                    raise ArithmeticError("native/own payout disagreement")
                showdowns += int(sum(own.folded) == 0)
                break
            assert own.actor is not None
            observation = own.observe(own.actor)
            menu = adapter.menu(native, observation)
            ledger = native.to_struct()
            if (
                tuple(ledger.player_contributions) != own.total_commitments
                or ledger.pot_size != own.pot
            ):
                raise ArithmeticError("native/own intermediate ledger mismatch")
            state = NoLimitState(own, rules)
            move = state.decode(state.actions[int(rng.integers(len(state.actions)))])
            native.apply_action(next(a for a, action in menu.items() if action == move))
            own = own.apply(move)
            actions += 1
    return {
        "hands": hands,
        "actions": actions,
        "showdowns": showdowns,
        "folds": hands - showdowns,
        "max_payout_error": error,
        "scope": (
            "matched full-pot/all-in HU 1/2, equal fully funded stacks; sampled traces"
        ),
    }
