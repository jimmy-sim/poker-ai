"""Checked-source admission; later read-only replay permits added future modules."""

import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation.averaging_history_inputs import (
    CONFIG,
    ENTRIES,
    forecast,
    inputs,
    load,
)
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

FORMAT = "poker-ai-averaging-history-v1"
CORRECTNESS = "poker-ai-averaging-history-software-and-forecast-v1"
ADMISSION = "poker-ai-averaging-history-admission-v1"
LOCAL_CHECKS = dict.fromkeys(
    ("base_311", "base_312", "all_extras_311", "all_extras_312", "slow_integrations"),
    "passed",
)
CI_JOBS = {"Python 3.11": "success", "Python 3.12": "success"}


def source(root: Path) -> dict[str, Any]:
    return source_provenance(root, root / CONFIG, entrypoints=ENTRIES)


def require_prefix_runtime(config: dict[str, Any], environment: dict[str, Any]) -> None:
    if any(environment[k] != config["prefix_runtime"][k] for k in ("python", "numpy")):
        raise ArithmeticError(
            "use recorded prefix runtime; never loosen original fingerprints"
        )


def validate_replay(proof: dict[str, Any], config: dict[str, Any]) -> None:
    if not isinstance(proof, dict):
        raise ArithmeticError("missing averaging replay proof")
    if (
        proof["status"] != "all_averaging_history_profiles_and_windows_replayed"
        or proof["new_postflop_training_performed"] is not False
        or not number(proof["seconds"], nonnegative=True)
        or any(
            not same(proof[k], value)
            for k, value in dict(
                source_cases=64,
                profiles=512,
                cumulative_boundaries=192,
                suffix_reconstructions=128,
                whole_reconstructions=64,
                identical_current_pairs=160,
                fixed_opponent_target_conditions=2048,
            ).items()
        )
    ):
        raise ArithmeticError("incomplete or altered averaging replay proof")
    for key, limit in dict(
        maximum_error_chips=config["tolerance_chips"],
        maximum_error_unitless=config["tolerance_unitless"],
        maximum_fixed_identity_error_chips=config["tolerance_chips"],
    ).items():
        if not number(proof[key], nonnegative=True) or proof[key] > limit:
            raise ArithmeticError("averaging replay numerical proof failed")


def validate_correctness(saved: dict[str, Any], config: dict[str, Any]) -> None:
    toy = saved["software"]
    if not isinstance(toy, dict):
        raise ArithmeticError("missing averaging software proof")
    proof = toy["replay"]
    validate_replay(proof, config)
    if (
        saved["format"] != CORRECTNESS
        or saved["status"] != "completed_software_and_forecast_no_new_poker_learning"
        or saved["failure"] is not None
        or not same(saved["config"], config)
        or saved["new_postflop_training_performed"] is not False
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or toy["scope"] != "EXPLICIT_SOFTWARE_FIXTURE_NOT_POKER_RESULTS"
        or toy["status"] != "passed_software_roundtrip_no_new_poker_training"
        or toy["failure"] is not None
        or toy["new_postflop_training_performed"] is not False
        or not same(toy["original_prefix_checks"], 192)
        or not same(toy["fixed_opponent_targets"], 2048)
    ):
        raise ArithmeticError("incomplete/changed averaging software proof")
    forecast = saved["forecast"]
    if (
        forecast["decision"] != "fits_requires_checked_admission"
        or forecast["new_postflop_training_performed"] is not False
        or not same(forecast["source_cells"], 64)
        or len(forecast["historical_cell_rows"]) != 64
        or not number(forecast["guarded_own_seconds"], nonnegative=True)
        or not 0 < forecast["guarded_own_seconds"] < config["maximum_own_seconds"]
        or not same(forecast["cap_seconds"], config["maximum_own_seconds"])
    ):
        raise ArithmeticError("averaging historical compute gate does not fit")


def require_admission(
    root: Path, config: dict[str, Any], *, require_clean: bool = True
) -> dict[str, Any]:
    current = source(root)
    if require_clean and current["dirty"] is not False:
        raise ValueError(
            "publish checked averaging code and admission before poker replay"
        )
    path = root / config["correctness_receipt"]
    correctness = json.loads(path.read_text())
    admission: dict[str, Any] = json.loads(
        (root / config["admission_receipt"]).read_text()
    )
    check_source(root, correctness["source"])
    validate_correctness(correctness, config)
    if (
        (require_clean and not same(current["sha256"], correctness["source"]["sha256"]))
        or admission["format"] != ADMISSION
        or admission["status"] != "admitted_same_trajectories_diagnosis_only"
        or admission["correctness_sha256"] != digest(path)
        or admission["source_sha256"] != correctness["source_sha256"]
        or admission["checked_commit"] != correctness["source"]["git_commit"]
        or type(admission["ci_run"]) is not int
        or admission["ci_run"] <= 0
        or not same(admission["ci_jobs"], CI_JOBS)
        or not same(admission["local_checks"], LOCAL_CHECKS)
    ):
        raise ArithmeticError(
            "source-bound averaging local/CI admission missing or changed"
        )
    if not same(correctness["forecast"], forecast(load(root))):
        raise ArithmeticError(
            "averaging historical forecast does not replay from pinned inputs"
        )
    return admission


def record_admission(
    root: Path, ci: dict[str, Any], local: dict[str, Any]
) -> dict[str, Any]:
    """Record independently observed CI/local metadata; never fabricate a CI result.

    The caller supplies actual observed job/check metadata. This is an auditable
    research receipt, not authentication of user-supplied CI JSON. Its source/hash
    binding prevents checked receipts from silently admitting new implementation.
    """
    config = inputs(root)
    current = source(root)
    correctness_path = root / config["correctness_receipt"]
    correctness = json.loads(correctness_path.read_text())
    check_source(root, correctness["source"])
    validate_correctness(correctness, config)
    if (
        current["dirty"] is not False
        or not same(current["sha256"], correctness["source"]["sha256"])
        or ci["checked_commit"] != correctness["source"]["git_commit"]
        or ci["source_sha256"] != correctness["source_sha256"]
        or type(ci["run_id"]) is not int
        or ci["run_id"] <= 0
        or not same(ci["jobs"], CI_JOBS)
        or local["source_sha256"] != correctness["source_sha256"]
        or not same(local["checks"], LOCAL_CHECKS)
    ):
        raise ArithmeticError(
            "averaging observed checks do not bind checked correctness source"
        )
    if not same(correctness["forecast"], forecast(load(root))):
        raise ArithmeticError(
            "averaging forecast differs from complete historical source"
        )
    return dict(
        format=ADMISSION,
        status="admitted_same_trajectories_diagnosis_only",
        correctness_sha256=digest(correctness_path),
        source_sha256=correctness["source_sha256"],
        checked_commit=correctness["source"]["git_commit"],
        ci_run=ci["run_id"],
        ci_jobs=ci["jobs"],
        local_checks=local["checks"],
        scope=(
            "same original 10m trajectories only; "
            "no stronger/default/fresh/global admission"
        ),
        environment=runtime_environment(),
    )
