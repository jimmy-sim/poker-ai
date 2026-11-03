"""Audit trained own-policy inference and explicit off-tree fallbacks in simulation."""

import argparse
import hashlib
import json
import platform
import time
from collections import Counter
from pathlib import Path
from typing import Any

from numpy.random import PCG64, Generator

from poker_ai.agents.no_limit import OwnNoLimitAgent
from poker_ai.cards import Deck
from poker_ai.engine import Action, ActionKind, new_hand
from poker_ai.validation.five_card import source_provenance


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    config = json.loads(args.config.read_text())
    required = {
        "training_report",
        "model",
        "method",
        "training_seed",
        "iteration",
        "deal_seeds",
        "hands_per_seed",
        "max_actions",
        "on_grid_fraction_error_tolerance",
        "purpose",
    }
    if set(config) != required or config["method"] not in ("external", "outcome"):
        raise ValueError("invalid inference audit config")
    for key in ("training_seed", "iteration", "hands_per_seed", "max_actions"):
        if type(config[key]) is not int or config[key] < (
            0 if key == "training_seed" else 1
        ):
            raise ValueError("invalid audit budget/seed")
    if (
        not config["deal_seeds"]
        or len(set(config["deal_seeds"])) != len(config["deal_seeds"])
        or any(type(s) is not int or s < 0 for s in config["deal_seeds"])
        or not 0 < config["on_grid_fraction_error_tolerance"] < 1
    ):
        raise ValueError("invalid independent deal seeds/tolerance")
    root = Path(__file__).resolve().parents[1]
    report_path = root / config["training_report"]
    training = json.loads(report_path.read_text())
    selected = [
        r
        for r in training["rows"]
        if r["model"] == config["model"]
        and r["method"] == config["method"]
        and r["seed"] == config["training_seed"]
        and r["iteration"] == config["iteration"]
    ]
    if len(selected) != 1:
        raise ValueError("select exactly one verified own training checkpoint")
    checkpoint = Path(selected[0]["checkpoint"])
    if (
        hashlib.sha256(checkpoint.read_bytes()).hexdigest()
        != selected[0]["checkpoint_sha256"]
    ):
        raise ValueError("own checkpoint does not match recorded training evidence")
    source = source_provenance(
        root, args.config, entrypoints=("scripts/verify_own_agent.py",)
    )
    started = time.perf_counter()
    agent = OwnNoLimitAgent.load(checkpoint, root / config["model"])
    nearest = OwnNoLimitAgent(agent.model, agent.rules, agent.rows, scheme="nearest")
    counters: Counter[str] = Counter()
    rows: list[dict[str, Any]] = []
    digest = hashlib.sha256()
    hands = actions = 0
    for seed in config["deal_seeds"]:
        deals = Generator(PCG64(seed))
        choices = Generator(PCG64(seed + 1000000))
        for index in range(config["hands_per_seed"]):
            deck = Deck.shuffled(deals)
            state = new_hand(
                agent.rules.stacks,
                deck,
                button=index % 2,
                small_blind=agent.rules.small_blind,
                big_blind=agent.rules.big_blind,
            )
            selected_actions = []
            for _ in range(config["max_actions"]):
                assert sum(state.stacks) + state.pot == sum(state.starting_stacks)
                if state.terminal:
                    assert sum(state.net_payoffs) == 0
                    hands += 1
                    break
                assert state.actor is not None
                decision = agent.distribution(
                    state.observe(state.actor), episode_seed=seed * 1000 + index
                )
                assert decision.shadow.failure is None, "on-grid shadow failed"
                assert all(
                    r.actual_total == r.virtual_total for r in decision.shadow.raises
                )
                assert not decision.shadow.starting_stack_mismatch
                counters[decision.status] += 1
                if decision.decoded is not None:
                    assert (
                        decision.decoded.mean_raise_fraction_error
                        <= config["on_grid_fraction_error_tolerance"]
                    )
                    assert decision.decoded.clipped_raise_mass == 0
                    assert decision.decoded.unavailable_raise_mass == 0
                action = decision.sample(choices)
                selected_actions.append((state.actor, action.kind.value, action.amount))
                state = state.apply(action)
                actions += 1
            else:
                raise AssertionError("inference audit hand action budget exceeded")
            digest.update(
                json.dumps(
                    (seed, index, deck.cards, selected_actions, state.stacks)
                ).encode()
            )
    for total in (7, 150):
        for seed in config["deal_seeds"]:
            state = new_hand(
                agent.rules.stacks, Deck.shuffled(Generator(PCG64(seed))), button=1
            )
            state = state.apply(Action(ActionKind.RAISE_TO, total)).apply(
                Action(ActionKind.CALL)
            )
            assert state.actor is not None
            for kind, policy in (("pseudo_harmonic", agent), ("nearest", nearest)):
                before = state
                decision = policy.distribution(
                    state.observe(state.actor), episode_seed=seed
                )
                for action, p in zip(
                    decision.actions, decision.probabilities, strict=True
                ):
                    if p:
                        state.apply(action)  # Validate every supported output.
                assert state == before
                rows.append(
                    {
                        "case": "off_grid_after_raise_call",
                        "raise_to": total,
                        "seed": seed,
                        "scheme": kind,
                        "status": decision.status,
                        "shadow_failure": decision.shadow.failure,
                        "actual_pot": state.pot,
                        "virtual_pot": None
                        if decision.shadow.observation is None
                        else decision.shadow.observation.pot,
                        "actions": [(a.kind.value, a.amount) for a in decision.actions],
                        "probabilities": decision.probabilities,
                        "clipped_raise_mass": None
                        if decision.decoded is None
                        else decision.decoded.clipped_raise_mass,
                    }
                )
    assert all(
        r["status"] == "shadow_failure"
        for r in rows
        if r["raise_to"] == 150 and r["scheme"] == "nearest"
    )
    output = {
        "schema_version": 1,
        "status": "passed",
        "config": config,
        "source": source,
        "checkpoint_sha256": selected[0]["checkpoint_sha256"],
        "training_report_sha256": hashlib.sha256(report_path.read_bytes()).hexdigest(),
        "on_grid_hands": hands,
        "on_grid_decisions": actions,
        "on_grid_lookup_counts": dict(counters),
        "on_grid_input_action_digest": digest.hexdigest(),
        "off_grid_cases": rows,
        "seconds": time.perf_counter() - started,
        "environment": {
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "limitations": [
            "small fixed-seed interface audit, not a win-rate experiment",
            "lookup hit rate depends on the sampled hands/actions",
            "uniform fallback is legal but not a strategic guarantee",
            "source fingerprint checks do not replace locked environment reproduction",
        ],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n")
    print(
        f"passed: {hands} on-grid hands, {actions} decisions; lookups={dict(counters)}",
        flush=True,
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
