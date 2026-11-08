"""Immutable experiment inputs and explicit software/CI admission receipts."""

import json
from pathlib import Path
from typing import Any

from poker_ai.postflop import controlled_profile
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import endpoint_reference, same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.training_isolation import check_inputs
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/controlled-learning-comparison.json"
ENTRIES = (
    "scripts/compare_controlled_learning.py",
    "scripts/audit_controlled_learning.py",
    "scripts/report_controlled_learning.py",
)
FORMAT = "poker-ai-controlled-learning-comparison-v1"
CORRECTNESS = "poker-ai-controlled-learning-correctness-v1"
ADMISSION = "poker-ai-controlled-learning-admission-v1"


def source(root: Path) -> dict[str, Any]:
    return source_provenance(root, root / CONFIG, entrypoints=ENTRIES)


def inputs(root: Path) -> tuple[dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    config = json.loads((root / CONFIG).read_text())
    fixed = dict(
        schema_version=1,
        status="preregistered_diagnostic_learning_only",
        worker_count=3,
        start_method="spawn",
        maximum_own_seconds=7200,
        maximum_native_seconds=3600,
        tolerance_chips=1e-9,
        expected_cells=140,
        expected_logical_checkpoints=840,
        comparison_config="configs/training-isolation.json",
        pipeline_summary="results/controlled-pipeline-check/report/summary.json",
        correctness_receipt="results/controlled-learning/correctness.json",
        admission_receipt="results/controlled-learning/admission.json",
        checkpoint_labels=dict(
            work=[100000, 1000000, 10000000], iteration=[16, 64, 128]
        ),
    )
    if (
        any(not same(config[k], v) for k, v in fixed.items())
        or any(digest(root / p) != value for p, value in config["input_sha256"].items())
        or len(config["input_sha256"]) != 6
    ):
        raise ArithmeticError("controlled learning protocol/prerequisite changed")
    for path in (
        "configs/controlled-pipeline-check.json",
        "configs/parallel-cell-profile.json",
    ):
        bound = json.loads((root / path).read_text())
        if any(digest(root / p) != value for p, value in bound["input_sha256"].items()):
            raise ArithmeticError("controlled prerequisite chain changed")
    for path in (
        "results/controlled-pipeline-check/own.json",
        "results/controlled-pipeline-check/native.json",
    ):
        check_source(root, json.loads((root / path).read_text())["source"])
    protocol = json.loads((root / config["comparison_config"]).read_text())
    check_inputs(root, protocol)
    comparison = protocol["future_comparison"]
    if not same(
        config["checkpoint_labels"],
        dict(
            work=comparison["node_work_checkpoints"],
            iteration=comparison["iteration_checkpoints"],
        ),
    ):
        raise ArithmeticError("original learning checkpoints changed")
    forecast = json.loads((root / config["pipeline_summary"]).read_text())
    if (
        forecast["decision"]
        != "forecasts_fit_requires_separate_checked_learning_runner"
    ):
        raise ArithmeticError("measured pipeline does not fit")
    cells = controlled_profile.cells(comparison)
    if len(cells) != 140:
        raise ArithmeticError("original learning grid changed")
    return config, comparison, cells


def prefixes(root: Path, cells: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    profile = json.loads(
        (root / "results/cached-node-profile/profile.json").read_text()
    )
    check_source(root, profile["source"])
    result = endpoint_reference(profile)
    if set(result) != {controlled_profile.identity(c) for c in cells} or len(
        result
    ) != len(cells):
        raise ArithmeticError("pinned serial prefix inventory changed")
    return result


def require_admission(
    root: Path, config: dict[str, Any], *, require_clean: bool = True
) -> dict[str, Any]:
    """Require recorded source-bound local/hosted checks before learning."""
    current = source(root)
    if require_clean and current["dirty"] is not False:
        raise ValueError("publish checked source/receipts before learning")
    correctness_path = root / config["correctness_receipt"]
    correctness = json.loads(correctness_path.read_text())
    admission: dict[str, Any] = json.loads(
        (root / config["admission_receipt"]).read_text()
    )
    check_source(root, correctness["source"])
    if (
        correctness["format"] != CORRECTNESS
        or correctness["status"] != "passed_toy_correctness_no_postflop_learning"
        or (
            require_clean
            and not same(correctness["source"]["sha256"], current["sha256"])
        )
        or admission["format"] != ADMISSION
        or admission["status"] != "admitted_original_diagnostic_only"
        or admission["correctness_sha256"] != digest(correctness_path)
        or admission["checked_commit"] != correctness["source"]["git_commit"]
        or admission["source_sha256"] != sha(correctness["source"]["sha256"])
        or type(admission["ci_run"]) is not int
        or admission["ci_run"] <= 0
        or not same(
            admission["ci_jobs"], {"Python 3.11": "success", "Python 3.12": "success"}
        )
        or not same(
            admission["local_checks"],
            {
                "base_311": "passed",
                "base_312": "passed",
                "all_extras_311": "passed",
                "all_extras_312": "passed",
                "slow_integrations": "passed",
            },
        )
    ):
        raise ArithmeticError(
            "source-bound correctness/local/CI admission missing or changed"
        )
    return admission


def pots(root: Path, comparison: dict[str, Any]) -> dict[str, float]:
    from poker_ai.postflop.game import load_spot

    return {
        game: float(load_spot(root / game).pot) for game in comparison["spot_files"]
    }


def read_own(root: Path, path: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    from poker_ai.postflop.learning_training import validate_grid

    saved = json.loads(path.read_text())
    config, comparison, cells = inputs(root)
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed_own_native_pending"
        or saved["failure"] is not None
        or not same(config, saved["config"])
        or not number(saved["seconds"], nonnegative=True)
        or saved["seconds"] >= config["maximum_own_seconds"]
        or saved["reference_output_used_in_training"] is not False
        or saved["training_performed"] is not True
    ):
        raise ArithmeticError("incomplete/changed controlled learning header")
    check_source(root, saved["source"])
    if sha(saved["source"]["sha256"]) != saved["source_sha256"]:
        raise ArithmeticError("controlled source binding changed")
    admission = require_admission(root, config, require_clean=False)
    if (
        not same(admission, saved["admission"])
        or saved["source_sha256"] != admission["source_sha256"]
    ):
        raise ArithmeticError("controlled admission receipt changed")
    from poker_ai.postflop.cell_process import THREAD_ENV, partition

    if not same(saved["batch"]["assignments"], partition(140, 3)):
        raise ArithmeticError("controlled fixed worker assignments changed")
    expected_prefix = prefixes(root, cells)
    for worker in saved["batch"]["workers"]:
        started = [e for e in worker["messages"] if e["kind"] == "started"]
        if len(started) != 1 or not same(started[0]["thread_environment"], THREAD_ENV):
            raise ArithmeticError("controlled worker environment changed")
        for event in worker["messages"]:
            if event["kind"] == "cell" and event["phase"] == "prefix":
                peer = expected_prefix[
                    controlled_profile.identity(cells[event["index"]])
                ]
                if (
                    event["iteration"] != peer["iterations"]
                    or event["work"] != peer["total_visits"]
                    or event["state_sha256"] != peer["state_sha256"]
                ):
                    raise ArithmeticError("saved serial prefix changed")
    rows = validate_grid(saved["batch"], cells, config["checkpoint_labels"])
    if not same(rows, saved["rows"]) or sum(len(r["labels"]) for r in rows) != 840:
        raise ArithmeticError("controlled saved row inventory changed")
    if any(r["source_sha256"] != saved["source_sha256"] for r in rows):
        raise ArithmeticError("controlled row source binding changed")
    return saved, comparison
