"""Preflight or run the bounded, documented anonymous public Slumbot pilot."""

import argparse
import gzip
import hashlib
import json
import math
import platform
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from numpy.random import PCG64, Generator

from poker_ai.agents.no_limit import OwnNoLimitAgent
from poker_ai.cards import Deck, parse_card
from poker_ai.engine import Action, ActionKind, new_hand
from poker_ai.evaluation.experiment import own_rows
from poker_ai.evaluation.slumbot_client import (
    HTTPTransport,
    OwnPublicPolicy,
    pilot_statistics,
    run_pilot,
)
from poker_ai.evaluation.slumbot_protocol import replay_public, verify_result
from poker_ai.validation.five_card import source_provenance


def load_config(path: Path) -> dict[str, Any]:
    raw: dict[str, Any] = json.loads(path.read_text())
    required = {
        "schema_version",
        "purpose",
        "base_url",
        "training_report",
        "model",
        "method",
        "iteration",
        "agent_seed",
        "hands",
        "action_seed",
        "mapping_episode_seed",
        "starting_stacks",
        "small_blind",
        "big_blind",
        "button",
        "minimum_request_interval_seconds",
        "http_timeout_seconds",
        "maximum_elapsed_seconds",
        "maximum_requests",
        "error_cooldown_seconds",
        "abort_ambiguous_post",
        "permission_source",
        "protocol_source",
        "limitations",
    }
    if (
        set(raw) != required
        or type(raw["schema_version"]) is not int
        or raw["schema_version"] != 1
    ):
        raise ValueError("invalid public pilot config")
    if (
        raw["base_url"] != "https://slumbot.com/slumbot/api/"
        or raw["abort_ambiguous_post"] is not True
    ):
        raise ValueError(
            "requires the documented public endpoint and ambiguous-POST abort"
        )
    for key in (
        "iteration",
        "agent_seed",
        "hands",
        "action_seed",
        "mapping_episode_seed",
        "maximum_requests",
    ):
        if type(raw[key]) is not int or raw[key] < (0 if key.endswith("seed") else 1):
            raise ValueError("invalid public pilot count/seed")
    if raw["hands"] > 100 or raw["maximum_requests"] > 1000:
        raise ValueError("this protocol pilot is bounded to 100 hands / 1000 requests")
    for key in (
        "minimum_request_interval_seconds",
        "http_timeout_seconds",
        "maximum_elapsed_seconds",
        "error_cooldown_seconds",
    ):
        if (
            type(raw[key]) not in (int, float)
            or not math.isfinite(raw[key])
            or raw[key] <= 0
        ):
            raise ValueError("invalid public request pacing/time budget")
    if (
        raw["minimum_request_interval_seconds"] < 0.5
        or raw["maximum_elapsed_seconds"] > 1800
    ):
        raise ValueError("pilot requires paced requests and at most 30 minutes")
    if raw["starting_stacks"] != [20000, 20000] or (
        raw["small_blind"],
        raw["big_blind"],
        raw["button"],
    ) != (50, 100, 1):
        raise ValueError(
            "requires the documented public stack/blind/position convention"
        )
    return raw


def frozen_policy(
    root: Path, config: dict[str, Any]
) -> tuple[OwnPublicPolicy, dict[str, Any]]:
    selection = {
        "training_report": config["training_report"],
        "primary_model": config["model"],
        "method": config["method"],
        "iteration": config["iteration"],
        "agent_seeds": [config["agent_seed"]],
    }
    row = own_rows(root, selection)[0]
    agent = OwnNoLimitAgent.load(Path(row["checkpoint"]), root / config["model"])
    if any(
        config["starting_stacks"][seat] * agent.rules.big_blind
        != agent.rules.stacks[seat] * config["big_blind"]
        for seat in (0, 1)
    ):
        raise ValueError("public pilot requires a matching-depth own checkpoint")
    policy = OwnPublicPolicy(agent, (config["small_blind"], config["big_blind"]))
    # Check both positions with own synthetic deals; these are not API requests
    # and do not consume the live action RNG stream or train the policy.
    state = new_hand(
        tuple(config["starting_stacks"]),
        Deck.shuffled(Generator(PCG64(41))),
        button=1,
        small_blind=50,
        big_blind=100,
    )
    for seat in (1, 0):
        if seat == 0:
            state = state.apply(Action(ActionKind.CALL))
        _, details = policy.choose(
            state.observe(seat), rng=Generator(PCG64(42)), episode_seed=43
        )
        if details["starting_stack_mismatch"]:
            raise ValueError("public preflight failed matching-depth normalization")
    return policy, {
        "checkpoint_sha256": row["checkpoint_sha256"],
        "model_sha256": hashlib.sha256(
            (root / config["model"]).read_bytes()
        ).hexdigest(),
        "training_source": json.loads((root / config["training_report"]).read_text())[
            "source"
        ],
    }


def replay_report(path: Path) -> None:
    report = json.loads(path.read_text())
    event_path = path.parent / report["events_file"]
    if hashlib.sha256(event_path.read_bytes()).hexdigest() != report["events_sha256"]:
        raise ArithmeticError("public event archive changed")
    events = json.loads(gzip.decompress(event_path.read_bytes()))
    if not isinstance(events, list):
        raise ValueError("invalid public event archive")
    records = report["records"]
    config = report["config"]
    for row in records:
        state = replay_public(
            row["action"],
            client_seat=row["client_pos"],
            hole=tuple(map(parse_card, row["hole_cards"])),
            board=tuple(map(parse_card, row["board"])),
            stacks=tuple(config["starting_stacks"]),
            small_blind=config["small_blind"],
            big_blind=config["big_blind"],
            button=config["button"],
        )
        verify_result(state, row["winnings"], max(config["starting_stacks"]))
    if len(records) != report["completed_hands"]:
        raise ArithmeticError("public completed-hand count changed")
    if [r["hand"] for r in records] != list(range(len(records))):
        raise ArithmeticError("public settled-hand prefix is duplicated or missing")
    if report["status"] == "completed" and len(records) != config["hands"]:
        raise ArithmeticError("public pilot marked complete before fixed N")
    summary = (
        pilot_statistics(records, config) if report["status"] == "completed" else None
    )
    if summary != report["pilot_summary"]:
        raise ArithmeticError("public recorded statistics changed")
    print(
        f"passed: {len(records)} recorded settlements and their statistics replay; "
        "no live requests"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/slumbot-pilot.json")
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("results/slumbot/public-pilots")
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--live", action="store_true")
    mode.add_argument("--replay-report", type=Path)
    args = parser.parse_args()
    if args.replay_report is not None:
        replay_report(args.replay_report)
        return 0
    config = load_config(args.config)
    root = Path(__file__).resolve().parents[1]
    policy, fingerprints = frozen_policy(root, config)
    if not args.live:
        print(
            f"ready: own matched-depth checkpoint; {config['hands']}-hand "
            "paced anonymous pilot; no gameplay requests sent"
        )
        return 0
    source = source_provenance(
        root, args.config, entrypoints=("scripts/benchmark_slumbot.py",)
    )
    run_id = datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    started = time.perf_counter()
    report = run_pilot(config, HTTPTransport(config), policy, progress=True)
    events = report.pop("events")
    event_path = args.output_dir / f"pilot-{run_id}-events.json.gz"
    event_path.write_bytes(
        gzip.compress(
            json.dumps(events, sort_keys=True, allow_nan=False).encode(), mtime=0
        )
    )
    report.update(
        {
            "schema_version": 1,
            "source": source,
            "own_policy": fingerprints,
            "events_file": event_path.name,
            "events_sha256": hashlib.sha256(event_path.read_bytes()).hexdigest(),
            "environment": {
                "python": platform.python_version(),
                "platform": platform.platform(),
            },
            "total_seconds": time.perf_counter() - started,
        }
    )
    output = args.output_dir / f"pilot-{run_id}.json"
    output.write_text(
        json.dumps(report, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(
        f"{report['status']}: {report['completed_hands']}/{config['hands']} settled; "
        f"report: {output}",
        flush=True,
    )
    if report["failure"] is not None:
        print(
            f"stopped: {report['failure']['type']}: {report['failure']['reason']}",
            flush=True,
        )
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
