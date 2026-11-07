"Opt-in river mass bins from declared priors, never actual hidden hands."

import hashlib
import json
import math
from collections.abc import Iterable
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import Any

from poker_ai.abstraction.made_category import MadeCategoryAbstraction
from poker_ai.abstraction.model import CardAbstraction
from poker_ai.cards import cards_to_mask
from poker_ai.engine import Observation
from poker_ai.evaluator import evaluate_best

VERSION = "river-range-mass-q8-v1"
MASS_INTERVALS = 8
MASS_ORDER = ("blocked", "loss", "tie", "win")


@dataclass(frozen=True)
class RangePrior:
    "Canonical weighted physical combos, with exact normalized decimal masses."

    combos: tuple[tuple[int, int], ...]
    masses: tuple[Fraction, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.combos, tuple)
            or not isinstance(self.masses, tuple)
            or not self.combos
            or len(self.combos) != len(self.masses)
            or len(set(self.combos)) != len(self.combos)
            or tuple(sorted(self.combos)) != self.combos
            or any(not isinstance(m, Fraction) or m <= 0 for m in self.masses)
            or sum(self.masses) != 1
        ):
            raise ValueError("invalid canonical declared range")
        for combo in self.combos:
            if not isinstance(combo, tuple) or len(combo) != 2 or combo[0] >= combo[1]:
                raise ValueError("range combos must be sorted physical pairs")
            cards_to_mask(combo)

    @classmethod
    def create(
        cls, entries: Iterable[tuple[tuple[int, ...], int | float]]
    ) -> "RangePrior":
        weights: dict[tuple[int, int], Fraction] = {}
        for cards, weight in entries:
            if len(cards) != 2:
                raise ValueError("range combo needs two cards")
            cards_to_mask(cards)
            combo = min(cards), max(cards)
            if combo in weights or type(weight) not in (int, float) or weight <= 0:
                raise ValueError("duplicate combo or invalid prior weight")
            if isinstance(weight, float) and not math.isfinite(weight):
                raise ValueError("prior weight must be finite")
            weights[combo] = Fraction(str(weight))
        if not weights:
            raise ValueError("declared range cannot be empty")
        total = sum(weights.values())
        combos = tuple(sorted(weights))
        return cls(combos, tuple(weights[c] / total for c in combos))

    def canonical_payload(self) -> list[dict[str, Any]]:
        return [
            {"cards": c, "mass": [m.numerator, m.denominator]}
            for c, m in zip(self.combos, self.masses, strict=True)
        ]


@dataclass(frozen=True)
class RangeContext:
    """A fixed two-seat prior namespace; no dealt hand or policy parameter."""

    priors: tuple[RangePrior, RangePrior]
    identifier: str = field(init=False)

    def __post_init__(self) -> None:
        if (
            not isinstance(self.priors, tuple)
            or len(self.priors) != 2
            or not all(isinstance(p, RangePrior) for p in self.priors)
        ):
            raise ValueError("need fixed priors for two seats")
        payload = [
            "declared-range-context-v1",
            [p.canonical_payload() for p in self.priors],
        ]
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
        object.__setattr__(self, "identifier", hashlib.sha256(encoded).hexdigest())


def mass_bin(mass: Fraction) -> int:
    """Eight [k/8,(k+1)/8) intervals, with exact p=1 in bin seven."""
    if not isinstance(mass, Fraction) or not 0 <= mass <= 1:
        raise ValueError("mass must be an exact fraction in [0,1]")
    return min(
        MASS_INTERVALS - 1, (mass.numerator * MASS_INTERVALS) // mass.denominator
    )


@dataclass(frozen=True)
class RiverMass:
    masses: tuple[Fraction, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.masses, tuple)
            or len(self.masses) != 4
            or any(not isinstance(m, Fraction) or m < 0 for m in self.masses)
            or sum(self.masses) != 1
            or self.masses[0] == 1
        ):
            raise ValueError("need normalized masses and a compatible opponent")

    @property
    def bins(self) -> tuple[int, ...]:
        return tuple(mass_bin(m) for m in self.masses)

    @property
    def conditional_equity(self) -> Fraction:
        "Showdown equity given static compatibility, not a strategy/EV feature."
        blocked, _, tie, win = self.masses
        return (win + tie / 2) / (1 - blocked)


def river_mass(
    hole: tuple[int, ...], board: tuple[int, ...], prior: RangePrior
) -> RiverMass:
    "Unconditional blocked/loss/tie/win prior masses, using observed cards only."
    if len(hole) != 2 or len(board) != 5:
        raise ValueError("river mass needs own two cards and five observed board cards")
    known = cards_to_mask(hole + board)
    own = evaluate_best(hole + board)
    masses = [Fraction(0) for _ in MASS_ORDER]
    for combo, mass in zip(prior.combos, prior.masses, strict=True):
        if known & cards_to_mask(combo):
            index = 0
        else:
            other = evaluate_best(combo + board)
            index = 1 if own < other else 2 if own == other else 3
        masses[index] += mass
    return RiverMass(tuple(masses))


class RangeMassAbstraction(MadeCategoryAbstraction):
    """Context-bound optional research encoder; no deployable serialization.

    Earlier observations retain the unchanged category key, with an empty range
    feature. River features use only the acting player's cards and fixed other
    prior. A changed range context cannot silently reuse the same key namespace.
    """

    def __init__(self, base: CardAbstraction, context: RangeContext) -> None:
        if not isinstance(context, RangeContext):
            raise ValueError("need an explicit fixed range context")
        super().__init__(base.models, base.config)
        self._range_context = context

    @property
    def range_context(self) -> RangeContext:
        return self._range_context

    def information(self, observation: Observation) -> str:
        if observation.seat not in (0, 1) or len(observation.stacks) != 2:
            raise ValueError("range mass encoder supports two seats only")
        parent = super().information(observation)
        if (
            tuple(sorted(observation.hole_cards))
            not in self.range_context.priors[observation.seat].combos
        ):
            raise ValueError("own hand is outside the declared range context")
        bins = (
            river_mass(
                observation.hole_cards,
                observation.board,
                self.range_context.priors[1 - observation.seat],
            ).bins
            if len(observation.board) == 5
            else ()
        )
        return json.dumps(
            [VERSION, self.range_context.identifier, parent, bins],
            separators=(",", ":"),
        )

    def save(self, path: Path, *, provenance: dict[str, Any]) -> None:
        raise ValueError(
            "range context has no deployable serialization; save only the"
            " base quantizer"
        )

    @classmethod
    def load(cls, path: Path, *, cache_size: int = 8192) -> "RangeMassAbstraction":
        raise ValueError(
            "load the base quantizer, then supply the fixed range context explicitly"
        )
