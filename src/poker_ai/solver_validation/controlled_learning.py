"""Comparison-only native audit of each immutable OWN controlled checkpoint."""

import json
import os
import time
from pathlib import Path
from typing import Any

from poker_ai.postflop import learning_protocol as protocol
from poker_ai.postflop import pipeline_cost
from poker_ai.postflop.cell_process import Send, partition, run_batch
from poker_ai.postflop.learning_artifacts import read_archive
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_training import replay_detail
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.controlled_pipeline import (
    compare_one,
    license_record,
    references,
)

FORMAT = "poker-ai-controlled-learning-native-audit-v1"


def native_job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    root, own_path = Path(payload["root"]), Path(payload["own_path"])
    deadline = Deadline(payload["remaining_seconds"])
    started = time.perf_counter()
    contexts = pipeline_cost.contexts(root, payload["comparison"])
    refs = references(contexts)
    send(dict(kind="prepared", seconds=time.perf_counter() - started))
    count, maximum = 0, 0.0
    saved = payload["own"]
    for row, blob in read_archive(
        own_path.with_name(saved["details_file"]),
        saved["details_sha256"],
        saved["rows"],
    ):
        deadline.check()
        if row["index"] not in indices:
            continue
        case = row["case"]
        key = case["spot_file"], case["representation"]
        context = contexts[key]
        _, detail = replay_detail(context, row, blob, 1e-9)
        result = compare_one(context, refs[key], detail)
        if result["maximum_error_chips"] > 1e-9:
            raise ArithmeticError("native controlled checkpoint comparison failed")
        maximum = max(maximum, result["maximum_error_chips"])
        send(dict(kind="cell", index=row["index"], id=row["id"], **result))
        count += 1
    return dict(cells=len(indices), snapshots=count, maximum_error_chips=maximum)


def validate(
    saved: dict[str, Any], own: dict[str, Any], own_path: Path
) -> dict[str, Any]:
    batch = saved["batch"]
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or (
            saved["own_sha256"] != digest(own_path)
            or saved["details_sha256"] != own["details_sha256"]
            or batch["status"] != "completed"
            or batch["failure"] is not None
            or saved["seconds"] >= 3600
        )
    ):
        raise ArithmeticError("incomplete/changed native controlled audit")
    if not same(batch["assignments"], partition(140, 3)):
        raise ArithmeticError("native fixed assignments changed")
    found = []
    maximum = 0.0
    by_id = {r["id"]: r for r in own["rows"]}
    for worker, assigned in zip(batch["workers"], batch["assignments"], strict=True):
        if worker["exitcode"] != 0:
            raise ArithmeticError("native worker failed")
        events = [e for e in worker["messages"] if e["kind"] == "cell"]
        for event in events:
            row = by_id[event["id"]]
            if event["index"] != row["index"] or event["index"] not in assigned:
                raise ArithmeticError("native checkpoint assigned incorrectly")
            errors = [
                abs(event["native_metrics"][k] - row["metrics"][k])
                for k in pipeline_cost.METRICS
            ]
            for target, response in enumerate(event["responses"]):
                if response["target"] != target:
                    raise ArithmeticError("native target changed")
                peer = row["responses"][target]
                for native_name, own_name in {
                    "exact_root_chips": "exact_reply_value_chips",
                    "restricted_root_chips": "restricted_reply_value_chips",
                    "achieved_exact_chips": "exact_reply_value_chips",
                    "achieved_restricted_chips": "restricted_reply_value_chips",
                    "achieved_river_before_chips": "river_before_value_chips",
                }.items():
                    errors.append(abs(response[native_name] - peer[own_name]))
            error = max(errors)
            if error > 1e-9 or not same(error, event["maximum_error_chips"]):
                raise ArithmeticError("native root/achieved reply scalar check changed")
            maximum = max(maximum, error)
            found.append(event["id"])
        done = [e for e in worker["messages"] if e["kind"] == "done"]
        if len(done) != 1 or done[0]["summary"]["snapshots"] != len(events):
            raise ArithmeticError("native completion inventory missing")
    if sorted(found) != sorted(by_id) or len(found) != len(by_id):
        raise ArithmeticError("native checkpoint grid incomplete")
    return dict(
        status="all_controlled_checkpoints_audited",
        snapshots=len(found),
        logical_checkpoints=sum(len(r["labels"]) for r in own["rows"]),
        maximum_error_chips=maximum,
        seconds=saved["seconds"],
        reference_strategies_used_in_training=False,
    )


def run(root: Path, own_path: Path, output: Path) -> dict[str, Any]:
    if output.exists() or output.with_suffix(".tmp").exists():
        raise FileExistsError("retain native controlled audit")
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    own, comparison = protocol.read_own(root, own_path)
    source = protocol.source(root)
    if source["dirty"] is not False:
        raise ValueError("publish own outputs before recorded native comparison")
    deadline = Deadline(3600)
    deadline.started = started
    license_config = json.loads((root / pipeline_cost.CONFIG).read_text())
    license_receipt = license_record(license_config)
    saved = dict(
        format=FORMAT,
        status="running",
        failure=None,
        source=source,
        environment=runtime_environment(),
        own_sha256=digest(own_path),
        details_sha256=own["details_sha256"],
        license=license_receipt,
        batch={},
        seconds=0.0,
        native_output_used_in_training=False,
    )
    persist(output, saved)
    try:
        run_batch(
            140,
            3,
            native_job,
            dict(
                root=str(root),
                own_path=str(own_path),
                comparison=comparison,
                own=own,
                remaining_seconds=3600 - (time.perf_counter() - started),
            ),
            deadline,
            saved["batch"],
        )
        saved["status"] = "completed"
        saved["seconds"] = time.perf_counter() - started
        validate(saved, own, own_path)
        deadline.check()
    except BaseException as error:
        saved["status"] = "incomplete"
        saved["failure"] = dict(type=type(error).__name__, reason=str(error))
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
