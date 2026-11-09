"""Source-bound software proofs and historical forecast, never new poker training."""

import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import averaging_history_protocol as protocol
from poker_ai.evaluation.averaging_history_inputs import forecast, inputs, load
from poker_ai.evaluation.averaging_history_replay import replay_archives
from poker_ai.evaluation.averaging_history_software import (
    software_controls,
    software_inputs,
    software_job,
)
from poker_ai.evaluation.averaging_history_validation import gather
from poker_ai.postflop.cell_process import run_batch
from poker_ai.postflop.learning_artifacts import sha, write_archive
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment


def software_roundtrip(
    config: dict[str, Any], folder: Path, binding: str, deadline: Deadline
) -> dict[str, Any]:
    """Run all three actual processes on clearly labeled tiny toy trajectories.

    Retain complete/partial files and worker events on failure. This exercise uses
    nonuniform Kuhn, not the known Hold'em spots. It cannot establish poker strength.
    """
    import json

    if folder.exists():
        raise FileExistsError("retain complete/partial averaging software fixture")
    folder.mkdir(parents=True)
    started = time.perf_counter()
    batch: dict[str, Any] = {}
    result: dict[str, Any] = dict(
        scope="EXPLICIT_SOFTWARE_FIXTURE_NOT_POKER_RESULTS",
        status="running",
        failure=None,
        batch=batch,
        new_postflop_training_performed=False,
    )
    try:
        data = software_inputs(config, deadline)
        software_controls(folder, data)
        scratch = folder / "scratch"
        cells = [
            dict(
                case=p.case,
                source_id=p.identifier,
                prefixes={
                    t: data.prefixes[p.identifier, t]
                    for t in data.config["original_average_replay_labels"]
                },
            )
            for p in data.base.policies
        ]
        payload = dict(
            config=data.config,
            cells=cells,
            scratch=str(scratch),
            binding=binding,
            remaining_seconds=deadline.seconds
            - (time.perf_counter() - deadline.started),
        )
        run_batch(64, 3, software_job, payload, deadline, batch)
        rows, masses = gather(batch, data, binding)
        path = folder / "own.json"
        saved: dict[str, Any] = dict(
            scope="EXPLICIT_SOFTWARE_FIXTURE_NOT_POKER_RESULTS",
            rows=rows,
            masses=masses,
            source_sha256=binding,
            details_file="own-profiles.jsonl.gz",
            mass_details_file="own-masses.jsonl.gz",
        )
        saved["details_sha256"] = write_archive(
            folder / saved["details_file"], scratch, rows
        )
        saved["mass_details_sha256"] = write_archive(
            folder / saved["mass_details_file"], scratch, masses
        )
        path.write_text(
            json.dumps(saved, sort_keys=True, indent=2, allow_nan=False) + "\n"
        )
        proof, matches = replay_archives(folder, path, saved, data, deadline)
        result.update(
            status="passed_software_roundtrip_no_new_poker_training",
            original_prefix_checks=192,
            replay=proof,
            fixed_opponent_targets=len(matches),
            profile_archive_sha256=saved["details_sha256"],
            mass_archive_sha256=saved["mass_details_sha256"],
        )
    except BaseException as error:
        result.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        result["seconds"] = time.perf_counter() - started
        (folder / "software.json").write_text(
            json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
        )
    return result


def run(root: Path, output: Path) -> dict[str, Any]:
    """Only toy steps and old timing arithmetic; no new Hold'em trajectory replay."""
    if output.exists() or output.with_suffix(".tmp").exists():
        raise FileExistsError("retain averaging correctness/forecast attempt")
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    config = inputs(root)
    source = protocol.source(root)
    if source["dirty"] is not False:
        raise ValueError(
            "publish checked averaging source before recording admission proof"
        )
    binding = sha(source["sha256"])
    scratch = (
        root
        / "results/runs"
        / ("averaging-software-" + sha(str(output.resolve()))[:12])
    )
    saved: dict[str, Any] = dict(
        format=protocol.CORRECTNESS,
        status="running",
        failure=None,
        config=config,
        source=source,
        source_sha256=binding,
        environment=runtime_environment(),
        software=None,
        forecast=None,
        software_folder=str(scratch),
        software_receipt_sha256=None,
        new_postflop_training_performed=False,
        seconds=0.0,
    )
    persist(output, saved)
    try:
        toy = software_roundtrip(config, scratch, binding, Deadline(120))
        saved["software"] = {k: v for k, v in toy.items() if k != "batch"}
        saved["software"]["worker_summaries"] = [
            dict(
                slot=w["slot"],
                exitcode=w["exitcode"],
                done=[e for e in w["messages"] if e["kind"] == "done"],
            )
            for w in toy["batch"]["workers"]
        ]
        saved["software_receipt_sha256"] = digest(scratch / "software.json")
        saved["forecast"] = forecast(load(root))
        saved["status"] = "completed_software_and_forecast_no_new_poker_learning"
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
