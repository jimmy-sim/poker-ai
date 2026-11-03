"""Read-only inference from own MCCFR checkpoints, with explicit legal fallbacks."""

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Literal

from numpy.random import Generator

from poker_ai.abstraction.actions import ActionAbstraction
from poker_ai.abstraction.model import CardAbstraction
from poker_ai.abstraction.shadow import (
    DecodedPolicy,
    Scheme,
    ShadowResult,
    decode_policy,
    legal_actions,
    reconcile,
)
from poker_ai.engine import Action, Observation
from poker_ai.training.checkpoint import FORMAT, load_checkpoint
from poker_ai.training.no_limit import NoLimitRules, NoLimitState, sample_no_limit

# Compare semantics that encode cards, keys, legal actions and payouts. Unrelated
# newly added analysis modules need not prevent inference from a frozen strategy.
ENCODER_FILES = (
    "cards.py",
    "engine.py",
    "equity.py",
    "evaluator.py",
    "abstraction/actions.py",
    "abstraction/clustering.py",
    "abstraction/model.py",
    "abstraction/potential.py",
    "training/no_limit.py",
)


@dataclass(frozen=True)
class PolicyRow:
    actions: tuple[int, ...]
    probabilities: tuple[float, ...] | None  # None: no average mass accumulated.


@dataclass(frozen=True)
class Decision:
    actions: tuple[Action, ...]
    probabilities: tuple[float, ...]
    status: Literal["matched", "unseen", "unaveraged", "shadow_failure"]
    shadow: ShadowResult
    decoded: DecodedPolicy | None

    def sample(self, rng: Generator) -> Action:
        return self.actions[int(rng.choice(len(self.actions), p=self.probabilities))]


@dataclass(frozen=True)
class InferenceContext:
    observation: Observation
    shadow: ShadowResult
    rules: NoLimitRules
    scheme: Scheme


class OwnNoLimitAgent:
    def __init__(
        self,
        model: CardAbstraction,
        rules: NoLimitRules,
        rows: Mapping[str, PolicyRow],
        *,
        scheme: Scheme = "pseudo_harmonic",
    ) -> None:
        if scheme not in ("nearest", "pseudo_harmonic"):
            raise ValueError("unknown public-history mapping scheme")
        self.model = model
        self.rules = rules
        self.rows = MappingProxyType(dict(rows))
        self.scheme = scheme

    @classmethod
    def load(
        cls, checkpoint: Path, model_path: Path, *, scheme: Scheme = "pseudo_harmonic"
    ) -> "OwnNoLimitAgent":
        payload = json.loads(checkpoint.read_text())
        if not isinstance(payload, dict) or payload.get("format") != FORMAT:
            raise ValueError("inference requires an own MCCFR checkpoint")
        config, source = payload["config"], payload["source"]
        if (
            not isinstance(source, dict)
            or not isinstance(config, dict)
            or not isinstance(config.get("training"), dict)
            or config.get("training", {}).get("game") != "no_limit"
        ):
            raise ValueError("inference requires an own no-limit checkpoint")
        if hashlib.sha256(model_path.read_bytes()).hexdigest() != config.get(
            "model_sha256"
        ):
            raise ValueError("own card model fingerprint mismatch")
        package_root = Path(__file__).resolve().parents[1]
        fingerprints = source.get("sha256", {})
        if not isinstance(fingerprints, dict):
            raise ValueError("invalid own encoder fingerprints")
        for relative in ENCODER_FILES:
            key = f"src/poker_ai/{relative}"
            if (
                fingerprints.get(key)
                != hashlib.sha256((package_root / relative).read_bytes()).hexdigest()
            ):
                raise ValueError(f"checkpoint encoder fingerprint mismatch: {relative}")
        raw = config["training"]["rules"]
        abstraction = ActionAbstraction(
            fractions=tuple(tuple(pair) for pair in raw["fractions"]),
            include_minimum=raw["include_minimum"],
            include_all_in=raw["include_all_in"],
        )
        rules = NoLimitRules(
            stacks=tuple(raw["stacks"]),
            button=raw["button"],
            action_abstraction=abstraction,
        )
        model = CardAbstraction.load(model_path)
        # Drop the first JSON parse before the validated training loader parses
        # it. Conversion retains average probabilities, not mutable train state.
        del payload

        def factory(rng: Generator) -> NoLimitState:
            return sample_no_limit(rules, rng, information_builder=model.information)

        solver = load_checkpoint(checkpoint, factory, expected_config=config)
        rows = {}
        for key, row in solver.rows.items():
            total = float(row.strategy_sum.sum())
            probabilities = (
                None if total <= 0 else tuple((row.strategy_sum / total).tolist())
            )
            rows[key] = PolicyRow(row.actions, probabilities)
        return cls(model, rules, rows, scheme=scheme)

    def prepare(
        self,
        observation: Observation,
        *,
        episode_seed: int,
        actual_blinds: tuple[int, int] = (1, 2),
    ) -> InferenceContext:
        """Reuse public reconciliation across policies with identical rules."""
        shadow = reconcile(
            observation,
            self.rules,
            episode_seed=episode_seed,
            scheme=self.scheme,
            actual_blinds=actual_blinds,
        )
        return InferenceContext(observation, shadow, self.rules, self.scheme)

    def distribution(
        self,
        observation: Observation,
        *,
        episode_seed: int,
        actual_blinds: tuple[int, int] = (1, 2),
    ) -> Decision:
        return self.distribution_prepared(
            self.prepare(
                observation, episode_seed=episode_seed, actual_blinds=actual_blinds
            )
        )

    def distribution_prepared(self, context: InferenceContext) -> Decision:
        if context.rules != self.rules or context.scheme != self.scheme:
            raise ValueError(
                "prepared public context has different betting rules or mapping scheme"
            )
        observation, shadow = context.observation, context.shadow
        _, actual_actions = legal_actions(observation, self.rules)
        fallback = (1 / len(actual_actions),) * len(actual_actions)
        if shadow.observation is None:
            return Decision(actual_actions, fallback, "shadow_failure", shadow, None)
        key = self.model.information(shadow.observation)
        row = self.rows.get(key)
        if row is None:
            return Decision(actual_actions, fallback, "unseen", shadow, None)
        if row.probabilities is None:
            return Decision(actual_actions, fallback, "unaveraged", shadow, None)
        decoded = decode_policy(
            observation,
            shadow.observation,
            self.rules,
            action_ids=row.actions,
            probabilities=row.probabilities,
            scheme=self.scheme,
        )
        return Decision(
            decoded.actions, decoded.probabilities, "matched", shadow, decoded
        )

    def act(
        self,
        observation: Observation,
        *,
        rng: Generator,
        episode_seed: int,
        actual_blinds: tuple[int, int] = (1, 2),
    ) -> Action:
        return self.distribution(
            observation, episode_seed=episode_seed, actual_blinds=actual_blinds
        ).sample(rng)
