"""Own B4 worker orchestration, immutable-prefix journals and frozen replay."""

import hashlib
import json
import math
import os
import sys
import time
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from poker_ai.evaluation import compact_sampled_inputs as inputs
from poker_ai.finite import FloatArray
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.cell_process import THREAD_ENV, Send, partition, run_batch
from poker_ai.postflop.compact_full_context import Context
from poker_ai.postflop.compact_full_run import check_runtime, runtime
from poker_ai.postflop.compact_sampled_capture import Journal, collect
from poker_ai.postflop.compact_sampled_state import decode, scores
from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.postflop.public_range_definition import contract
from poker_ai.postflop.public_study import peak_rss_bytes
from poker_ai.postflop.river_study import Deadline, digest

FORMAT = "compact-sampled-own-v1"


def journal_rows(
    path: Path, fingerprint: str, scope: str, slot: int, *, complete: bool
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    raw = path.read_bytes()
    rows: list[dict[str, Any]] = []
    offset = 0
    for line in raw.splitlines(keepends=True):
        if not line.endswith(b"\n"):
            if complete:
                raise ArithmeticError("complete journal has an unfinished write")
            break
        event = json.loads(line)
        if (
            event["sequence"] != len(rows)
            or type(event["sequence"]) is not int
            or event["source_fingerprint"] != fingerprint
            or event["scope"] != scope
            or event["slot"] != slot
            or type(event["slot"]) is not int
        ):
            raise ArithmeticError("journal sequence/source/worker identity changed")
        rows.append(event)
        offset += len(line)
    return rows, dict(
        file=path.name,
        bytes=len(raw),
        sha256=digest(path),
        complete_lines=len(rows),
        unfinished_bytes=len(raw) - offset,
        unfinished_sha256=hashlib.sha256(raw[offset:]).hexdigest()
        if offset < len(raw)
        else None,
    )


def no_reference_runtime() -> None:
    if any(
        name == "pyspiel"
        or name.startswith(("open_spiel", "poker_ai.solver_validation"))
        for name in sys.modules
    ):
        raise ArithmeticError("own training worker imported a reference implementation")


def job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    root, folder = Path(payload["root"]), Path(payload["folder"])
    started = time.perf_counter()
    deadline = Deadline(payload["remaining_seconds"])
    inputs.check_source(root, payload["source"])
    if payload["scope"] == "real":
        from poker_ai.evaluation.compact_sampled_gate import worker_admission

        worker_admission(root, Path(payload["admission"]), payload["admission_sha256"])
    no_reference_runtime()
    lookup = inputs.game_contexts(root, payload["scope"])
    journal = Journal(
        folder / f"worker-{slot}.jsonl",
        payload["source"]["fingerprint"],
        payload["scope"],
        slot,
    )
    journal.add("worker_started", indices=indices, pid=os.getpid())
    send(dict(kind="prepared", seconds=time.perf_counter() - started))
    results = []
    try:
        for index in indices:
            deadline.check()
            case = payload["cases"][index]
            context = lookup[case["spot_file"], case["representation"]]
            result = collect(
                context,
                case,
                index,
                payload["scope"],
                payload["labels"],
                folder,
                payload["source"]["fingerprint"],
                journal,
                deadline,
            )
            results.append(result)
            send(dict(kind="cell", phase="trained", index=index, row=result))
        no_reference_runtime()
        summary = dict(
            paths=len(results),
            checkpoints=3 * len(results),
            readouts=9 * len(results),
            peak_process_rss_bytes=peak_rss_bytes(),
        )
        journal.add("worker_done", summary=summary)
        return summary
    except BaseException as error:
        journal.add("worker_error", type=type(error).__name__, reason=str(error))
        raise


def gather(
    root: Path, folder: Path, saved: dict[str, Any], *, score: bool
) -> dict[str, Any]:
    """All immutable receipts first; raw-state replay performs no sampled steps."""
    scope, fingerprint = saved["scope"], saved["source"]["fingerprint"]
    cases, labels = inputs.cases(root, scope), inputs.labels(root, scope)
    assignments = partition(len(cases), inputs.protocol(root)["worker_count"])
    lookup = inputs.game_contexts(root, scope)
    layouts = [dict(**c.binding, **c.diagnostics) for c in lookup.values()]
    warm_rows: list[dict[str, Any]] = []
    points: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    paths: list[dict[str, Any]] = []
    journals: list[dict[str, Any]] = []
    worker_receipts: list[dict[str, Any]] = []
    for slot, indices in enumerate(assignments):
        events, receipt = journal_rows(
            folder / f"worker-{slot}.jsonl", fingerprint, scope, slot, complete=True
        )
        journals.append(receipt)
        if (
            not events
            or events[0]["kind"] != "worker_started"
            or events[0]["indices"] != indices
            or events[-1]["kind"] != "worker_done"
        ):
            raise ArithmeticError("worker start/completion journal missing")
        position = 1
        for index in indices:
            case = cases[index]
            context = lookup[case["spot_file"], case["representation"]]
            began, warm_event = events[position : position + 2]
            position += 2
            if (
                began["kind"] != "path_started"
                or began["index"] != index
                or canonical(began["case"]) != canonical(case)
                or warm_event["kind"] != "warm"
                or warm_event["index"] != index
                or canonical(warm_event["case"]) != canonical(case)
                or canonical(warm_event["binding"]) != canonical(context.binding)
            ):
                raise ArithmeticError("path/warm journal identity changed")
            warm_receipt = warm_event["receipt"]
            if warm_receipt["file"] != f"{index:02d}.json.gz":
                raise ArithmeticError("warm file ownership changed")
            warm = files.load_snapshot(folder / "warms", warm_receipt)
            decode(context, warm, None, fingerprint, scope)
            if warm["seed"] != case["seed"] or warm["path_index"] != index:
                raise ArithmeticError("warm source case changed")
            warm_rows.append(dict(**case, path_index=index, receipt=warm_receipt))
            for label in labels:
                event = events[position]
                position += 1
                if (
                    event["kind"] != "checkpoint"
                    or event["index"] != index
                    or event["work_checkpoint"] != label
                    or canonical(event["case"]) != canonical(case)
                    or canonical(event["binding"]) != canonical(context.binding)
                    or event["receipt"]["file"] != f"{index:02d}-{label}.json.gz"
                ):
                    raise ArithmeticError("checkpoint journal identity/source changed")
                state = files.load_snapshot(folder / "states", event["receipt"])
                if (
                    state["seed"] != case["seed"]
                    or state["path_index"] != index
                    or state["work_checkpoint"] != label
                    or canonical(state["warm_receipt"]) != canonical(warm_receipt)
                    or state["total_node_work"] != event["confirmed_work"]
                    or state["iteration"] != event["iteration"]
                    or state["guard_sha256"] != event["guard_sha256"]
                ):
                    raise ArithmeticError(
                        "raw state/journal/work/warm receipt disagree"
                    )
                arrays, profiles = decode(context, state, warm, fingerprint, scope)
                point = dict(
                    **case,
                    path_index=index,
                    work_checkpoint=label,
                    context_sha256=context.context_sha256,
                    state_receipt=event["receipt"],
                    warm_receipt=warm_receipt,
                    guard_sha256=state["guard_sha256"],
                    iteration=state["iteration"],
                    total_node_work=state["total_node_work"],
                    previous_node_work=state["previous_node_work"],
                    last_iteration_work=state["last_iteration_work"],
                    initialization_work=state["initialization_work"],
                    sampled_traversals=state["sampled_traversals"],
                    tree_nodes=len(context.scoring.partition.player),
                    information_sets=len(context.scoring.partition.keys),
                    recall_violations=context.diagnostics["recall_violations"],
                    menus_compatible=context.diagnostics["menus_compatible"],
                    **{
                        k: contract(root)["sampled"][k]
                        for k in (
                            "sampling",
                            "batch_size",
                            "regret_mode",
                            "regret_weighting",
                            "average_weighting",
                            "initial_exact_expectation",
                        )
                    },
                )
                points.append(point)
                if score:
                    rows.extend(
                        dict(**point, **metric)
                        for metric in scores(context, state, arrays, profiles)
                    )
            done = events[position]
            position += 1
            if (
                done["kind"] != "path_done"
                or done["index"] != index
                or canonical(done["case"]) != canonical(case)
                or done["confirmed_work"] != points[-1]["total_node_work"]
                or done["iteration"] != points[-1]["iteration"]
                or done["checkpoints"] != 3
                or done["readouts"] != 9
            ):
                raise ArithmeticError("complete training path receipt changed")
            paths.append(done)
        if position != len(events) - 1:
            raise ArithmeticError("worker journal has extra/missing events")
        summary = events[-1]["summary"]
        worker_receipts.append(dict(slot=slot, pid=events[0]["pid"], summary=summary))
        if any(
            summary[k] != v * len(indices)
            for k, v in (("paths", 1), ("checkpoints", 3), ("readouts", 9))
        ):
            raise ArithmeticError("worker summary count changed")
    warm_rows.sort(key=lambda r: r["path_index"])
    points.sort(key=lambda r: (r["path_index"], r["work_checkpoint"]))
    rows.sort(
        key=lambda r: (
            r["path_index"],
            r["work_checkpoint"],
            inputs.READOUTS.index(r["readout"]),
        )
    )
    paths.sort(key=lambda r: r["index"])
    if (
        len(points) != 108
        or {inputs.identity(r, inputs.POINT) for r in points}
        != inputs.expected(root, scope, readouts=False)
        or (
            score
            and (
                len(rows) != 324
                or {inputs.identity(r, inputs.IDENTITY) for r in rows}
                != inputs.expected(root, scope, readouts=True)
            )
        )
    ):
        raise ArithmeticError("complete108-state/324-readout grid required")
    return dict(
        warms=warm_rows,
        points=points,
        rows=rows,
        paths=paths,
        journals=journals,
        worker_receipts=worker_receipts,
        partitions=layouts,
        raw_states_checked=108,
        readouts_checked=len(rows),
        sampled_training_performed=False,
    )


def partial(folder: Path) -> dict[str, Any]:
    """Retain confirmed prefix receipts and unknown progress; never infer completion."""
    summaries = []
    for path in sorted(folder.glob("worker-*.jsonl")):
        raw = path.read_bytes()
        completed: list[dict[str, Any]] = []
        tail = b""
        invalid = None
        for line in raw.splitlines(keepends=True):
            try:
                if invalid is not None:
                    raise ValueError("after invalid prefix")
                if not line.endswith(b"\n"):
                    raise ValueError("unfinished JSON write")
                event = json.loads(line)
                slot = int(path.stem.removeprefix("worker-"))
                if (
                    type(event["sequence"]) is not int
                    or event["sequence"] != len(completed)
                    or type(event["slot"]) is not int
                    or event["slot"] != slot
                    or (
                        completed
                        and any(
                            event[k] != completed[0][k]
                            for k in ("source_fingerprint", "scope")
                        )
                    )
                ):
                    raise ValueError("invalid journal identity/sequence")
                completed.append(event)
            except (ValueError, UnicodeDecodeError, KeyError, TypeError) as error:
                if invalid is None:
                    invalid = str(error)
                tail += line
        summaries.append(
            dict(
                file=path.name,
                sha256=digest(path),
                confirmed_events=len(completed),
                last_confirmed_event=completed[-1] if completed else None,
                unfinished_bytes=len(tail),
                invalid_prefix_reason=invalid,
                authentication=(
                    "Internal journal prefix only; raw states/source not replayed"
                ),
                progress_after_last_event="unknown",
            )
        )
    return dict(
        journals=summaries,
        complete=False,
        retained_temporaries=[
            str(p.relative_to(folder)) for p in folder.rglob("*.tmp")
        ],
    )


def check_batch(saved: dict[str, Any], captured: dict[str, Any]) -> None:
    """Cross-check independent pipe and fsynced journal completion receipts."""
    batch = saved["training_batch"]
    assignments = partition(36, 3)
    if (
        batch["status"] != "completed"
        or batch["failure"] is not None
        or batch["worker_count"] != 3
        or batch["assignments"] != assignments
        or len(batch["workers"]) != 3
    ):
        raise ArithmeticError("complete source-bound workers required")
    pids: set[int] = set()
    paths = {row["index"]: row for row in captured["paths"]}
    for slot, worker in enumerate(batch["workers"]):
        messages = worker["messages"]
        indices = assignments[slot]
        if (
            worker["slot"] != slot
            or type(worker["pid"]) is not int
            or worker["pid"] <= 0
            or worker["pid"] in pids
            or type(worker["exitcode"]) is not int
            or worker["exitcode"] != 0
            or [m["kind"] for m in messages]
            != ["started", "prepared", *(["cell"] * 12), "done"]
            or messages[0]["pid"] != worker["pid"]
            or messages[0]["thread_environment"] != THREAD_ENV
        ):
            raise ArithmeticError("worker process/event/completion identity changed")
        pids.add(worker["pid"])
        for event, index in zip(messages[2:-1], indices, strict=True):
            path_result = {
                k: v
                for k, v in paths[index].items()
                if k not in {"sequence", "source_fingerprint", "scope", "slot", "kind"}
            }
            if (
                event["phase"] != "trained"
                or event["index"] != index
                or canonical(event["row"]) != canonical(path_result)
            ):
                raise ArithmeticError("worker pipe and immutable path journal disagree")
        summary = messages[-1]["summary"]
        if canonical(captured["worker_receipts"][slot]) != canonical(
            dict(slot=slot, pid=worker["pid"], summary=summary)
        ):
            raise ArithmeticError(
                "pipe and immutable journal worker summaries disagree"
            )
        if any(
            summary[k] != n
            for k, n in (("paths", 12), ("checkpoints", 36), ("readouts", 108))
        ):
            raise ArithmeticError("worker completion counts changed")
        for event, keys in (
            (messages[1], ("seconds",)),
            (messages[-1], ("seconds", "cpu_seconds")),
            (batch, ("seconds", "parent_cpu_seconds", "reaped_children_cpu_seconds")),
        ):
            if any(
                type(event[k]) not in (int, float)
                or not math.isfinite(event[k])
                or event[k] < 0
                for k in keys
            ):
                raise ArithmeticError("invalid worker lifecycle timing")


def run(
    root: Path,
    output: Path,
    scope: str,
    checks: Path,
    started: float,
    admission: Path | None = None,
) -> dict[str, Any]:
    if scope not in ("software", "real"):
        raise ValueError("cost scope cannot start sampling")
    if (
        output.exists()
        or (output.parent / "states").exists()
        or (output.parent / "warms").exists()
    ):
        raise FileExistsError("retain complete/partial sampled output")
    source = inputs.source(root)
    config = inputs.protocol(root)
    cap = (
        config["software_maximum_seconds"]
        if scope == "software"
        else contract(root)["sampled"]["maximum_seconds"]
    )
    deadline = Deadline(cap)
    deadline.started = started
    cpu, children = time.process_time(), os.times()
    saved: dict[str, Any] = dict(
        format=FORMAT,
        scope=scope,
        status="running",
        failure=None,
        source=source,
        runtime=runtime(),
        actual_admission=False,
        fresh_global_admission=False,
        new_agent_default=False,
        rows=[],
        training_batch={},
        protocol_sha256=inputs.SPEC_SHA,
        partial_evidence=None,
    )

    def persist() -> None:
        now = os.times()
        saved.update(
            seconds=time.perf_counter() - started,
            parent_cpu_seconds=time.process_time() - cpu,
            reaped_children_cpu_seconds=(
                now.children_user
                + now.children_system
                - children.children_user
                - children.children_system
            ),
            peak_process_rss_bytes=peak_rss_bytes(),
        )
        files.atomic(output, saved)

    try:
        persist()
        from poker_ai.evaluation.compact_sampled_gate import (
            require_admission,
            require_checks,
        )

        saved["checks"] = require_checks(root, checks)
        check_runtime(saved["runtime"], real=scope == "real")
        if scope == "real":
            if admission is None:
                raise ValueError("published sampled admission required")
            saved["admission"] = require_admission(root, admission)
        deadline.check()
        payload = dict(
            root=str(root),
            folder=str(output.parent),
            scope=scope,
            source=source,
            cases=inputs.cases(root, scope),
            labels=inputs.labels(root, scope),
            remaining_seconds=max(
                0.001, deadline.seconds - (time.perf_counter() - deadline.started)
            ),
            admission=str(admission) if admission else None,
            admission_sha256=digest(admission) if admission else None,
        )
        run_batch(
            36, config["worker_count"], job, payload, deadline, saved["training_batch"]
        )
        deadline.check()
        captured = gather(root, output.parent, saved, score=True)
        saved.update(captured)
        inputs.check_source(root, source)
        saved["status"] = "completed"
        persist()
        saved["replay"] = replay(root, output)
        deadline.check()
    except (Exception, KeyboardInterrupt) as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
            partial_evidence=partial(output.parent),
        )
    finally:
        persist()
    return saved


def replay(root: Path, path: Path) -> dict[str, Any]:
    saved = json.loads(path.read_text())
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or saved["actual_admission"] is not False
        or saved["fresh_global_admission"] is not False
        or saved["new_agent_default"] is not False
        or saved["protocol_sha256"] != inputs.SPEC_SHA
    ):
        raise ArithmeticError("partial or changed sampled own receipt")
    inputs.check_source(root, saved["source"])
    check_runtime(saved["runtime"], real=saved["scope"] == "real")
    captured = gather(root, path.parent, saved, score=True)
    if any(canonical(captured[k]) != canonical(saved[k]) for k in captured):
        raise ArithmeticError("sampled raw-state/journal/metric replay changed")
    check_batch(saved, captured)
    return dict(
        raw_states_checked=108,
        warm_origins_checked=36,
        readouts_checked=324,
        maximum_metric_error_chips=0.0,
        sampled_training_performed=False,
        trajectory_retrained=False,
        actual_admission=False,
    )


def policy_rows(
    root: Path, path: Path, saved: dict[str, Any]
) -> Iterator[tuple[Context, dict[str, Any], FloatArray]]:
    """Read only already-authenticated OWN states for scalar reference comparison."""
    lookup = inputs.game_contexts(root, saved["scope"])
    rows = {inputs.identity(r, inputs.IDENTITY): r for r in saved["rows"]}
    for point in saved["points"]:
        context = lookup[point["spot_file"], point["representation"]]
        state = files.load_snapshot(path.parent / "states", point["state_receipt"])
        warm = files.load_snapshot(path.parent / "warms", point["warm_receipt"])
        _, profiles = decode(
            context, state, warm, saved["source"]["fingerprint"], saved["scope"]
        )
        for readout in inputs.READOUTS:
            key = inputs.identity(dict(point, readout=readout), inputs.IDENTITY)
            yield context, rows[key], context.scoring.expand(profiles[readout])
