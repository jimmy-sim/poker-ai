"""Data-only conservative forecast from a pinned historical report clock."""

import json
import math
from pathlib import Path
from typing import Any

from known_turn_half_policy_mixture.plan import contract as prior_contract

from known_mixture_residual_map.plan import contract, digest

PRIOR_JOB = Path("results/known-turn-collision-medium-transfer/report/job-state.json")


def forecast(root: Path) -> dict[str, Any]:
    """Reject any bound equal to or above the frozen whole-process cap."""
    data = contract(root)
    previous = prior_contract(root)
    if (
        previous["prior_report_job_path"] != PRIOR_JOB.as_posix()
        or digest(root / PRIOR_JOB) != previous["prior_report_job_sha256"]
    ):
        raise ArithmeticError("published prior report clock changed")
    prior: dict[str, Any] = json.loads((root / PRIOR_JOB).read_bytes())
    actual = prior["observed_wall_seconds"]
    rounded = math.ceil(actual * 1000) / 1000
    seconds = (
        data["forecast_multiplier"] * rounded + data["failure_save_reserve_seconds"]
    )
    if (
        prior["status"] != "passed"
        or rounded != data["prior_report_seconds_rounded_up"]
        or seconds != data["forecast_seconds"]
    ):
        raise ArithmeticError("historical report clock or forecast changed")
    return {
        "status": "admitted" if seconds < data["own_cap_seconds"] else "rejected",
        "prior_report_seconds_rounded_up": rounded,
        "forecast_seconds": seconds,
        "own_cap_seconds": data["own_cap_seconds"],
        "reserve_within_cap_seconds": data["failure_save_reserve_seconds"],
    }
