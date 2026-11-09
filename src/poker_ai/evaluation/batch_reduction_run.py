"""Source-gated reduction correctness/cost prefixes and learner-free replay."""

import json
import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import batch_reduction_inputs as inputs
from poker_ai.evaluation.batch_cost_profile import original_prefixes
from poker_ai.evaluation.batch_reduction_measure import measure
from poker_ai.evaluation.batch_reduction_validation import gather, grid
from poker_ai.postflop import pipeline_cost
from poker_ai.postflop.cell_process import Send, run_batch
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment


def job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    deadline = Deadline(payload["remaining_seconds"])
    contexts = pipeline_cost.contexts(Path(payload["root"]), payload["comparison"])
    return measure_paths(indices, payload, send, contexts, deadline)


def measure_paths(
    indices: list[int],
    payload: dict[str, Any],
    send: Send,
    contexts: dict[Any, Any],
    deadline: Deadline,
) -> dict[str, Any]:
    for i in indices:
        peer = payload["peers"][i]
        tree = contexts[
            peer["path"]["spot_file"], peer["path"]["representation"]
        ].partition
        for repeat in range(payload["repeats"]):
            deadline.check()
            send(
                dict(
                    kind="prepared", phase="prefix_started", index=i, repetition=repeat
                )
            )
            row = measure(tree, peer["path"], original_prefixes(peer), repeat, deadline)
            if any(not same(row[k], peer[k]) for k in inputs.IDENTITY):
                raise ArithmeticError("new prefix differs from archived state/work")
            send(dict(kind="cell", index=i, row=row))
    return dict(paths=len(indices), rows=len(indices) * payload["repeats"])


def fresh(path: Path) -> None:
    if path.exists() or path.with_suffix(".tmp").exists():
        raise FileExistsError("retain reduction attempt")


def run(root: Path, output: Path, kind: str) -> dict[str, Any]:
    if kind not in ("correctness", "profile"):
        raise ValueError("unknown reduction stage")
    fresh(output)
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    config = inputs.config_inputs(root)
    current, binding = inputs.binding(root)
    checked = inputs.require_checks(root)
    env = runtime_environment()
    base = json.loads((root / "configs/frozen-pass-batches.json").read_text())
    if any(env[k] != base["prefix_runtime"][k] for k in ("python", "numpy")):
        raise ArithmeticError("reduction prefixes require original runtime")
    correctness_hash = None
    if kind == "profile":
        previous = replay(root, root / inputs.CORRECTNESS)
        if previous["kind"] != "correctness":
            raise ArithmeticError("complete correctness must precede timing")
        correctness_hash = digest(root / inputs.CORRECTNESS)
    repeats = 1 if kind == "correctness" else 3
    deadline = Deadline(900)
    deadline.started = started
    saved: dict[str, Any] = dict(
        format=inputs.FORMAT,
        scope=config["status"],
        status="running",
        failure=None,
        kind=kind,
        repeats=repeats,
        config=config,
        source=current,
        source_sha256=binding,
        code_checks=checked,
        environment=env,
        correctness_sha256=correctness_hash,
        batch={},
        rows=[],
        forecast=None,
        seconds=0.0,
        prefix_training_requested=True,
        short_prefix_training_attempted=False,
        completed_endpoints=0,
        long_learning_performed=False,
        strength_scores_measured=False,
        reference_constructed=False,
        new_policy_archive=False,
    )
    persist(output, saved)
    try:
        original, peers = inputs.prerequisites(root)
        comparison = json.loads((root / "configs/training-isolation.json").read_text())[
            "future_comparison"
        ]
        run_batch(
            72,
            3,
            job,
            dict(
                root=str(root),
                comparison=comparison,
                peers=peers,
                repeats=repeats,
                remaining_seconds=900 - (time.perf_counter() - started),
            ),
            deadline,
            saved["batch"],
        )
        saved["rows"] = gather(saved["batch"], peers, repeats, original["config"])
        saved["forecast"] = grid(saved["rows"], peers, repeats, original["config"])
        deadline.check()
        saved["status"] = "completed_" + kind + "_not_strength"
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        workers = saved["batch"].get("workers", [])
        saved["short_prefix_training_attempted"] = any(
            e.get("phase") == "prefix_started" for w in workers for e in w["messages"]
        )
        saved["completed_endpoints"] = sum(
            e["kind"] == "cell" for w in workers for e in w["messages"]
        )
        saved["seconds"] = time.perf_counter() - started
        saved["parent_cpu_seconds"] = time.process_time() - cpu
        now = os.times()
        saved["reaped_children_cpu_seconds"] = (
            now.children_user
            + now.children_system
            - children.children_user
            - children.children_system
        )
        persist(output, saved)
    return saved


def replay(root: Path, path: Path) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads(path.read_text())
    config = inputs.config_inputs(root)
    check_source(root, saved["source"])
    kind = saved["kind"]
    repeats = 1 if kind == "correctness" else 3
    if (
        kind not in ("correctness", "profile")
        or saved["format"] != inputs.FORMAT
        or saved["scope"] != config["status"]
        or saved["status"] != "completed_" + kind + "_not_strength"
        or saved["failure"] is not None
        or not same(saved["config"], config)
        or not same(saved["repeats"], repeats)
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or not number(saved["seconds"], nonnegative=True)
        or saved["seconds"] >= 900
        or saved["prefix_training_requested"] is not True
        or saved["short_prefix_training_attempted"] is not True
        or not same(saved["completed_endpoints"], 72 * repeats)
        or any(
            saved[k] is not False
            for k in (
                "long_learning_performed",
                "strength_scores_measured",
                "reference_constructed",
                "new_policy_archive",
            )
        )
    ):
        raise ArithmeticError("incomplete reduction receipt")
    checked = inputs.require_checks(root, clean=False)
    if (
        not same(saved["code_checks"], checked)
        or saved["source_sha256"] != checked["source_sha256"]
    ):
        raise ArithmeticError("reduction checked source mismatch")
    original, peers = inputs.prerequisites(root)
    rows = gather(saved["batch"], peers, repeats, original["config"])
    result = grid(rows, peers, repeats, original["config"])
    if not same(rows, saved["rows"]) or not same(result, saved["forecast"]):
        raise ArithmeticError("reduction raw rows/forecast changed")
    if kind == "profile":
        if (
            saved["correctness_sha256"] != digest(root / inputs.CORRECTNESS)
            or replay(root, root / inputs.CORRECTNESS)["kind"] != "correctness"
        ):
            raise ArithmeticError("reduction correctness binding changed")
    elif saved["correctness_sha256"] is not None:
        raise ArithmeticError("correctness cannot bind later evidence")
    return saved
