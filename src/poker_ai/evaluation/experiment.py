"""Fixed-protocol match tasks; fresh workers retain frozen own policies only."""

import csv
import gzip
import hashlib
import importlib.metadata
import io
import json
import re
import time
from pathlib import Path
from typing import Any, cast

import numpy as np
from numpy.random import PCG64, Generator, SeedSequence

from poker_ai.abstraction.actions import ActionAbstraction
from poker_ai.agents.no_limit import OwnNoLimitAgent
from poker_ai.cards import Deck
from poker_ai.evaluation.baselines import Baseline, Bot, FrozenOwnBot, Kind
from poker_ai.evaluation.matches import play_hand
from poker_ai.evaluation.openspiel import OpenSpielBaseline
from poker_ai.evaluation.statistics import summarize_pairs
from poker_ai.training.no_limit import NoLimitRules


def betting_rules(config: dict[str, Any]) -> NoLimitRules:
    raw = config["rules"]
    if set(raw) != {
        "stacks",
        "button",
        "small_blind",
        "big_blind",
        "fractions",
        "include_minimum",
        "include_all_in",
    }:
        raise ValueError("invalid match betting settings")
    abstraction = ActionAbstraction(
        fractions=tuple(tuple(p) for p in raw["fractions"]),
        include_minimum=raw["include_minimum"],
        include_all_in=raw["include_all_in"],
    )
    rules = NoLimitRules(
        stacks=tuple(raw["stacks"]),
        button=raw["button"],
        small_blind=raw["small_blind"],
        big_blind=raw["big_blind"],
        action_abstraction=abstraction,
    )
    if (rules.button, rules.small_blind, rules.big_blind) != (1, 1, 2) or rules.stacks[
        0
    ] != rules.stacks[1]:
        raise ValueError(
            "native comparison requires equal stacks, button1 and 1/2 blinds"
        )
    if abstraction != ActionAbstraction(
        fractions=((1, 1),), include_minimum=False, include_all_in=True
    ):
        raise ValueError("this study requires the declared full-pot/all-in grid")
    return rules


def load_config(path: Path) -> dict[str, Any]:
    raw: dict[str, Any] = json.loads(path.read_text())
    required = {
        "schema_version",
        "purpose",
        "training_report",
        "primary_model",
        "method",
        "iteration",
        "agent_seeds",
        "rules",
        "opponents",
        "pilot_deals",
        "pilot_deal_seed",
        "main_deals",
        "main_deal_seed",
        "action_seed",
        "mapping_episode_seed",
        "workers",
        "max_actions_per_hand",
        "max_seconds_per_opponent",
        "native_validation",
        "inference",
        "primary_projection_mass_limit",
        "limitations",
    }
    if (
        set(raw) != required
        or type(raw["schema_version"]) is not int
        or raw["schema_version"] != 1
    ):
        raise ValueError("invalid evaluation config")
    for key in (
        "pilot_deals",
        "main_deals",
        "iteration",
        "max_actions_per_hand",
        "workers",
    ):
        if type(raw[key]) is not int or raw[key] < 1:
            raise ValueError("invalid evaluation counts")
    for key in (
        "pilot_deal_seed",
        "main_deal_seed",
        "action_seed",
        "mapping_episode_seed",
    ):
        if type(raw[key]) is not int or raw[key] < 0:
            raise ValueError("invalid match seeds")
    seeds = raw["agent_seeds"]
    if (
        not seeds
        or any(type(s) is not int or s < 0 for s in seeds)
        or len(set(seeds)) != len(seeds)
    ):
        raise ValueError("fixed agent seeds must be distinct")
    if (
        raw["pilot_deal_seed"] == raw["main_deal_seed"]
        or not 2 <= raw["pilot_deals"] < raw["main_deals"]
        or not 1 <= raw["workers"] <= 4
    ):
        raise ValueError("invalid independent pilot/main compute budgets")
    if (
        type(raw["max_seconds_per_opponent"]) not in (float, int)
        or not np.isfinite(raw["max_seconds_per_opponent"])
        or raw["max_seconds_per_opponent"] <= 0
    ):
        raise ValueError("invalid opponent time budget")
    opponents = raw["opponents"]
    if (
        not isinstance(opponents, list)
        or len(opponents) != 6
        or len({o["name"] for o in opponents}) != 6
    ):
        raise ValueError("declare six distinct baseline opponents")
    for opponent in opponents:
        if (
            not isinstance(opponent["name"], str)
            or re.fullmatch(r"[a-z0-9_]+", opponent["name"]) is None
        ):
            raise ValueError("invalid opponent identifier")
        kind = opponent["kind"]
        expected = {"name", "kind"}
        if kind in ("equity", "tight_aggressive"):
            expected |= {"equity_samples", "equity_seed", "raise_equity", "call_margin"}
        elif kind == "openspiel_ismcts":
            expected |= {
                "version",
                "implementation",
                "simulations",
                "world_samples",
                "uct_c",
                "rollouts",
            }
            if opponent["version"] != "2.0.2" or opponent["rollouts"] != 1:
                raise ValueError("native baseline version/rollout mismatch")
        elif kind not in ("random", "always_call", "always_raise"):
            raise ValueError("unknown baseline kind")
        if set(opponent) != expected:
            raise ValueError("invalid opponent fields")
    infer = raw["inference"]
    if (
        set(infer)
        != {"alpha", "family_size", "primary_test", "ci", "variance_reduction"}
        or type(infer["family_size"]) is not int
        or infer["family_size"] != len(opponents)
    ):
        raise ValueError("the test family must include all six pooled opponents")
    if type(infer["alpha"]) not in (float, int) or not 0 < infer["alpha"] < 1:
        raise ValueError("invalid inference alpha")
    validation = raw["native_validation"]
    if (
        set(validation) != {"hands", "seed", "payoff_tolerance"}
        or type(validation["hands"]) is not int
        or validation["hands"] < 1
        or type(validation["seed"]) is not int
        or validation["seed"] < 0
        or validation["payoff_tolerance"] != 1e-9
    ):
        raise ValueError("invalid native mechanics gate")
    if raw["method"] != "external" or raw["primary_projection_mass_limit"] != 0:
        raise ValueError("this study requires external sampling and identical actions")
    betting_rules(raw)
    return raw


def opponent_bot(raw: dict[str, Any], rules: NoLimitRules) -> Bot:
    if raw["kind"] == "openspiel_ismcts":
        if importlib.metadata.version("open_spiel") != raw["version"]:
            raise ValueError("audited OpenSpiel version required")
        return OpenSpielBaseline(
            rules,
            simulations=raw["simulations"],
            world_samples=raw["world_samples"],
            uct_c=raw["uct_c"],
        )
    parameters = {
        key: raw[key]
        for key in ("equity_samples", "equity_seed", "raise_equity", "call_margin")
        if key in raw
    }
    return Baseline(cast(Kind, raw["kind"]), rules, **parameters)


def own_rows(root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    training = json.loads((root / config["training_report"]).read_text())
    if training["status"] != "completed":
        raise ValueError("own training prerequisite failed")
    selected = [
        r
        for r in training["rows"]
        if r["model"] == config["primary_model"]
        and r["method"] == config["method"]
        and r["iteration"] == config["iteration"]
        and r["seed"] in config["agent_seeds"]
    ]
    if len(selected) != len(config["agent_seeds"]) or {
        r["seed"] for r in selected
    } != set(config["agent_seeds"]):
        raise ValueError("frozen own agent set incomplete or duplicated")
    model = root / config["primary_model"]
    if (
        hashlib.sha256(model.read_bytes()).hexdigest()
        != training["model_sha256"][config["primary_model"]]
    ):
        raise ValueError("frozen own model changed")
    for row in selected:
        if (
            hashlib.sha256(Path(row["checkpoint"]).read_bytes()).hexdigest()
            != row["checkpoint_sha256"]
        ):
            raise ValueError("frozen own checkpoint changed; regenerate own self-play")
    return sorted(selected, key=lambda r: config["agent_seeds"].index(r["seed"]))


def worker(task: dict[str, Any]) -> dict[str, Any]:
    config, raw = task["config"], task["opponent"]
    root = Path(task["root"])
    rules = betting_rules(config)
    started = time.perf_counter()
    own = []
    shared_model = None
    for row in task["own_rows"]:
        if (
            hashlib.sha256(Path(row["checkpoint"]).read_bytes()).hexdigest()
            != row["checkpoint_sha256"]
        ):
            raise ValueError("own checkpoint changed before worker load")
        agent = OwnNoLimitAgent.load(
            Path(row["checkpoint"]), root / config["primary_model"]
        )
        if agent.rules != rules:
            raise ValueError("frozen agent betting rules differ from benchmark")
        if shared_model is None:
            shared_model = agent.model
        agent.model = shared_model
        own.append((row["seed"], FrozenOwnBot(agent)))
    opponent = opponent_bot(raw, rules)
    deals = config[task["mode"] + "_deals"]
    deal_seed = config[task["mode"] + "_deal_seed"]
    profits = np.empty((deals, len(own), 2), dtype=np.float64)
    rows = []
    failure = None
    completed_deals = 0
    for deal in range(deals):
        if time.perf_counter() - started > config["max_seconds_per_opponent"]:
            failure = (
                "declared opponent time budget exceeded; no partial-prefix inference"
            )
            break
        deck = Deck.shuffled(Generator(PCG64(SeedSequence([deal_seed, deal]))))
        deck_hash = hashlib.sha256(bytes(deck.cards)).hexdigest()
        for index, (agent_seed, bot) in enumerate(own):
            for seat in (0, 1):
                before = bot.lookups.copy()
                result = play_hand(
                    bot,
                    opponent,
                    rules,
                    deck,
                    seat,
                    action_seed=(
                        config["action_seed"],
                        task["opponent_index"],
                        agent_seed,
                        deal,
                        seat,
                    ),
                    episode_seed=config["mapping_episode_seed"] + deal,
                    max_actions=config["max_actions_per_hand"],
                )
                profits[deal, index, seat] = result.profit
                counts = bot.lookups - before
                rows.append(
                    {
                        "deal": deal,
                        "deck_sha256": deck_hash,
                        "agent_seed": agent_seed,
                        "own_seat": seat,
                        "profit_chips": result.profit,
                        "actions": result.actions,
                        **{
                            f"own_{status}": counts[status]
                            for status in (
                                "matched",
                                "unseen",
                                "unaveraged",
                                "shadow_failure",
                            )
                        },
                    }
                )
        completed_deals += 1
    destination = Path(task["raw_dir"]) / (raw["name"] + "-hands.csv.gz")
    destination.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]) if rows else ["deal"])
    writer.writeheader()
    writer.writerows(rows)
    destination.write_bytes(gzip.compress(buffer.getvalue().encode(), mtime=0))
    lookups = {str(seed): dict(bot.lookups) for seed, bot in own}
    projected = sum(bot.projected_decisions for _, bot in own)
    if projected or any(bot.lookups["shadow_failure"] for _, bot in own):
        raise ArithmeticError("matched-grid benchmark changed action/public ledger")
    result_report: dict[str, Any] = {
        "opponent": raw["name"],
        "mode": task["mode"],
        "status": "aborted" if failure else "completed",
        "failure": failure,
        "completed_deals": completed_deals,
        "hands": len(rows),
        "seconds": time.perf_counter() - started,
        "raw_file": str(destination),
        "raw_sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        "lookup_counts_by_seed": lookups,
        "projected_decisions": projected,
        "primary_inference": None,
        "per_seed": [],
    }
    if failure is not None:
        return result_report
    parameters = {
        "big_blind": rules.big_blind,
        "maximum_loss": max(rules.stacks),
        "alpha": config["inference"]["alpha"],
        "family_size": config["inference"]["family_size"],
    }
    result_report["primary_inference"] = summarize_pairs(
        profits.mean(axis=1), **parameters
    )
    for index, (seed, _) in enumerate(own):
        stats = summarize_pairs(profits[:, index, :], **parameters)
        result_report["per_seed"].append(
            {
                "seed": seed,
                **{
                    key: stats[key]
                    for key in (
                        "mbb_per_hand",
                        "mean_chips_per_hand",
                        "cluster_se_mbb_per_hand",
                        "clt_interval_mbb_per_hand",
                        "paired_to_unpaired_variance_ratio",
                    )
                },
            }
        )
    return result_report
