"""Explicit synthetic timings: complete inventories, max/partition formula and gates."""

import copy
from typing import Any

import pytest

from poker_ai.evaluation.matched_update_forecast import forecast


def fixture(
    projection: float = 100.0,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    paths = [dict(EXPLICIT_SYNTHETIC_CONTEXT=i) for i in range(24)]
    expected = [
        dict(path_index=i, work_label=100000, EXPLICIT_SYNTHETIC_CHECK=True)
        for i in range(24)
    ]
    rows = []
    for i in range(24):
        for repeat in range(3):
            elapsed = (projection - 1.0) * 100000 / 9999900
            projected = 1.0 + elapsed * 9999900 / 100000
            rows.append(
                dict(
                    path_index=i,
                    path=paths[i],
                    repetition=repeat,
                    initialization_visits=100,
                    incremental_visits=100000,
                    total_work=100100,
                    iteration=101,
                    guard_sha256="a" * 64,
                    readout_sha256=dict(uniform="b" * 64, linear="c" * 64),
                    original_checkpoint=expected[i],
                    setup_and_warm_seconds=1.0,
                    incremental_seconds=elapsed,
                    projected_training_seconds=projected,
                    cpu_seconds=0.01,
                )
            )
    return rows, paths, expected


def test_complete_max_context_fixed_partition_and_original_formula() -> None:
    rows, paths, expected = fixture()
    # The slowest third repeat is deliberately in the middle worker, last case.
    slow = next(r for r in rows if (r["path_index"], r["repetition"]) == (22, 2))
    slow["incremental_seconds"] *= 2
    slow["projected_training_seconds"] = (
        slow["setup_and_warm_seconds"] + slow["incremental_seconds"] * 9999900 / 100000
    )
    proof = forecast(rows, paths, expected)
    maxima = [
        max(r["projected_training_seconds"] for r in rows if r["path_index"] == i)
        for i in range(24)
    ]
    assert proof["context_maxima_seconds"] == maxima
    assert proof["worker_partition_seconds"] == [
        sum(maxima[i] for i in range(slot, 24, 3)) for slot in range(3)
    ]
    assert proof["training_forecast_seconds"] == max(proof["worker_partition_seconds"])
    assert proof["guarded_own_seconds"] == 2 * (
        2 * proof["training_forecast_seconds"] + 600
    )
    assert proof["strict_below7200"] is True
    assert proof["strength_results"] is False
    assert proof["causal_speedup_claim"] is False


def test_strict_cap_boundary_is_failure_without_rounding_or_relaxation() -> None:
    rows, paths, expected = fixture(187.5)
    proof = forecast(rows, paths, expected)
    assert proof["training_forecast_seconds"] == 1500
    assert proof["guarded_own_seconds"] == 7200
    assert proof["strict_below7200"] is False


@pytest.mark.parametrize(
    "kind",
    [
        "missing",
        "duplicate",
        "subset",
        "bool_index",
        "bool_repeat",
        "context",
        "source_checkpoint",
        "zero_time",
        "nan_time",
        "changed_projection",
        "changed_guard",
        "changed_readout",
        "changed_work",
        "warm_too_large",
        "increment_too_short",
    ],
)
def test_incomplete_corrupt_or_nonfinite_timings_rejected(kind: str) -> None:
    rows, paths, expected = fixture()
    if kind == "missing":
        rows.pop()
    elif kind == "duplicate":
        rows[-1] = copy.deepcopy(rows[0])
    elif kind == "subset":
        paths.pop()
    elif kind == "bool_index":
        rows[0]["path_index"] = True
    elif kind == "bool_repeat":
        rows[0]["repetition"] = True
    elif kind == "context":
        rows[0]["path"] = dict(EXPLICIT_SYNTHETIC_CONTEXT=23)
    elif kind == "source_checkpoint":
        rows[0]["original_checkpoint"] = dict(path_index=23)
    elif kind == "zero_time":
        rows[0]["incremental_seconds"] = 0.0
    elif kind == "nan_time":
        rows[0]["incremental_seconds"] = float("nan")
    elif kind == "changed_projection":
        rows[0]["projected_training_seconds"] += 1
    elif kind == "changed_guard":
        rows[0]["guard_sha256"] = "f" * 64
    elif kind == "changed_readout":
        rows[0]["readout_sha256"]["linear"] = "f" * 64
    elif kind == "changed_work":
        rows[0]["total_work"] += 1
    elif kind == "warm_too_large":
        rows[0]["initialization_visits"] = 100000
    else:
        rows[0]["incremental_visits"] = 99999
    with pytest.raises(ArithmeticError):
        forecast(rows, paths, expected)
