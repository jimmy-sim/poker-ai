"""Retained own study orchestration with source gates before every real stage."""

import json
import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import private_prefix_baselines as baselines
from poker_ai.evaluation.private_prefix_design import OLD, REAL, TOY, Design
from poker_ai.evaluation.private_prefix_exercise import exercise, score_captures
from poker_ai.evaluation.private_prefix_gates import require as require_checks
from poker_ai.evaluation.private_prefix_io import archive, fresh, gather, retain_partial
from poker_ai.evaluation.private_prefix_journal import Batch, Events, Journal
from poker_ai.evaluation.private_prefix_pairs import fixed_pairs, self_pairs
from poker_ai.evaluation.private_prefix_read import FORMAT
from poker_ai.evaluation.private_prefix_report import write as write_report
from poker_ai.evaluation.private_prefix_sources import (
    contract,
    kernel_evidence,
    load,
    source,
)
from poker_ai.evaluation.private_prefix_toy import (
    baselines as toy_baselines,
)
from poker_ai.evaluation.private_prefix_toy import (
    fixture,
)
from poker_ai.evaluation.private_prefix_toy import (
    maps as toy_maps,
)
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment


def prepare(
    root: Path, path: Path, scope: str, *, bound_source: dict[str, Any] | None = None
) -> tuple[dict[str, Any], Path, Deadline, float]:
    fresh(path)
    started = time.perf_counter()
    config, driver = contract(root)
    actual_current = source(root)
    if bound_source is None:
        current = actual_current
        if current["dirty"] is not False:
            raise ArithmeticError("publish clean complete private-prefix source first")
    else:
        check_source(root, bound_source)
        if not same(actual_current["sha256"], bound_source["sha256"]):
            raise ArithmeticError("profile parent clean code snapshot changed")
        current = bound_source
    cap = 180 if scope == TOY else 900 if scope == OLD else 7200
    deadline = Deadline(cap)
    deadline.started = started
    scratch = root / "results/runs/private-prefix" / str(time.time_ns())
    scratch.mkdir(parents=True, exist_ok=False)
    saved: dict[str, Any] = dict(
        format=FORMAT,
        scope=scope,
        status="running",
        failure=None,
        source=current,
        source_capture="current_clean_before_output"
        if bound_source is None
        else "profile_parent_clean_before_output",
        stage_start_git_status=actual_current["git_status"],
        source_sha256=sha(current["sha256"]),
        config=config,
        driver=driver,
        input_sha256=kernel_evidence(root),
        environment=runtime_environment(),
        scratch=str(scratch),
        events=[],
        captures=[],
        masses=[],
        rows=[],
        fixed_matches=[],
        baseline_rows=[],
        baseline_fixed=[],
        self_pairs=[],
        fixed_pairs=[],
        training_attempted_paths=0,
        initialized_training_paths=0,
        training_performed=False,
        reference_constructed=False,
        reference_output_used_in_training=False,
        new_agent_default=False,
        fresh_global_admission=False,
        report=None,
        parent_cpu_started=time.process_time(),
        children_cpu_started=os.times().children_user + os.times().children_system,
    )
    return saved, scratch, deadline, started


def finish(
    path: Path,
    saved: dict[str, Any],
    scratch: Path,
    deadline: Deadline,
    started: float,
    error: BaseException | None,
) -> None:
    late_error = None
    if error is None:
        try:
            deadline.check()
        except BaseException as overdue:
            error = late_error = overdue
    if error is not None:
        saved.update(
            status="failed_own_private_prefix_not_admitted",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        try:
            gather(saved)
        except BaseException as gather_error:
            saved["gather_failure"] = dict(
                type=type(gather_error).__name__, reason=str(gather_error)
            )
        retain_partial(path, saved, scratch)
    saved["seconds"] = time.perf_counter() - started
    saved["parent_cpu_seconds"] = time.process_time() - saved.pop("parent_cpu_started")
    saved["reaped_children_cpu_seconds"] = (
        os.times().children_user
        + os.times().children_system
        - saved.pop("children_cpu_started")
    )
    persist(path, saved)
    if late_error is not None:
        raise late_error


def tiny(root: Path, path: Path) -> dict[str, Any]:
    require_checks(root, clean=True)
    saved, scratch, deadline, started = prepare(root, path, TOY)
    journal = Journal(
        path.with_name(path.stem + "-events.jsonl"),
        saved["source_sha256"],
        "explicit_sequential_toy",
    )
    saved["events"] = Events(journal, 0)
    saved["baseline_rows"] = Events(journal, 1)
    saved["baseline_fixed"] = Events(journal, 2)
    saved["journal_file"] = journal.path.name
    error = None
    try:
        persist(path, saved)
        design, context, opponents = fixture(saved["config"])
        saved["manifest"] = design.manifest()
        saved["fixture"] = (
            "ONE_NONUNIFORM_KUHN_TWO_PRIVATE_CHANCE_LEVELS_DUPLICATED_LOGICAL_CONTEXTS"
        )
        baseline_rows, baseline_fixed = toy_baselines(
            design,
            context,
            opponents,
            scratch,
            saved["source_sha256"],
            deadline,
            saved["baseline_rows"].append,
            saved["baseline_fixed"].append,
        )
        # Keep journal-backed lists; the helper's independently accumulated
        # sorted return is checked without replacing those append containers.
        if sorted(saved["baseline_rows"], key=lambda r: r["id"]) != baseline_rows:
            raise ArithmeticError("retained toy baseline callbacks differ")
        if len(saved["baseline_fixed"]) != len(baseline_fixed):
            raise ArithmeticError("retained toy baseline fixed callbacks differ")
        archive(path, saved, scratch, "baseline_rows", "baseline")
        exercise(
            path, saved, design, lambda _: context, opponents.matches, scratch, deadline
        )
        selves, targets = toy_maps(
            design, saved["baseline_rows"], saved["baseline_fixed"]
        )
        saved["self_pairs"] = self_pairs(design, saved["rows"], selves)
        saved["fixed_pairs"] = fixed_pairs(saved["fixed_matches"], targets)
        saved["report"] = write_report(
            saved, path.parent / "report", {p["spot_file"]: 2.0 for p in design.paths}
        )
        saved["status"] = "completed_own_native_pending"
    except BaseException as caught:
        error = caught
        raise
    finally:
        saved["journal"] = journal.close()
        finish(path, saved, scratch, deadline, started, error)
    return saved


def old(
    root: Path,
    path: Path,
    *,
    sources: Any | None = None,
    bound_source: dict[str, Any] | None = None,
    shared_deadline: Deadline | None = None,
) -> dict[str, Any]:
    """Called inside the admitted900-second profile, not an alternate forecast."""
    from poker_ai.evaluation.private_prefix_admission import require_software
    from poker_ai.evaluation.private_prefix_old import copy

    require_software(root)
    saved, scratch, deadline, started = prepare(
        root, path, OLD, bound_source=bound_source
    )
    if shared_deadline is not None:
        deadline = shared_deadline
    journal = Journal(
        path.with_name(path.stem + "-events.jsonl"),
        saved["source_sha256"],
        "old_source_copy_and_score",
    )
    saved["events"] = Events(journal, 0)
    saved["journal_file"] = journal.path.name
    error = None
    try:
        persist(path, saved)
        sources = sources or load(root)
        design = Design.build(saved["config"], mode="old")
        saved.update(
            manifest=design.manifest(),
            baseline_rows=baselines.rows(sources),
            baseline_fixed=sources.parent.fixed,
            input_sha256=baselines.source_hashes(root, sources),
        )
        copy(root, path, saved, sources, design, scratch, deadline)
        score_captures(
            path,
            saved,
            design,
            sources.context,
            lambda r, p, b: baselines.fixed_for(sources, r, p, b),
            scratch,
            deadline,
        )
        selves, targets = baselines.maps(
            design, saved["baseline_rows"], saved["baseline_fixed"]
        )
        saved["self_pairs"] = self_pairs(design, saved["rows"], selves)
        saved["fixed_pairs"] = fixed_pairs(saved["fixed_matches"], targets)
        saved["report"] = write_report(
            saved,
            path.parent / "report",
            {
                p["spot_file"]: float(
                    json.loads((root / p["spot_file"]).read_text())["pot"]
                )
                for p in design.paths
            },
        )
        saved["status"] = "completed_own_native_pending"
    except BaseException as caught:
        error = caught
        raise
    finally:
        saved["journal"] = journal.close()
        finish(path, saved, scratch, deadline, started, error)
    return saved


def study(root: Path, path: Path) -> dict[str, Any]:
    from poker_ai.evaluation.private_prefix_admission import (
        ADMISSION,
    )
    from poker_ai.evaluation.private_prefix_admission import (
        require as require_admission,
    )
    from poker_ai.evaluation.private_prefix_design import inventory
    from poker_ai.evaluation.private_prefix_jobs import training
    from poker_ai.evaluation.private_prefix_quality import summarize
    from poker_ai.evaluation.private_prefix_worker_checks import complete, partial_cells
    from poker_ai.postflop.cell_process import run_batch
    from poker_ai.postflop.river_study import digest

    begun, cpu, times = time.perf_counter(), time.process_time(), os.times()
    admission = require_admission(root, clean=True)
    saved, scratch, deadline, _ = prepare(root, path, REAL)
    deadline.started = begun
    saved["parent_cpu_started"] = cpu
    saved["children_cpu_started"] = times.children_user + times.children_system
    journal = Journal(
        path.with_name(path.stem + "-events.jsonl"),
        saved["source_sha256"],
        "new_training",
    )
    saved["training_batch"] = Batch(journal)
    saved["journal_file"] = journal.path.name
    saved.update(
        admission=admission,
        admission_sha256=digest(root / ADMISSION),
    )
    error = None
    try:
        env = saved["environment"]
        if env["python"] != "3.11.17" or env["numpy"] != "2.4.6":
            raise ArithmeticError("new real study requires original recorded runtime")
        persist(path, saved)
        sources = load(root)
        design = Design.build(saved["config"], mode="real")
        saved.update(
            manifest=design.manifest(),
            baseline_rows=baselines.rows(sources),
            baseline_fixed=sources.parent.fixed,
            input_sha256=baselines.source_hashes(root, sources),
        )
        try:
            run_batch(
                48,
                3,
                training,
                dict(
                    root=str(root),
                    config=saved["config"],
                    scratch=str(scratch),
                    binding=saved["source_sha256"],
                    admission_sha256=saved["admission_sha256"],
                    remaining_seconds=7200 - (time.perf_counter() - begun),
                ),
                deadline,
                saved["training_batch"],
            )
            complete(saved["training_batch"], 48)
        finally:
            saved["events"] = Events(journal, 3, partial_cells(saved["training_batch"]))
            gather(saved)
            saved["training_event_count"] = len(saved["events"])
            persist(path, saved)
        inventory(design, saved, scored=False)
        archive(path, saved, scratch, "captures", "captures")
        archive(path, saved, scratch, "masses", "masses")
        score_captures(
            path,
            saved,
            design,
            sources.context,
            lambda r, p, b: baselines.fixed_for(sources, r, p, b),
            scratch,
            deadline,
        )
        selves, targets = baselines.maps(
            design, saved["baseline_rows"], saved["baseline_fixed"]
        )
        saved["self_pairs"] = self_pairs(design, saved["rows"], selves)
        saved["fixed_pairs"] = fixed_pairs(saved["fixed_matches"], targets)
        pots = {
            p["spot_file"]: float(
                json.loads((root / p["spot_file"]).read_text())["pot"]
            )
            for p in design.paths
        }
        saved["known_case_quality_limits"] = summarize(saved["rows"], pots)
        saved["report"] = write_report(saved, path.parent / "report", pots)
        check_source(root, saved["source"])
        saved["status"] = "completed_own_native_pending"
    except BaseException as caught:
        error = caught
        raise
    finally:
        saved["journal"] = journal.close()
        finish(path, saved, scratch, deadline, begun, error)
    return saved
