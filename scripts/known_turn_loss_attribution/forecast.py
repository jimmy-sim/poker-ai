"""Data-only conservative admission for one four-policy saved replay."""

import json
import math
from pathlib import Path
from typing import Any

from known_turn_loss_attribution.plan import contract

WET_DIAGNOSIS = Path("results/known-wet-residual-diagnosis/diagnosis/job-state.json")
RECENCY_REPORT = Path("results/known-turn-regret-recency/report/job-state.json")


def forecast(root: Path) -> dict[str, Any]:
    """Double the sum of both pinned prior whole jobs, then add 120s."""
    plan = contract(root)
    old = json.loads((root / WET_DIAGNOSIS).read_bytes())
    recent = json.loads((root / RECENCY_REPORT).read_bytes())
    a = old["observed_wall_seconds"]
    b = recent["observed_wall_seconds"]
    bound = 2 * (a + b) + 120
    if (
        old["status"] != "passed"
        or old["cap_seconds"] != 900
        or recent["status"] != "passed"
        or recent["cap_seconds"] != 3600
        or not all(math.isfinite(x) and x > 0 for x in (a, b))
        or a != plan["prior_wet_diagnosis_wall_seconds"]
        or b != plan["prior_recency_report_wall_seconds"]
        or not math.isclose(bound, plan["forecast_bound_seconds"], abs_tol=1e-12)
    ):
        raise ArithmeticError("pinned prior whole-process clocks changed")
    return {
        "status": "admitted" if bound < 900 else "rejected",
        "prior_wet_diagnosis_seconds": a,
        "prior_recency_report_seconds": b,
        "strict_bound_seconds": bound,
        "hard_cap_seconds": 900,
        "rule": "2*(wet_diagnosis+recency_report)+120<900",
    }
