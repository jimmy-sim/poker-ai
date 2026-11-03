"""Differential no-limit Hold'em action traces against optional PokerKit.

The external state exists only in this validation script. Production transitions
and player observations use the own engine exclusively.
"""

import argparse
import hashlib
import importlib
import importlib.metadata
import json
import platform
import time
import warnings
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from numpy.random import PCG64, Generator

from poker_ai.cards import Deck, format_card, parse_card
from poker_ai.engine import Action, ActionKind, HoldemState, Street, new_hand
from poker_ai.validation.five_card import source_provenance


@dataclass
class Reference:
    """Explicit chance tape and seat rotation around the independent state."""

    oracle: Any
    origin: int
    size: int
    board: tuple[int, ...]
    burns: tuple[int, ...]
    board_offset: int = 0
    burn_offset: int = 0
    short_allin_reference_allowances: int = 0

    def pump(self) -> None:
        for _ in range(30):
            if not self.oracle.status or self.oracle.actor_index is not None:
                return
            if self.oracle.can_burn_card():
                self.oracle.burn_card(format_card(self.burns[self.burn_offset]))
                self.burn_offset += 1
            elif self.oracle.can_deal_board():
                count = int(self.oracle.board_dealing_count)
                cards = self.board[self.board_offset : self.board_offset + count]
                self.oracle.deal_board("".join(map(format_card, cards)))
                self.board_offset += count
            elif self.oracle.can_select_runout_count():
                self.oracle.select_runout_count(1)
            else:
                raise AssertionError("reference has an unhandled pending operation")
        raise AssertionError("reference chance steps failed to terminate")

    def values(self, values: Any) -> tuple[Fraction, ...]:
        result = [Fraction(0)] * self.size
        for index, value in enumerate(values):
            result[(self.origin + index) % self.size] = Fraction(value)
        return tuple(result)

    def compare(self, state: HoldemState) -> None:
        self.pump()
        assert state.terminal == (not self.oracle.status), "terminal status differs"
        assert state.board == self.board[: self.board_offset], (
            "board progression differs"
        )
        if state.terminal:
            unrounded = [
                Fraction(start - paid)
                for start, paid in zip(
                    state.starting_stacks, state.total_commitments, strict=True
                )
            ]
            for pot, winners in zip(state.pots, state.pot_winners, strict=True):
                for seat in winners:
                    unrounded[seat] += Fraction(pot.amount, len(winners))
            assert tuple(unrounded) == self.values(self.oracle.stacks), (
                "rational terminal payouts differ"
            )
            return
        assert state.stacks == self.values(self.oracle.stacks), "active stacks differ"
        actor = (self.origin + int(self.oracle.actor_index)) % self.size
        assert state.actor == actor, "actor order differs"
        assert state.street_commitments == self.values(self.oracle.bets), (
            "street wagers differ"
        )
        legal = state.legal_actions
        assert legal.call_amount == self.oracle.checking_or_calling_amount, (
            "call amount differs"
        )
        reference_min = self.oracle.min_completion_betting_or_raising_to_amount
        reference_max = self.oracle.max_completion_betting_or_raising_to_amount
        if legal.min_raise_to is None and reference_min is not None:
            # Independently reconstruct the public wager history. Rule 49 keeps
            # a prior caller/bettor closed when the added amount is short of a
            # full raise. PokerKit 0.7.7 can incorrectly reopen after calls.
            price = state.big_blind if state.street == Street.PREFLOP else 0
            full_raise = state.big_blind
            previous = None
            for record in state.history:
                if record.street != state.street:
                    continue
                if record.action.kind == ActionKind.RAISE_TO:
                    assert record.action.amount is not None
                    increment = record.action.amount - price
                    if increment >= full_raise:
                        full_raise = increment
                    price = record.action.amount
                if record.seat == actor:
                    previous = price
            if (
                previous is not None
                and previous > 0
                and 0 < price - previous < full_raise
            ):
                self.short_allin_reference_allowances += 1
                return
        assert legal.min_raise_to == reference_min, "minimum raise differs"
        assert legal.max_raise_to == reference_max, "maximum raise differs"

    def apply(self, action: Action) -> None:
        if action.kind == ActionKind.FOLD:
            with warnings.catch_warnings():
                warnings.filterwarnings(
                    "ignore", message="There is no reason for this player to fold.*"
                )
                self.oracle.fold()
        elif action.kind in (ActionKind.CHECK, ActionKind.CALL):
            self.oracle.check_or_call()
        else:
            self.oracle.complete_bet_or_raise_to(action.amount)


def reference_for(
    state: HoldemState, deck: Deck, *, fractional: bool = True
) -> Reference:
    pokerkit = importlib.import_module("pokerkit")
    names = (
        "ANTE_POSTING",
        "BET_COLLECTION",
        "BLIND_OR_STRADDLE_POSTING",
        "RUNOUT_COUNT_SELECTION",
        "HOLE_CARDS_SHOWING_OR_MUCKING",
        "HAND_KILLING",
        "CHIPS_PUSHING",
        "CHIPS_PULLING",
    )
    automations = tuple(getattr(pokerkit.Automation, name) for name in names)
    size = len(state.stacks)
    origin = (state.button + 1) % size
    stacks = tuple(
        state.starting_stacks[(origin + index) % size] for index in range(size)
    )
    oracle = pokerkit.NoLimitTexasHoldem.create_state(
        automations,
        True,
        0,
        (state.small_blind, state.big_blind),
        state.big_blind,
        stacks,
        size,
        mode=pokerkit.Mode.CASH_GAME,
        rake=lambda amount, state: (0, amount),
        divmod=(lambda amount, divisor: (Fraction(amount) / divisor, 0))
        if fractional
        else divmod,
    )
    for index in range(size):
        cards = state.hole_cards[(origin + index) % size]
        oracle.deal_hole("".join(map(format_card, cards)), player_index=index)
    tape = deck.cards[2 * size :]
    return Reference(
        oracle,
        origin,
        size,
        tape[1:4] + (tape[5], tape[7]),
        (tape[0], tape[4], tape[6]),
    )


def choose(state: HoldemState, rng: Generator, mode: int) -> Action:
    """Validation drivers vary action patterns; these are not strength baselines."""
    legal = state.legal_actions
    passive = Action(ActionKind.CHECK if legal.can_check else ActionKind.CALL)
    # PokerKit 0.7.7 asserts on a last-funded free fold with a secured side pot;
    # retain a separate explicit canary and test this path analytically in ours.
    funded = sum(
        not state.folded[i] and state.stacks[i] > 0 for i in range(len(state.stacks))
    )
    if funded == 1 or mode == 0 or (mode == 3 and state.street == Street.PREFLOP):
        return passive
    if mode == 1:
        choices = [passive, passive]
    else:
        choices = [passive, passive, Action(ActionKind.FOLD)]
    if legal.min_raise_to is not None and legal.max_raise_to is not None:
        choices += [
            Action(ActionKind.RAISE_TO, legal.min_raise_to),
            Action(ActionKind.RAISE_TO, legal.max_raise_to),
            Action(
                ActionKind.RAISE_TO,
                int(rng.integers(legal.min_raise_to, legal.max_raise_to + 1)),
            ),
        ]
    return choices[int(rng.integers(len(choices)))]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    if not isinstance(config, dict) or set(config) != {
        "hands",
        "seed",
        "min_stack",
        "max_stack",
        "max_actions",
    }:
        raise ValueError("invalid engine validation config")
    for key in config:
        if type(config[key]) is not int or config[key] < (0 if key == "seed" else 1):
            raise ValueError(f"invalid {key}")
    if config["max_stack"] < config["min_stack"]:
        raise ValueError("invalid stack interval")
    root = Path(__file__).resolve().parents[1]
    provenance = source_provenance(
        root, args.config, entrypoints=("scripts/validate_engine.py",)
    )
    # Probe a declared model difference rather than silently treating it as a match.
    canary = new_hand((100, 1, 100), Deck(), button=2)
    canary_reference = reference_for(canary, Deck())
    canary_reference.pump()
    difference = {
        "scenario": "short_big_blind_bring_in",
        "stacks": [100, 1, 100],
        "button": 2,
        "own_call": canary.legal_actions.call_amount,
        "reference_call": int(canary_reference.oracle.checking_or_calling_amount),
        "own_min_raise": canary.legal_actions.min_raise_to,
        "reference_min_raise": (
            canary_reference.oracle.min_completion_betting_or_raising_to_amount
        ),
        "interpretation": (
            "nominal-blind model differs from posted-blind reference behavior"
        ),
    }
    assert (difference["own_call"], difference["reference_call"]) == (2, 1)
    assert config["min_stack"] >= 2, (
        "matched trace domain requires covered starting blinds"
    )
    secured = new_hand((5, 100, 100), Deck(), button=2)
    secured_ref = reference_for(secured, Deck())
    for action in (
        Action(ActionKind.RAISE_TO, 10),
        Action(ActionKind.CALL),
        Action(ActionKind.CALL),
        Action(ActionKind.FOLD),
    ):
        secured_ref.pump()
        secured_ref.apply(action)
        secured = secured.apply(action)
    secured_ref.pump()
    reference_exception = None
    try:
        secured_ref.apply(Action(ActionKind.FOLD))
    except AssertionError:
        reference_exception = "AssertionError"
    secured = secured.apply(Action(ActionKind.FOLD))
    assert reference_exception == "AssertionError"
    assert secured.stacks == (15, 90, 100)
    secured_difference = {
        "scenario": "free_fold_after_secured_side_pot",
        "reference_exception": reference_exception,
        "own_final_stacks": secured.stacks,
        "interpretation": "secured side pot retained while folding remaining main pot",
    }
    prior_caller = new_hand((28, 3, 15, 48), Deck(), button=1)
    prior_reference = reference_for(prior_caller, Deck())
    for action in (
        Action(ActionKind.CALL),
        Action(ActionKind.RAISE_TO, 3),
        Action(ActionKind.CALL),
        Action(ActionKind.CALL),
    ):
        prior_reference.pump()
        prior_reference.apply(action)
        prior_caller = prior_caller.apply(action)
    prior_reference.pump()
    caller_difference = {
        "scenario": "prior_caller_after_short_all_in",
        "own_min_raise": prior_caller.legal_actions.min_raise_to,
        "reference_min_raise": (
            prior_reference.oracle.min_completion_betting_or_raising_to_amount
        ),
        "reference_can_raise_to_5": prior_reference.oracle.can_complete_bet_or_raise_to(
            5
        ),
        "interpretation": (
            "prior caller faces only one extra chip after a two-chip full wager"
        ),
    }
    assert prior_caller.legal_actions.min_raise_to is None
    # A tied eleven-chip pot exposes the default reference's remainder rule.
    holes = tuple(
        tuple(map(parse_card, text.split()))
        for text in ("2d 3h", "4d 5h", "6d 7h", "8d 9h")
    )
    board = tuple(map(parse_card, "Tc Jc Qc Kc Ac".split()))
    prefix = tuple(cards[i] for i in range(2) for cards in holes)
    rest = [card for card in range(52) if card not in prefix + board]
    order = prefix + (rest[0],) + board[:3] + (rest[1], board[3], rest[2], board[4])
    odd_deck = Deck(order + tuple(card for card in range(52) if card not in order))
    odd = new_hand((100, 100, 3, 100), odd_deck, button=3)
    odd_ref = reference_for(odd, odd_deck, fractional=False)
    actions = [
        Action(ActionKind.RAISE_TO, 3),
        Action(ActionKind.CALL),
        Action(ActionKind.CALL),
        Action(ActionKind.FOLD),
    ]
    while not odd.terminal:
        action = actions.pop(0) if actions else Action(ActionKind.CHECK)
        odd_ref.pump()
        odd_ref.apply(action)
        odd = odd.apply(action)
    odd_ref.pump()
    assert odd.stacks == (101, 98, 4, 100)
    odd_difference = {
        "scenario": "multiple_odd_chips_in_tied_pot",
        "own_final_stacks": odd.stacks,
        "reference_default_final_stacks": tuple(
            map(int, odd_ref.values(odd_ref.oracle.stacks))
        ),
        "interpretation": "ours spreads remainder one chip per winner clockwise",
    }
    rng = Generator(PCG64(config["seed"]))
    completed = actions_checked = showdowns = side_pot_hands = 0
    reference_raise_allowances = 0
    board_runouts = 0
    failures: list[dict[str, object]] = []
    digest = hashlib.sha256()
    started = time.perf_counter()
    for index in range(config["hands"]):
        size = int(rng.integers(2, 7))
        stacks = tuple(
            int(value)
            for value in rng.integers(
                config["min_stack"], config["max_stack"] + 1, size
            )
        )
        button = int(rng.integers(size))
        deck = Deck.shuffled(rng)
        state = new_hand(stacks, deck, button=button)
        reference = reference_for(state, deck)
        selected: list[dict[str, object]] = []
        try:
            for _ in range(config["max_actions"]):
                reference.compare(state)
                if state.terminal:
                    completed += 1
                    reference_raise_allowances += (
                        reference.short_allin_reference_allowances
                    )
                    board_runouts += int(len(state.board) == 5)
                    showdowns += int(sum(not flag for flag in state.folded) > 1)
                    side_pot_hands += int(
                        len([pot for pot in state.pots if not pot.uncalled]) > 1
                    )
                    break
                action = choose(state, rng, index % 4)
                selected.append({"kind": action.kind.value, "amount": action.amount})
                reference.apply(action)
                state = state.apply(action)
                actions_checked += 1
            else:
                raise AssertionError("validation action budget exceeded")
        except (AssertionError, ValueError, RuntimeError) as error:
            failures.append(
                {
                    "hand_index": index,
                    "reason": str(error),
                    "stacks": stacks,
                    "button": button,
                    "deck": deck.cards,
                    "actions": selected,
                }
            )
            break
        digest.update(
            json.dumps(
                {
                    "stacks": stacks,
                    "button": button,
                    "deck": deck.cards,
                    "actions": selected,
                    "final_stacks": state.stacks,
                },
                sort_keys=True,
            ).encode()
        )
        if completed % 100 == 0:
            print(f"Matched {completed}/{config['hands']} hands", flush=True)
    report = {
        "schema_version": 2,
        "status": "passed"
        if not failures and completed == config["hands"]
        else "failed",
        "config": config,
        "documented_reference_differences": [
            difference,
            secured_difference,
            caller_difference,
            odd_difference,
        ],
        "matched_domain": "two through six seats, starting stacks cover 1/2 blinds",
        "hands_completed": completed,
        "actions_checked": actions_checked,
        "documented_reference_short_allin_raise_allowances": reference_raise_allowances,
        "comparison_scope": (
            "shared legal action traces and exact rational terminal payouts; "
            "integer rounding tested separately"
        ),
        "five_card_board_hands": board_runouts,
        "showdowns": showdowns,
        "side_pot_hands": side_pot_hands,
        "failures": failures,
        "input_and_trace_sha256": digest.hexdigest(),
        "source": provenance,
        "validation_seconds": time.perf_counter() - started,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
            "numpy": importlib.metadata.version("numpy"),
            "pokerkit": importlib.metadata.version("pokerkit"),
        },
        "reference": {
            "package": "pokerkit",
            "license": "MIT",
            "role": "validation only",
        },
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(report["status"], args.output)
    return 0 if report["status"] == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
