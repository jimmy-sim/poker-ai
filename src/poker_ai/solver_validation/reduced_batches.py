"""Comparison-only OpenSpiel scalars for every own frozen-batch profile."""

import json
import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import reduced_study_inputs as inputs
from poker_ai.evaluation.reduced_study_protocol import fresh_output
from poker_ai.evaluation.reduced_study_run import replay, validate_replay
from poker_ai.postflop import pipeline_cost
from poker_ai.postflop.cell_process import Send, partition, run_batch
from poker_ai.postflop.learning_artifacts import read_archive, sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_training import replay_detail
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.controlled_pipeline import (
    compare_one,
    license_record,
    references,
)

FORMAT = "poker-ai-reduced-dispatch-batch-study-native-v1"


def error(result: dict[str, Any], peer: dict[str, Any]) -> float:
    if (
        not same(result["id"], peer["id"])
        or not same(result["path_index"], peer["path_index"])
        or not same(result["work_label"], peer["work_label"])
        or result["policy_sha256"] != peer["receipt"]["policy_sha256"]
        or not same(result["own_reply_sha256"], peer["reply_sha256"])
        or set(result["native_metrics"]) != set(peer["metrics"])
        or len(result["responses"]) != 2
        or not same([r["target"] for r in result["responses"]], [0, 1])
    ):
        raise ArithmeticError("native batch source/profile/reply identity changed")
    errors = []
    for k, v in result["native_metrics"].items():
        if not number(v):
            raise ArithmeticError("nonfinite native batch metric")
        errors.append(abs(v - peer["metrics"][k]))
    names = dict(
        exact_root_chips="exact_reply_value_chips",
        restricted_root_chips="restricted_reply_value_chips",
        achieved_exact_chips="exact_reply_value_chips",
        achieved_restricted_chips="restricted_reply_value_chips",
        achieved_river_before_chips="river_before_value_chips",
    )
    for target, response in enumerate(result["responses"]):
        for actual, expected in names.items():
            if not number(response[actual]):
                raise ArithmeticError("nonfinite native batch root/achieved reply")
            errors.append(abs(response[actual] - peer["responses"][target][expected]))
    maximum = max(errors)
    if not same(maximum, result["maximum_error_chips"]):
        raise ArithmeticError("native batch maximum error changed")
    return float(maximum)


def native_job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    started = time.perf_counter()
    contexts = pipeline_cost.contexts(Path(payload["root"]), payload["comparison"])
    refs = references(contexts)
    deadline = Deadline(payload["remaining_seconds"])
    send(dict(kind="prepared", seconds=time.perf_counter() - started))
    saved = payload["own"]
    path = Path(payload["own_path"])
    count = 0
    maximum = 0.0
    for row, blob in read_archive(
        path.with_name(saved["details_file"]), saved["details_sha256"], saved["rows"]
    ):
        deadline.check()
        if row["path_index"] not in indices:
            continue
        key = row["case"]["spot_file"], row["case"]["representation"]
        _, detail = replay_detail(contexts[key], row, blob, 1e-9)
        result = dict(
            id=row["id"],
            path_index=row["path_index"],
            work_label=row["work_label"],
            policy_sha256=row["receipt"]["policy_sha256"],
            own_reply_sha256=row["reply_sha256"],
            **compare_one(contexts[key], refs[key], detail),
        )
        delta = error(result, row)
        if delta > 1e-9:
            raise ArithmeticError("independent frozen-batch audit failed")
        maximum = max(maximum, delta)
        send(dict(kind="cell", **result))
        count += 1
    return dict(paths=len(indices), profiles=count, maximum_error_chips=maximum)


def validate(
    saved: dict[str, Any], own: dict[str, Any], own_path: Path
) -> dict[str, Any]:
    batch = saved["batch"]
    if (
        saved["format"] != FORMAT
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or saved["own_sha256"] != digest(own_path)
        or saved["details_sha256"] != own["details_sha256"]
        or not same(saved["reference"], own["config"]["native_reference"])
        or saved["license"]["sha256"]
        != own["config"]["native_reference"]["license_sha256"]
        or not saved["license"]["installed_license_files"]
        or saved["reference_actions_exported"] is not False
        or saved["training_performed"] is not False
        or not number(saved["seconds"], nonnegative=True)
        or saved["seconds"] >= 900
        or batch["status"] != "completed"
        or batch["failure"] is not None
        or not same(batch["assignments"], partition(88, 3))
        or len(batch["workers"]) != 3
    ):
        raise ArithmeticError("incomplete/changed native batch receipt")
    validate_replay(saved["own_replay"])
    if (
        not number(batch["seconds"], nonnegative=True)
        or saved["own_replay"]["seconds"] + batch["seconds"] > saved["seconds"]
    ):
        raise ArithmeticError("native replay/batch elapsed accounting changed")
    by_id = {r["id"]: r for r in own["rows"]}
    if len(by_id) != 480:
        raise ArithmeticError("native own profile grid incomplete")
    found = []
    maximum = 0.0
    for slot, (worker, assigned) in enumerate(
        zip(batch["workers"], batch["assignments"], strict=True)
    ):
        if not same(worker["slot"], slot) or not same(worker["exitcode"], 0):
            raise ArithmeticError("native batch worker failed")
        events = [e for e in worker["messages"] if e["kind"] == "cell"]
        local = 0.0
        for event in events:
            peer = by_id[event["id"]]
            if (
                type(event["path_index"]) is not int
                or event["path_index"] not in assigned
            ):
                raise ArithmeticError("native profile assigned incorrectly")
            delta = error(event, peer)
            if delta > 1e-9:
                raise ArithmeticError("native batch numerical proof failed")
            local = max(local, delta)
            found.append(event["id"])
        done = [e for e in worker["messages"] if e["kind"] == "done"]
        if len(done) != 1 or not same(
            done[0]["summary"],
            dict(paths=len(assigned), profiles=len(events), maximum_error_chips=local),
        ):
            raise ArithmeticError("native batch worker completion changed")
        maximum = max(maximum, local)
    if len(found) != 480 or set(found) != set(by_id) or len(set(found)) != 480:
        raise ArithmeticError("native batch profile grid missing/duplicate")
    return dict(
        status="all480_frozen_batch_profiles_independently_audited",
        profiles=480,
        maximum_error_chips=maximum,
        seconds=saved["seconds"],
        reference_strategies_used_in_training=False,
    )


def run(root: Path, own_path: Path, output: Path) -> dict[str, Any]:
    fresh_output(output)
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    current, binding = inputs.binding(root)
    config = inputs.config_inputs(root)
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
        reference=config["native_reference"],
        license=None,
        own_replay=None,
        batch={},
        seconds=0.0,
        training_performed=False,
        reference_actions_exported=False,
    )
    persist(output, saved)
    try:
        saved["license"] = license_record(config)
        own, _, saved["own_replay"] = replay(root, own_path, deadline)
        saved["details_sha256"] = own["details_sha256"]
        comparison = json.loads((root / "configs/training-isolation.json").read_text())[
            "future_comparison"
        ]
        run_batch(
            88,
            3,
            native_job,
            dict(
                root=str(root),
                own_path=str(own_path),
                own=own,
                comparison=comparison,
                remaining_seconds=900 - (time.perf_counter() - started),
            ),
            deadline,
            saved["batch"],
        )
        deadline.check()
        saved["status"] = "completed"
        saved["seconds"] = time.perf_counter() - started
        validate(saved, own, own_path)
    except BaseException as exc:
        saved.update(
            status="incomplete", failure=dict(type=type(exc).__name__, reason=str(exc))
        )
        raise
    finally:
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
