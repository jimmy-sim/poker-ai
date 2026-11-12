"""Fixed-width public own-prior categories; never actual private alternatives."""

import json
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

from poker_ai.abstraction.range_mass import RangeMassAbstraction, RangePrior, mass_bin
from poker_ai.cards import cards_to_mask
from poker_ai.engine import Observation
from poker_ai.evaluator import HandCategory, evaluate_best

VERSION = "public-own-category-q8-packed-v1"
ORDER = ("blocked", *(c.name.lower() for c in HandCategory))
BITS = 30


def pack(bins: tuple[int, ...]) -> int:
    if len(bins) != 10 or any(type(b) is not int or not 0 <= b < 8 for b in bins):
        raise ValueError("need exactly ten integer interval labels in0..7")
    return sum(b << (3 * k) for k, b in enumerate(bins))


def unpack(word: int) -> tuple[int, ...]:
    """Decode interval labels only, never recover exact probability masses."""
    if type(word) is not int or not 0 <= word < 1 << BITS:
        raise ValueError("need a30-bit nonnegative integer word")
    return tuple((word >> (3 * k)) & 7 for k in range(10))


@dataclass(frozen=True)
class PublicOwnMass:
    masses: tuple[Fraction, ...]

    def __post_init__(self) -> None:
        if (
            not isinstance(self.masses, tuple)
            or len(self.masses) != 10
            or any(not isinstance(m, Fraction) or m < 0 for m in self.masses)
            or sum(self.masses) != 1
        ):
            raise ValueError("need ten unconditional exact masses summing to one")

    @property
    def bins(self) -> tuple[int, ...]:
        return tuple(mass_bin(m) for m in self.masses)

    @property
    def word(self) -> int:
        return pack(self.bins)


def public_own_mass(board: tuple[int, ...], prior: RangePrior) -> PublicOwnMass:
    """Pool COMPLETE prior alternatives using ONLY the public river board.

    Alternatives sharing the actual own hand's cards remain hypotheses. No
    actual own/opponent hand is accepted. Board-blocked mass remains explicit;
    even an all-blocked standalone prior is representable without normalization.
    """
    if len(board) != 5 or not isinstance(prior, RangePrior):
        raise ValueError("need five public river cards and a canonical prior")
    known = cards_to_mask(board)
    masses = [Fraction(0) for _ in ORDER]
    for hand, weight in zip(prior.combos, prior.masses, strict=True):
        index = (
            0
            if known & cards_to_mask(hand)
            else 1 + int(evaluate_best(hand + board).category)
        )
        masses[index] += weight
    return PublicOwnMass(tuple(masses))


class PublicOwnRangeAbstraction(RangeMassAbstraction):
    """Opt-in refinement of the complete parent, not a deployable model format."""

    def information(self, observation: Observation) -> str:
        if type(observation.seat) is not int or type(observation.actor) is not int:
            raise ValueError("need integer acting-seat indices")
        parent = super().information(observation)
        word = (
            public_own_mass(
                observation.board, self.range_context.priors[observation.seat]
            ).word
            if len(observation.board) == 5
            else None
        )
        return json.dumps([VERSION, parent, word], separators=(",", ":"))

    def save(self, path: Path, *, provenance: dict[str, Any]) -> None:
        raise ValueError("public own-range encoder has no deployable serialization")

    @classmethod
    def load(cls, path: Path, *, cache_size: int = 8192) -> "PublicOwnRangeAbstraction":
        raise ValueError("supply the base quantizer and explicit fixed range context")
