"""Bounded-return log growth and distinct fixed/fractional bankroll processes."""

import math
from dataclasses import dataclass
from statistics import NormalDist
from typing import Any

import numpy as np
from numpy.random import Generator
from numpy.typing import NDArray

from poker_ai.toy.tree import FloatArray, Tree


@dataclass(frozen=True)
class ReturnLaw:
    """Net profit / fixed maximum loss unit, bounded in [-1,1].

    Fraction f means wealth multiplies by 1+f*return. It is a mathematical
    position scaling model, not a claim that poker stakes can be scaled freely.
    """

    outcomes: FloatArray
    probabilities: FloatArray

    def __post_init__(self) -> None:
        x, p = self.outcomes, self.probabilities
        if (
            x.ndim != 1
            or not len(x)
            or p.shape != x.shape
            or not np.all(np.isfinite(x))
            or not np.all(np.isfinite(p))
            or np.any(np.abs(x) > 1)
            or np.any(p < 0)
            or not np.isclose(p.sum(), 1, atol=1e-12, rtol=0)
        ):
            raise ValueError("invalid bounded normalized return law")

    @property
    def mean(self) -> float:
        return float(self.outcomes @ self.probabilities)

    def log_growth(self, fraction: float) -> float:
        if not math.isfinite(fraction) or not 0 <= fraction < 1:
            raise ValueError("fraction must be in [0,1); no borrowing")
        return float(self.probabilities @ np.log1p(fraction * self.outcomes))

    def kelly(self, cap: float = 0.95) -> float:
        """Maximize concave E[ln(1+fX)] over [0,cap], under this fixed law."""
        if not math.isfinite(cap) or not 0 < cap < 1:
            raise ValueError("cap must be in (0,1)")
        if self.mean <= 0:
            return 0.0

        def derivative(f: float) -> float:
            return float(self.probabilities @ (self.outcomes / (1 + f * self.outcomes)))

        if derivative(cap) >= 0:
            return cap
        low, high = 0.0, cap
        for _ in range(80):
            middle = (low + high) / 2
            if derivative(middle) > 0:
                low = middle
            else:
                high = middle
        return (low + high) / 2


def binary_law(win_probability: float) -> ReturnLaw:
    if not math.isfinite(win_probability) or not 0 <= win_probability <= 1:
        raise ValueError("invalid win probability")
    return ReturnLaw(
        np.array([-1.0, 1.0]), np.array([1 - win_probability, win_probability])
    )


def robust_binary_fraction(lower: float, upper: float, cap: float = 0.95) -> float:
    """Worst-case expected log growth over a specified probability interval.

    For f>=0, log growth increases in p. Thus the worst p is lower, and its
    nonnegative Kelly fraction is max(0,2*lower-1), capped. This is a sensitivity
    set supplied by the experiment, NOT a confidence set inferred from poker.
    """
    if not (0 <= lower <= upper <= 1):
        raise ValueError("invalid probability uncertainty interval")
    return binary_law(lower).kelly(cap)


def own_toy_return_law(
    tree: Tree,
    own: FloatArray,
    opponent: FloatArray,
    seat: int,
    rake_rate: float,
) -> ReturnLaw:
    """Exact terminal law; uncapped rake on all pots, including folds.

    Fee is rate*resolved_pot, paid by winner; split equally on a tie. This is an
    explicit toy fee schedule, not a real cash-game schedule. Net returns are
    scaled by the game's maximum absolute gross loss (2 Kuhn, 13 Leduc).
    """
    if seat not in (0, 1) or not math.isfinite(rake_rate) or not 0 <= rake_rate <= 0.1:
        raise ValueError("invalid toy seat/rake rate")
    profile = opponent.copy()
    profile[tree.owners == seat] = own[tree.owners == seat]
    reaches = tree.reaches(tree.edges(profile))
    terminal = np.flatnonzero(tree.player == -2)
    probabilities = tree.chance_reach[terminal] * reaches[terminal].prod(axis=1)
    gross = tree.terminal_values[terminal] * (1 if seat == 0 else -1)
    scale = float(np.max(np.abs(tree.terminal_values)))
    returns = gross.copy()
    for i, node in enumerate(terminal):
        state = tree.states[node]
        share = (
            (0.0 if state.folded == seat else 1.0)
            if state.folded is not None
            else (1.0 if gross[i] > 0 else 0.5 if gross[i] == 0 else 0.0)
        )
        returns[i] -= rake_rate * sum(state.paid) * share
    return ReturnLaw(returns / scale, probabilities)


def eventual_ruin(start: int, target: int, win_probability: float) -> float:
    """P(hit 0 before target), fixed +/-1 stake, absorbing boundaries, no fees."""
    _validate_walk(start, target, win_probability)
    if start == 0:
        return 1.0
    if start == target or win_probability == 1:
        return 0.0
    if win_probability == 0:
        return 1.0
    if win_probability == 0.5:
        return 1 - start / target
    log_ratio = math.log1p(-win_probability) - math.log(win_probability)
    if log_ratio > 0:
        hit_upper = (
            math.exp((start - target) * log_ratio)
            * (-math.expm1(-start * log_ratio))
            / (-math.expm1(-target * log_ratio))
        )
    else:
        hit_upper = math.expm1(start * log_ratio) / math.expm1(target * log_ratio)
    return 1 - hit_upper


def _validate_walk(start: int, target: int, probability: float) -> None:
    if (
        type(start) is not int
        or type(target) is not int
        or not 0 <= start <= target
        or target < 1
        or not math.isfinite(probability)
        or not 0 <= probability <= 1
    ):
        raise ValueError("invalid fixed-stake absorbing walk")


def finite_ruin(start: int, target: int, probability: float, horizon: int) -> float:
    """Finite-horizon exact absorbing-chain dynamic program, not eventual ruin."""
    _validate_walk(start, target, probability)
    if type(horizon) is not int or horizon < 0:
        raise ValueError("invalid horizon")
    mass = np.zeros(target + 1)
    mass[start] = 1
    for _ in range(horizon):
        updated = np.zeros_like(mass)
        updated[0], updated[-1] = mass[0], mass[-1]
        updated[2:] += probability * mass[1:-1]
        updated[:-2] += (1 - probability) * mass[1:-1]
        mass = updated
    return float(mass[0])


def _probability_summary(events: NDArray[np.bool_]) -> dict[str, Any]:
    """Independent-path binomial Wilson interval; not a hand-level interval."""
    n, successes = len(events), int(events.sum())
    p, z = successes / n, NormalDist().inv_cdf(0.975)
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    half = z / denominator * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return {
        "count": successes,
        "paths": n,
        "probability": p,
        "wilson_95": [max(0.0, center - half), min(1.0, center + half)],
    }


def simulate_fixed_stake(
    start: int,
    target: int,
    probability: float,
    horizon: int,
    paths: int,
    rng: Generator,
) -> dict[str, Any]:
    _validate_walk(start, target, probability)
    if type(horizon) is not int or horizon < 0 or type(paths) is not int or paths < 2:
        raise ValueError("invalid simulation dimensions")
    wealth = np.full(paths, start, dtype=np.int64)
    for _ in range(horizon):
        active = (wealth > 0) & (wealth < target)
        changes = np.where(rng.random(paths) < probability, 1, -1)
        wealth += changes * active
    return {
        "ruin": _probability_summary(wealth == 0),
        "unabsorbed": _probability_summary((wealth > 0) & (wealth < target)),
    }


def simulate_fractional(
    law: ReturnLaw,
    fraction: float,
    horizon: int,
    paths: int,
    rng: Generator,
    threshold: float = 0.2,
    drawdown_threshold: float = 0.5,
    persistence: float = 0.0,
) -> dict[str, Any]:
    """Independent paths; within-path returns can have sticky Markov dependence.

    Each step retains the previous outcome with probability persistence; otherwise
    resamples from law. Initial outcome follows law, so marginals stay fixed.
    Threshold crossing means wealth <= threshold*INITIAL wealth at any step;
    drawdown is 1-wealth/running_peak. Wealth is strictly positive for f<1, so
    threshold crossing is NOT bankruptcy. Natural-log wealth avoids underflow.
    """
    law.log_growth(fraction)
    if (
        type(horizon) is not int
        or horizon < 0
        or type(paths) is not int
        or paths < 2
        or not 0 < threshold < 1
        or not 0 < drawdown_threshold < 1
        or not 0 <= persistence < 1
    ):
        raise ValueError("invalid fractional simulation parameters")
    log_wealth, log_peak = np.zeros(paths), np.zeros(paths)
    crossed = np.zeros(paths, dtype=np.bool_)
    max_log_drawdown = np.zeros(paths)
    indices = rng.choice(len(law.outcomes), size=paths, p=law.probabilities)
    increments = np.log1p(fraction * law.outcomes)
    for step in range(horizon):
        if step:
            fresh = rng.choice(len(law.outcomes), size=paths, p=law.probabilities)
            indices = (
                np.where(rng.random(paths) < persistence, indices, fresh)
                if persistence
                else fresh
            )
        log_wealth += increments[indices]
        log_peak = np.maximum(log_peak, log_wealth)
        max_log_drawdown = np.maximum(max_log_drawdown, log_peak - log_wealth)
        crossed |= log_wealth <= math.log(threshold)
    drawdowns = -np.expm1(-max_log_drawdown)
    return {
        "threshold_crossing": _probability_summary(crossed),
        "drawdown_exceedance": _probability_summary(drawdowns >= drawdown_threshold),
        "terminal_loss": _probability_summary(log_wealth < 0),
        "mean_terminal_log_wealth": float(log_wealth.mean()),
        "se_terminal_log_wealth": float(log_wealth.std(ddof=1) / math.sqrt(paths)),
        "terminal_log_wealth_quantiles_05_50_95": np.quantile(
            log_wealth, [0.05, 0.5, 0.95]
        ).tolist(),
        "maximum_drawdown_quantiles_05_50_95": np.quantile(
            drawdowns, [0.05, 0.5, 0.95]
        ).tolist(),
        "literal_bankruptcy": "impossible in this f<1 bounded fractional model",
        "independent_unit": "one complete path, not individual correlated steps",
    }
