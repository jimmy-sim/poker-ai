"""Short real-prefix timings and full old-own overhead, never long-run admission."""

import json
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import matched_update_code_gate as gate
from poker_ai.evaluation import matched_update_inputs as inputs
from poker_ai.evaluation import matched_update_software as software
from poker_ai.evaluation.matched_update_forecast import forecast, job
from poker_ai.evaluation.matched_update_overhead import run as overhead
from poker_ai.evaluation.matched_update_run import source
from poker_ai.postflop.cell_process import run_batch
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.matched_updates import read as read_native

FOLDER = "results/matched-update-pipeline/"
SOFTWARE = FOLDER + "software-own.json"
SOFTWARE_NATIVE = FOLDER + "software-native.json"
PROFILE = FOLDER + "profile.json"
OVERHEAD = FOLDER + "overhead/own.json"
OVERHEAD_NATIVE = FOLDER + "overhead/native.json"


def software_proof(root: Path) -> dict[str, Any]:
    own_path = root / SOFTWARE
    own, _, proof = software.read(root, own_path)
    native = read_native(root, root / SOFTWARE_NATIVE, own_path, own)
    return dict(
        own_sha256=digest(own_path),
        native_sha256=digest(root / SOFTWARE_NATIVE),
        own_replay=proof,
        native=native,
        source_sha256=own["source_sha256"],
    )


def timings(saved: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        e["row"]
        for w in saved["batch"].get("workers", [])
        for e in w["messages"]
        if e["kind"] == "cell" and e["phase"] == "timing"
    ]


def run(root: Path, output: Path, overhead_path: Path) -> dict[str, Any]:
    if output.exists() or output.with_suffix(".tmp").exists():
        raise FileExistsError(
            "retain this complete/failed timing attempt; no favorable retry"
        )
    started = time.perf_counter()
    deadline = Deadline(900)
    deadline.started = started
    saved: dict[str, Any] = dict(
        status="running",
        failure=None,
        source=None,
        source_sha256=None,
        config=None,
        code_checks=None,
        software_proof=None,
        environment=runtime_environment(),
        batch={},
        timing_rows=[],
        forecast=None,
        overhead_file=None,
        overhead_sha256=None,
        overhead_seconds=None,
        prefix_training_requested=False,
        completed_prefix_timings=0,
        full_trajectory_study_performed=False,
        reference_constructed=False,
        long_run_admitted=False,
        seconds=0.0,
    )
    try:
        saved["source"] = source(root)
        saved["source_sha256"] = sha(saved["source"]["sha256"])
        persist(output, saved)
        if saved["source"]["dirty"] is not False:
            raise ArithmeticError("publish clean checked source before timing")
        saved["config"] = inputs.config_inputs(root)
        if any(
            saved["environment"][k] != saved["config"]["required_runtime"][k]
            for k in ("python", "numpy")
        ):
            raise ArithmeticError("real prefix timing requires original Python/NumPy")
        saved["code_checks"] = gate.require(root, clean=False)
        saved["software_proof"] = software_proof(root)
        if saved["software_proof"]["source_sha256"] != saved["source_sha256"]:
            raise ArithmeticError("timing source differs from completed tiny proof")
        sources = inputs.load(root)
        saved["source_inputs"] = sources.manifest["input_sha256"]
        saved["prefix_training_requested"] = True
        run_batch(
            24,
            3,
            job,
            dict(
                root=str(root), remaining_seconds=900 - (time.perf_counter() - started)
            ),
            deadline,
            saved["batch"],
        )
        saved["timing_rows"] = timings(saved)
        saved["forecast"] = forecast(
            saved["timing_rows"],
            sources.paths,
            [sources.original(i, 100000) for i in range(24)],
        )
        persist(output, saved)
        measured = overhead(root, overhead_path, deadline, saved["source"])
        saved["overhead_file"] = str(overhead_path.relative_to(output.parent))
        saved["overhead_sha256"] = digest(overhead_path)
        saved["overhead_seconds"] = measured["seconds"]
        deadline.check()
        saved["status"] = (
            "completed_own_profile_native_pending"
            if saved["forecast"]["strict_below7200"]
            else "completed_own_profile_failed_forecast_gate"
        )
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        saved["timing_rows"] = timings(saved)
        saved["completed_prefix_timings"] = len(saved["timing_rows"])
        saved["seconds"] = time.perf_counter() - started
        persist(output, saved)
    return saved


def read(root: Path, path: Path) -> tuple[dict[str, Any], inputs.Sources]:
    saved: dict[str, Any] = json.loads(path.read_text())
    check_source(root, saved["source"])
    if (
        saved["status"]
        not in (
            "completed_own_profile_native_pending",
            "completed_own_profile_failed_forecast_gate",
        )
        or saved["failure"] is not None
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["config"] != inputs.config_inputs(root)
        or any(
            saved[k] is not False
            for k in (
                "full_trajectory_study_performed",
                "reference_constructed",
                "long_run_admitted",
            )
        )
        or saved["prefix_training_requested"] is not True
        or type(saved["completed_prefix_timings"]) is not int
        or saved["completed_prefix_timings"] != 72
        or type(saved["seconds"]) not in (int, float)
        or not 0 <= saved["seconds"] < 900
        or saved["batch"]["status"] != "completed"
    ):
        raise ArithmeticError("incomplete/changed matched timing receipt")
    if (
        saved["code_checks"] != gate.require(root, clean=False)
        or compare(saved["software_proof"], software_proof(root)) > 1e-12
        or any(
            saved["environment"][k] != saved["config"]["required_runtime"][k]
            for k in ("python", "numpy")
        )
    ):
        raise ArithmeticError("timing source/proof/runtime changed")
    sources = inputs.load(root)
    if (
        not same(saved["timing_rows"], timings(saved))
        or not same(
            saved["forecast"],
            forecast(
                saved["timing_rows"],
                sources.paths,
                [sources.original(i, 100000) for i in range(24)],
            ),
        )
        or saved["source_inputs"] != sources.manifest["input_sha256"]
    ):
        raise ArithmeticError("timing work/projection/raw-row binding changed")
    if (
        not isinstance(saved["overhead_file"], str)
        or Path(saved["overhead_file"]).is_absolute()
        or ".." in Path(saved["overhead_file"]).parts
        or digest(path.parent / saved["overhead_file"]) != saved["overhead_sha256"]
        or type(saved["overhead_seconds"]) not in (int, float)
        or not 0 <= saved["overhead_seconds"] < 600
    ):
        raise ArithmeticError("complete old-policy overhead binding/cap changed")
    return saved, sources
