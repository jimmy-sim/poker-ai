"""Admitted same-trajectory replay, retained own artifacts and read-only reports."""

import json
import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import averaging_history_protocol as protocol
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs, inputs, load
from poker_ai.evaluation.averaging_history_replay import replay_archives
from poker_ai.evaluation.averaging_history_training import own_job
from poker_ai.evaluation.averaging_history_validation import gather
from poker_ai.postflop.cell_process import run_batch
from poker_ai.postflop.learning_artifacts import sha, write_archive
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment


def run(root: Path, output: Path) -> dict[str, Any]:
    if output.exists() or output.with_suffix(".tmp").exists():
        raise FileExistsError("retain averaging trajectory attempt")
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    config = inputs(root)
    environment = runtime_environment()
    protocol.require_prefix_runtime(config, environment)
    deadline = Deadline(config["maximum_own_seconds"])
    deadline.started = started
    admission = protocol.require_admission(root, config)
    source = protocol.source(root)
    data = load(root)
    scratch = root / "results/runs/averaging-history" / str(time.time_ns())
    scratch.mkdir(parents=True, exist_ok=False)
    saved: dict[str, Any] = dict(
        format=protocol.FORMAT,
        status="running",
        failure=None,
        config=config,
        source=source,
        source_sha256=sha(source["sha256"]),
        admission=admission,
        environment=environment,
        scratch=str(scratch),
        batch={},
        rows=[],
        masses=[],
        fixed_matches=[],
        own_replay=None,
        details_file=None,
        details_sha256=None,
        mass_details_file=None,
        mass_details_sha256=None,
        report=None,
        seconds=0.0,
        training_performed=True,
        new_learning_rule=False,
        reference_output_used_in_training=False,
    )
    persist(output, saved)
    try:
        cells = [
            dict(
                case=p.case,
                source_id=p.identifier,
                prefixes={
                    t: data.prefixes[p.identifier, t]
                    for t in config["original_average_replay_labels"]
                },
            )
            for p in data.base.policies
        ]
        comparison = json.loads((root / "configs/training-isolation.json").read_text())[
            "future_comparison"
        ]
        run_batch(
            64,
            3,
            own_job,
            dict(
                root=str(root),
                comparison=comparison,
                cells=cells,
                config=config,
                scratch=str(scratch),
                binding=saved["source_sha256"],
                remaining_seconds=config["maximum_own_seconds"]
                - (time.perf_counter() - started),
            ),
            deadline,
            saved["batch"],
        )
        saved["rows"], saved["masses"] = gather(
            saved["batch"], data, saved["source_sha256"]
        )
        for suffix, rows_key, name_key, hash_key in (
            ("profiles", "rows", "details_file", "details_sha256"),
            ("masses", "masses", "mass_details_file", "mass_details_sha256"),
        ):
            deadline.check()
            archive = output.with_name(output.stem + "-" + suffix + ".jsonl.gz")
            if archive.exists() or archive.with_suffix(".tmp").exists():
                raise FileExistsError("retain averaging policy/mass archive attempt")
            saved[hash_key] = write_archive(archive, scratch, saved[rows_key])
            saved[name_key] = archive.name
        saved["own_replay"], saved["fixed_matches"] = replay_archives(
            root, output, saved, data, deadline
        )
        deadline.check()
        from poker_ai.evaluation.averaging_history_report import write_report

        saved["report"] = write_report(root, data, saved, output.parent / "report")
        if (
            saved["report"]["profiles"] != 512
            or saved["report"]["cumulative_boundaries"] != 192
            or saved["report"]["fixed_opponent_target_conditions"] != 2048
            or len(saved["report"]["figures"]) != 6
        ):
            raise ArithmeticError("averaging report grid/figure inventory incomplete")
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


def read_saved(root: Path, path: Path) -> tuple[dict[str, Any], HistoryInputs]:
    saved: dict[str, Any] = json.loads(path.read_text())
    config = inputs(root)
    if (
        saved["format"] != protocol.FORMAT
        or saved["status"] != "completed_own_native_pending"
        or saved["failure"] is not None
        or not same(saved["config"], config)
        or saved["training_performed"] is not True
        or saved["new_learning_rule"] is not False
        or saved["reference_output_used_in_training"] is not False
        or not number(saved["seconds"], nonnegative=True)
        or saved["seconds"] >= config["maximum_own_seconds"]
    ):
        raise ArithmeticError("incomplete/changed averaging trajectory receipt")
    check_source(root, saved["source"])
    protocol.validate_replay(saved["own_replay"], config)
    if saved["own_replay"]["seconds"] > saved["seconds"]:
        raise ArithmeticError("own replay time exceeds recorded averaging stage")
    protocol.require_prefix_runtime(config, saved["environment"])
    admission = protocol.require_admission(root, config, require_clean=False)
    if (
        not same(saved["admission"], admission)
        or saved["source_sha256"] != admission["source_sha256"]
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
    ):
        raise ArithmeticError("averaging source/admission binding changed")
    data = load(root)
    rows, masses = gather(saved["batch"], data, saved["source_sha256"])
    if (
        not same(rows, saved["rows"])
        or not same(masses, saved["masses"])
        or len(saved["fixed_matches"]) != 2048
    ):
        raise ArithmeticError("averaging header differs from complete worker ledgers")
    return saved, data


def replay(
    root: Path, path: Path, deadline: Deadline | None = None
) -> tuple[dict[str, Any], HistoryInputs, dict[str, Any]]:
    started = time.perf_counter()
    deadline = deadline or Deadline(900)
    saved, data = read_saved(root, path)
    proof, matches = replay_archives(root, path, saved, data, deadline)
    error = compare(matches, saved["fixed_matches"])
    if error > data.config["tolerance_chips"]:
        raise ArithmeticError("saved averaging fixed-opponent comparisons changed")
    proof["maximum_error_chips"] = max(proof["maximum_error_chips"], error)
    proof["seconds"] = time.perf_counter() - started
    deadline.check()
    return saved, data, proof
