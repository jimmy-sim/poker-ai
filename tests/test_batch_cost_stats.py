"""Real cProfile recursion/caller format plus strict malformed-ledger rejection."""

import copy
import cProfile
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.batch_cost_stats import extract, filename, validate

ROOT = Path(__file__).resolve().parents[1]


def recursive(depth: int) -> int:
    return recursive(depth - 1) + 1 if depth else 0


def real_stats() -> dict[str, Any]:
    profiler = cProfile.Profile()
    profiler.runcall(recursive, 3)
    return extract(profiler, ROOT)


def test_recursive_function_and_caller_count_orders_are_distinct() -> None:
    stats = real_stats()
    frame = next(f for f in stats["functions"] if f["name"] == "recursive")
    edge = next(
        c
        for c in stats["callers"]
        if c["caller"] == frame["id"] and c["callee"] == frame["id"]
    )
    assert (frame["primitive_calls"], frame["total_calls"]) == (1, 4)
    assert (edge["primitive_calls"], edge["total_calls"]) == (1, 3)
    assert stats["total_self_seconds"] >= 0


@pytest.mark.parametrize(
    "name,expected",
    [
        ("/task/repo/src/poker_ai/example.py", "src/poker_ai/example.py"),
        (
            "/tmp/env/lib/python3.11/site-packages/numpy/core.py",
            "site-packages/numpy/core.py",
        ),
        ("/runtime/lib/python3.12/json/decoder.py", "stdlib/json/decoder.py"),
        ("/somewhere/other.py", "external/other.py"),
        ("~", "~"),
        ("<frozen os>", "<frozen os>"),
    ],
)
def test_portable_profiler_paths(name: str, expected: str) -> None:
    assert filename(name, Path("/task/repo")) == expected


@pytest.mark.parametrize(
    "damage",
    [
        "missing_field",
        "duplicate_frame",
        "bad_id",
        "absolute_path",
        "negative_line",
        "count_bool",
        "reversed_counts",
        "negative_time",
        "nan",
        "infinite",
        "self_exceeds_inclusive",
        "duplicate_edge",
        "unknown_caller",
        "missing_frame_count",
        "wrong_total",
    ],
)
def test_malformed_profiler_ledgers_are_rejected(damage: str) -> None:
    s = copy.deepcopy(real_stats())
    f = s["functions"][0]
    if damage == "missing_field":
        s.pop("callers")
    elif damage == "duplicate_frame":
        s["functions"].append(copy.deepcopy(f))
        s["frame_count"] += 1
    elif damage == "bad_id":
        f["id"] = "f" * 64
    elif damage == "absolute_path":
        f["file"] = "/outside.py"
    elif damage == "negative_line":
        f["line"] = -1
    elif damage == "count_bool":
        f["total_calls"] = True
    elif damage == "reversed_counts":
        f["primitive_calls"] = f["total_calls"] + 1
    elif damage == "negative_time":
        f["self_seconds"] = -1.0
    elif damage == "nan":
        f["self_seconds"] = float("nan")
    elif damage == "infinite":
        f["cumulative_seconds"] = float("inf")
    elif damage == "self_exceeds_inclusive":
        f["self_seconds"] = f["cumulative_seconds"] + 1
    elif damage == "duplicate_edge":
        s["callers"].append(copy.deepcopy(s["callers"][0]))
        s["edge_count"] += 1
    elif damage == "unknown_caller":
        s["callers"][0]["caller"] = "f" * 64
    elif damage == "missing_frame_count":
        s["frame_count"] -= 1
    elif damage == "wrong_total":
        s["total_self_seconds"] += 1
    with pytest.raises((ArithmeticError, KeyError)):
        validate(s)
