"""Bounded offline own measurement, immutable archives and read-only replay."""

import json
import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation.averaging_history_protocol import (
    validate_replay as upstream_proof,
)
from poker_ai.evaluation.window_fallback_compute import evaluate_window, fixed_targets
from poker_ai.evaluation.window_fallback_inputs import (
    CONFIG,
    ENTRIES,
    FallbackInputs,
    inputs,
    load,
    windows,
)
from poker_ai.evaluation.window_fallback_replay import replay_archives
from poker_ai.evaluation.window_fallback_validation import FORMAT, grid, validate_replay
from poker_ai.postflop.controlled_checkpoints import write_snapshot
from poker_ai.postflop.learning_artifacts import sha, write_archive
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance


def source(root: Path) -> dict[str, Any]:
    return source_provenance(root, root / CONFIG, entrypoints=ENTRIES)


def available(output: Path) -> Path:
    archive = output.with_name(output.stem + "-profiles.jsonl.gz")
    if any(
        p.exists()
        for p in (
            output,
            output.with_suffix(".tmp"),
            archive,
            archive.with_suffix(".tmp"),
        )
    ):
        raise FileExistsError("retain complete/partial window fallback attempt")
    return archive


def run(root: Path, output: Path) -> dict[str, Any]:
    archive = available(output)
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    config = inputs(root)
    deadline = Deadline(config["maximum_own_seconds"])
    deadline.started = started
    provenance = source(root)
    if provenance["dirty"] is not False:
        raise ValueError("publish checked window fallback source before measurement")
    scratch = root / "results/runs/window-fallback" / str(time.time_ns())
    scratch.mkdir(parents=True, exist_ok=False)
    saved: dict[str, Any] = dict(
        format=FORMAT,
        status="running",
        failure=None,
        config=config,
        source=provenance,
        source_sha256=sha(provenance["sha256"]),
        environment=runtime_environment(),
        source_report_sha256=digest(root / config["source_report"]),
        scratch=str(scratch),
        upstream_replay=None,
        upstream_native=None,
        rows=[],
        panels=[],
        fixed_matches=[],
        own_replay=None,
        details_file=None,
        details_sha256=None,
        report=None,
        seconds=0.0,
        training_performed=False,
        reference_output_used_in_training=False,
    )
    persist(output, saved)
    try:
        data = load(root, deadline)
        saved["upstream_replay"], saved["upstream_native"] = data.replay, data.native
        for window in windows(data, deadline):
            evaluations, panel = evaluate_window(
                window, config, saved["source_sha256"], deadline
            )
            for evaluation in evaluations:
                before = time.perf_counter()
                metadata = evaluation.metadata
                relative = f"snapshots/{metadata['id']}.json.gz"
                receipt = write_snapshot(
                    scratch / relative,
                    window.context.partition,
                    evaluation.policy,
                    metadata,
                )
                saved["rows"].append(
                    dict(
                        **metadata,
                        file=relative,
                        receipt=receipt,
                        metadata_sha256=sha(metadata),
                        seconds=time.perf_counter() - before,
                    )
                )
            saved["panels"].append(panel)
            matches, _ = fixed_targets(window, evaluations, data, deadline)
            saved["fixed_matches"].extend(matches)
            if window.index % 8 == 7:
                saved["seconds"] = time.perf_counter() - started
                persist(output, saved)
        grid(saved, data)
        deadline.check()
        saved["details_sha256"] = write_archive(archive, scratch, saved["rows"])
        saved["details_file"] = archive.name
        saved["own_replay"] = replay_archives(data, output, saved, deadline)
        validate_replay(saved["own_replay"], config)
        from poker_ai.evaluation.window_fallback_report import write_report

        saved["report"] = write_report(root, data, saved, output.parent / "report")
        if len(saved["report"]["figures"]) != 4:
            raise ArithmeticError("window fallback figure inventory incomplete")
        deadline.check()
        saved["status"] = "completed_own_native_pending"
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
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


def read_saved(
    root: Path, path: Path, deadline: Deadline
) -> tuple[dict[str, Any], FallbackInputs]:
    saved: dict[str, Any] = json.loads(path.read_text())
    config = inputs(root)
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed_own_native_pending"
        or saved["failure"] is not None
        or not same(saved["config"], config)
        or saved["training_performed"] is not False
        or saved["reference_output_used_in_training"] is not False
        or not number(saved["seconds"], nonnegative=True)
        or saved["seconds"] >= config["maximum_own_seconds"]
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["source_report_sha256"] != digest(root / config["source_report"])
    ):
        raise ArithmeticError("incomplete/changed saved window fallback receipt")
    check_source(root, saved["source"])
    validate_replay(saved["own_replay"], config)
    data = load(root, deadline)
    upstream_proof(saved["upstream_replay"], data.history.config)
    if (
        not same(saved["upstream_native"], data.native)
        or saved["upstream_replay"]["seconds"] + saved["own_replay"]["seconds"]
        > saved["seconds"]
    ):
        raise ArithmeticError(
            "window fallback input proof or elapsed accounting changed"
        )
    grid(saved, data)
    deadline.check()
    return saved, data


def replay(
    root: Path, path: Path, deadline: Deadline | None = None
) -> tuple[dict[str, Any], FallbackInputs, dict[str, Any]]:
    started = time.perf_counter()
    deadline = deadline or Deadline(900)
    saved, data = read_saved(root, path, deadline)
    proof = replay_archives(data, path, saved, deadline)
    proof["maximum_error_chips"] = max(
        proof["maximum_error_chips"], data.replay["maximum_error_chips"]
    )
    proof["maximum_error_unitless"] = max(
        proof["maximum_error_unitless"], data.replay["maximum_error_unitless"]
    )
    proof["upstream_profiles_replayed"] = data.replay["profiles"]
    proof["seconds"] = time.perf_counter() - started
    validate_replay(proof, data.config)
    deadline.check()
    return saved, data, proof
