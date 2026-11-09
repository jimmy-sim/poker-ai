"""Deterministic raw-prefix and forecast exports; no scoring or learning."""

import json
from pathlib import Path
from typing import Any

from poker_ai.postflop.learning_report import write_csv
from poker_ai.postflop.river_study import digest


def write_report(saved: dict[str, Any], output: Path) -> dict[str, str]:
    output.mkdir(parents=True, exist_ok=True)
    points = []
    for row in saved["rows"]:
        points.append(
            dict(
                index=row["index"],
                **row["path"],
                repetition=row["repetition"],
                initialization_visits=row["initialization_visits"],
                total_work=row["total_work"],
                incremental_visits=row["incremental_visits"],
                iteration=row["iteration"],
                sampled_traversals=row["sampled_traversals"],
                setup_and_warm_seconds=row["setup_and_warm_seconds"],
                incremental_seconds=row["incremental_seconds"],
                cpu_seconds=row["cpu_seconds"],
                projected_training_seconds=row["projected_training_seconds"],
                guard_sha256=row["guard_sha256"],
                uniform_readout_sha256=row["readout_sha256"]["uniform"],
                linear_readout_sha256=row["readout_sha256"]["linear"],
            )
        )
    write_csv(output / "prefixes.csv", points)
    summary = dict(
        scope=saved["scope"],
        kind=saved["kind"],
        status=saved["status"],
        endpoints=len(points),
        seconds=saved["seconds"],
        forecast=saved["forecast"],
        strength_scores_measured=False,
        long_learning_admitted=False,
    )
    (output / "summary.json").write_text(
        json.dumps(summary, sort_keys=True, indent=2) + "\n"
    )
    return {n: digest(output / n) for n in ("prefixes.csv", "summary.json")}
