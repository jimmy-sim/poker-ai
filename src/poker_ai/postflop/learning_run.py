"""Bounded original 140-cell own training, immutable artifacts and report IO."""

import json
import os
import time
from pathlib import Path
from typing import Any

from poker_ai.postflop import learning_protocol as protocol
from poker_ai.postflop.cell_process import run_batch
from poker_ai.postflop.learning_artifacts import sha, write_archive
from poker_ai.postflop.learning_report import write_report
from poker_ai.postflop.learning_training import own_job, validate_grid
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment


def persist(path: Path, saved: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(saved, sort_keys=True, indent=2, allow_nan=False) + "\n"
    )
    temporary.replace(path)


def run(root: Path, output: Path) -> dict[str, Any]:
    if output.exists() or output.with_suffix(".tmp").exists():
        raise FileExistsError("retain original controlled learning receipt")
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    config, comparison, cells = protocol.inputs(root)
    deadline = Deadline(config["maximum_own_seconds"])
    deadline.started = started
    admission = protocol.require_admission(root, config)
    source = protocol.source(root)
    prefix = protocol.prefixes(root, cells)
    scratch = root / "results/runs/controlled-learning" / str(time.time_ns())
    scratch.mkdir(parents=True, exist_ok=False)
    saved: dict[str, Any] = dict(
        format=protocol.FORMAT,
        status="running",
        failure=None,
        config=config,
        source=source,
        source_sha256=sha(source["sha256"]),
        admission=admission,
        environment=runtime_environment(),
        scratch=str(scratch),
        batch={},
        rows=[],
        seconds=0.0,
        details_file=None,
        details_sha256=None,
        reference_output_used_in_training=False,
        training_performed=True,
    )
    persist(output, saved)
    try:
        run_batch(
            140,
            3,
            own_job,
            dict(
                root=str(root),
                comparison=comparison,
                cells=cells,
                remaining_seconds=config["maximum_own_seconds"]
                - (time.perf_counter() - started),
                scratch=str(scratch),
                labels=config["checkpoint_labels"],
                source_sha256=saved["source_sha256"],
                prefixes=prefix,
                tolerance=config["tolerance_chips"],
            ),
            deadline,
            saved["batch"],
        )
        saved["rows"] = validate_grid(
            saved["batch"], cells, config["checkpoint_labels"]
        )
        if sum(len(r["labels"]) for r in saved["rows"]) != 840:
            raise ArithmeticError(
                "controlled comparison lacks all 840 logical checkpoints"
            )
        deadline.check()
        bundle = output.with_name(output.stem + "-profiles.jsonl.gz")
        saved["details_sha256"] = write_archive(bundle, scratch, saved["rows"])
        saved["details_file"] = bundle.name
        deadline.check()
        write_report(
            saved, comparison, protocol.pots(root, comparison), output.parent / "report"
        )
        deadline.check()
        saved["status"] = "completed_own_native_pending"
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
