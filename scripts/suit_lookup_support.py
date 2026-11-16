"""Private exact suit-translation kernel; no card-result or strategy cache."""

import functools
import hashlib
import json
import os
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from types import MethodType, ModuleType
from typing import Any

import grouped_depth_support as fields

from poker_ai import cards
from poker_ai.abstraction import potential

BASE = potential.canonical_cards
BASE_MASK: Callable[..., Any] = vars(potential)["cards_to_mask"]
PERMUTATIONS = potential.SUIT_PERMUTATIONS
TABLE = tuple(
    tuple(4 * (card // 4) + permutation[card % 4] for card in range(52))
    for permutation in PERMUTATIONS
)
FROZEN_TABLE = TABLE
SCOPE = (
    "main-process exact canonicalization; all24 permutations per request; "
    "no result cache or native hooks"
)
DEPENDENCIES: tuple[tuple[ModuleType, str, Any], ...] = tuple(
    (module, name, getattr(module, name))
    for module, names in (
        (potential, ("cards_to_mask", "SUIT_PERMUTATIONS")),
        (cards, ("card_bit", "_require_int_in_range", "DECK_SIZE", "format_card")),
    )
    for name in names
)


def table_sha() -> str:
    return hashlib.sha256(fields.canonical(TABLE)).hexdigest()


def check_table(expected: str) -> None:
    if (
        TABLE is not FROZEN_TABLE
        or type(TABLE) is not tuple
        or len(TABLE) != 24
        or any(type(row) is not tuple or len(row) != 52 for row in TABLE)
        or any(type(value) is not int for row in TABLE for value in row)
        or table_sha() != expected
    ):
        raise ArithmeticError("fixed complete suit-translation table required")
    for row, permutation in zip(TABLE, PERMUTATIONS, strict=True):
        for card, translated in enumerate(row):
            rank, suit = divmod(card, 4)
            if translated != rank * 4 + permutation[suit]:
                raise ArithmeticError(
                    "suit table differs from independent rank/suit rule"
                )


def dependencies_unchanged() -> bool:
    return TABLE is FROZEN_TABLE and all(
        getattr(module, name, None) is value for module, name, value in DEPENDENCIES
    )


def primitive(value: Any) -> bool:
    return type(value) is tuple and all(type(card) is int for card in value)


def translated_cards(
    hole: tuple[int, ...], board: tuple[int, ...]
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Original length/mask validation, sorting and minimum; fixed translations.

    Scoped dispatch calls this only for builtin tuples of builtin integers and
    unchanged captured dependencies. Unsupported callers use BASE directly.
    """
    if len(hole) != 2 or len(board) not in (0, 3, 4, 5):
        raise ValueError("need two private cards and a Hold'em board length")
    BASE_MASK(hole + board)
    return min(
        (
            tuple(sorted(row[card] for card in hole)),
            tuple(sorted(row[card] for card in board)),
        )
        for row in TABLE
    )


@contextmanager
def kernel_scope(
    mode: str, output: Path, maximum: int, expected_table: str
) -> Iterator[dict[str, Any]]:
    """Same guarded request observer in both modes; native spawned code untouched."""
    if (
        mode not in ("original", "lookup")
        or type(maximum) is not int
        or maximum <= 0
        or potential.canonical_cards is not BASE
        or threading.current_thread() is not threading.main_thread()
    ):
        raise ArithmeticError("unsupported, nested or changed suit kernel scope")
    check_table(expected_table)
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
        lookup_evaluations=0,
        fallbacks=0,
        errors=0,
        restored=False,
        aliases_remaining=None,
        table_sha256=expected_table,
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
            raise ArithmeticError("suit kernel process/thread/request capacity changed")
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
        if mode == "lookup" and eligible:
            state["lookup_evaluations"] += 1
            call = translated_cards
        else:
            state["original_evaluations"] += 1
            call = BASE
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
    pid: int,
    thread: int,
    *,
    require_lookup: bool = False,
) -> dict[str, Any]:
    """Validate complete retained accounting, not fresh card or poker computation."""
    if (
        type(maximum) is not int
        or maximum <= 0
        or type(pid) is not int
        or pid <= 0
        or type(thread) is not int
        or thread <= 0
        or type(require_lookup) is not bool
    ):
        raise ArithmeticError("canonical kernel parser context required")
    row: dict[str, Any] = json.loads(output.read_text())
    counters = (
        "maximum",
        "pid",
        "thread",
        "requests",
        "original_evaluations",
        "lookup_evaluations",
        "fallbacks",
        "errors",
        "aliases_remaining",
    )
    if (
        set(row) != {"status", "mode", *counters, "restored", "table_sha256", "scope"}
        or any(type(row[k]) is not int or row[k] < 0 for k in counters)
        or row["scope"] != SCOPE
        or row["status"] != "complete"
        or row["mode"] != mode
        or mode not in ("original", "lookup")
        or row["maximum"] != maximum
        or row["pid"] != pid
        or row["thread"] != thread
        or row["table_sha256"] != expected_table
        or row["restored"] is not True
        or row["aliases_remaining"] != 0
        or row["errors"] != 0
        or not 0 < row["requests"] <= maximum
        or row["requests"] != row["original_evaluations"] + row["lookup_evaluations"]
        or row["fallbacks"] > row["original_evaluations"]
        or (mode == "original" and row["lookup_evaluations"] != 0)
        or (mode == "lookup" and row["original_evaluations"] != row["fallbacks"])
        or (mode == "lookup" and require_lookup and row["lookup_evaluations"] == 0)
    ):
        raise ArithmeticError("complete same-context kernel accounting required")
    return row
