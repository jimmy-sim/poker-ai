"""Heads-up fixed-limit training adapter over the own validated Hold'em engine.

Chance is sampled as a full uniform deck in the root factory. Future cards stay
in dealer state and never enter a policy key. Reusing this chance tape across own
branches correlates samples but preserves their expectation. This initial limit
model requires enough funding to cover every capped wager, so short-limit-all-in
completion/reopening rules are outside its domain.
"""

import json
from collections.abc import Callable
from dataclasses import dataclass

from numpy.random import Generator

from poker_ai.cards import Deck
from poker_ai.engine import Action, ActionKind, HoldemState, Observation, new_hand

InformationBuilder = Callable[[Observation], str]


def exact_information(observation: Observation) -> str:
    """Perfect-recall public history plus own cards; no dealer-state argument."""
    return json.dumps(
        {
            "seat": observation.seat,
            "button": observation.button,
            "hole": sorted(observation.hole_cards),
            "board": observation.board,
            "stacks": observation.stacks,
            "paid": observation.total_commitments,
            "street": int(observation.street),
            "history": [
                (r.seat, int(r.street), r.action.kind.value, r.action.amount)
                for r in observation.history
            ],
        },
        sort_keys=True,
        separators=(",", ":"),
    )


@dataclass(frozen=True, slots=True)
class LimitRules:
    stacks: tuple[int, int] = (200, 200)
    button: int = 1
    small_blind: int = 1
    big_blind: int = 2
    bet_cap: int = 4

    def __post_init__(self) -> None:
        if (
            type(self.small_blind) is not int
            or type(self.big_blind) is not int
            or self.small_blind < 1
            or self.big_blind != 2 * self.small_blind
        ):
            raise ValueError("limit model requires positive 1:2 blinds")
        if type(self.bet_cap) is not int or self.bet_cap < 2:
            raise ValueError("bet cap must allow at least two bets")
        if type(self.button) is not int or self.button not in (0, 1):
            raise ValueError("heads-up button must be zero or one")
        if (
            not isinstance(self.stacks, tuple)
            or len(self.stacks) != 2
            or any(
                type(s) is not int or s <= self.maximum_commitment for s in self.stacks
            )
        ):
            raise ValueError(
                "limit stacks must cover every capped wager without all-ins"
            )

    @property
    def bet_sizes(self) -> tuple[int, int, int, int]:
        return (self.big_blind, self.big_blind, 2 * self.big_blind, 2 * self.big_blind)

    @property
    def maximum_commitment(self) -> int:
        return self.bet_cap * sum(self.bet_sizes)


@dataclass(frozen=True)
class LimitState:
    dealer: HoldemState
    rules: LimitRules
    information_builder: InformationBuilder = exact_information

    @property
    def terminal(self) -> bool:
        return self.dealer.terminal

    @property
    def chance(self) -> bool:
        return False  # Chance world is explicitly sampled by the root factory.

    @property
    def chance_probabilities(self) -> tuple[float, ...]:
        raise ValueError("Hold'em chance is sampled in the root factory")

    @property
    def actor(self) -> int:
        return 0 if self.dealer.actor is None else self.dealer.actor

    @property
    def raise_to(self) -> int:
        return self.dealer.current_bet + self.rules.bet_sizes[int(self.dealer.street)]

    @property
    def actions(self) -> tuple[int, ...]:
        if self.terminal:
            return ()
        legal = self.dealer.legal_actions
        bets = int(self.dealer.street == 0) + sum(
            r.street == self.dealer.street and r.action.kind == ActionKind.RAISE_TO
            for r in self.dealer.history
        )
        may_raise = (
            bets < self.rules.bet_cap
            and legal.min_raise_to is not None
            and legal.max_raise_to is not None
            and legal.min_raise_to <= self.raise_to <= legal.max_raise_to
        )
        return (
            ((0,) if not legal.can_check else ()) + (1,) + ((2,) if may_raise else ())
        )

    @property
    def information(self) -> str:
        if self.terminal:
            raise ValueError("terminal states have no acting information set")
        return self.information_builder(self.dealer.observe(self.actor))

    @property
    def payoff(self) -> float:
        return float(self.dealer.net_payoffs[0])

    def child(self, action: int) -> "LimitState":
        if type(action) is not int or action not in self.actions:
            raise ValueError("illegal fixed-limit action")
        if action == 0:
            move = Action(ActionKind.FOLD)
        elif action == 1:
            move = Action(
                ActionKind.CHECK
                if self.dealer.legal_actions.can_check
                else ActionKind.CALL
            )
        else:
            move = Action(ActionKind.RAISE_TO, self.raise_to)
        return LimitState(self.dealer.apply(move), self.rules, self.information_builder)


def sample_limit(
    rules: LimitRules,
    rng: Generator,
    *,
    information_builder: InformationBuilder = exact_information,
) -> LimitState:
    return LimitState(
        new_hand(
            rules.stacks,
            Deck.shuffled(rng),
            button=rules.button,
            small_blind=rules.small_blind,
            big_blind=rules.big_blind,
        ),
        rules,
        information_builder,
    )
