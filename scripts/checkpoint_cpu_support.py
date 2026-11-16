"""Bounded parent-only CPU observation of the own-archive checkpoint callsite.

Only that callsite starts a root. Decode and score calls elsewhere pass through.
The original reusable replay function and spawned native workers stay unchanged.
This diagnostic records software costs; it cannot admit a new poker study.
"""

import copy
import functools
import math
import os
import sys
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from types import MethodType, ModuleType
from typing import Any

import profile_coarse_reader as coarse

CATEGORIES = ("own_checkpoint", "checkpoint_decode", "checkpoint_score")
ORIGINAL_CATEGORIES = coarse.CATEGORIES
BUSY = False
Clock = Callable[[], dict[str, Any]]


@contextmanager
def categories() -> Iterator[None]:
    """Use the frozen predecessor's data validator for this private category set."""
    global BUSY
    if (
        BUSY
        or ORIGINAL_CATEGORIES
        != ("matrix_build", "spot_tree_build", "checkpoint_replay")
        or coarse.CATEGORIES is not ORIGINAL_CATEGORIES
        or threading.current_thread() is not threading.main_thread()
    ):
        raise ArithmeticError("fresh main-thread checkpoint region context required")
    BUSY = True
    coarse.CATEGORIES = CATEGORIES
    primary = False
    try:
        yield
    except BaseException:
        primary = True
        raise
    finally:
        changed = coarse.CATEGORIES is not CATEGORIES
        coarse.CATEGORIES = ORIGINAL_CATEGORIES
        BUSY = False
        if changed and not primary:
            raise ArithmeticError("checkpoint category registry changed")


def check_clock(value: Any) -> None:
    if (
        type(value) is not dict
        or set(value) != {"wall", "cpu", "pid", "thread"}
        or any(type(value[k]) is not int or value[k] <= 0 for k in ("pid", "thread"))
        or any(
            type(value[k]) not in (int, float)
            or not math.isfinite(value[k])
            or value[k] < 0
            for k in ("wall", "cpu")
        )
    ):
        raise ArithmeticError("finite nonnegative clock and typed producer required")


class ScopedRegions(coarse.Regions):
    """Time selected boundaries while preserving original return/error identity."""

    def owner(self) -> None:
        if os.getpid() != self.pid or threading.get_ident() != self.thread:
            self.errors += 1
            raise ArithmeticError("serial parent checkpoint observer required")

    def stamp(self) -> dict[str, Any]:
        value = self.read_clock()
        check_clock(value)
        if value["pid"] != self.pid or value["thread"] != self.thread:
            raise ArithmeticError("clock producer changed")
        return copy.deepcopy(value)

    def wrap(self, category: str, function: Callable[..., Any]) -> Callable[..., Any]:
        if category not in CATEGORIES or getattr(function, "_coarse_cpu_region", False):
            raise ArithmeticError("fresh known checkpoint boundary required")

        @functools.wraps(function)
        def selected(*args: Any, **kwargs: Any) -> Any:
            if not self.active:
                return function(*args, **kwargs)
            self.owner()
            inside = any(
                self.rows[i]["category"] == "own_checkpoint" for i in self.stack
            )
            if category != "own_checkpoint" and not inside:
                return function(*args, **kwargs)
            if (
                self.emitting
                or self.total >= self.maximum
                or (category == "own_checkpoint" and inside)
            ):
                self.errors += 1
                raise ArithmeticError("checkpoint recursion/reentrancy/cap unsupported")
            index = len(self.rows)
            row: dict[str, Any] = dict(
                index=index,
                read=self.read_index,
                parent=self.stack[-1] if self.stack else None,
                category=category,
                status="running",
                before=self.stamp(),
            )
            self.rows.append(row)
            self.stack.append(index)
            self.total += 1
            primary: BaseException | None = None
            entered = False
            try:
                self.publish(row)
                entered = True
                return function(*args, **kwargs)
            except BaseException as error:
                primary = error
                row["failure_kind"] = type(error).__name__
                if not entered:
                    self.errors += 1
                raise
            finally:
                try:
                    row.update(
                        status="complete" if primary is None else "primary_failed",
                        after=self.stamp(),
                    )
                    self.publish(row)
                    if not self.stack or self.stack[-1] != index:
                        raise ArithmeticError("selected stack changed")
                except BaseException:
                    self.errors += 1
                    row["status"] = (
                        "observer_failed"
                        if primary is None
                        else "primary_with_observer_failure"
                    )
                    if primary is None:
                        raise
                finally:
                    if self.stack and self.stack[-1] == index:
                        self.stack.pop()

        marker = "_coarse_cpu_region"
        setattr(selected, marker, True)
        return selected


def modules() -> Iterator[ModuleType]:
    """Only declared project aliases, including private entry/support modules."""
    for name, module in list(sys.modules.items()):
        if isinstance(module, ModuleType) and (
            name.startswith("poker_ai.")
            or name.startswith("compact_suit.")
            or name in ("profile_checkpoint_cpu", "checkpoint_cpu_support")
        ):
            yield module


def is_alias(value: Any, function: Callable[..., Any]) -> bool:
    return (
        value is function
        or isinstance(value, MethodType)
        and value.__func__ is function
    )


class Bindings:
    """Restore every declared attribute and initial/late alias, even after failure."""

    def __init__(self, failures: list[str]) -> None:
        self.saved: list[tuple[Any, str, Any, Any, Any]] = []
        self.initial: list[tuple[ModuleType, str, Any]] = []
        self.failures = failures
        self.remaining: int | None = None
        self.restored = False

    def replace(self, old: Any, new: Any, *, save: bool) -> None:
        for module in modules():
            for name, value in list(vars(module).items()):
                if is_alias(value, old):
                    if save:
                        self.initial.append((module, name, value))
                    replacement = (
                        MethodType(new, value.__self__)
                        if isinstance(value, MethodType)
                        else new
                    )
                    setattr(module, name, replacement)

    def install(self, owner: Any, name: str, wrapper: Any, *, aliases: bool) -> None:
        descriptor = vars(owner)[name]
        function = (
            descriptor.__func__ if isinstance(descriptor, classmethod) else descriptor
        )
        if not callable(function) or getattr(function, "_coarse_cpu_region", False):
            raise ArithmeticError("fresh callable checkpoint binding required")
        self.saved.append((owner, name, descriptor, function, wrapper))
        setattr(
            owner,
            name,
            classmethod(wrapper) if isinstance(descriptor, classmethod) else wrapper,
        )
        if aliases:
            self.replace(function, wrapper, save=True)

    def restore(self) -> None:
        def attempt(owner: Any, name: str, value: Any) -> None:
            try:
                setattr(owner, name, value)
            except BaseException as error:
                self.failures.append(type(error).__name__)

        for owner, name, descriptor, function, wrapper in reversed(self.saved):
            current = vars(owner).get(name)
            current_function = (
                current.__func__ if isinstance(current, classmethod) else current
            )
            if current_function is not wrapper:
                self.failures.append("binding_changed")
            attempt(owner, name, descriptor)
            # Each alias is an independent cleanup operation: one failure cannot
            # prevent restoration of the remaining attributes or late imports.
            for module in modules():
                for alias, value in list(vars(module).items()):
                    if is_alias(value, wrapper):
                        replacement = (
                            MethodType(function, value.__self__)
                            if isinstance(value, MethodType)
                            else function
                        )
                        attempt(module, alias, replacement)
        for module, name, value in self.initial:
            attempt(module, name, value)
        self.remaining = sum(
            is_alias(value, wrapper)
            for module in modules()
            for value in vars(module).values()
            for _, _, _, _, wrapper in self.saved
        )
        self.restored = (
            self.remaining == 0
            and all(
                vars(o).get(n) is descriptor for o, n, descriptor, _, _ in self.saved
            )
            and not self.failures
        )


class Observer:
    """One fresh serial parent scope and at most three separately recorded reads."""

    def __init__(
        self,
        *,
        enabled: bool,
        maximum: int = 4096,
        read_clock: Clock = coarse.clock,
        event_sink: Callable[[int, dict[str, Any]], None] | None = None,
        read_sink: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        if type(enabled) is not bool:
            raise TypeError("explicit observer mode required")
        self.enabled = enabled
        self.event_sink, self.read_sink = event_sink, read_sink
        self.regions = ScopedRegions(maximum, read_clock=read_clock)
        self.reads: list[dict[str, Any]] = []
        self.installed = False
        self.started = False
        self.reading = False
        self.restored = False
        self.remaining: int | None = None
        self.cleanup_failures: list[str] = []
        self.original_root_unchanged = False

    @contextmanager
    def hooks(self) -> Iterator[None]:
        from poker_ai.evaluation import opponent_learning_own as own
        from poker_ai.postflop import learning_artifacts as artifacts
        from poker_ai.postflop import learning_training as training
        from poker_ai.postflop.controlled_scoring import ScoringContext

        self.regions.owner()
        if self.started or self.installed:
            raise ArithmeticError("observer scope is fresh and cannot be reused")
        root_name = "replay_snapshot"
        original = getattr(own, root_name)
        if original is not training.replay_snapshot:
            raise ArithmeticError("original named checkpoint callsite required")
        self.started = True
        bindings = Bindings(self.cleanup_failures)
        primary: BaseException | None = None
        with categories():
            try:
                if self.enabled:
                    for category, owner, name in (
                        ("checkpoint_decode", artifacts, "decode"),
                        ("checkpoint_score", ScoringContext, "score"),
                    ):
                        bindings.install(
                            owner,
                            name,
                            self.regions.wrap(category, getattr(owner, name)),
                            aliases=True,
                        )
                    bindings.install(
                        own,
                        root_name,
                        self.regions.wrap("own_checkpoint", original),
                        aliases=False,
                    )
                self.installed = True
                yield
            except BaseException as error:
                primary = error
                raise
            finally:
                self.installed = False
                self.regions.active = False
                bindings.restore()
                self.remaining = bindings.remaining
                self.original_root_unchanged = training.replay_snapshot is original
                self.restored = (
                    bindings.restored
                    and getattr(own, root_name) is original
                    and self.original_root_unchanged
                )
                if not self.restored and primary is None:
                    raise ArithmeticError("checkpoint observer cleanup incomplete")

    @contextmanager
    def read(self, index: int) -> Iterator[dict[str, Any]]:
        self.regions.owner()
        if (
            not self.installed
            or self.reading
            or self.regions.active
            or self.regions.stack
            or type(index) is not int
            or index != len(self.reads)
            or not 0 <= index < 3
        ):
            self.regions.errors += 1
            raise ArithmeticError("ordered serial read within installed scope required")
        events: list[dict[str, Any]] = []
        self.regions.rows = []
        self.regions.read_index = index

        def emit(event: dict[str, Any]) -> None:
            events.append(event)
            if self.event_sink is not None:
                self.event_sink(index, event)

        self.regions.emit = emit
        row: dict[str, Any] = dict(index=index, status="running")
        self.reads.append(row)
        self.reading = True
        self.regions.active = self.enabled
        primary: BaseException | None = None
        try:
            row["before"] = self.regions.stamp()
            if self.read_sink is not None:
                self.read_sink(copy.deepcopy(row))
            yield row
        except BaseException as error:
            primary = error
            row["failure_kind"] = type(error).__name__
            raise
        finally:
            self.regions.active = False
            self.reading = False
            row["status"] = "partial"
            try:
                row["after"] = self.regions.stamp()
                if (
                    primary is None
                    and not self.regions.stack
                    and not self.regions.errors
                ):
                    row["status"] = "complete"
            except BaseException as error:
                row["observer_failure_kind"] = type(error).__name__
                self.regions.errors += 1
                if primary is None:
                    raise
            finally:
                row["ledger"] = dict(
                    status=row["status"],
                    errors=self.regions.errors,
                    rows=copy.deepcopy(self.regions.rows),
                    pid=self.regions.pid,
                    thread=self.regions.thread,
                )
                row["events"] = events
                if self.read_sink is not None:
                    try:
                        self.read_sink(copy.deepcopy(row))
                    except BaseException as error:
                        self.regions.errors += 1
                        row["status"] = "partial"
                        row["retention_failure_kind"] = type(error).__name__
                        if primary is None:
                            raise

    def state(self) -> dict[str, Any]:
        return dict(
            enabled=self.enabled,
            pid=self.regions.pid,
            thread=self.regions.thread,
            active=self.installed or self.regions.active or self.reading,
            restored=self.restored,
            aliases_remaining=self.remaining,
            original_root_unchanged=self.original_root_unchanged,
            errors=self.regions.errors,
            cleanup_failures=list(self.cleanup_failures),
            selected_calls=self.regions.total,
            maximum=self.regions.maximum,
            read_count=len(self.reads),
            categories=list(CATEGORIES),
        )


def validate_read(row: dict[str, Any], expected: int) -> dict[str, Any]:
    """Strict data-only nesting/accounting; no checkpoint or scoring execution."""
    if (
        type(expected) is not int
        or expected < 0
        or type(row) is not dict
        or set(row) != {"index", "status", "before", "after", "ledger", "events"}
        or row["status"] != "complete"
    ):
        raise ArithmeticError("complete read and typed expected inventory required")
    index, before, after = row["index"], row["before"], row["after"]
    if type(index) is not int or not 0 <= index < 3:
        raise ArithmeticError("typed ordered read index required")
    for stamp in (before, after):
        check_clock(stamp)
    ledger = row["ledger"]
    if (
        type(ledger) is not dict
        or set(ledger) != {"status", "errors", "rows", "pid", "thread"}
        or ledger["status"] != "complete"
        or type(ledger["errors"]) is not int
        or ledger["errors"] != 0
        or type(ledger["rows"]) is not list
        or type(row["events"]) is not list
        or len(ledger["rows"]) != expected * 3
        or any(
            type(ledger[k]) is not int
            or ledger[k] != before[k]
            or after[k] != before[k]
            for k in ("pid", "thread")
        )
        or any(after[k] < before[k] for k in ("cpu", "wall"))
    ):
        raise ArithmeticError("complete typed ledger identity/order required")
    for item in [*ledger["rows"], *row["events"]]:
        if type(item) is not dict:
            raise ArithmeticError("selected boundary object required")
        keys = {"read", "index", "parent", "category", "status", "before"}
        if item.get("status") == "complete":
            keys.add("after")
        if (
            set(item) != keys
            or item.get("status") not in ("running", "complete")
            or type(item["read"]) is not int
            or type(item["index"]) is not int
            or (item["parent"] is not None and type(item["parent"]) is not int)
        ):
            raise ArithmeticError("typed selected boundary schema required")
        for stamp in (
            (item["before"],)
            if item["status"] == "running"
            else (item["before"], item["after"])
        ):
            check_clock(stamp)
            if any(stamp[k] != before[k] for k in ("pid", "thread")):
                raise ArithmeticError("selected producer changed")
    with categories():
        result = coarse.validate_regions(
            ledger, row["events"], before["pid"], before["thread"], index
        )
    if any(result["groups"][key]["calls"] != expected for key in CATEGORIES):
        raise ArithmeticError(
            "complete fixed checkpoint/decode/score inventory required"
        )
    rows = ledger["rows"]
    for offset in range(0, len(rows), 3):
        root, decode, score = rows[offset : offset + 3]
        if (
            [x["category"] for x in (root, decode, score)] != list(CATEGORIES)
            or root["parent"] is not None
            or decode["parent"] != offset
            or score["parent"] != offset
        ):
            raise ArithmeticError("one ordered decode and score per own root required")
    for item in rows:
        if not all(
            before[k] <= item["before"][k] <= item["after"][k] <= after[k]
            for k in ("cpu", "wall")
        ):
            raise ArithmeticError("selected region outside complete read")
    read_cpu = after["cpu"] - before["cpu"]
    outside = read_cpu - result["selected_union_cpu"]
    if outside < -1e-9:
        raise ArithmeticError("selected CPU exceeds complete read")
    return dict(
        result, read_cpu_seconds=read_cpu, outside_checkpoint_cpu_seconds=outside
    )


def validate_state(
    state: dict[str, Any],
    reads: list[dict[str, Any]],
    *,
    enabled: bool,
    pid: int,
    thread: int,
    expected: int,
    maximum: int = 4096,
) -> list[dict[str, Any]]:
    """Bind saved reads to the actual completed producer and fixed three-read plan."""
    wanted = dict(
        enabled=enabled,
        pid=pid,
        thread=thread,
        active=False,
        restored=True,
        aliases_remaining=0,
        original_root_unchanged=True,
        errors=0,
        cleanup_failures=[],
        selected_calls=9 * expected if enabled else 0,
        maximum=maximum,
        read_count=3,
        categories=list(CATEGORIES),
    )
    if (
        type(reads) is not list
        or len(reads) != 3
        or type(state) is not dict
        or set(state) != set(wanted)
    ):
        raise ArithmeticError("complete observer producer state required")
    if any(type(state[k]) is not type(v) or state[k] != v for k, v in wanted.items()):
        raise ArithmeticError("restored fixed observer state required")
    results = []
    for index, row in enumerate(reads):
        result = validate_read(row, expected if enabled else 0)
        if (
            row["index"] != index
            or row["before"]["pid"] != pid
            or row["before"]["thread"] != thread
        ):
            raise ArithmeticError("actual ordered producer reads required")
        if index and any(
            reads[index - 1]["after"][k] > row["before"][k] for k in ("cpu", "wall")
        ):
            raise ArithmeticError("complete reads overlap or clocks decrease")
        results.append(result)
    return results
