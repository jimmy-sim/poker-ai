"""Admitted saved-policy diagnosis; no learning, policy changes or native outputs."""

import json
import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import batch_current_inputs as inputs
from poker_ai.evaluation.batch_current_cells import job
from poker_ai.evaluation.batch_current_replay import replay_archives
from poker_ai.evaluation.batch_current_validation import gather
from poker_ai.postflop.cell_process import run_batch
from poker_ai.postflop.learning_artifacts import sha, write_archive
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment


def fresh(path: Path) -> None:
    if path.exists() or path.with_suffix(".tmp").exists():
        raise FileExistsError("retain current diagnosis attempt")


def run(root: Path, output: Path) -> dict[str, Any]:
    from poker_ai.evaluation.batch_current_protocol import require_admission

    fresh(output)
    fresh(output.with_name(output.stem + "-profiles.jsonl.gz"))
    if (output.parent / "report").exists():
        raise FileExistsError("retain current diagnosis report")
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    config = inputs.config_inputs(root)
    current, binding = inputs.binding(root)
    admission = require_admission(root)
    deadline = Deadline(3600)
    deadline.started = started
    scratch = root / "results/runs/batch-current-diagnosis" / str(time.time_ns())
    scratch.mkdir(parents=True, exist_ok=False)
    saved: dict[str, Any] = dict(
        format=inputs.FORMAT,
        status="running",
        failure=None,
        config=config,
        source=current,
        source_sha256=binding,
        environment=runtime_environment(),
        admission=admission,
        scratch=str(scratch),
        source_inputs=None,
        reference=None,
        batch={},
        rows=[],
        fixed_matches=[],
        details_file=None,
        details_sha256=None,
        own_replay=None,
        report=None,
        seconds=0.0,
        scoring_requested=True,
        completed_current_profiles=0,
        completed_fixed_targets=0,
        training_performed=False,
        reference_constructed=False,
        policies_modified=False,
        new_agent_default=False,
        fresh_global_admission=False,
    )
    persist(output, saved)
    try:
        sources = inputs.load(root)
        saved["source_inputs"] = inputs.source_hashes(root, sources)
        saved["reference"] = config["native_reference"]
        run_batch(
            72,
            3,
            job,
            dict(
                root=str(root),
                scratch=str(scratch),
                binding=binding,
                remaining_seconds=3600 - (time.perf_counter() - started),
            ),
            deadline,
            saved["batch"],
        )
        saved["rows"], saved["fixed_matches"] = gather(saved["batch"], sources, binding)
        archive = output.with_name(output.stem + "-profiles.jsonl.gz")
        saved["details_file"] = archive.name
        saved["details_sha256"] = write_archive(archive, scratch, saved["rows"])
        saved["own_replay"] = replay_archives(output, saved, sources, deadline)
        from poker_ai.evaluation.batch_current_report import write_report

        saved["report"] = write_report(root, saved, sources, output.parent / "report")
        deadline.check()
        saved["status"] = "completed_own_native_pending"
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        events = [
            e
            for w in saved["batch"].get("workers", [])
            for e in w["messages"]
            if e["kind"] == "cell"
        ]
        saved["completed_current_profiles"] = sum(
            e.get("phase") == "profile" for e in events
        )
        saved["completed_fixed_targets"] = sum(
            e.get("phase") == "fixed" for e in events
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


def validate_replay(proof: dict[str, Any]) -> None:
    fixed = dict(
        status="all216currents_and1728fixed_targets_replayed",
        current_profiles=216,
        fixed_targets=1728,
        training_performed=False,
        reference_constructed=False,
    )
    if (
        any(not same(proof[k], v) for k, v in fixed.items())
        or not number(proof["seconds"], nonnegative=True)
        or not number(proof["maximum_error_chips"], nonnegative=True)
        or proof["maximum_error_chips"] > 1e-9
    ):
        raise ArithmeticError("incomplete current diagnosis replay proof")


def read_saved(root: Path, path: Path) -> tuple[dict[str, Any], inputs.Sources]:
    from poker_ai.evaluation.batch_current_protocol import require_admission

    saved: dict[str, Any] = json.loads(path.read_text())
    check_source(root, saved["source"])
    if (
        saved["format"] != inputs.FORMAT
        or saved["scoring_requested"] is not True
        or not same(saved["completed_current_profiles"], 216)
        or not same(saved["completed_fixed_targets"], 1728)
        or saved["status"] != "completed_own_native_pending"
        or saved["failure"] is not None
        or not same(saved["config"], inputs.config_inputs(root))
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or not same(saved["reference"], inputs.config_inputs(root)["native_reference"])
        or not number(saved["seconds"], nonnegative=True)
        or saved["seconds"] >= 3600
        or any(
            saved[k] is not False
            for k in (
                "training_performed",
                "reference_constructed",
                "policies_modified",
                "new_agent_default",
                "fresh_global_admission",
            )
        )
    ):
        raise ArithmeticError("incomplete current diagnosis receipt")
    admission = require_admission(root, clean=False)
    if (
        not same(admission, saved["admission"])
        or saved["source_sha256"] != admission["source_sha256"]
    ):
        raise ArithmeticError("current diagnosis admission mismatch")
    sources = inputs.load(root)
    if not same(inputs.source_hashes(root, sources), saved["source_inputs"]):
        raise ArithmeticError("current diagnosis source bytes changed")
    rows, fixed = gather(saved["batch"], sources, saved["source_sha256"])
    if not same(rows, saved["rows"]) or not same(fixed, saved["fixed_matches"]):
        raise ArithmeticError("current diagnosis raw worker rows changed")
    validate_replay(saved["own_replay"])
    return saved, sources


def replay(
    root: Path, path: Path, deadline: Deadline | None = None
) -> tuple[dict[str, Any], inputs.Sources, dict[str, Any]]:
    saved, sources = read_saved(root, path)
    proof = replay_archives(path, saved, sources, deadline or Deadline(3600))
    validate_replay(proof)
    return saved, sources, proof
