"""Heads-up no-limit training adapter using legal finite pot-relative actions."""

from dataclasses import dataclass, field

from numpy.random import Generator

from poker_ai.abstraction.actions import ActionAbstraction
from poker_ai.cards import Deck
from poker_ai.engine import Action, ActionKind, HoldemState, new_hand
from poker_ai.training.holdem import InformationBuilder, exact_information


@dataclass(frozen=True, slots=True)
class NoLimitRules:
    stacks: tuple[int, int] = (200, 200)
    button: int = 1
    small_blind: int = 1
    big_blind: int = 2
    action_abstraction: ActionAbstraction = field(default_factory=ActionAbstraction)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.stacks, tuple)
            or len(self.stacks) != 2
            or any(type(s) is not int or s < 1 for s in self.stacks)
        ):
            raise ValueError("no-limit training requires two positive integer stacks")
        if type(self.button) is not int or self.button not in (0, 1):
            raise ValueError("invalid heads-up button")
        if (
            type(self.small_blind) is not int
            or type(self.big_blind) is not int
            or self.small_blind < 1
            or self.big_blind != 2 * self.small_blind
        ):
            raise ValueError("training uses positive 1:2 blinds")


@dataclass(frozen=True)
class NoLimitState:
    dealer: HoldemState
    rules: NoLimitRules
    information_builder: InformationBuilder = exact_information

    @property
    def terminal(self) -> bool:
        return self.dealer.terminal

    @property
    def chance(self) -> bool:
        return False  # Uniform complete chance world sampled by root factory.

    @property
    def chance_probabilities(self) -> tuple[float, ...]:
        raise ValueError("no-limit chance is sampled in the root factory")

    @property
    def actor(self) -> int:
        return 0 if self.dealer.actor is None else self.dealer.actor

    @property
    def raise_targets(self) -> tuple[int, ...]:
        if self.terminal:
            return ()
        return self.rules.action_abstraction.raises(self.dealer.observe(self.actor))

    @property
    def actions(self) -> tuple[int, ...]:
        if self.terminal:
            return ()
        fold = () if self.dealer.legal_actions.can_check else (0,)
        return fold + (1,) + tuple(range(2, 2 + len(self.raise_targets)))

    @property
    def information(self) -> str:
        if self.terminal:
            raise ValueError("terminal state has no acting information set")
        return self.information_builder(self.dealer.observe(self.actor))

    @property
    def payoff(self) -> float:
        return float(self.dealer.net_payoffs[0])

    def decode(self, action: int) -> Action:
        if type(action) is not int or action not in self.actions:
            raise ValueError("illegal abstract no-limit action")
        if action == 0:
            return Action(ActionKind.FOLD)
        if action == 1:
            return Action(
                ActionKind.CHECK
                if self.dealer.legal_actions.can_check
                else ActionKind.CALL
            )
        return Action(ActionKind.RAISE_TO, self.raise_targets[action - 2])

    def child(self, action: int) -> "NoLimitState":
        return NoLimitState(
            self.dealer.apply(self.decode(action)), self.rules, self.information_builder
        )


def sample_no_limit(
    rules: NoLimitRules,
    rng: Generator,
    *,
    information_builder: InformationBuilder = exact_information,
) -> NoLimitState:
    return NoLimitState(
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
