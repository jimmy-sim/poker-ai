"""Exact software sentinels and pinned historical work audit; no Hold'em training."""

import json
import math
import time
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.controlled_training import ArrayState, expected_pass
from poker_ai.postflop.range_protocol import CONTROLS
from poker_ai.postflop.river_study import digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.toy.tree import Tree
from poker_ai.training.mccfr import Updates, external_updates
from poker_ai.validation.five_card import source_provenance

FORMAT = "poker-ai-training-isolation-correctness-v1"
CONFIG = "configs/training-isolation.json"
ENTRYPOINT = "scripts/check_training_isolation.py"
FULL = "results/range-mass-admission/study.json"
SAMPLED = "results/range-mass-sampled/study.json"
SPOTS = [
    "configs/learning-spots/dev_low_oop.json",
    "configs/learning-spots/dev_medium_oop.json",
]
INPUTS = {
    "configs/range-mass-policy-swaps.json",
    "results/policy-swaps/study.json",
    "results/policy-swaps/study-profiles.json.gz",
    "results/policy-swaps/independent.json",
    "configs/range-mass-protocol.json",
    FULL,
    SAMPLED,
    "results/card-models/potential-8.json",
    *SPOTS,
}


def validate_config(config: dict[str, Any]) -> None:
    """Only the fixed correctness milestone; learning is separately preregistered."""
    later = config["future_comparison"]
    if (
        type(config["schema_version"]) is not int
        or config["schema_version"] != 1
        or config["status"] != "correctness_only_not_learning_results"
        or set(config["input_sha256"]) != INPUTS
        or any(
            not isinstance(s, str)
            or len(s) != 64
            or any(c not in "0123456789abcdef" for c in s)
            for s in config["input_sha256"].values()
        )
        or later["status"] != "preregistered_not_run"
        or later["representations"] != ["exact", "texture_range_q8_b8"]
        or later["spot_files"] != SPOTS
        or later["seeds"] != [20261301, 20261302, 20261303]
        or any(type(s) is not int for s in later["seeds"])
        or later["traversal"] != ["full", "external"]
        or later["regret_rule"] != ["signed", "clipped"]
        or later["regret_weight"] != ["uniform", "linear"]
        or later["average_weight"] != ["uniform", "linear"]
        or later["common_averaging_phase"] != "opponent_pass"
        or later["common_averaging_mass"] != "chance_own_reach"
        or later["node_work_checkpoints"] != [100000, 1000000, 10000000]
        or later["iteration_checkpoints"] != [16, 64, 128]
        or any(
            type(t) is not int
            for t in later["node_work_checkpoints"] + later["iteration_checkpoints"]
        )
        or type(later["maximum_own_seconds"]) is not int
        or later["maximum_own_seconds"] != 7200
        or later["full_only_bridge"]
        != [
            "cold_target_history_mass",
            "warm_target_history_mass",
            "warm_target_chance_mass",
            "warm_opponent_chance_mass",
        ]
        or later["bridge_rules"]
        != {
            "regret_rule": "clipped",
            "regret_weight": "uniform",
            "average_weight": "linear",
        }
        or config["sentinel"]
        != {
            "game": "kuhn_nonuniform_chance_software_fixture",
            "policies": ["positive", "zero_support"],
            "targets": [0, 1],
            "maximum_selector_paths": 10000,
            "tolerance": 1e-12,
        }
        or type(config["sentinel"]["maximum_selector_paths"]) is not int
    ):
        raise ValueError("invalid training-isolation correctness protocol")


def check_inputs(root: Path, config: dict[str, Any]) -> None:
    validate_config(config)
    if any(digest(root / name) != sha for name, sha in config["input_sha256"].items()):
        raise ArithmeticError("training-isolation prerequisite changed")


def sentinel_tree() -> ArrayTree:
    """Explicit software fixture: Kuhn rules, nonuniform first-card chance.

    This is not standard fair-deck Kuhn and has no game-value strength claim.
    Keeping the legal information partition exercises shared histories.
    """
    tree = Tree.build("kuhn")
    chance = tree.chance_edges.copy()
    chance[0, :3] = [0.1, 0.3, 0.6]
    reach = np.ones(len(tree.player))
    for node in range(len(tree.player)):
        for column in range(int(tree.valid[node].sum())):
            child = tree.children[node, column]
            reach[child] = reach[node] * (
                chance[node, column] if tree.player[node] == -1 else 1.0
            )
    return replace(tree, chance_edges=chance, chance_reach=reach)


def sentinel_policy(tree: ArrayTree, name: str) -> FloatArray:
    weights = tree.legal.copy()
    if name == "positive":
        for i in range(len(tree.keys)):
            weights[i, 0] = 2 + i % 3
            weights[i, 1] = 5 - i % 2
    elif name == "zero_support":
        weights[:, 1:] = 0
    else:
        raise ValueError("unknown software policy")
    return tree.normalize(weights)


class NextChoice(Exception):
    def __init__(self, probabilities: FloatArray) -> None:
        self.probabilities = probabilities.copy()


def enumerate_pass(
    tree: ArrayTree, policy: FloatArray, target: int, *, maximum_paths: int
) -> list[tuple[float, Updates]]:
    """Enumerate the JOINT adaptive selector tape, including independent draws
    in every enumerated own-action subtree. This is not a terminal-path average.
    Zero-probability choices are omitted; the sampler is not changed.
    """
    tree.validate_policy(policy)
    lookup = {key: i for i, key in enumerate(tree.keys)}
    result: list[tuple[float, Updates]] = []

    def frozen(key: str, actions: tuple[int, ...]) -> FloatArray:
        i = lookup[key]
        if actions != tree.actions[i]:
            raise ValueError("sentinel menu mismatch")
        return policy[i, : len(actions)].copy()

    def walk(tape: tuple[int, ...], mass: float) -> None:
        index = 0

        def select(probabilities: FloatArray) -> int:
            nonlocal index
            if (
                not np.all(np.isfinite(probabilities))
                or np.any(probabilities < 0)
                or not np.isclose(probabilities.sum(), 1, atol=1e-12, rtol=0)
            ):
                raise ArithmeticError("invalid selector probabilities")
            if index == len(tape):
                raise NextChoice(probabilities)
            selected = tape[index]
            index += 1
            if probabilities[selected] <= 0:
                raise ArithmeticError("zero-support selector draw")
            return selected

        try:
            update = external_updates(ArrayState(tree), target, frozen, select)
        except NextChoice as choice:
            for selected, probability in enumerate(choice.probabilities):
                if probability > 0:
                    walk(tape + (selected,), mass * float(probability))
        else:
            if len(result) >= maximum_paths:
                raise ValueError("selector enumeration cap exceeded")
            result.append((mass, update))

    walk((), 1.0)
    return result


def dense_updates(tree: ArrayTree, table: dict[str, FloatArray]) -> FloatArray:
    result = np.zeros_like(tree.legal)
    lookup = {key: i for i, key in enumerate(tree.keys)}
    for key, value in table.items():
        i = lookup[key]
        result[i, : len(value)] = value
    return result


def sentinel_checks(config: dict[str, Any]) -> list[dict[str, Any]]:
    tree = sentinel_tree()
    rows = []
    tolerance = config["sentinel"]["tolerance"]
    for name in config["sentinel"]["policies"]:
        policy = sentinel_policy(tree, name)
        for target in config["sentinel"]["targets"]:
            samples = enumerate_pass(
                tree,
                policy,
                target,
                maximum_paths=config["sentinel"]["maximum_selector_paths"],
            )
            full = expected_pass(tree, policy, target)
            regret, average, clipped = (np.zeros_like(tree.legal) for _ in range(3))
            for probability, update in samples:
                delta = dense_updates(tree, update.regrets)
                regret += probability * delta
                average += probability * dense_updates(tree, update.averages)
                clipped += probability * np.maximum(delta, 0)
            full_regret = dense_updates(tree, full.regrets)
            regret_error = float(np.max(np.abs(regret - full_regret)))
            average_error = float(
                np.max(np.abs(average - dense_updates(tree, full.averages)))
            )
            probability = math.fsum(p for p, _ in samples)
            if max(regret_error, average_error, abs(probability - 1)) > tolerance:
                raise ArithmeticError("frozen-pass expectation sentinel failed")
            rows.append(
                {
                    "policy": name,
                    "target": target,
                    "selector_paths": len(samples),
                    "probability_mass": probability,
                    "maximum_regret_error": regret_error,
                    "maximum_average_error": average_error,
                    "maximum_expected_clip_vs_clip_expected": float(
                        np.max(np.abs(clipped - np.maximum(full_regret, 0)))
                    ),
                    "scope": (
                        "software fixture; frozen-pass increments, "
                        "not training strength"
                    ),
                }
            )
    if not any(r["maximum_expected_clip_vs_clip_expected"] > tolerance for r in rows):
        raise ArithmeticError("sentinel did not exercise clipping nonlinearity")
    return rows


def historical_work(root: Path) -> list[dict[str, Any]]:
    """Audit original endpoints, not new work-matched or causal outcomes."""
    full, sampled = (json.loads((root / path).read_text()) for path in (FULL, SAMPLED))
    controls = full["config"]["representations"]
    seeds = full["config"]["later_sampled"]["seeds"]
    if (
        controls != CONTROLS
        or full["config"]["spot_files"] != SPOTS
        or full["status"] != "completed"
        or sampled["status"] != "completed"
        or full["config"] != sampled["config"]
        or seeds != [20261301, 20261302, 20261303]
    ):
        raise ArithmeticError("historical work selection changed")
    rows = []
    for filename in SPOTS:
        for name in controls:
            anchors = [
                r
                for r in full["rows"]
                if r["spot_file"] == filename
                and r["representation"] == name
                and r["iteration"] == 4096
            ]
            diag = [
                d
                for d in full["diagnostics"]
                if d["spot_file"] == filename and d["representation"] == name
            ]
            if len(anchors) != 1 or len(diag) != 1:
                raise ArithmeticError("missing/duplicate historical full endpoint")
            anchor = anchors[0]
            nodes = diag[0]["tree_nodes"]
            if type(nodes) is not int or anchor["total_node_work"] != 2 * nodes * 4096:
                raise ArithmeticError("historical full work mismatch")
            for seed in seeds:
                cells = [
                    r
                    for r in sampled["rows"]
                    if r["spot_file"] == filename
                    and r["representation"] == name
                    and r["seed"] == seed
                    and r["node_work_checkpoint"] == 10000000
                ]
                if len(cells) != 1:
                    raise ArithmeticError(
                        "missing/duplicate historical sampled endpoint"
                    )
                cell = cells[0]
                total, previous, last = (
                    cell[k]
                    for k in (
                        "total_node_work",
                        "previous_node_work",
                        "last_iteration_node_work",
                    )
                )
                if (
                    any(
                        type(cell[k]) is not int
                        for k in [
                            "total_node_work",
                            "previous_node_work",
                            "last_iteration_node_work",
                            "iteration",
                            "initialization_node_work",
                            "recursive_node_visits",
                            "overshoot",
                        ]
                    )
                    or cell["iteration"] <= 1
                    or cell["initialization_node_work"] != 2 * nodes
                    or total
                    != cell["initialization_node_work"] + cell["recursive_node_visits"]
                    or not previous < 10000000 <= total
                    or total != previous + last
                    or not 0 <= total - 10000000 < last <= 2 * nodes
                    or cell["overshoot"] != total - 10000000
                ):
                    raise ArithmeticError("historical sampled work mismatch")
                rows.append(
                    {
                        "spot_file": filename,
                        "representation": name,
                        "seed": seed,
                        "tree_nodes": nodes,
                        "full_iterations": 4096,
                        "sampled_iterations": cell["iteration"],
                        "full_node_work": anchor["total_node_work"],
                        "sampled_node_work": total,
                        "sampled_overshoot": cell["overshoot"],
                        "full_over_sampled_work": anchor["total_node_work"] / total,
                    }
                )
    if len(rows) != 30:
        raise ArithmeticError("historical work grid incomplete")
    return rows


def evidence(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    check_inputs(root, config)
    return {
        "format": FORMAT,
        "status": "passed_correctness_only",
        "config": config,
        "sentinels": sentinel_checks(config),
        "historical_work": historical_work(root),
        "new_postflop_training": False,
        "causal_strength_result": False,
        "fresh_global_admission": False,
    }


def run(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    if config_path.resolve() != (root / CONFIG).resolve():
        raise ValueError("use the fixed correctness config")
    if output.exists():
        raise FileExistsError("retain previous correctness receipt")
    started = time.perf_counter()
    source = source_provenance(root, config_path, entrypoints=(ENTRYPOINT,))
    if source["dirty"] is not False:
        raise ValueError("publish checked correctness code first")
    result = evidence(root, json.loads(config_path.read_text()))
    result.update(
        source=source,
        environment=runtime_environment(),
        started_at_utc=datetime.now(UTC).isoformat(),
        seconds=time.perf_counter() - started,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    )
    return result


def replay(root: Path, path: Path) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads(path.read_text())
    json.dumps(saved, allow_nan=False)
    source = saved["source"]
    required = {str(p.relative_to(root)) for p in (root / "src").rglob("*.py")} | {
        CONFIG,
        ENTRYPOINT,
        "pyproject.toml",
        "uv.lock",
    }
    if (
        source["dirty"] is not False
        or not source["git_commit"]
        or set(source["sha256"]) != required
        or type(saved["seconds"]) not in (int, float)
        or not math.isfinite(saved["seconds"])
        or saved["seconds"] < 0
    ):
        raise ArithmeticError("invalid correctness source")
    if any(digest(root / p) != sha for p, sha in source["sha256"].items()):
        raise ArithmeticError("correctness source changed")
    if json.dumps(saved["config"], sort_keys=True) != json.dumps(
        json.loads((root / CONFIG).read_text()), sort_keys=True
    ):
        raise ArithmeticError("correctness config binding changed")
    actual = evidence(root, saved["config"])
    if set(saved) != set(actual) | {
        "source",
        "environment",
        "started_at_utc",
        "seconds",
    }:
        raise ArithmeticError("correctness receipt fields changed")
    # Sentinel utility uses fixture chips; retain the predeclared 1e-12 bound.
    if json.dumps(saved["historical_work"], sort_keys=True) != json.dumps(
        actual["historical_work"], sort_keys=True
    ) or any(
        json.dumps(saved[k], sort_keys=True) != json.dumps(actual[k], sort_keys=True)
        for k in actual
        if k not in ("sentinels", "historical_work")
    ):
        raise ArithmeticError("correctness grid/claim changed")
    rows = saved["sentinels"]
    if len(rows) != len(actual["sentinels"]):
        raise ArithmeticError("correctness sentinel grid incomplete")
    for a, b in zip(rows, actual["sentinels"], strict=True):
        if set(a) != set(b):
            raise ArithmeticError("sentinel fields changed")
        for key in b:
            if key in (
                "probability_mass",
                "maximum_regret_error",
                "maximum_average_error",
                "maximum_expected_clip_vs_clip_expected",
            ):
                if (
                    type(a[key]) not in (float, int)
                    or not math.isfinite(a[key])
                    or abs(a[key] - b[key]) > 1e-12
                ):
                    raise ArithmeticError("sentinel numerical replay failed")
            elif type(a[key]) is not type(b[key]) or a[key] != b[key]:
                raise ArithmeticError("sentinel identity changed")
    return saved
