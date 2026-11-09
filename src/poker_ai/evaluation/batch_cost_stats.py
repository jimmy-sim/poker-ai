"""Portable cProfile call graph, exclusive costs and independent visit accounting.

Function tuples are (primitive,total,self,cumulative,callers). cProfile CALLER
tuples reverse the first two fields: (total,primitive,self,cumulative). Preserve
that distinction, including recursion. Cumulative costs overlap across levels.
"""

import cProfile
import math
import pstats
import re
from pathlib import Path
from typing import Any, cast

from poker_ai.evaluation.batch_cost_inputs import duration
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import same

Frame = tuple[str, int, str]
Caller = tuple[int, int, float, float]
Stat = tuple[int, int, float, float, dict[Frame, Caller]]


def filename(name: str, root: Path) -> str:
    if name.startswith(str(root.resolve()) + "/"):
        return name[len(str(root.resolve())) + 1 :]
    if "/site-packages/" in name:
        return "site-packages/" + name.split("/site-packages/", 1)[1]
    matched = re.search(r"/lib/python[0-9.]+/(.+)", name)
    if matched:
        return "stdlib/" + matched.group(1)
    if Path(name).is_absolute():
        return "external/" + Path(name).name
    return name


def extract(profile: cProfile.Profile, root: Path) -> dict[str, Any]:
    raw = cast(dict[Frame, Stat], vars(pstats.Stats(profile))["stats"])
    frames = {k: dict(file=filename(k[0], root), line=k[1], name=k[2]) for k in raw}
    identifiers = {k: sha(v) for k, v in frames.items()}
    if len(set(identifiers.values())) != len(raw):
        raise ArithmeticError("portable profiler frame collision")
    functions: list[dict[str, Any]] = []
    callers: list[dict[str, Any]] = []
    for frame, values in raw.items():
        cc, nc, tt, ct, incoming = values
        functions.append(
            dict(
                id=identifiers[frame],
                **frames[frame],
                primitive_calls=cc,
                total_calls=nc,
                self_seconds=tt,
                cumulative_seconds=ct,
            )
        )
        for caller, (nc, cc, tt, ct) in incoming.items():
            callers.append(
                dict(
                    caller=identifiers[caller],
                    callee=identifiers[frame],
                    primitive_calls=cc,
                    total_calls=nc,
                    self_seconds=tt,
                    cumulative_seconds=ct,
                )
            )
    result = dict(
        functions=sorted(functions, key=lambda r: r["id"]),
        callers=sorted(callers, key=lambda r: (r["caller"], r["callee"])),
        total_self_seconds=math.fsum(r["self_seconds"] for r in functions),
        frame_count=len(functions),
        edge_count=len(callers),
    )
    validate(result)
    return result


def validate(saved: dict[str, Any]) -> None:
    if set(saved) != {
        "functions",
        "callers",
        "total_self_seconds",
        "frame_count",
        "edge_count",
    }:
        raise ArithmeticError("profiler fields changed")
    functions, callers = saved["functions"], saved["callers"]
    if (
        not functions
        or not same(saved["frame_count"], len(functions))
        or not same(saved["edge_count"], len(callers))
        or not duration(saved["total_self_seconds"])
    ):
        raise ArithmeticError("profiler function/caller inventory changed")
    ids = set()
    for row in functions:
        if set(row) != {
            "id",
            "file",
            "line",
            "name",
            "primitive_calls",
            "total_calls",
            "self_seconds",
            "cumulative_seconds",
        }:
            raise ArithmeticError("profiler frame fields changed")
        if (
            not isinstance(row["file"], str)
            or not row["file"]
            or Path(row["file"]).is_absolute()
            or ".." in Path(row["file"]).parts
            or type(row["line"]) is not int
            or row["line"] < 0
            or not isinstance(row["name"], str)
            or not row["name"]
            or row["id"] != sha({k: row[k] for k in ("file", "line", "name")})
            or row["id"] in ids
        ):
            raise ArithmeticError("profiler frame identity invalid/duplicate")
        ids.add(row["id"])
    edges = set()
    for row in callers:
        if set(row) != {
            "caller",
            "callee",
            "primitive_calls",
            "total_calls",
            "self_seconds",
            "cumulative_seconds",
        }:
            raise ArithmeticError("profiler caller fields changed")
        key = row["caller"], row["callee"]
        if row["caller"] not in ids or row["callee"] not in ids or key in edges:
            raise ArithmeticError("profiler caller binding invalid/duplicate")
        edges.add(key)
    for row in [*functions, *callers]:
        if (
            type(row["primitive_calls"]) is not int
            or type(row["total_calls"]) is not int
            or not 0 <= row["primitive_calls"] <= row["total_calls"]
            or row["total_calls"] <= 0
            or not duration(row["self_seconds"])
            or not duration(row["cumulative_seconds"])
            or row["self_seconds"] > row["cumulative_seconds"] + 1e-9
        ):
            raise ArithmeticError("invalid profiler calls/time")
    total = math.fsum(r["self_seconds"] for r in functions)
    if abs(total - saved["total_self_seconds"]) > 1e-9:
        raise ArithmeticError("profiler exclusive time accounting changed")


def call_accounting(stats: dict[str, Any], endpoint: dict[str, Any]) -> dict[str, int]:
    validate(stats)
    functions = stats["functions"]

    def calls(file: str, name: str) -> int:
        return sum(
            r["total_calls"]
            for r in functions
            if r["file"] == file and r["name"] == name
        )

    actual = dict(
        external_calls=calls("src/poker_ai/training/mccfr.py", "external_updates"),
        recursive_visit_calls=calls("src/poker_ai/training/mccfr.py", "visit"),
        batch_mean_calls=calls(
            "src/poker_ai/postflop/frozen_batches.py", "mean_updates"
        ),
    )
    expected = dict(
        external_calls=endpoint["sampled_traversals"],
        recursive_visit_calls=endpoint["incremental_visits"],
        batch_mean_calls=2 * (endpoint["iteration"] - 1)
        if endpoint["path"]["batch_size"] > 1
        else 0,
    )
    if not same(actual, expected):
        raise ArithmeticError("profiled call counts do not match charged training work")
    return actual
