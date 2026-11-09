"""New source/IO proof and conditional admission; the old gate stays closed."""

import json
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import reduced_study_inputs as inputs
from poker_ai.evaluation.batch_reduction_run import replay as replay_reduction
from poker_ai.evaluation.frozen_batch_protocol import JOBS as JOBS
from poker_ai.evaluation.frozen_batch_protocol import LOCAL as LOCAL
from poker_ai.evaluation.frozen_batch_protocol import fresh_output as fresh_output
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment

SOFTWARE = inputs.SOFTWARE
CHECKS = inputs.CHECKS
ADMITTED = inputs.ADMITTED


def run_correctness(root: Path, output: Path) -> dict[str, Any]:
    fresh_output(output)
    started = time.perf_counter()
    config = inputs.config_inputs(root)
    current, binding = inputs.binding(root)
    saved: dict[str, Any] = dict(
        format=inputs.FORMAT + "-software",
        status="running",
        failure=None,
        config=config,
        protocol=inputs.protocol(root),
        source=current,
        source_sha256=binding,
        environment=runtime_environment(),
        software=None,
        seconds=0.0,
        new_postflop_training_performed=False,
        scope="TOY_SOFTWARE_NOT_HOLDEM_STRENGTH",
    )
    persist(output, saved)
    try:
        from poker_ai.evaluation.reduced_study_fixture import roundtrip

        folder = (
            root
            / "results/runs"
            / ("reduced-study-software-" + sha(str(output.resolve()))[:16])
        )
        result, _, path = roundtrip(folder, config, binding, Deadline(180))
        saved["software"] = dict(
            status=result["status"],
            scope=result["scope"],
            replay=result["own_replay"],
            prefix_checks=len(result["prefix_checks"]),
            receipt_sha256=digest(path),
            archive_sha256={
                k: result[k]
                for k in (
                    "details_sha256",
                    "mass_details_sha256",
                    "current_details_sha256",
                )
            },
            worker_completions=[
                [
                    e["summary"]
                    for w in b["workers"]
                    for e in w["messages"]
                    if e["kind"] == "done"
                ]
                for b in result["batches"]
            ],
        )
        saved["status"] = "passed_explicit_backend_toy_IO_no_postflop_learning"
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        saved["seconds"] = time.perf_counter() - started
        persist(output, saved)
    return saved


def validate_correctness(
    root: Path, saved: dict[str, Any], config: dict[str, Any]
) -> None:
    from poker_ai.evaluation.reduced_study_fixture import SCOPE
    from poker_ai.evaluation.reduced_study_run import validate_replay

    check_source(root, saved["source"])
    if (
        saved["format"] != inputs.FORMAT + "-software"
        or saved["status"] != "passed_explicit_backend_toy_IO_no_postflop_learning"
        or saved["failure"] is not None
        or not same(saved["config"], config)
        or not same(saved["protocol"], inputs.protocol(root))
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["new_postflop_training_performed"] is not False
        or saved["scope"] != "TOY_SOFTWARE_NOT_HOLDEM_STRENGTH"
        or not number(saved["seconds"], nonnegative=True)
        or saved["seconds"] >= 180
    ):
        raise ArithmeticError("incomplete changed reduced-study software proof")
    s = saved["software"]
    validate_replay(s["replay"])
    if (
        s["status"] != "passed_complete_toy_IO_no_postflop_learning"
        or s["scope"] != SCOPE
        or not same(s["prefix_checks"], 144)
        or not same(
            s["worker_completions"],
            [
                [dict(paths=8, profiles=48, masses=48, currents=24, prefix_checks=48)]
                * 3,
                [dict(paths=16, profiles=96, masses=96, currents=48, prefix_checks=0)]
                * 3,
            ],
        )
        or set(s["archive_sha256"])
        != {"details_sha256", "mass_details_sha256", "current_details_sha256"}
        or any(
            not isinstance(h, str)
            or len(h) != 64
            or any(c not in "0123456789abcdef" for c in h)
            for h in [s["receipt_sha256"], *s["archive_sha256"].values()]
        )
    ):
        raise ArithmeticError("incomplete reduced-study backend IO inventory")


def record_code_checks(
    root: Path, ci: dict[str, Any], local: dict[str, Any]
) -> dict[str, Any]:
    config = inputs.config_inputs(root)
    current, h = inputs.binding(root)
    proof = json.loads((root / SOFTWARE).read_text())
    validate_correctness(root, proof, config)
    if (
        proof["source_sha256"] != h
        or not same(proof["source"]["sha256"], current["sha256"])
        or ci["checked_commit"] != proof["source"]["git_commit"]
        or ci["source_sha256"] != h
        or local["source_sha256"] != h
        or type(ci["run_id"]) is not int
        or ci["run_id"] <= 0
        or not same(ci["jobs"], JOBS)
        or not same(local["checks"], LOCAL)
    ):
        raise ArithmeticError("observed study code checks do not bind tested source")
    return dict(
        format=inputs.FORMAT + "-checks",
        status="checked_code_not_long_admission",
        source_sha256=h,
        correctness_sha256=digest(root / SOFTWARE),
        checked_commit=ci["checked_commit"],
        ci_run=ci["run_id"],
        ci_jobs=ci["jobs"],
        local_checks=local["checks"],
    )


def require_code_checks(root: Path, *, clean: bool = True) -> dict[str, Any]:
    config = inputs.config_inputs(root)
    proof = json.loads((root / SOFTWARE).read_text())
    validate_correctness(root, proof, config)
    saved: dict[str, Any] = json.loads((root / CHECKS).read_text())
    current = inputs.source(root)
    if (
        saved["format"] != inputs.FORMAT + "-checks"
        or saved["status"] != "checked_code_not_long_admission"
        or saved["source_sha256"] != proof["source_sha256"]
        or saved["correctness_sha256"] != digest(root / SOFTWARE)
        or saved["checked_commit"] != proof["source"]["git_commit"]
        or type(saved["ci_run"]) is not int
        or saved["ci_run"] <= 0
        or not same(saved["ci_jobs"], JOBS)
        or not same(saved["local_checks"], LOCAL)
        or (
            clean
            and (
                current["dirty"] is not False
                or not same(current["sha256"], proof["source"]["sha256"])
            )
        )
    ):
        raise ArithmeticError("reduced-study checked source changed")
    return saved


def expected_admission(root: Path, *, clean: bool = True) -> dict[str, Any]:
    config = inputs.config_inputs(root)
    p = inputs.protocol(root)
    checked = require_code_checks(root, clean=clean)
    correct = replay_reduction(root, root / p["reduction_correctness"])
    profile = replay_reduction(root, root / p["reduction_profile"])
    if (
        correct["kind"] != "correctness"
        or profile["kind"] != "profile"
        or profile["forecast"]["decision"] != "fits_requires_checked_admission"
        or not 0 < profile["forecast"]["guarded_own_seconds"] < 7200
    ):
        raise ArithmeticError(
            "reduction compute gate absent or failed; no long learning"
        )
    # The earlier implementation files proven at all72 endpoints remain unchanged.
    check_source(root, profile["source"])
    files = [
        SOFTWARE,
        CHECKS,
        p["reduction_correctness"],
        p["reduction_profile"],
        p["reduction_code_checks"],
        p["reduction_config"],
        p["base_config"],
        inputs.CONFIG,
    ]
    return dict(
        format=inputs.FORMAT + "-admission",
        status="admitted_known_game_diagnostic_only",
        source_sha256=checked["source_sha256"],
        input_sha256={f: digest(root / f) for f in files},
        checked_commit=checked["checked_commit"],
        ci_run=checked["ci_run"],
        guarded_own_seconds=profile["forecast"]["guarded_own_seconds"],
        maximum_own_seconds=config["maximum_own_seconds"],
        maximum_native_seconds=config["maximum_native_seconds"],
        scope="72paths480profiles only; no stronger/default/fresh/global admission",
    )


def record_admission(root: Path) -> dict[str, Any]:
    return expected_admission(root)


def require_admission(root: Path, *, clean: bool = True) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads((root / ADMITTED).read_text())
    if not same(saved, expected_admission(root, clean=clean)):
        raise ArithmeticError("reduced-study admission changed")
    return saved
