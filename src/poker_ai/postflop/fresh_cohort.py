"""Prospective structural case selection and fail-closed development admission."""

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.cards import format_card, parse_card
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.river_artifacts import IDENTITY, checked_artifacts
from poker_ai.postflop.river_report import checked_audit
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.toy.analysis import evaluate

LIMITS = {
    "full_tree_exploitability_pot_limit": 0.001,
    "sampled_median_exploitability_pot_limit": 0.01,
    "sampled_max_exploitability_pot_limit": 0.025,
    "minimum_uniform_reach_average_row_coverage": 0.95,
    "independent_tolerance_chips": 1e-9,
}
ENTRYPOINTS = (
    "scripts/prepare_fresh_validation.py",
    "scripts/validate_fresh_games.py",
    "scripts/audit_fresh_games.py",
    "scripts/report_fresh_games.py",
)


def validate_config(config: dict[str, Any]) -> None:
    if (
        config["schema_version"] != 1
        or config["candidate"] != "external"
        or config["encoding"] != "exact"
        or config["sampling_weighting"] != "linear"
        or config["initial_exact_expectation"] is not True
        or any(config[k] != v for k, v in LIMITS.items())
    ):
        raise ValueError("unsupported frozen fresh-validation procedure/limits")
    for key in ("training_seeds", "total_node_thresholds", "full_tree_checkpoints"):
        values = config[key]
        if (
            not values
            or len(set(values)) != len(values)
            or any(type(v) is not int or v < 1 for v in values)
            or (key != "training_seeds" and values != sorted(values))
        ):
            raise ValueError("invalid fixed seeds/checkpoints")
    if (
        config["maximum_seconds_total"] <= 0
        or not np.isfinite(config["maximum_seconds_total"])
        or config["maximum_tree_nodes"] < 1
        or config["maximum_selection_attempts_per_spot"] < 1
        or not config["strata"]
        or len({s["name"] for s in config["strata"]}) != len(config["strata"])
    ):
        raise ValueError("invalid declared cohort/budget")


def rank_signature(board: list[int]) -> tuple[tuple[int, ...], int]:
    return tuple(sorted(c // 4 + 2 for c in board[:3])), board[3] // 4 + 2


def texture_matches(board: list[int], texture: str) -> bool:
    ranks = [c // 4 + 2 for c in board]
    suits = [c % 4 for c in board[:3]]
    if len(set(ranks)) != 4:
        return False
    if texture == "dry":
        return len(set(suits)) == 3 and all(
            abs(a - b) >= 3 for i, a in enumerate(ranks[:3]) for b in ranks[i + 1 : 3]
        )
    if texture == "wet":
        return len(set(suits)) == 2 and max(ranks[:3]) - min(ranks[:3]) <= 4
    raise ValueError("unknown structural texture")


def source_hashes(root: Path) -> dict[str, str]:
    paths = sorted((root / "src").rglob("*.py")) + [root / p for p in ENTRYPOINTS]
    paths += [root / "uv.lock", root / "pyproject.toml"]
    return {str(p.relative_to(root)): digest(p) for p in paths}


def learning_paths(root: Path) -> list[str]:
    """Dependencies of the actual fixed own learner, shared with development."""
    paths = [
        "cards.py",
        "evaluator.py",
        "finite.py",
        "abstraction/actions.py",
        "training/mccfr.py",
        "training/checkpoint.py",
        "training/holdem.py",
        "training/no_limit.py",
        "postflop/game.py",
        "postflop/tree.py",
        "postflop/matrix.py",
        "postflop/learning.py",
        "postflop/sampling.py",
        "postflop/jit_cfr.py",
        "toy/analysis.py",
        "toy/cfr.py",
    ]
    return ["src/poker_ai/" + p for p in paths] + [
        str(p.relative_to(root))
        for p in sorted((root / "src/poker_ai/engine").glob("*.py"))
    ]


def prepare_cohort(root: Path, config_path: Path) -> dict[str, Any]:
    """Generate once by legality/texture/novelty only. No game tree or solver calls."""
    config: dict[str, Any] = json.loads(config_path.read_text())
    validate_config(config)
    freeze_path = root / config["freeze_file"]
    filenames = [f"configs/fresh-spots/{s['name']}.json" for s in config["strata"]]
    if freeze_path.exists() or any((root / p).exists() for p in filenames):
        raise FileExistsError("retain preregistered cohort; refusing replacement")
    known = sorted(
        p for d in config["known_spot_directories"] for p in (root / d).glob("*.json")
    )
    forbidden = {
        rank_signature([parse_card(c) for c in json.loads(p.read_text())["board"]])
        for p in known
    }
    rng = Generator(PCG64(config["selection_seed"]))
    records, selected = [], []
    for stratum, filename in zip(config["strata"], filenames, strict=True):
        for _attempt in range(1, config["maximum_selection_attempts_per_spot"] + 1):
            board = [int(c) for c in rng.choice(52, 4, replace=False)]
            signature = rank_signature(board)
            if (
                texture_matches(board, stratum["texture"])
                and signature not in forbidden
            ):
                forbidden.add(signature)
                break
        else:
            raise ValueError("declared structural-selection attempt cap exceeded")
        available = np.array([c for c in range(52) if c not in board])
        holes = [int(c) for c in rng.choice(available, 8, replace=False)]
        weights = [int(w) for w in rng.integers(1, 4, size=4)]
        raw = json.loads((root / stratum["template"]).read_text())
        raw.update(
            name=stratum["name"],
            board=[format_card(c) for c in board],
            texture=stratum["texture"],
            max_tree_nodes=config["maximum_tree_nodes"],
        )
        desired = raw["button"] if stratum["position"] == "ip" else 1 - raw["button"]
        if stratum["position"] not in ("ip", "oop"):
            raise ValueError("unsupported root position")
        if raw["actor"] != desired:
            raw["prefix_actions"].append({"kind": "check"})
        raw.update(actor=desired, hero=desired)
        raw["ranges"] = [
            [
                {
                    "cards": [
                        format_card(c)
                        for c in holes[4 * seat + 2 * i : 4 * seat + 2 * i + 2]
                    ],
                    "weight": weights[2 * seat + i],
                }
                for i in range(2)
            ]
            for seat in range(2)
        ]
        selected.append((filename, raw))
        records.append(
            {
                "spot_file": filename,
                "selection_attempts": _attempt,
                "template": stratum["template"],
                "position": stratum["position"],
                "board_rank_signature": signature,
            }
        )
    # Complete structural selection before any output is written.
    for filename, raw in selected:
        path = root / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(raw, indent=2, sort_keys=True) + "\n")
        load_spot(path)  # Strict legal-prefix/card checks only; no values/training.
    freeze = {
        "format": "poker-ai-fresh-freeze-v1",
        "config_sha256": digest(config_path),
        "source_sha256": source_hashes(root),
        "development_sha256": {
            config[k]: digest(root / config[k])
            for k in ("development_report", "development_audit", "development_policy")
        },
        "known_spot_sha256": {str(p.relative_to(root)): digest(p) for p in known},
        "template_sha256": {
            s["template"]: digest(root / s["template"]) for s in config["strata"]
        },
        "spot_sha256": {p: digest(root / p) for p in filenames},
        "selection": records,
    }
    freeze_path.write_text(json.dumps(freeze, indent=2, sort_keys=True) + "\n")
    return freeze


def verify_freeze(
    root: Path, config_path: Path
) -> tuple[dict[str, Any], dict[str, Any]]:
    config: dict[str, Any] = json.loads(config_path.read_text())
    validate_config(config)
    freeze: dict[str, Any] = json.loads((root / config["freeze_file"]).read_text())
    expected = {f"configs/fresh-spots/{s['name']}.json" for s in config["strata"]}
    if (
        freeze["format"] != "poker-ai-fresh-freeze-v1"
        or freeze["config_sha256"] != digest(config_path)
        or freeze["source_sha256"] != source_hashes(root)
        or set(freeze["spot_sha256"]) != expected
    ):
        raise ArithmeticError("frozen protocol/source/cohort mismatch")
    for field in (
        "development_sha256",
        "known_spot_sha256",
        "template_sha256",
        "spot_sha256",
    ):
        if any(digest(root / p) != h for p, h in freeze[field].items()):
            raise ArithmeticError("frozen input hash mismatch")
    return config, freeze


def require_published_freeze(root: Path, config: dict[str, Any]) -> None:
    """A resealed or untracked manifest cannot admit reserved work."""
    result = subprocess.run(
        ["git", "show", "HEAD:" + config["freeze_file"]],
        cwd=root,
        capture_output=True,
        check=False,
    )
    if (
        result.returncode != 0
        or result.stdout != (root / config["freeze_file"]).read_bytes()
    ):
        raise ArithmeticError(
            "cohort freeze must be committed unchanged before admission"
        )


def development_gate(root: Path, config_path: Path) -> dict[str, Any]:
    """Read-only admission. Verify before constructing any fresh game tree."""
    config, freeze = verify_freeze(root, config_path)
    require_published_freeze(root, config)
    path = root / config["development_report"]
    report, snapshots = checked_artifacts(path)
    checked_audit(path, root / config["development_audit"], report)
    for k in (
        "encoding",
        "sampling_weighting",
        "initial_exact_expectation",
        "total_node_thresholds",
        "full_tree_backend",
        "full_tree_checkpoints",
        "maximum_tree_nodes",
        *LIMITS,
    ):
        if config[k] != report["config"][k]:
            raise ArithmeticError("procedure differs from accepted development control")
    if set(config["training_seeds"]) & (
        set(report["config"]["training_seeds"])
        | set(report["config"]["frozen_panel"]["seeds"])
    ):
        raise ArithmeticError("fresh training seeds overlap recorded development seeds")
    for p in learning_paths(root):
        if digest(root / p) != report["source"]["sha256"][p]:
            raise ArithmeticError(
                "learning implementation differs from development evidence"
            )
    checks = [
        r for r in report["acceptance"]["checks"] if r["variant"] == config["candidate"]
    ]
    if len(checks) != len(report["config"]["spot_files"]) or not all(
        r["passed"] for r in checks
    ):
        raise ArithmeticError("selected procedure fails archived development gate")
    maximum = 0.0
    count = 0
    for filename, sha in report["spot_sha256"].items():
        if digest(root / filename) != sha:
            raise ArithmeticError("development spot changed")
        tree = MatrixTree.build(SpotTree.build(load_spot(root / filename)))
        for snapshot in snapshots:
            if snapshot["spot_file"] != filename or not (
                (
                    snapshot["method"] == config["candidate"]
                    and snapshot["node_threshold"]
                    == config["total_node_thresholds"][-1]
                )
                or (
                    snapshot["method"] == "full_cfr_plus"
                    and snapshot["iteration"] == config["full_tree_checkpoints"][-1]
                )
            ):
                continue
            row = next(
                r for r in report["rows"] if all(r[k] == snapshot[k] for k in IDENTITY)
            )
            metrics = evaluate(
                tree, tree.dense_exact(tuple(tuple(p) for p in snapshot["policy"]))
            )
            maximum = max(
                maximum,
                abs(metrics.exploitability - row["exploitability_chips"]),
                abs(metrics.value_player_zero - row["value_player_zero_chips"]),
            )
            count += 1
    if maximum > config["independent_tolerance_chips"] or count != len(checks) * (
        len(report["config"]["training_seeds"]) + 1
    ):
        raise ArithmeticError("development replay incomplete/outside tolerance")
    return {
        "status": "passed",
        "selected_method": config["candidate"],
        "development_checks": checks,
        "replayed_final_policies": count,
        "maximum_replay_error_chips": maximum,
        "freeze_sha256": digest(root / config["freeze_file"]),
        "config_sha256": digest(config_path),
        "source_fingerprint": hashlib.sha256(
            json.dumps(freeze["source_sha256"], sort_keys=True).encode()
        ).hexdigest(),
    }
