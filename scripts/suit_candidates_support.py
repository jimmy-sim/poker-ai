"""Private exact lexicographic suit minimization; static hole geometry only."""

import functools
import hashlib
import itertools
import json
import os
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from types import MethodType, ModuleType
from typing import Any

import grouped_depth_support as fields
import suit_lookup_support as lookup

from poker_ai.abstraction import potential

BASE = lookup.BASE
BASE_MASK: Callable[..., Any] = lookup.BASE_MASK
TABLE = lookup.TABLE
ALL: Callable[..., Any] = lookup.translated_cards
Pair = tuple[int, int]
Slot = tuple[Pair, tuple[int, ...]]
SCOPE = (
    "main-process exact private-minimum factorization; static card geometry; "
    "no adaptive full-hand result cache or native hooks"
)
LOOKUP_DEPENDENCIES = tuple(
    (name, getattr(lookup, name))
    for name in ("BASE", "BASE_MASK", "TABLE", "translated_cards")
)


def make_geometry() -> tuple[tuple[Slot | None, ...], ...]:
    rows = []
    for a in range(52):
        row: list[Slot | None] = []
        for b in range(52):
            if a == b:
                row.append(None)
                continue
            private = tuple((min(t[a], t[b]), max(t[a], t[b])) for t in TABLE)
            smallest = min(private)
            row.append(
                (smallest, tuple(i for i, h in enumerate(private) if h == smallest))
            )
        rows.append(tuple(row))
    return tuple(rows)


GEOMETRY = make_geometry()
FROZEN_GEOMETRY = GEOMETRY


def geometry_sha() -> str:
    return hashlib.sha256(fields.canonical(GEOMETRY)).hexdigest()


def check_geometry(expected_table: str, expected_geometry: str) -> None:
    """Independent literal S4 specification for every ordered hole, before use."""
    lookup.check_table(expected_table)
    if (
        TABLE is not lookup.TABLE
        or GEOMETRY is not FROZEN_GEOMETRY
        or type(GEOMETRY) is not tuple
        or len(GEOMETRY) != 52
        or any(type(row) is not tuple or len(row) != 52 for row in GEOMETRY)
        or geometry_sha() != expected_geometry
    ):
        raise ArithmeticError("complete fixed ordered-hole geometry required")
    permutations = tuple(itertools.permutations(range(4)))
    if permutations != lookup.PERMUTATIONS:
        raise ArithmeticError("literal permutation order changed")
    counts = {2: 0, 4: 0, 6: 0}
    for a, row in enumerate(GEOMETRY):
        for b, slot in enumerate(row):
            if a == b:
                if slot is not None:
                    raise ArithmeticError("duplicate-card sentinel changed")
                continue
            if (
                type(slot) is not tuple
                or len(slot) != 2
                or type(slot[0]) is not tuple
                or len(slot[0]) != 2
                or type(slot[1]) is not tuple
                or any(type(x) is not int for x in (*slot[0], *slot[1]))
            ):
                raise ArithmeticError("typed exact geometry slot required")
            projected = [
                tuple(sorted((4 * (a // 4) + p[a % 4], 4 * (b // 4) + p[b % 4])))
                for p in permutations
            ]
            minimum = min(projected)
            indices = tuple(i for i, h in enumerate(projected) if h == minimum)
            expected_count = 6 if a % 4 == b % 4 else (4 if a // 4 == b // 4 else 2)
            if slot != (minimum, indices) or len(indices) != expected_count:
                raise ArithmeticError("ordered-hole geometry differs from literal S4")
            counts[len(indices)] += 1
    if counts != {2: 1872, 4: 156, 6: 624}:
        raise ArithmeticError("complete ordered-hole tie inventory required")


def dependencies_unchanged() -> bool:
    return (
        GEOMETRY is FROZEN_GEOMETRY
        and TABLE is lookup.TABLE
        and ALL is lookup.translated_cards
        and BASE_MASK is lookup.BASE_MASK
        and lookup.dependencies_unchanged()
        and all(
            getattr(lookup, name, None) is value for name, value in LOOKUP_DEPENDENCIES
        )
    )


def primitive(value: Any) -> bool:
    return lookup.primitive(value)


def reduced_cards(
    hole: tuple[int, ...], board: tuple[int, ...]
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Exact lexicographic factorization, only under scoped primitive dispatch.

    min(H_p, B_p) = (h*, min B_p among all p with H_p == h*).
    Length and physical-card validation precede table indexing as in BASE.
    Static private values are returned in a fresh tuple, not a shared object.
    """
    if len(hole) != 2 or len(board) not in (0, 3, 4, 5):
        raise ValueError("need two private cards and a Hold'em board length")
    BASE_MASK(hole + board)
    slot = GEOMETRY[hole[0]][hole[1]]
    if slot is None:
        raise ArithmeticError("validated distinct cards have no geometry")
    private, indices = slot
    answer = (private[0], private[1])
    if not board:
        return answer, ()
    return answer, min(
        tuple(sorted(TABLE[index][card] for card in board)) for index in indices
    )


@contextmanager
def kernel_scope(
    mode: str, output: Path, maximum: int, expected_table: str, expected_geometry: str
) -> Iterator[dict[str, Any]]:
    """Same guarded request observer in both modes; native spawned code untouched."""
    if (
        mode not in ("all", "reduced")
        or type(maximum) is not int
        or maximum <= 0
        or potential.canonical_cards is not BASE
        or threading.current_thread() is not threading.main_thread()
    ):
        raise ArithmeticError(
            "unsupported, nested or changed suit-candidate kernel scope"
        )
    check_geometry(expected_table, expected_geometry)
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists() or output.is_symlink():
        raise ValueError("fresh kernel receipt required")
    state: dict[str, Any] = dict(
        status="running",
        mode=mode,
        maximum=maximum,
        pid=os.getpid(),
        thread=threading.get_ident(),
        requests=0,
        original_evaluations=0,
        all_evaluations=0,
        reduced_evaluations=0,
        fallbacks=0,
        errors=0,
        restored=False,
        aliases_remaining=None,
        table_sha256=expected_table,
        geometry_sha256=expected_geometry,
        scope=SCOPE,
    )
    output.write_bytes(fields.canonical(state) + b"\n")
    initial: list[tuple[ModuleType, str, Any]] = []
    primary = False

    @functools.wraps(BASE)
    def observed(*args: Any, **kwargs: Any) -> Any:
        if (
            os.getpid() != state["pid"]
            or threading.get_ident() != state["thread"]
            or state["requests"] >= maximum
        ):
            state["errors"] += 1
            raise ArithmeticError(
                "suit-candidate kernel process/thread/request capacity changed"
            )
        state["requests"] += 1
        eligible = (
            not kwargs
            and len(args) == 2
            and primitive(args[0])
            and primitive(args[1])
            and dependencies_unchanged()
        )
        if not eligible:
            state["fallbacks"] += 1
        call: Callable[..., Any]
        if not eligible:
            state["original_evaluations"] += 1
            call = BASE
        elif mode == "all":
            state["all_evaluations"] += 1
            call = ALL
        else:
            state["reduced_evaluations"] += 1
            call = reduced_cards
        try:
            return call(*args, **kwargs)
        except BaseException:
            state["errors"] += 1
            raise

    try:
        fields.aliases(BASE, observed, initial)
        if potential.canonical_cards is not observed:
            raise ArithmeticError("defining kernel alias not installed")
        yield state
    except BaseException:
        primary = True
        raise
    finally:
        try:
            if potential.canonical_cards is not observed:
                state["errors"] += 1
            fields.aliases(observed, BASE)
            for module, name, value in initial:
                setattr(module, name, value)
            remaining = sum(
                value is observed
                or (isinstance(value, MethodType) and value.__func__ is observed)
                for module in fields.owned_modules()
                for value in vars(module).values()
            )
            state.update(
                aliases_remaining=remaining,
                restored=potential.canonical_cards is BASE and remaining == 0,
                status="complete"
                if not primary
                and state["errors"] == 0
                and potential.canonical_cards is BASE
                and remaining == 0
                else "failed_retained",
            )
            output.write_bytes(fields.canonical(state) + b"\n")
        except BaseException:
            if not primary:
                raise


def read_kernel(
    output: Path,
    mode: str,
    maximum: int,
    expected_table: str,
    expected_geometry: str,
    pid: int,
    thread: int,
    *,
    require_reduced: bool = False,
) -> dict[str, Any]:
    """Validate complete retained accounting, not fresh card or poker computation."""
    if (
        type(maximum) is not int
        or maximum <= 0
        or type(pid) is not int
        or pid <= 0
        or type(thread) is not int
        or thread <= 0
        or type(require_reduced) is not bool
    ):
        raise ArithmeticError("suit-candidate kernel parser context required")
    row: dict[str, Any] = json.loads(output.read_text())
    counters = (
        "maximum",
        "pid",
        "thread",
        "requests",
        "original_evaluations",
        "all_evaluations",
        "reduced_evaluations",
        "fallbacks",
        "errors",
        "aliases_remaining",
    )
    if (
        set(row)
        != {
            "status",
            "mode",
            *counters,
            "restored",
            "table_sha256",
            "geometry_sha256",
            "scope",
        }
        or any(type(row[k]) is not int or row[k] < 0 for k in counters)
        or row["scope"] != SCOPE
        or row["status"] != "complete"
        or row["mode"] != mode
        or mode not in ("all", "reduced")
        or row["maximum"] != maximum
        or row["pid"] != pid
        or row["thread"] != thread
        or row["table_sha256"] != expected_table
        or row["geometry_sha256"] != expected_geometry
        or row["restored"] is not True
        or row["aliases_remaining"] != 0
        or row["errors"] != 0
        or not 0 < row["requests"] <= maximum
        or row["requests"]
        != row["original_evaluations"]
        + row["all_evaluations"]
        + row["reduced_evaluations"]
        or row["fallbacks"] != row["original_evaluations"]
        or (mode == "all" and row["reduced_evaluations"] != 0)
        or (mode == "reduced" and row["all_evaluations"] != 0)
        or (mode == "reduced" and require_reduced and row["reduced_evaluations"] == 0)
    ):
        raise ArithmeticError("complete same-context kernel accounting required")
    return row
