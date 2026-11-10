"""Recompute source/whole-clock/forecast admission using own published evidence.

Admission permits only the prospective known-game trajectory study. It is not
agent/default/fresh/global admission or a statement of improved poker strength.
No learner or native calculator is constructed by these receipt checks.
"""

import json
import math
from pathlib import Path
from typing import Any

from poker_ai.evaluation import private_prefix_gates as gates
from poker_ai.evaluation.matched_update_lifecycle import child_path, measured
from poker_ai.evaluation.private_prefix_design import OLD, TOY
from poker_ai.evaluation.private_prefix_forecast import forecast
from poker_ai.evaluation.private_prefix_journal import validate as validate_journal
from poker_ai.evaluation.private_prefix_read import read
from poker_ai.evaluation.private_prefix_sources import FOLDER, source
from poker_ai.postflop.parallel_profile import finite, same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.solver_validation.matched_update_audit import published
from poker_ai.solver_validation.private_prefix import validate as validate_native

SOFTWARE = FOLDER + "software/own.json"
SOFTWARE_NATIVE = FOLDER + "software/native.json"
PROFILE = FOLDER + "profile.json"
OLD_OWN = FOLDER + "overhead/own.json"
OLD_NATIVE = FOLDER + "overhead/native.json"
ADMISSION = FOLDER + "admission.json"


def native_journal(path: Path, saved: dict[str, Any]) -> None:
    expected = (
        {0: saved["events"]}
        if saved["scope"] == TOY
        else {w["slot"]: w["messages"] for w in saved["batch"]["workers"]}
    )
    validate_journal(
        path.with_name(saved["journal_file"]),
        saved["journal"],
        saved["source_sha256"],
        expected,
    )


def bound_files(root: Path, paths: list[Path]) -> dict[str, str]:
    return {str(p.relative_to(root)): digest(p) for p in paths}


def require_software(root: Path) -> dict[str, Any]:
    checks = gates.require(root, clean=False)
    own_path, native_path = root / SOFTWARE, root / SOFTWARE_NATIVE
    a, b = (
        measured(root, own_path, "tiny_own"),
        measured(root, native_path, "tiny_native"),
    )
    own, _ = read(root, own_path, Deadline(180))
    native = json.loads(native_path.read_text())
    native_journal(native_path, native)
    check_source(root, native["source"])
    proof = validate_native(native, own, own_path)
    if (
        own["scope"] != TOY
        or proof["profiles"] != 1080
        or proof["fixed_targets"] != 2880
        or own["source_sha256"] != checks["source_sha256"]
        or native["source_sha256"] != checks["source_sha256"]
        or a["hostname"] != b["hostname"]
        or b["started_perf_counter"] < a["started_perf_counter"] + a["seconds"]
        or b["shared_seconds"] + 1e-6 < a["seconds"] + b["seconds"]
    ):
        raise ArithmeticError("complete single-clock source-bound tiny proof required")
    for name, h in own["report"].items():
        if digest(own_path.parent / "report" / name) != h:
            raise ArithmeticError("tiny whole-command report artifact changed")
    expected = {
        "self-points.csv",
        "self-groups.csv",
        "fixed-pairs.csv",
        "summary.json",
        "current.png",
        "uniform_average.png",
        "linear_average.png",
    }
    if set(own["report"]) != expected:
        raise ArithmeticError("tiny proof must include complete tables and all plots")
    files = [own_path, native_path, child_path(own_path), child_path(native_path)]
    files.extend(
        (
            own_path.with_name(own["journal_file"]),
            native_path.with_name(native["journal_file"]),
        )
    )
    files.extend(
        own_path.with_name(own[k + "_file"])
        for k in ("captures", "masses", "details", "baseline")
    )
    return dict(
        status="complete_tiny_software_only_not_real_admission",
        source_sha256=checks["source_sha256"],
        core_profiles=432,
        core_ledgers=288,
        core_fixed_targets=1152,
        baseline_profiles=648,
        baseline_fixed_targets=1728,
        shared_seconds=b["shared_seconds"],
        maximum_native_error_chips=proof["maximum_error_chips"],
        input_sha256=bound_files(root, files),
        long_run_admitted=False,
    )


def profile_screen(root: Path) -> dict[str, Any]:
    path = root / PROFILE
    raw: dict[str, Any] = json.loads(path.read_text())
    measurement = measured(root, path, "profile")
    checks = gates.require(root, clean=False)
    check_source(root, raw["source"])
    from poker_ai.evaluation.private_prefix_worker_checks import complete

    events = complete(raw["batch"], 144)
    validate_journal(
        path.with_name(raw["journal_file"]),
        raw["journal"],
        raw["source_sha256"],
        {w["slot"]: w["messages"] for w in raw["batch"]["workers"]},
    )
    if any(e["phase"] != "timing" for e in events) or not same(
        sorted((e["row"] for e in events), key=lambda r: (r["repeat"], r["index"])),
        raw["rows"],
    ):
        raise ArithmeticError("profile timing rows differ from raw fixed worker events")
    for e in events:
        if not same(e["index"], 48 * e["row"]["repeat"] + e["row"]["index"]):
            raise ArithmeticError("profiling event routed to wrong repeat/path")
    if (
        raw["status"] != "completed_profile_inputs_not_admission"
        or raw["failure"] is not None
        or raw["source_sha256"] != checks["source_sha256"]
        or raw["reference_constructed"] is not False
    ):
        raise ArithmeticError("complete current-source own profiling required")
    prediction = forecast(raw["rows"], raw["config"], raw["source_sha256"])
    if not same(prediction, raw["forecast"]):
        raise ArithmeticError("conservative complete forecast changed")
    assignments = prediction["assignments"]
    # Subtract only actual sequential warm/setup+sampling intervals per worker.
    # Everything else in the WHOLE profile command remains in the residual:
    # startup, source/proof reads, spawn/join, guard serialization, old432/288/1152
    # scoring/archive/replay/report, final writes and all other required setup.
    training_wall = max(
        math.fsum(
            r["setup_seconds"] + r["incremental_seconds"]
            for r in raw["rows"]
            if r["index"] in indices
        )
        for indices in assignments
    )
    overhead = measurement["seconds"] - training_wall
    if not finite(overhead) or overhead >= 600 or prediction["passes"] is not True:
        raise ArithmeticError("whole own profiling exceeds unchanged conservative gate")
    old_path = root / OLD_OWN
    if digest(old_path) != raw["old_own_sha256"]:
        raise ArithmeticError("complete old-policy overhead receipt changed")
    old = json.loads(old_path.read_text())
    if (
        old["scope"] != OLD
        or old["status"] != "completed_own_native_pending"
        or old["training_performed"] is not False
        or len(old["rows"]) != 432
        or len(old["masses"]) != 288
        or len(old["fixed_matches"]) != 1152
        or old["source_sha256"] != raw["source_sha256"]
    ):
        raise ArithmeticError("full old-policy overhead shape/source required")
    return dict(
        forecast=prediction,
        whole_profile_seconds=measurement["seconds"],
        actual_prefix_training_parallel_seconds=training_wall,
        all_nontraining_and_old_overhead_seconds=overhead,
        old_own_sha256=digest(old_path),
        long_run_admitted=False,
    )


def evidence(root: Path) -> dict[str, Any]:
    checks = gates.require(root, clean=False)
    software = require_software(root)
    profile = profile_screen(root)
    own_path, native_path = root / OLD_OWN, root / OLD_NATIVE
    measurement = measured(root, native_path, "timing_native")
    own, _ = read(root, own_path, Deadline(900))
    native = json.loads(native_path.read_text())
    native_journal(native_path, native)
    check_source(root, native["source"])
    proof = validate_native(native, own, own_path)
    if (
        own["scope"] != OLD
        or proof["profiles"] != 432
        or proof["fixed_targets"] != 1152
        or native["source_sha256"] != checks["source_sha256"]
        or not 2 * measurement["seconds"] < 900
    ):
        raise ArithmeticError("complete old native twice-elapsed forecast gate failed")
    files = [
        root / gates.CHECKS,
        root / PROFILE,
        child_path(root / PROFILE),
        own_path,
        native_path,
        child_path(native_path),
    ]
    files.extend(
        own_path.with_name(own[k + "_file"]) for k in ("captures", "masses", "details")
    )
    files.append(own_path.with_name(own["journal_file"]))
    profile_raw = json.loads((root / PROFILE).read_text())
    files.extend(
        (
            (root / PROFILE).with_name(profile_raw["journal_file"]),
            native_path.with_name(native["journal_file"]),
        )
    )
    inputs = {
        **software["input_sha256"],
        **own["input_sha256"],
        **bound_files(root, files),
    }
    return dict(
        format="poker-ai-private-prefix-admission-v1",
        status="checked_known_game_trajectory_admission_not_agent_strength",
        source=checks["source"],
        source_sha256=checks["source_sha256"],
        code_checks_sha256=digest(root / gates.CHECKS),
        software=software,
        profile=profile,
        native_complete_seconds=measurement["seconds"],
        maximum_old_native_error_chips=proof["maximum_error_chips"],
        input_sha256=inputs,
        long_run_admitted=True,
        new_agent_default=False,
        fresh_global_admission=False,
        candidate_strength_still_unmeasured=True,
    )


def record(root: Path) -> dict[str, Any]:
    gates.require(root, clean=True)
    return evidence(root)


def require(root: Path, *, clean: bool) -> dict[str, Any]:
    gates.require(root, clean=clean)
    path = root / ADMISSION
    saved: dict[str, Any] = json.loads(path.read_text())
    if not same(saved, evidence(root)):
        raise ArithmeticError("published private-prefix admission does not recompute")
    if source(root)["sha256"] != saved["source"]["sha256"]:
        raise ArithmeticError("current complete source differs from admitted inventory")
    published(root, path)
    return saved
