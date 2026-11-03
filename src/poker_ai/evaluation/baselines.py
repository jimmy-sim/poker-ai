"""Fixed, public-observation-only baseline policies for matched-grid evaluation."""

import hashlib
import json
from collections import Counter
from functools import lru_cache
from typing import Literal, Protocol

from numpy.random import PCG64, Generator

from poker_ai.abstraction.potential import canonical_cards
from poker_ai.abstraction.shadow import legal_actions
from poker_ai.agents.no_limit import OwnNoLimitAgent
from poker_ai.engine import Action, ActionKind, Observation
from poker_ai.equity import monte_carlo_equity
from poker_ai.training.no_limit import NoLimitRules

Kind = Literal["random", "always_call", "always_raise", "tight_aggressive", "equity"]


class Bot(Protocol):
    def act(
        self, observation: Observation, *, rng: Generator, episode_seed: int
    ) -> Action: ...


@lru_cache(maxsize=32768)
def _equity(
    hole: tuple[int, ...], board: tuple[int, ...], samples: int, seed: int
) -> float:
    digest = hashlib.sha256(json.dumps((hole, board, samples, seed)).encode()).digest()
    rng = Generator(PCG64(int.from_bytes(digest[:16], "little")))
    return monte_carlo_equity(hole, board=board, rng=rng, samples=samples).equity


def _premium(hole: tuple[int, ...]) -> bool:
    high, low = sorted((c // 4 for c in hole), reverse=True)
    suited = hole[0] % 4 == hole[1] % 4
    # Eight-eight or better, ATs+, KJs+, QJs, AKo/AQo. A transparent hand chart,
    # not a trained or claimed optimal TAG/preflop strategy.
    return (
        (high == low and high >= 6)
        or (high == 12 and low >= (8 if suited else 10))
        or (suited and high == 11 and low >= 9)
        or (suited and high == 10 and low == 9)
    )


class Baseline:
    def __init__(
        self,
        kind: Kind,
        rules: NoLimitRules,
        *,
        equity_samples: int = 64,
        equity_seed: int = 20261129,
        raise_equity: float = 0.65,
        call_margin: float = 0.05,
    ) -> None:
        if kind not in (
            "random",
            "always_call",
            "always_raise",
            "tight_aggressive",
            "equity",
        ):
            raise ValueError("unknown baseline")
        if (
            type(equity_samples) is not int
            or equity_samples < 1
            or type(equity_seed) is not int
            or equity_seed < 0
        ):
            raise ValueError("invalid fixed equity sample budget/seed")
        if not 0 <= call_margin <= 1 or not 0 <= raise_equity <= 1:
            raise ValueError("invalid equity heuristic thresholds")
        self.kind, self.rules = kind, rules
        self.equity_samples, self.equity_seed = equity_samples, equity_seed
        self.raise_equity, self.call_margin = raise_equity, call_margin

    def act(
        self, observation: Observation, *, rng: Generator, episode_seed: int
    ) -> Action:
        _, actions = legal_actions(observation, self.rules)
        passive = next(
            a for a in actions if a.kind in (ActionKind.CALL, ActionKind.CHECK)
        )
        raises = [a for a in actions if a.kind == ActionKind.RAISE_TO]
        if self.kind == "random":
            return actions[int(rng.integers(len(actions)))]
        if self.kind == "always_call":
            return passive
        if self.kind == "always_raise":
            return raises[-1] if raises else passive
        legal = observation.legal_actions
        assert legal is not None
        if self.kind == "tight_aggressive" and not observation.board:
            return (
                (raises[0] if raises else passive)
                if _premium(observation.hole_cards)
                else (passive if legal.can_check else Action(ActionKind.FOLD))
            )
        hole, board = canonical_cards(observation.hole_cards, observation.board)
        equity = _equity(hole, board, self.equity_samples, self.equity_seed)
        if equity >= self.raise_equity and raises:
            return raises[0]
        if (
            legal.can_check
            or equity
            >= legal.call_amount / (observation.pot + legal.call_amount)
            + self.call_margin
        ):
            return passive
        return Action(ActionKind.FOLD)


class FrozenOwnBot:
    """Audit counters do not update frozen strategy rows or train on opponents."""

    def __init__(self, agent: OwnNoLimitAgent) -> None:
        self.agent = agent
        self.lookups: Counter[str] = Counter()
        self.projected_decisions = 0

    def act(
        self, observation: Observation, *, rng: Generator, episode_seed: int
    ) -> Action:
        decision = self.agent.distribution(observation, episode_seed=episode_seed)
        self.lookups[decision.status] += 1
        if decision.decoded is not None:
            self.projected_decisions += int(
                decision.decoded.clipped_raise_mass > 0
                or decision.decoded.unavailable_raise_mass > 0
                or decision.decoded.mean_raise_fraction_error > 0
            )
        return decision.sample(rng)
