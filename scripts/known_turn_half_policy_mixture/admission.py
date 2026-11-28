"""Data-only strict compute admission; never load or score a parent policy."""

import json
import math
import os
import time
from pathlib import Path
from typing import Any

from known_turn_half_policy_mixture.gate import (
    clean_head,
    require_proof,
    source_fingerprint,
)
from known_turn_half_policy_mixture.plan import contract


def forecast(root: Path) -> dict[str, Any]:
    """Recompute both published 2×prior+reserve strict bounds in seconds."""
    data = contract(root)
    report = json.loads((root / data["prior_report_job_path"]).read_bytes())
    native = json.loads((root / data["prior_native_job_path"]).read_bytes())
    for record, expected in (
        (report, data["prior_report_seconds"]),
        (native, data["prior_native_seconds"]),
    ):
        if (
            record["status"] != "passed"
            or record["exit_code"] != 0
            or record["source_fingerprint"] != data["source_fingerprint"]
            or math.ceil(record["observed_wall_seconds"] * 1000) / 1000 != expected
        ):
            raise ArithmeticError("pinned prior timing or source changed")
    own = 2 * data["prior_report_seconds"] + data["failure_save_reserve_seconds"]
    reference = 2 * data["prior_native_seconds"] + data["failure_save_reserve_seconds"]
    if (
        own != data["forecast_seconds"]
        or reference != data["native_forecast_seconds"]
        or data["forecast_multiplier"] != 2
        or data["failure_save_reserve_seconds"] != 120
    ):
        raise ArithmeticError("preregistered compute forecast changed")
    return {
        "status": "admitted"
        if own < data["own_cap_seconds"] and reference < data["native_cap_seconds"]
        else "rejected",
        "own_forecast_seconds": own,
        "native_forecast_seconds": reference,
        "own_cap_seconds": data["own_cap_seconds"],
        "native_cap_seconds": data["native_cap_seconds"],
        "rule": "strict 2*ceil(prior_wall_ms)/1000+120<900 separately",
    }


def run(root: Path, output: Path) -> None:
    """Publish one data-only admission with retained failure if a bound fails."""
    started = time.perf_counter()
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_proof(root, fingerprint)
    if output.exists():
        raise FileExistsError("retain prior half-mixture admission")
    output.mkdir(parents=True)
    decision = forecast(root)
    with (output / "decision.json").open("x") as stream:
        json.dump(decision, stream, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    with (output / "job-state.json").open("x") as stream:
        json.dump(
            {
                "status": decision["status"],
                "head": head,
                "source_fingerprint": fingerprint,
                "seconds": time.perf_counter() - started,
                "data_only": True,
            },
            stream,
            indent=2,
            sort_keys=True,
        )
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    if decision["status"] != "admitted":
        raise ArithmeticError("half-mixture strict compute forecast rejected")
