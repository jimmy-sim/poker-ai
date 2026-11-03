"""Heads-up showdown equity under fixed hands or a uniform opponent range.

Equity is expected pot share: win=1, tie=1/2, loss=0. It is not a betting strategy
or an EV estimate net of costs. All conditioning cards are removed before any
enumeration or sampling; no reference poker library is used.
"""

import math
from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from itertools import combinations
from typing import Literal

from numpy.random import Generator

from poker_ai.cards import FULL_DECK_MASK, cards_to_mask, mask_to_cards
from poker_ai.evaluator import evaluate_best

Outcome = Literal["win", "tie", "loss"]


def _confidence_level(level: float) -> None:
    if type(level) not in (int, float):
        raise TypeError("confidence_level must be numeric")
    if not math.isfinite(level) or not 0 < level < 1:
        raise ValueError("confidence_level must be finite and strictly between 0 and 1")


@dataclass(frozen=True, slots=True)
class EquityResult:
    """Outcome counts and uncertainty for a conditional heads-up equity.

    Exact enumeration has no Monte Carlo sampling error. For sampled bounded
    payoffs Xi in {0, 1/2, 1}, report an estimated standard error and a conservative
    two-sided Hoeffding interval. The latter stays nonzero-width after observing
    only wins or losses; an empirical standard error of zero is not certainty.
    """

    wins: int
    ties: int
    losses: int
    method: Literal["exact", "monte_carlo"]
    confidence_level: float | None = None

    def __post_init__(self) -> None:
        for count in (self.wins, self.ties, self.losses):
            if type(count) is not int:
                raise TypeError("outcome counts must be built-in integers")
            if count < 0:
                raise ValueError("outcome counts cannot be negative")
        if self.trials < 1:
            raise ValueError("at least one outcome is required")
        if self.method == "monte_carlo":
            if self.confidence_level is None:
                raise ValueError("Monte Carlo results need a confidence level")
            _confidence_level(self.confidence_level)
        elif self.method != "exact" or self.confidence_level is not None:
            raise ValueError("exact results have no sampling confidence level")

    @property
    def trials(self) -> int:
        return self.wins + self.ties + self.losses

    @property
    def equity(self) -> float:
        return (self.wins + self.ties / 2) / self.trials

    @property
    def outcome_variance(self) -> float:
        """Descriptive payoff variance; exact population variance when enumerated."""
        second_moment = (self.wins + self.ties / 4) / self.trials
        return max(0.0, second_moment - self.equity**2)

    @property
    def standard_error(self) -> float | None:
        """SE from unbiased sample variance; absent for exact results or n=1."""
        if self.method == "exact" or self.trials < 2:
            return None
        return math.sqrt(self.outcome_variance / (self.trials - 1))

    @property
    def confidence_interval(self) -> tuple[float, float] | None:
        """Finite-sample Hoeffding interval for independent fixed-budget draws.

        P(|mean-E[Xi]| >= epsilon) <= 2 exp(-2 n epsilon^2), since Xi is in [0,1].
        Invert at alpha=1-confidence_level, then intersect with [0,1]. This is
        conservative; it is not a normal approximation or an anytime interval.
        """
        if self.confidence_level is None:
            return None
        radius = math.sqrt(
            math.log(2 / (1 - self.confidence_level)) / (2 * self.trials)
        )
        return max(0.0, self.equity - radius), min(1.0, self.equity + radius)


@dataclass(frozen=True)
class _Prepared:
    hero: tuple[int, ...]
    villain: tuple[int, ...] | None
    board: tuple[int, ...]
    available: tuple[int, ...]

    @property
    def missing_board(self) -> int:
        return 5 - len(self.board)

    @property
    def states(self) -> int:
        if self.villain is not None:
            return math.comb(len(self.available), self.missing_board)
        return math.comb(len(self.available), 2) * math.comb(
            len(self.available) - 2, self.missing_board
        )


def _prepare(
    hero: Iterable[int],
    villain: Iterable[int] | None,
    board: Iterable[int],
    dead_cards: Iterable[int],
) -> _Prepared:
    h = tuple(hero)
    v = None if villain is None else tuple(villain)
    b, dead = tuple(board), tuple(dead_cards)
    if len(h) != 2 or (v is not None and len(v) != 2):
        raise ValueError("each specified player hand must contain exactly two cards")
    if len(b) > 5:
        raise ValueError("board can contain zero through five cards")
    known = h + (() if v is None else v) + b + dead
    mask = cards_to_mask(known)
    available = mask_to_cards(FULL_DECK_MASK ^ mask)
    if len(available) < 5 - len(b) + (2 if v is None else 0):
        raise ValueError("not enough cards remain after conditioning and exclusions")
    return _Prepared(h, v, b, available)


def equity_state_count(
    hero: Iterable[int],
    villain: Iterable[int] | None = None,
    board: Iterable[int] = (),
    *,
    dead_cards: Iterable[int] = (),
) -> int:
    """Count exact outcomes before committing compute; unknown villains are uniform."""
    return _prepare(hero, villain, board, dead_cards).states


def _outcome(
    hero: tuple[int, ...], villain: tuple[int, ...], board: tuple[int, ...]
) -> Outcome:
    first, second = evaluate_best(hero + board), evaluate_best(villain + board)
    return "win" if first > second else "tie" if first == second else "loss"


def exact_equity(
    hero: Iterable[int],
    villain: Iterable[int] | None = None,
    board: Iterable[int] = (),
    *,
    dead_cards: Iterable[int] = (),
    max_states: int = 2_000_000,
) -> EquityResult:
    """Enumerate all equally weighted legal opponent/runout combinations.

    None means every available two-card opponent hand is equally likely; a
    specified opponent hand is fixed. With an unknown opponent, choose its two
    cards first, then a board completion from the remaining deck. This enumerates
    C(n,2)*C(n-2,missing_board) equally weighted states, with card removal.
    """
    if type(max_states) is not int:
        raise TypeError("max_states must be an integer")
    if max_states < 1:
        raise ValueError("max_states must be positive")
    prepared = _prepare(hero, villain, board, dead_cards)
    if prepared.states > max_states:
        raise ValueError(
            f"Exact equity needs {prepared.states:,} outcomes; "
            f"above max_states={max_states:,}. "
            "use Monte Carlo or explicitly raise the budget."
        )
    counts: Counter[Outcome] = Counter()
    opponents = (
        (prepared.villain,)
        if prepared.villain is not None
        else combinations(prepared.available, 2)
    )
    for opponent in opponents:
        remaining = tuple(card for card in prepared.available if card not in opponent)
        for runout in combinations(remaining, prepared.missing_board):
            counts[_outcome(prepared.hero, opponent, prepared.board + runout)] += 1
    return EquityResult(counts["win"], counts["tie"], counts["loss"], "exact")


def monte_carlo_equity(
    hero: Iterable[int],
    villain: Iterable[int] | None = None,
    board: Iterable[int] = (),
    *,
    rng: Generator,
    samples: int = 10_000,
    dead_cards: Iterable[int] = (),
    confidence_level: float = 0.95,
) -> EquityResult:
    """Sample independent legal deals, with explicit RNG and fixed sample budget.

    Draw all unknown cards without replacement within a trial. Whole trials are
    independent and may repeat. The first two sampled cards belong to an unknown
    opponent, followed by a board completion; permutations have equal multiplicity,
    matching the exact enumeration's uniform conditional distribution.
    """
    if not isinstance(rng, Generator):
        raise TypeError("rng must be an explicit numpy.random.Generator")
    if type(samples) is not int:
        raise TypeError("samples must be an integer")
    if samples < 1:
        raise ValueError("samples must be positive")
    _confidence_level(confidence_level)
    prepared = _prepare(hero, villain, board, dead_cards)
    unknown = 2 if prepared.villain is None else 0
    draw_count = unknown + prepared.missing_board
    counts: Counter[Outcome] = Counter()
    for _ in range(samples):
        indices = rng.choice(len(prepared.available), draw_count, replace=False)
        drawn = tuple(prepared.available[int(index)] for index in indices)
        opponent = drawn[:2] if prepared.villain is None else prepared.villain
        counts[_outcome(prepared.hero, opponent, prepared.board + drawn[unknown:])] += 1
    return EquityResult(
        counts["win"], counts["tie"], counts["loss"], "monte_carlo", confidence_level
    )
