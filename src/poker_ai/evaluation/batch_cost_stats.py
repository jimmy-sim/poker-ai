"""Lossless raw cProfile entries, portable code identities and visit accounting.

Standard pstats labels can overwrite generated functions sharing file/line/name.
Keep one row per raw entry and use raw code-object identity for caller edges.
A structural code digest supplies a portable code_id; entry_index distinguishes
separately created identical code objects without losing either cost record.
"""

import cProfile
import inspect
import math
import re
import struct
from pathlib import Path
from types import CodeType
from typing import Any, Protocol, cast

from poker_ai.evaluation.batch_cost_inputs import duration
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import same


class Call(Protocol):
    code: CodeType | str
    callcount: int
    reccallcount: int
    inlinetime: float
    totaltime: float


class Entry(Call, Protocol):
    calls: list[Call] | None


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


def constant(value: Any, root: Path) -> Any:
    """Canonical compiler constants, without object addresses or marshal refs."""
    if isinstance(value, CodeType):
        return ["code", code_data(value, root)]
    if value is Ellipsis:
        return ["ellipsis"]
    if isinstance(value, bytes):
        return ["bytes", value.hex()]
    if isinstance(value, float):
        return ["float64", struct.pack("<d", value).hex()]
    if isinstance(value, complex):
        return ["complex", constant(value.real, root), constant(value.imag, root)]
    if isinstance(value, tuple):
        return ["tuple", [constant(x, root) for x in value]]
    if isinstance(value, frozenset):
        values = [constant(x, root) for x in value]
        return ["frozenset", sorted(values, key=sha)]
    if value is None or type(value) in (bool, int, str):
        return value
    raise TypeError("unsupported compiler constant in profiler code identity")


def code_data(code: CodeType, root: Path) -> dict[str, Any]:
    return dict(
        file=filename(code.co_filename, root),
        line=code.co_firstlineno,
        name=code.co_name,
        qualname=code.co_qualname,
        bytecode=code.co_code.hex(),
        constants=[constant(x, root) for x in code.co_consts],
        names=code.co_names,
        variables=code.co_varnames,
        free=code.co_freevars,
        cells=code.co_cellvars,
        args=code.co_argcount,
        posonly=code.co_posonlyargcount,
        kwonly=code.co_kwonlyargcount,
        flags=code.co_flags,
        locals=code.co_nlocals,
        stack=code.co_stacksize,
        lines=code.co_linetable.hex(),
        exceptions=code.co_exceptiontable.hex(),
    )


def frame(code: CodeType | str, root: Path) -> dict[str, Any]:
    if isinstance(code, str):
        return dict(
            file="~",
            line=0,
            name=code,
            qualname=code,
            arguments=[],
            code_sha256=sha(["builtin", code]),
        )
    count = (
        code.co_argcount
        + code.co_kwonlyargcount
        + bool(code.co_flags & inspect.CO_VARARGS)
        + bool(code.co_flags & inspect.CO_VARKEYWORDS)
    )
    return dict(
        file=filename(code.co_filename, root),
        line=code.co_firstlineno,
        name=code.co_name,
        qualname=code.co_qualname,
        arguments=list(code.co_varnames[:count]),
        code_sha256=sha(code_data(code, root)),
    )


META = ("file", "line", "name", "qualname", "arguments", "code_sha256")


def extract(profile: cProfile.Profile, root: Path) -> dict[str, Any]:
    entries = cast(list[Entry], profile.getstats())
    identities = {id(e.code): i for i, e in enumerate(entries)}
    if len(identities) != len(entries):
        raise ArithmeticError("duplicate raw profiler code object")
    functions: list[dict[str, Any]] = []
    builtin: dict[str, list[int]] = {}
    for index, entry in enumerate(entries):
        metadata = frame(entry.code, root)
        code_id = sha(metadata)
        functions.append(
            dict(
                **metadata,
                code_id=code_id,
                entry_index=index,
                id=sha([code_id, index]),
                primitive_calls=entry.callcount - entry.reccallcount,
                total_calls=entry.callcount,
                self_seconds=entry.inlinetime,
                cumulative_seconds=entry.totaltime,
            )
        )
        if isinstance(entry.code, str):
            builtin.setdefault(entry.code, []).append(index)
    callers = []
    for index, entry in enumerate(entries):
        for child in entry.calls or []:
            target = identities.get(id(child.code))
            if target is None and isinstance(child.code, str):
                candidates = builtin.get(child.code, [])
                if len(candidates) == 1:
                    target = candidates[0]
            if target is None:
                raise ArithmeticError("ambiguous raw profiler child code")
            callers.append(
                dict(
                    caller=functions[index]["id"],
                    callee=functions[target]["id"],
                    primitive_calls=child.callcount - child.reccallcount,
                    total_calls=child.callcount,
                    self_seconds=child.inlinetime,
                    cumulative_seconds=child.totaltime,
                )
            )
    result = dict(
        functions=functions,
        callers=sorted(callers, key=lambda r: (r["caller"], r["callee"])),
        total_self_seconds=math.fsum(e.inlinetime for e in entries),
        frame_count=len(entries),
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
    for index, row in enumerate(functions):
        if set(row) != set(META) | {
            "id",
            "code_id",
            "entry_index",
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
            or any(
                not isinstance(row[k], str) or not row[k] for k in ("name", "qualname")
            )
            or not isinstance(row["arguments"], list)
            or any(not isinstance(a, str) for a in row["arguments"])
            or not isinstance(row["code_sha256"], str)
            or len(row["code_sha256"]) != 64
            or any(c not in "0123456789abcdef" for c in row["code_sha256"])
            or row["code_id"] != sha({k: row[k] for k in META})
            or not same(row["entry_index"], index)
            or row["id"] != sha([row["code_id"], index])
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
    if (
        abs(
            math.fsum(r["self_seconds"] for r in functions)
            - saved["total_self_seconds"]
        )
        > 1e-9
    ):
        raise ArithmeticError("profiler exclusive time accounting changed")


def call_accounting(stats: dict[str, Any], endpoint: dict[str, Any]) -> dict[str, int]:
    validate(stats)

    def calls(file: str, name: str) -> int:
        return int(
            sum(
                r["total_calls"]
                for r in stats["functions"]
                if r["file"] == file and r["name"] == name
            )
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
