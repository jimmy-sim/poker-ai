"""Source-bound software/code checks, timing replay and long-study admission."""

import json
import math
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import frozen_batch_inputs as inputs
from poker_ai.evaluation.frozen_batch_math import proofs
from poker_ai.evaluation.frozen_batch_profile import forecast, gather
from poker_ai.evaluation.frozen_batch_software import parity
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest
from poker_ai.reproducibility import runtime_environment

FOLDER = "results/frozen-pass-batches/"
SOFTWARE = FOLDER + "correctness.json"
CHECKS = FOLDER + "code-checks.json"
TIMING = FOLDER + "profile.json"
ADMITTED = FOLDER + "admission.json"
LOCAL = dict.fromkeys(
    ("base_311", "base_312", "all_extras_311", "all_extras_312", "slow_integrations"),
    "passed",
)
JOBS = {"Python 3.11": "success", "Python 3.12": "success"}


def fresh_output(path: Path) -> None:
    if path.exists() or path.with_suffix(".tmp").exists():
        raise FileExistsError("retain original batch receipt attempt")


def run_correctness(root: Path, output: Path) -> dict[str, Any]:
    fresh_output(output)
    started = time.perf_counter()
    config = inputs.config_inputs(root)
    current, binding = inputs.binding(root)
    saved: dict[str, Any] = dict(
        format=inputs.CORRECTNESS,
        status="running",
        failure=None,
        config=config,
        source=current,
        source_sha256=binding,
        environment=runtime_environment(),
        math=[],
        parity=[],
        software=None,
        seconds=0.0,
        new_postflop_training_performed=False,
        scope="TOY_SOFTWARE_NOT_HOLDEM_STRENGTH",
    )
    persist(output, saved)
    try:
        saved["math"] = proofs()
        saved["parity"] = parity()
        from poker_ai.evaluation.frozen_batch_fixture import roundtrip
        from poker_ai.postflop.river_study import Deadline

        folder = (
            root
            / "results/runs"
            / ("frozen-batch-software-" + sha(str(output.resolve()))[:16])
        )
        software, _, path = roundtrip(folder, config, binding, Deadline(120))
        saved["software"] = dict(
            status=software["status"],
            scope=software["scope"],
            replay=software["own_replay"],
            original_prefix_checks=len(software["prefix_checks"]),
            receipt_sha256=digest(path),
            archive_sha256={
                k: software[k]
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
                for b in software["batches"]
            ],
        )
        saved["status"] = "passed_software_no_postflop_learning"
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
    check_source(root, saved["source"])
    if (
        saved["format"] != inputs.CORRECTNESS
        or saved["status"] != "passed_software_no_postflop_learning"
        or saved["failure"] is not None
        or not same(saved["config"], config)
        or saved["new_postflop_training_performed"] is not False
        or saved["scope"] != "TOY_SOFTWARE_NOT_HOLDEM_STRENGTH"
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or not number(saved["seconds"], nonnegative=True)
    ):
        raise ArithmeticError("incomplete or changed batch software proof")
    actual = proofs()
    if len(saved["math"]) != 4 or len(saved["parity"]) != 120:
        raise ArithmeticError("batch software grid incomplete")
    software = saved["software"]
    from poker_ai.evaluation.frozen_batch_fixture import SCOPE
    from poker_ai.evaluation.frozen_batch_run import validate_replay

    if (
        software["status"] != "passed_complete_toy_IO_no_postflop_learning"
        or software["scope"] != SCOPE
        or not same(software["original_prefix_checks"], 144)
        or not same(
            software["worker_completions"],
            [
                [dict(paths=8, profiles=48, masses=48, currents=24, prefix_checks=48)]
                * 3,
                [dict(paths=16, profiles=96, masses=96, currents=48, prefix_checks=0)]
                * 3,
            ],
        )
    ):
        raise ArithmeticError("incomplete complete-grid batch software exercise")
    validate_replay(software["replay"])
    for row, peer in zip(saved["math"], actual, strict=True):
        if set(row) != set(peer):
            raise ArithmeticError("batch math proof fields changed")
        for key, value in peer.items():
            if type(value) is float:
                if not number(row[key]) or abs(row[key] - value) > 1e-12:
                    raise ArithmeticError("batch math proof replay changed")
            elif not same(row[key], value):
                raise ArithmeticError("batch math proof identity changed")
    # Recompute independent dense/old parity in the reader's runtime. Historical
    # floating fingerprints are not asserted across NumPy/platform versions.
    for row, peer in zip(saved["parity"], parity(), strict=True):
        if set(row) != set(peer) or any(
            not same(row[k], peer[k]) for k in peer if k != "readout_sha256"
        ):
            raise ArithmeticError("batch parity proof identity changed")
        if set(row["readout_sha256"]) != {"uniform", "linear"} or any(
            not isinstance(h, str)
            or len(h) != 64
            or any(c not in "0123456789abcdef" for c in h)
            for h in row["readout_sha256"].values()
        ):
            raise ArithmeticError("invalid batch parity fingerprint")


def record_code_checks(
    root: Path, ci: dict[str, Any], local: dict[str, Any]
) -> dict[str, Any]:
    config = inputs.config_inputs(root)
    current, binding = inputs.binding(root)
    saved = json.loads((root / SOFTWARE).read_text())
    validate_correctness(root, saved, config)
    if (
        not same(current["sha256"], saved["source"]["sha256"])
        or ci["checked_commit"] != saved["source"]["git_commit"]
        or ci["source_sha256"] != binding
        or local["source_sha256"] != binding
        or type(ci["run_id"]) is not int
        or ci["run_id"] <= 0
        or not same(ci["jobs"], JOBS)
        or not same(local["checks"], LOCAL)
    ):
        raise ArithmeticError("observed batch code checks do not bind software source")
    return dict(
        format=inputs.ADMISSION + "-code-checks",
        status="checked_code_not_long_study_admission",
        correctness_sha256=digest(root / SOFTWARE),
        source_sha256=binding,
        checked_commit=saved["source"]["git_commit"],
        ci_run=ci["run_id"],
        ci_jobs=ci["jobs"],
        local_checks=local["checks"],
        scope="permits fixed216-row prefix timing only, no strength claim",
    )


def require_code_checks(
    root: Path, config: dict[str, Any], *, clean: bool = True
) -> dict[str, Any]:
    current = inputs.source(root)
    saved = json.loads((root / SOFTWARE).read_text())
    validate_correctness(root, saved, config)
    checked: dict[str, Any] = json.loads((root / CHECKS).read_text())
    if (
        (clean and current["dirty"] is not False)
        or (clean and not same(current["sha256"], saved["source"]["sha256"]))
        or checked["format"] != inputs.ADMISSION + "-code-checks"
        or checked["status"] != "checked_code_not_long_study_admission"
        or checked["correctness_sha256"] != digest(root / SOFTWARE)
        or checked["source_sha256"] != saved["source_sha256"]
        or checked["checked_commit"] != saved["source"]["git_commit"]
        or type(checked["ci_run"]) is not int
        or checked["ci_run"] <= 0
        or not same(checked["ci_jobs"], JOBS)
        or not same(checked["local_checks"], LOCAL)
    ):
        raise ArithmeticError("missing/changed checked batch source receipt")
    return checked


def read_profile(root: Path, path: Path) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads(path.read_text())
    config = inputs.config_inputs(root)
    check_source(root, saved["source"])
    if (
        saved["format"] != inputs.PROFILE
        or saved["status"] != "completed_timing_not_strength"
        or saved["failure"] is not None
        or not same(saved["config"], config)
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["new_postflop_training_performed"] is not True
        or saved["strength_scores_measured"] is not False
        or not number(saved["seconds"], nonnegative=True)
        or saved["seconds"] >= 900
    ):
        raise ArithmeticError("incomplete/changed batch timing receipt")
    rows = gather(saved["batch"], config)
    if not same(rows, saved["rows"]) or not same(
        forecast(rows, config), saved["forecast"]
    ):
        raise ArithmeticError("batch forecast does not replay from all timing rows")
    data = inputs.prerequisites(root)
    # Every recorded prefix identity is checked against the pinned own archive,
    # even if all three timing repetitions are tampered with consistently.
    for row in rows:
        context = data.base.context(row["path"])
        if row["initialization_visits"] != 2 * len(context.partition.player) or row[
            "last_iteration_visits"
        ] > 2 * row["path"]["batch_size"] * len(context.partition.player):
            raise ArithmeticError(
                "timing initialization/traversal work differs from frozen game"
            )
        if row["path"]["batch_size"] != 1:
            continue
        originals = inputs.prefix_map(data, row["path"])
        for weight, check in zip(inputs.WEIGHTS, row["prefix_checks"], strict=True):
            peer = originals[weight][100000]
            expected = dict(
                average_weight=weight,
                work_label=100000,
                original_id=peer["id"],
                policy_sha256=peer["receipt"]["policy_sha256"],
                **{
                    k: peer[k]
                    for k in (
                        "iteration",
                        "previous_work",
                        "total_work",
                        "last_iteration_visits",
                        "initialization_visits",
                        "state_sha256",
                    )
                },
            )
            if not same(check, expected):
                raise ArithmeticError(
                    "timing B1 prefix no longer matches original archive"
                )
    return saved


def record_admission(root: Path) -> dict[str, Any]:
    config = inputs.config_inputs(root)
    checked = require_code_checks(root, config)
    profile = read_profile(root, root / TIMING)
    current, binding = inputs.binding(root)
    if (
        not same(current["sha256"], profile["source"]["sha256"])
        or profile["source_sha256"] != checked["source_sha256"]
        or profile["forecast"]["decision"] != "fits_requires_checked_admission"
        or not 0 < profile["forecast"]["guarded_own_seconds"] < 7200
    ):
        raise ArithmeticError("batch compute gate fails; stop before long learning")
    return dict(
        format=inputs.ADMISSION,
        status="admitted_known_game_diagnostic_only",
        source_sha256=binding,
        code_checks_sha256=digest(root / CHECKS),
        correctness_sha256=digest(root / SOFTWARE),
        profile_sha256=digest(root / TIMING),
        guarded_own_seconds=profile["forecast"]["guarded_own_seconds"],
        checked_commit=checked["checked_commit"],
        ci_run=checked["ci_run"],
        scope="72fixed paths480profiles only, no default/fresh/global admission",
    )


def require_admission(root: Path, *, clean: bool = True) -> dict[str, Any]:
    config = inputs.config_inputs(root)
    checked = require_code_checks(root, config, clean=clean)
    profile = read_profile(root, root / TIMING)
    saved: dict[str, Any] = json.loads((root / ADMITTED).read_text())
    if (
        saved["format"] != inputs.ADMISSION
        or saved["status"] != "admitted_known_game_diagnostic_only"
        or saved["source_sha256"] != checked["source_sha256"]
        or saved["code_checks_sha256"] != digest(root / CHECKS)
        or saved["correctness_sha256"] != digest(root / SOFTWARE)
        or saved["profile_sha256"] != digest(root / TIMING)
        or saved["checked_commit"] != checked["checked_commit"]
        or not same(saved["ci_run"], checked["ci_run"])
        or not math.isclose(
            saved["guarded_own_seconds"],
            profile["forecast"]["guarded_own_seconds"],
            abs_tol=0,
            rel_tol=0,
        )
        or profile["forecast"]["decision"] != "fits_requires_checked_admission"
    ):
        raise ArithmeticError("batch long-study source/compute admission changed")
    return saved
