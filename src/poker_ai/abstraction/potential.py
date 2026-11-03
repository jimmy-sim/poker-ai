"""Conditional equity distributions over future streets, sampled from own rules.

A histogram over final-board conditional equity is distribution aware. Potential
features include conditional-equity distributions at EVERY future board length
(flop, turn, river as applicable), plus current expected showdown share. Nested
Monte Carlo introduces measurement noise; these features are estimates, not exact
information-loss certificates or a replication of an external abstraction system.
"""

import hashlib
import itertools
import json
from dataclasses import asdict, dataclass

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.cards import cards_to_mask
from poker_ai.equity import monte_carlo_equity
from poker_ai.toy.tree import FloatArray

SUIT_PERMUTATIONS = tuple(itertools.permutations(range(4)))


@dataclass(frozen=True, slots=True)
class FeatureConfig:
    runouts: int = 8
    opponent_samples: int = 8
    current_samples: int = 64
    bins: int = 9
    seed: int = 20261118

    def __post_init__(self) -> None:
        for name in ("runouts", "opponent_samples", "current_samples", "bins", "seed"):
            value = getattr(self, name)
            if type(value) is not int or value < (0 if name == "seed" else 1):
                raise ValueError(f"invalid feature {name}")
        if self.bins < 2:
            raise ValueError("need at least two equity grid points")


@dataclass(frozen=True)
class Potential:
    equity: float
    board_lengths: tuple[int, ...]
    histograms: FloatArray


def canonical_cards(
    hole: tuple[int, ...], board: tuple[int, ...]
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Canonicalize all 24 suit permutations and unordered known card sets.

    Card order within a known board does not affect conditional equity. Past
    street information is separately reconstructed from the original public
    prefixes by the information-key builder; it is not recovered from this key.
    """
    if len(hole) != 2 or len(board) not in (0, 3, 4, 5):
        raise ValueError("need two private cards and a Hold'em board length")
    cards_to_mask(hole + board)
    return min(
        (
            tuple(sorted(4 * (card // 4) + permutation[card % 4] for card in hole)),
            tuple(sorted(4 * (card // 4) + permutation[card % 4] for card in board)),
        )
        for permutation in SUIT_PERMUTATIONS
    )


def feature_rng(
    hole: tuple[int, ...], board: tuple[int, ...], config: FeatureConfig
) -> Generator:
    """Deterministic public/own-card seed, independent of the training RNG.

    The feature seed depends on canonical known cards and feature settings only,
    never actual opponent holes or future dealer cards. Python's randomized hash
    is not used. Bucket-count ablations share the same feature measurements.
    """
    canonical = canonical_cards(hole, board)
    digest = hashlib.sha256(
        json.dumps((canonical, asdict(config)), sort_keys=True).encode()
    ).digest()
    return Generator(PCG64(int.from_bytes(digest[:16], "little")))


def grid_histogram(values: FloatArray, bins: int) -> FloatArray:
    """Nearest grid-point histogram on linspace(0,1,bins), ties round upward."""
    if (
        type(bins) is not int
        or bins < 2
        or values.ndim != 1
        or len(values) == 0
        or not np.all(np.isfinite(values))
        or np.any(values < 0)
        or np.any(values > 1)
    ):
        raise ValueError("invalid equity samples/grid")
    positions = np.floor(values * (bins - 1) + 0.5).astype(np.int64)
    return np.asarray(
        np.bincount(positions, minlength=bins) / len(values), dtype=np.float64
    )


def estimate_potential(
    hole: tuple[int, ...],
    board: tuple[int, ...],
    *,
    config: FeatureConfig,
    rng: Generator,
) -> Potential:
    """Sample current equity and distributions of future conditional equity.

    At each outer future-board draw, nested Monte Carlo estimates showdown equity
    against a uniform opponent, conditional on that future board. Opponent cards
    are removed jointly with all known cards. Each street's marginal is valid;
    outer boards are shared across streets to represent the same development.
    Current equity is a separate bounded Monte Carlo estimate. River has only a
    single current-strength point, never artificial future-variation histograms.
    """
    canonical_cards(hole, board)  # Validation before any RNG consumption.
    current = monte_carlo_equity(
        hole, None, board, samples=config.current_samples, rng=rng
    ).equity
    future = tuple(length for length in (3, 4, 5) if length > len(board))
    histograms = [grid_histogram(np.array([current]), config.bins)]
    if future:
        used = set(hole + board)
        remaining = np.array([card for card in range(52) if card not in used])
        values = np.zeros((len(future), config.runouts))
        for sample in range(config.runouts):
            extra = tuple(
                int(card)
                for card in rng.choice(remaining, 5 - len(board), replace=False)
            )
            completed = board + extra
            for index, length in enumerate(future):
                values[index, sample] = monte_carlo_equity(
                    hole,
                    None,
                    completed[:length],
                    samples=config.opponent_samples,
                    rng=rng,
                ).equity
        histograms += [grid_histogram(row, config.bins) for row in values]
    return Potential(current, (len(board),) + future, np.stack(histograms))


def deterministic_potential(
    hole: tuple[int, ...], board: tuple[int, ...], config: FeatureConfig
) -> Potential:
    canonical_hole, canonical_board = canonical_cards(hole, board)
    return estimate_potential(
        canonical_hole,
        canonical_board,
        config=config,
        rng=feature_rng(canonical_hole, canonical_board, config),
    )
