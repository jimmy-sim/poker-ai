"""Whole comparison stages: published own bytes first, partial native retention."""

import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation.frozen_batch_validation import full_sources
from poker_ai.evaluation.private_prefix_admission import (
    profile_screen,
    require_software,
)
from poker_ai.evaluation.private_prefix_design import OLD, TOY
from poker_ai.evaluation.private_prefix_gates import require as require_checks
from poker_ai.evaluation.private_prefix_journal import Batch, Events, Journal
from poker_ai.evaluation.private_prefix_read import read
from poker_ai.evaluation.private_prefix_sources import load, source
from poker_ai.evaluation.private_prefix_worker_checks import complete, partial_cells
from poker_ai.postflop.cell_process import Send, run_batch
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.controlled_pipeline import license_record
from poker_ai.solver_validation.matched_array_reference import ScalarReference
from poker_ai.solver_validation.matched_update_audit import published
from poker_ai.solver_validation.private_prefix import (
    FORMAT,
    audit_rows,
    gather,
    validate,
)


def job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    root = Path(payload["root"])
    if (
        digest(Path(payload["own_path"])) != payload["own_sha256"]
        or sha(source(root)["sha256"]) != payload["binding"]
    ):
        raise ArithmeticError("native own/source bytes changed after publication")
    deadline = Deadline(payload["remaining_seconds"])
    sources = load(root)
    opponents = {p.identifier: p for p in full_sources(sources.parent.archived.data)}
    refs = {}
    cache = {}
    send(dict(kind="prepared", phase="reference_setup_started"))
    for i in indices:
        context = sources.context(i)
        pair = []
        for tree in (context.exact, context.partition):
            if id(tree) not in cache:
                cache[id(tree)] = ScalarReference(tree)
            pair.append(cache[id(tree)])
        refs[i] = pair[0], pair[1]
    send(dict(kind="prepared", phase="reference_setup_completed"))

    def opponent(peer: dict[str, Any]) -> Any:
        identifier = peer["opponent_profile_id"]
        return opponents[identifier].policy, sources.parent.archived.data.replies[
            identifier, peer["target"]
        ]

    return audit_rows(
        Path(payload["own_path"]),
        payload["own"],
        indices,
        sources.context,
        refs,
        opponent,
        send,
        deadline,
    )


def audit(root: Path, own_path: Path, path: Path, kind: str) -> dict[str, Any]:
    if path.exists() or path.is_symlink() or path.with_suffix(".tmp").exists():
        raise FileExistsError("retain complete/partial private-prefix native attempt")
    started = time.perf_counter()
    current = source(root)
    if current["dirty"] is not False:
        raise ArithmeticError("publish clean own evidence before native stage")
    cap = 180 if kind == "tiny_native" else 900
    deadline = Deadline(cap)
    deadline.started = started
    saved: dict[str, Any] = dict(
        format=FORMAT,
        status="running",
        failure=None,
        source=current,
        source_sha256=sha(current["sha256"]),
        scope=None,
        own_sha256=digest(own_path),
        details_sha256=None,
        publication=None,
        license=None,
        reference=None,
        environment=runtime_environment(),
        events=[],
        rows=[],
        fixed=[],
        batch={},
        reference_setup_started=False,
        reference_setup_completed=False,
        training_performed=False,
        reference_actions_exported=False,
        reference_output_used_in_training=False,
        long_run_admitted=False,
        completed_profiles=0,
        completed_fixed_targets=0,
        maximum_error_chips=None,
        seconds=0.0,
        parent_cpu_started=time.process_time(),
        children_cpu_started=os.times().children_user + os.times().children_system,
    )
    journal = Journal(
        path.with_name(path.stem + "-events.jsonl"),
        saved["source_sha256"],
        "native_comparison",
    )
    saved["events"] = Events(journal, 0)
    saved["batch"] = Batch(journal)
    saved["journal_file"] = journal.path.name
    try:
        persist(path, saved)
        require_checks(root, clean=False)
        saved["publication"] = published(root, own_path)
        if kind == "tiny_native":
            from poker_ai.evaluation.matched_update_lifecycle import measured

            origin = measured(root, own_path, "tiny_own")
            if origin["hostname"] != __import__("socket").gethostname():
                raise ArithmeticError("shared software clock changed host")
            deadline.started = origin["started_perf_counter"]
            deadline.check()
        else:
            require_software(root)
            if kind == "timing_native":
                profile_screen(root)
        own, sources = read(root, own_path, deadline)
        saved.update(
            scope=own["scope"],
            details_sha256=own["details_sha256"],
            reference=own["config"]["reference"],
            own_replay=own["replayed_now"],
        )
        saved["license"] = license_record({"native_reference": saved["reference"]})
        deadline.check()
        if own["source_sha256"] != saved["source_sha256"]:
            raise ArithmeticError("native and own exact source cohorts differ")
        if own["scope"] == TOY:
            if kind != "tiny_native":
                raise ArithmeticError("toy scope cannot be a real native comparison")
            _, context, opponents = sources
            saved["reference_setup_started"] = True
            reference = ScalarReference(context.partition)
            saved["reference_setup_completed"] = True
            saved["execution"] = "EXPLICIT_SEQUENTIAL_TINY_NOT_SPAWNED"
            summary = audit_rows(
                own_path,
                own,
                list(range(48)),
                lambda _: context,
                {i: (reference, reference) for i in range(48)},
                opponents.opponent,
                saved["events"].append,
                deadline,
            )
            saved["summary"] = summary
        else:
            if (kind == "timing_native") != (own["scope"] == OLD):
                raise ArithmeticError("real native kind and old/study scope differ")
            saved["execution"] = "THREE_SPAWNED_FIXED_PATH_PARTITIONS"
            try:
                run_batch(
                    48,
                    3,
                    job,
                    dict(
                        root=str(root),
                        own_path=str(own_path),
                        own=own,
                        own_sha256=digest(own_path),
                        binding=saved["source_sha256"],
                        remaining_seconds=cap - (time.perf_counter() - started),
                    ),
                    deadline,
                    saved["batch"],
                )
                saved["events"] = complete(saved["batch"], 48)
            finally:
                if not saved["events"]:
                    saved["events"] = partial_cells(saved["batch"])
                prepared = [
                    e
                    for w in saved["batch"].get("workers", [])
                    for e in w["messages"]
                    if e["kind"] == "prepared"
                ]
                saved["reference_setup_started"] = any(
                    e["phase"] == "reference_setup_started" for e in prepared
                )
                saved["reference_setup_completed"] = (
                    sum(e["phase"] == "reference_setup_completed" for e in prepared)
                    == 3
                )
        gather(saved)
        saved["maximum_error_chips"] = max(
            e["result"]["maximum_error_chips"] for e in saved["events"]
        )
        # The shared software clock includes this final full own replay as well.
        own, _ = read(root, own_path, deadline)
        saved["final_own_replay"] = own["replayed_now"]
        saved["status"] = "completed_native_comparison_only"
        saved["seconds"] = time.perf_counter() - started
        validate(saved, own, own_path)
        deadline.check()
    except BaseException as error:
        saved.update(
            status="failed_native_private_prefix_not_admitted",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        gather(saved)
        raise
    finally:
        saved["journal"] = journal.close()
        saved["seconds"] = time.perf_counter() - started
        saved["parent_cpu_seconds"] = time.process_time() - saved.pop(
            "parent_cpu_started"
        )
        saved["reaped_children_cpu_seconds"] = (
            os.times().children_user
            + os.times().children_system
            - saved.pop("children_cpu_started")
        )
        persist(path, saved)
    return saved
