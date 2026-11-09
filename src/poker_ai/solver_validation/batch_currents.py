"""Comparison-only scalar audit of216 saved currents and1728 fixed targets."""

import json
import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import batch_current_inputs as inputs
from poker_ai.evaluation.averaging_history_replay import archive_path
from poker_ai.evaluation.batch_current_cells import policies
from poker_ai.evaluation.batch_current_run import fresh, replay, validate_replay
from poker_ai.evaluation.frozen_batch_validation import full_sources
from poker_ai.postflop.cell_process import Send, partition, run_batch
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.learning_artifacts import decode, read_archive, sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_training import replay_detail
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.averaging_history import compare_fixed, fixed_error
from poker_ai.solver_validation.controlled_pipeline import (
    compare_one,
    license_record,
    references,
)
from poker_ai.solver_validation.frozen_batches import error as self_error

FORMAT = inputs.FORMAT + "-native"


def job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    deadline = Deadline(payload["remaining_seconds"])
    root = Path(payload["root"])
    sources = inputs.load(root)
    send(dict(kind="prepared", phase="reference_setup_started"))
    refs = references(sources.data.base.contexts)
    send(dict(kind="prepared", phase="reference_setup_completed"))
    opponents = {p.identifier: p for p in full_sources(sources.data)}
    own = payload["own"]
    path = Path(payload["own_path"])
    matches: dict[str, list[dict[str, Any]]] = {}
    for row in own["fixed_matches"]:
        matches.setdefault(row["own_snapshot_id"], []).append(row)
    cache: dict[Any, Any] = {}
    self_count = fixed_count = 0
    maximum = 0.0
    for kind in ("current", "average"):
        stream = (
            read_archive(
                archive_path(path, own["details_file"]),
                own["details_sha256"],
                own["rows"],
            )
            if kind == "current"
            else policies(sources, "average")
        )
        for row, blob in stream:
            deadline.check()
            if row["path_index"] not in indices:
                continue
            if kind == "average" and (
                row["path_index"] >= 72
                or row["work_label"] != sources.own["config"]["work_labels"][-1]
            ):
                continue
            context = sources.data.base.context(row["case"])
            key = row["case"]["spot_file"], row["case"]["representation"]
            if kind == "current":
                _, detail = replay_detail(context, row, blob, 1e-9)
                result = dict(
                    id=row["id"],
                    path_index=row["path_index"],
                    work_label=row["work_label"],
                    policy_sha256=row["receipt"]["policy_sha256"],
                    own_reply_sha256=row["reply_sha256"],
                    **compare_one(context, refs[key], detail),
                )
                delta = self_error(result, row)
                if delta > 1e-9:
                    raise ArithmeticError("independent current scalar audit failed")
                send(
                    dict(
                        kind="cell",
                        phase="self",
                        index=row["path_index"],
                        result=result,
                    )
                )
                self_count += 1
                maximum = max(maximum, delta)
            else:
                detail = decode(blob, context, row)
            policy = unpack_policy(context.partition, detail["policy"])
            for peer in matches.get(row["id"], []):
                result = compare_fixed(
                    sources.data, peer, policy, opponents, refs[key][1], cache
                )
                delta = fixed_error(result, peer)
                if delta > 1e-9:
                    raise ArithmeticError("independent fixed scalar audit failed")
                send(
                    dict(
                        kind="cell",
                        phase="fixed",
                        index=row["path_index"],
                        result=result,
                    )
                )
                fixed_count += 1
                maximum = max(maximum, delta)
    return dict(
        paths=len(indices),
        current_profiles=self_count,
        fixed_targets=fixed_count,
        cached_opponent_targets=len(cache),
        maximum_error_chips=maximum,
    )


def validate(
    saved: dict[str, Any], own: dict[str, Any], own_path: Path
) -> dict[str, Any]:
    batch = saved["batch"]
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["own_sha256"] != digest(own_path)
        or saved["details_sha256"] != own["details_sha256"]
        or saved["training_performed"] is not False
        or saved["reference_actions_exported"] is not False
        or saved["reference_setup_started"] is not True
        or not same(saved["reference_setup_completed_workers"], 3)
        or not number(saved["seconds"], nonnegative=True)
        or saved["seconds"] >= 900
        or not same(saved["reference"], own["reference"])
        or saved["license"]["sha256"] != own["reference"]["license_sha256"]
        or not saved["license"]["installed_license_files"]
        or batch["status"] != "completed"
        or batch["failure"] is not None
        or not same(batch["assignments"], partition(72, 3))
        or len(batch["workers"]) != 3
    ):
        raise ArithmeticError("incomplete current native receipt")
    validate_replay(saved["own_replay"])
    by_id = {r["id"]: r for r in own["rows"]}
    fixed = {
        (r["own_snapshot_id"], r["opponent_profile_id"], r["target"]): r
        for r in own["fixed_matches"]
    }
    seen = []
    seen_fixed = []
    maximum = 0.0
    cached = 0
    for slot, (worker, assigned) in enumerate(
        zip(batch["workers"], batch["assignments"], strict=True)
    ):
        if not same(worker["slot"], slot) or not same(worker["exitcode"], 0):
            raise ArithmeticError("current native worker failed")
        a = b = 0
        local = 0.0
        setup = [e["phase"] for e in worker["messages"] if e["kind"] == "prepared"]
        if setup != ["reference_setup_started", "reference_setup_completed"]:
            raise ArithmeticError("native reference setup inventory changed")
        for e in worker["messages"]:
            if e["kind"] != "cell":
                continue
            if type(e["index"]) is not int or e["index"] not in assigned:
                raise ArithmeticError("current native source assignment changed")
            row = e["result"]
            if e["phase"] == "self":
                peer = by_id[row["id"]]
                if not same(e["index"], peer["path_index"]):
                    raise ArithmeticError("current native self path changed")
                delta = self_error(row, peer)
                seen.append(row["id"])
                a += 1
            elif e["phase"] == "fixed":
                key = row["own_snapshot_id"], row["opponent_profile_id"], row["target"]
                peer = fixed[key]
                if not same(e["index"], peer["path_index"]):
                    raise ArithmeticError("current native fixed path changed")
                delta = fixed_error(row, peer)
                seen_fixed.append(key)
                b += 1
            else:
                raise ArithmeticError("unknown current native row")
            local = max(local, delta)
        done = [e for e in worker["messages"] if e["kind"] == "done"]
        if (
            a != 72
            or b != 576
            or len(done) != 1
            or not same(
                done[0]["summary"],
                dict(
                    paths=24,
                    current_profiles=72,
                    fixed_targets=576,
                    cached_opponent_targets=32,
                    maximum_error_chips=local,
                ),
            )
            or local > 1e-9
        ):
            raise ArithmeticError("current native completion counts/error changed")
        maximum = max(maximum, local)
        cached += 32
    if (
        len(seen) != 216
        or len(set(seen)) != 216
        or set(seen) != set(by_id)
        or len(seen_fixed) != 1728
        or len(set(seen_fixed)) != 1728
        or set(seen_fixed) != set(fixed)
    ):
        raise ArithmeticError("current native grid missing or duplicate")
    if (
        not number(batch["seconds"], nonnegative=True)
        or saved["own_replay"]["seconds"] + batch["seconds"] > saved["seconds"] + 1e-9
    ):
        raise ArithmeticError("current native elapsed accounting changed")
    return dict(
        status="all216currents_and1728fixed_targets_independently_audited",
        current_profiles=216,
        fixed_targets=1728,
        unique_opponent_targets=32,
        worker_cached_root_evaluations=cached,
        maximum_error_chips=maximum,
        seconds=saved["seconds"],
        reference_strategies_used_in_training=False,
    )


def record_setup(saved: dict[str, Any]) -> None:
    messages = [e for w in saved["batch"].get("workers", []) for e in w["messages"]]
    saved["reference_setup_started"] = any(
        e.get("phase") == "reference_setup_started" for e in messages
    )
    saved["reference_setup_completed_workers"] = sum(
        e.get("phase") == "reference_setup_completed" for e in messages
    )


def run(root: Path, own_path: Path, output: Path) -> dict[str, Any]:
    fresh(output)
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    current, binding = inputs.binding(root)
    deadline = Deadline(900)
    deadline.started = started
    saved: dict[str, Any] = dict(
        format=FORMAT,
        status="running",
        failure=None,
        source=current,
        source_sha256=binding,
        environment=runtime_environment(),
        own_sha256=digest(own_path),
        details_sha256=None,
        reference=None,
        license=None,
        own_replay=None,
        batch={},
        seconds=0.0,
        training_performed=False,
        reference_actions_exported=False,
        reference_setup_started=False,
        reference_setup_completed_workers=0,
    )
    persist(output, saved)
    try:
        own, sources, proof = replay(root, own_path, deadline)
        saved["details_sha256"] = own["details_sha256"]
        saved["reference"] = own["reference"]
        saved["own_replay"] = proof
        saved["license"] = license_record(dict(native_reference=own["reference"]))
        run_batch(
            72,
            3,
            job,
            dict(
                root=str(root),
                own=own,
                own_path=str(own_path),
                remaining_seconds=900 - (time.perf_counter() - started),
            ),
            deadline,
            saved["batch"],
        )
        deadline.check()
        saved["status"] = "completed"
        record_setup(saved)
        saved["seconds"] = time.perf_counter() - started
        validate(saved, own, own_path)
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        record_setup(saved)
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


def read(root: Path, path: Path, own: dict[str, Any], own_path: Path) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads(path.read_text())
    check_source(root, saved["source"])
    return validate(saved, own, own_path)
