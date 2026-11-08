"""Typed, finite checkpoint contracts; scientific gains are never repaired/clipped."""

import math
import re
from typing import Any

from poker_ai.postflop.pipeline_cost import METRICS


def number(value: Any, *, nonnegative: bool = False) -> bool:
    return (
        type(value) in (int, float)
        and math.isfinite(value)
        and (not nonnegative or value >= 0)
    )


def validate_row(row: dict[str, Any]) -> None:
    counts = (
        "index",
        "iteration",
        "previous_work",
        "total_work",
        "last_iteration_visits",
        "initialization_visits",
        "tree_nodes",
        "information_sets",
        "padded_width",
    )
    if (
        any(type(row[k]) is not int or row[k] < 0 for k in counts)
        or not row["iteration"]
    ):
        raise ArithmeticError("invalid controlled checkpoint counts")
    expected_id = f"cell-{row['index']:03d}-iteration-{row['iteration']}"
    if row["id"] != expected_id or row["file"] != f"snapshots/{expected_id}.json.gz":
        raise ArithmeticError("controlled snapshot path/identity changed")
    metrics = row["metrics"]
    if (
        set(metrics) != set(METRICS)
        or any(not number(v) for v in metrics.values())
        or any(metrics[k] < -1e-9 for k in METRICS[:-1])
        or abs(metrics[METRICS[0]] - metrics[METRICS[1]] - metrics[METRICS[2]]) > 1e-9
    ):
        raise ArithmeticError("nonfinite or inconsistent controlled metrics")
    if (
        not number(row["maximum_accounting_error"], nonnegative=True)
        or row["maximum_accounting_error"] > 1e-9
    ):
        raise ArithmeticError("invalid controlled root accounting")
    d = row["diagnostics"]
    if (
        not number(d["regret_norm"], nonnegative=True)
        or not number(d["positive_average_coverage"], nonnegative=True)
        or d["positive_average_coverage"] > 1
        or any(
            type(d[k]) is not int or d[k] < 0
            for k in ("river_partition_rows", "river_partition_rows_visited")
        )
        or d["river_partition_rows_visited"] > d["river_partition_rows"]
    ):
        raise ArithmeticError("invalid controlled coverage/norm")
    n, visited = d["river_partition_rows"], d["river_partition_rows_visited"]
    if (
        d["river_visit_coverage"] is not None
        if n == 0
        else not number(d["river_visit_coverage"], nonnegative=True)
        or abs(d["river_visit_coverage"] - visited / n) > 1e-12
    ):
        raise ArithmeticError("controlled river coverage denominator changed")
    initial = (
        0
        if row["case"]["bridge"] == "cold_target_history_mass"
        else 2 * row["tree_nodes"]
    )
    if row["initialization_visits"] != initial or row["last_iteration_visits"] <= 0:
        raise ArithmeticError("controlled initialization work changed")
    if (
        row["case"]["traversal"] == "full"
        and row["total_work"] != 2 * row["tree_nodes"] * row["iteration"]
    ):
        raise ArithmeticError("full traversal work changed")
    for k in (
        "seconds",
        "cpu_seconds",
        "initialization_seconds",
        "elapsed_cell_seconds",
    ):
        if not number(row[k], nonnegative=True):
            raise ArithmeticError("invalid controlled timing")
    receipts = row["receipt"]
    hashes = [
        row["metadata_sha256"],
        row["source_sha256"],
        row["state_sha256"],
        receipts["sha256"],
        receipts["policy_sha256"],
    ]
    replies = row["reply_sha256"]
    if len(replies) != 2 or any(
        set(r) != {"exact", "restricted", "river_before"} for r in replies
    ):
        raise ArithmeticError("controlled own-reply fingerprint inventory changed")
    hashes.extend(v for r in replies for v in r.values())
    if any(
        type(v) is not str or re.fullmatch("[0-9a-f]{64}", v) is None for v in hashes
    ):
        raise ArithmeticError("invalid controlled hash")
    if type(receipts["bytes"]) is not int or receipts["bytes"] <= 0:
        raise ArithmeticError("invalid own snapshot size")
    for axis, target in row["labels"]:
        if axis not in ("work", "iteration") or type(target) is not int or target <= 0:
            raise ArithmeticError("invalid controlled checkpoint label")
