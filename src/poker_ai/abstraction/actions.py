"""Finite pot-relative raise sets and explicit local off-grid size translation.

Raise amounts are total street commitments. A fraction f means an increment of
f times the pot AFTER matching the current wager, above the current price. This
is an action discretizer; it does not solve off-tree public-state reconciliation.
"""

from bisect import bisect_left
from dataclasses import dataclass
from typing import Literal

from numpy.random import Generator

from poker_ai.engine import Observation


@dataclass(frozen=True, slots=True)
class ActionAbstraction:
    fractions: tuple[tuple[int, int], ...] = ((1, 2), (1, 1), (2, 1))
    include_minimum: bool = True
    include_all_in: bool = True

    def __post_init__(self) -> None:
        if not isinstance(self.fractions, tuple) or not self.fractions:
            raise ValueError("declare a nonempty tuple of rational pot fractions")
        for pair in self.fractions:
            if (
                not isinstance(pair, tuple)
                or len(pair) != 2
                or any(type(x) is not int or x < 1 for x in pair)
            ):
                raise ValueError("pot fractions need positive built-in integers")
        if (
            type(self.include_minimum) is not bool
            or type(self.include_all_in) is not bool
        ):
            raise TypeError("action endpoint options must be booleans")

    def raises(self, observation: Observation) -> tuple[int, ...]:
        """Sorted unique legal totals; clamp/merge rounded and short-all-in sizes."""
        legal = observation.legal_actions
        if legal is None:
            raise ValueError("need the acting player's legal actions")
        if legal.min_raise_to is None or legal.max_raise_to is None:
            return ()
        low, high = legal.min_raise_to, legal.max_raise_to
        price = observation.street_commitments[observation.seat] + legal.call_amount
        pot_after_call = observation.pot + legal.call_amount
        totals = set()
        for numerator, denominator in self.fractions:
            # Exact rational nearest-integer rounding, halves upward.
            increment = (2 * pot_after_call * numerator + denominator) // (
                2 * denominator
            )
            totals.add(min(high, max(low, price + increment)))
        if self.include_minimum:
            totals.add(low)
        if self.include_all_in:
            totals.add(high)
        return tuple(sorted(totals))

    def translation(
        self,
        observation: Observation,
        observed_total: int,
        *,
        scheme: Literal["nearest", "pseudo_harmonic"] = "pseudo_harmonic",
    ) -> tuple[tuple[int, float], ...]:
        """Probability distribution over neighboring legal abstract raise totals.

        Exact sizes map to themselves. Nearest uses chip distance, ties lower.
        Pseudo-harmonic lower probability for normalized sizes A<=x<=B is
        (B-x)(1+A)/((B-A)(1+x)). Here increments above price are normalized by
        pot-after-call, yielding (b-x)*(P+a)/((b-a)*(P+x)) in chip increments.
        This implements the local formula, not a full off-tree strategy solver.
        """
        if scheme not in ("nearest", "pseudo_harmonic"):
            raise ValueError("unknown raise translation scheme")
        if type(observed_total) is not int:
            raise TypeError("observed raise-to must be a built-in int")
        choices = self.raises(observation)
        legal = observation.legal_actions
        if (
            not choices
            or legal is None
            or legal.min_raise_to is None
            or legal.max_raise_to is None
            or not legal.min_raise_to <= observed_total <= legal.max_raise_to
        ):
            raise ValueError("observed raise is outside legal full-game bounds")
        if observed_total <= choices[0]:
            return ((choices[0], 1.0),)
        if observed_total >= choices[-1]:
            return ((choices[-1], 1.0),)
        index = bisect_left(choices, observed_total)
        if choices[index] == observed_total:
            return ((observed_total, 1.0),)
        lower, upper = choices[index - 1], choices[index]
        if scheme == "nearest":
            chosen = (
                lower if observed_total - lower <= upper - observed_total else upper
            )
            return ((chosen, 1.0),)
        price = observation.street_commitments[observation.seat] + legal.call_amount
        pot = observation.pot + legal.call_amount
        probability = (
            (upper - observed_total)
            * (pot + lower - price)
            / ((upper - lower) * (pot + observed_total - price))
        )
        return ((lower, probability), (upper, 1 - probability))

    def translate(
        self,
        observation: Observation,
        observed_total: int,
        *,
        rng: Generator,
        scheme: Literal["nearest", "pseudo_harmonic"] = "pseudo_harmonic",
    ) -> int:
        distribution = self.translation(observation, observed_total, scheme=scheme)
        if len(distribution) == 1:
            return distribution[0][0]
        return (
            distribution[0][0]
            if rng.random() < distribution[0][1]
            else distribution[1][0]
        )
