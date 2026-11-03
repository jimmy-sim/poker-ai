"""Strict versioned spot inputs and exact conditional card worlds.

Ranges are explicit weighted physical two-card combinations. Product weights are
conditioned on board compatibility and mutual card removal. Public prefix actions
fix pot/stacks/position; they do not infer endogenous ranges. All future community
cards are dealt at hidden chance nodes before betting, an equivalent chance-world
representation. Acting information never includes opponent cards or future cards.
"""

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from poker_ai.abstraction.actions import ActionAbstraction
from poker_ai.cards import Deck, cards_to_mask, parse_card
from poker_ai.engine import Action, ActionKind, HoldemState, new_hand
from poker_ai.training.holdem import exact_information
from poker_ai.training.no_limit import NoLimitRules, NoLimitState


@dataclass(frozen=True, slots=True)
class RangeHand:
    cards: tuple[int, int]
    weight: float


@dataclass(frozen=True)
class Spot:
    name: str
    board: tuple[int, ...]
    ranges: tuple[tuple[RangeHand, ...], tuple[RangeHand, ...]]
    rules: NoLimitRules
    prefix: tuple[Action, ...]
    pot: int
    stacks: tuple[int, int]
    actor: int
    hero: int
    texture: str
    max_tree_nodes: int
    joint: tuple[tuple[int, int, float], ...]

    @property
    def worlds(self) -> int:
        count = 52 - 4 - len(self.board)
        future = count if len(self.board) == 4 else count * (count - 1)
        return len(self.joint) * future


def _cards(raw: Any, count: int | None = None) -> tuple[int, ...]:
    if not isinstance(raw, list) or any(not isinstance(s, str) for s in raw):
        raise ValueError("cards must be a list of card strings")
    result = tuple(parse_card(s) for s in raw)
    if count is not None and len(result) != count:
        raise ValueError("incorrect card count")
    cards_to_mask(result)
    return result


def _positive_int(value: Any) -> bool:
    return type(value) is int and value > 0


def load_spot(path: Path) -> Spot:
    import math

    raw = json.loads(path.read_text())
    fields = {
        "schema_version",
        "name",
        "board",
        "ranges",
        "starting_stacks",
        "button",
        "blinds",
        "prefix_actions",
        "pot",
        "stacks",
        "actor",
        "hero",
        "texture",
        "action_abstraction",
        "max_tree_nodes",
        "range_conditioning",
    }
    if (
        not isinstance(raw, dict)
        or set(raw) != fields
        or type(raw["schema_version"]) is not int
        or raw["schema_version"] != 1
    ):
        raise ValueError("invalid versioned spot fields")
    if (
        not isinstance(raw["name"], str)
        or re.fullmatch(r"[a-z0-9_-]+", raw["name"]) is None
        or not isinstance(raw["texture"], str)
    ):
        raise ValueError("invalid spot identity/texture")
    if raw["range_conditioning"] != "product_weights_conditioned_on_card_removal":
        raise ValueError("unknown range conditioning convention")
    board = _cards(raw["board"])
    if len(board) not in (3, 4):
        raise ValueError("a spot starts on flop or turn")
    if not isinstance(raw["ranges"], list) or len(raw["ranges"]) != 2:
        raise ValueError("declare both physical-card ranges")
    ranges = []
    for entries in raw["ranges"]:
        if not isinstance(entries, list) or not entries:
            raise ValueError("each range needs weighted combos")
        hands = []
        seen = set()
        for entry in entries:
            if not isinstance(entry, dict) or set(entry) != {"cards", "weight"}:
                raise ValueError("invalid range entry")
            parsed = tuple(sorted(_cards(entry["cards"], 2)))
            weight = entry["weight"]
            if (
                type(weight) not in (int, float)
                or not math.isfinite(weight)
                or weight <= 0
                or parsed in seen
            ):
                raise ValueError("invalid weight or duplicate physical combo")
            seen.add(parsed)
            hands.append(RangeHand((parsed[0], parsed[1]), float(weight)))
        ranges.append(tuple(hands))
    abstraction = raw["action_abstraction"]
    if not isinstance(abstraction, dict) or set(abstraction) != {
        "fractions",
        "include_minimum",
        "include_all_in",
    }:
        raise ValueError("invalid spot action abstraction")
    betting = ActionAbstraction(
        fractions=tuple(tuple(pair) for pair in abstraction["fractions"]),
        include_minimum=abstraction["include_minimum"],
        include_all_in=abstraction["include_all_in"],
    )
    if (
        not isinstance(raw["starting_stacks"], list)
        or len(raw["starting_stacks"]) != 2
        or not isinstance(raw["blinds"], list)
        or len(raw["blinds"]) != 2
    ):
        raise ValueError("declare two starting stacks and both blinds")
    rules = NoLimitRules(
        stacks=tuple(raw["starting_stacks"]),
        button=raw["button"],
        small_blind=raw["blinds"][0],
        big_blind=raw["blinds"][1],
        action_abstraction=betting,
    )
    if not isinstance(raw["prefix_actions"], list):
        raise ValueError("prefix actions must be a list")
    prefix = []
    for entry in raw["prefix_actions"]:
        if not isinstance(entry, dict) or "kind" not in entry:
            raise ValueError("invalid public prefix action")
        kind = ActionKind(entry["kind"])
        expected = {"kind", "amount"} if kind == ActionKind.RAISE_TO else {"kind"}
        if set(entry) != expected:
            raise ValueError("invalid prefix action fields")
        prefix.append(Action(kind, entry.get("amount")))
    if (
        not _positive_int(raw["pot"])
        or not _positive_int(raw["max_tree_nodes"])
        or not isinstance(raw["stacks"], list)
        or len(raw["stacks"]) != 2
        or any(type(s) is not int or s < 0 for s in raw["stacks"])
        or type(raw["actor"]) is not int
        or raw["actor"] not in (0, 1)
        or type(raw["hero"]) is not int
        or raw["hero"] not in (0, 1)
    ):
        raise ValueError("invalid public root/budget")
    joint = []
    for first, h0 in enumerate(ranges[0]):
        for second, h1 in enumerate(ranges[1]):
            known = h0.cards + h1.cards + board
            if len(set(known)) == len(known):
                product = h0.weight * h1.weight
                if not math.isfinite(product) or product <= 0:
                    raise ValueError(
                        "joint weight outside finite positive floating range"
                    )
                joint.append((first, second, product))
    total = sum(weight for _, _, weight in joint)
    if total <= 0 or not math.isfinite(total):
        raise ValueError("no legal finite joint range after card removal")
    spot = Spot(
        raw["name"],
        board,
        (ranges[0], ranges[1]),
        rules,
        tuple(prefix),
        raw["pot"],
        tuple(raw["stacks"]),
        raw["actor"],
        raw["hero"],
        raw["texture"],
        raw["max_tree_nodes"],
        tuple((i, j, p / total) for i, j, p in joint),
    )
    i, j, _ = spot.joint[0]
    used = set(board + spot.ranges[0][i].cards + spot.ranges[1][j].cards)
    future = tuple(card for card in range(52) if card not in used)[: 5 - len(board)]
    dealer = spot_dealer(spot, i, j, future)
    if (
        dealer.terminal
        or dealer.board != board
        or dealer.pot != spot.pot
        or dealer.stacks != spot.stacks
        or dealer.actor != spot.actor
    ):
        raise ValueError(
            "public prefix does not reproduce stated pot/stacks/actor/board"
        )
    return spot


def spot_dealer(
    spot: Spot, first: int, second: int, future: tuple[int, ...]
) -> HoldemState:
    """An explicit chance world with fixed public board and hidden continuation."""
    holes = (spot.ranges[0][first].cards, spot.ranges[1][second].cards)
    completed = spot.board + future
    cards_to_mask(holes[0] + holes[1] + completed)
    if len(completed) != 5:
        raise ValueError("chance world must complete the five-card board")
    order = ((spot.rules.button + 1) % 2, spot.rules.button)
    private = tuple(holes[seat][index] for index in range(2) for seat in order)
    used = set(private + completed)
    burns = tuple(card for card in range(52) if card not in used)[:3]
    prefix = (
        private
        + (burns[0],)
        + completed[:3]
        + (burns[1], completed[3], burns[2], completed[4])
    )
    deck = Deck(prefix + tuple(card for card in range(52) if card not in prefix))
    state = new_hand(
        spot.rules.stacks,
        deck,
        button=spot.rules.button,
        small_blind=spot.rules.small_blind,
        big_blind=spot.rules.big_blind,
    )
    for action in spot.prefix:
        state = state.apply(action)
    return state


@dataclass(frozen=True)
class SpotState:
    spot: Spot
    first: int | None = None
    second: int | None = None
    future: tuple[int, ...] = ()
    dealer: HoldemState | None = None

    @property
    def chance(self) -> bool:
        return self.dealer is None

    @property
    def terminal(self) -> bool:
        return self.dealer is not None and self.dealer.terminal

    @property
    def actor(self) -> int:
        return (
            0 if self.dealer is None or self.dealer.actor is None else self.dealer.actor
        )

    @property
    def actions(self) -> tuple[int, ...]:
        if self.dealer is not None:
            return NoLimitState(self.dealer, self.spot.rules).actions
        if self.first is None:
            return tuple(sorted({i for i, _, _ in self.spot.joint}))
        if self.second is None:
            return tuple(j for i, j, _ in self.spot.joint if i == self.first)
        used = set(
            self.spot.board
            + self.spot.ranges[0][self.first].cards
            + self.spot.ranges[1][self.second].cards
            + self.future
        )
        return tuple(card for card in range(52) if card not in used)

    @property
    def chance_probabilities(self) -> tuple[float, ...]:
        if not self.chance:
            raise ValueError("only chance nodes have chance probabilities")
        if self.first is None:
            return tuple(
                sum(p for i, _, p in self.spot.joint if i == action)
                for action in self.actions
            )
        if self.second is None:
            total = sum(p for i, _, p in self.spot.joint if i == self.first)
            return tuple(
                next(
                    p for i, j, p in self.spot.joint if i == self.first and j == action
                )
                / total
                for action in self.actions
            )
        return (1 / len(self.actions),) * len(self.actions)

    @property
    def information(self) -> str:
        if self.dealer is None or self.dealer.actor is None:
            raise ValueError("information requires a decision node")
        return exact_information(self.dealer.observe(self.dealer.actor))

    @property
    def payoff(self) -> float:
        if self.dealer is None:
            raise ValueError("payoff requires a terminal deal")
        return float(self.dealer.net_payoffs[0])

    def child(self, action: int) -> "SpotState":
        if type(action) is not int or action not in self.actions:
            raise ValueError("invalid spot action")
        if self.dealer is not None:
            child = NoLimitState(self.dealer, self.spot.rules).child(action)
            return SpotState(
                self.spot, self.first, self.second, self.future, child.dealer
            )
        if self.first is None:
            return SpotState(self.spot, action)
        if self.second is None:
            return SpotState(self.spot, self.first, action)
        future = self.future + (action,)
        dealer = (
            None
            if len(future) < 5 - len(self.spot.board)
            else spot_dealer(self.spot, self.first, self.second, future)
        )
        return SpotState(self.spot, self.first, self.second, future, dealer)
