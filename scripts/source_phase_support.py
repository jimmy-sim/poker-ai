"""Nested source-loader boundaries, with reusable defining functions untouched."""

import copy
import functools
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from types import ModuleType
from typing import Any

import checkpoint_cpu_support as prior
import profile_coarse_reader as coarse

ROOT = "source_load"
CHILDREN = (
    "previous_sources",
    "compact_game",
    "compact_game",
    "parent_replay",
    "original_contexts",
    "original_boundaries",
)
CATEGORIES = (ROOT, *dict.fromkeys(CHILDREN))
BUSY = False


@dataclass(frozen=True)
class ModuleAlias:
    """Forward one module alias without modifying its defining module."""

    _delegate: ModuleType
    _selected_name: str
    _selected_call: Callable[..., Any]

    def __getattr__(self, name: str) -> Any:
        return (
            self._selected_call
            if name == self._selected_name
            else getattr(self._delegate, name)
        )


class Regions(prior.ScopedRegions):
    """A root encloses six serial children; unrelated calls pass through."""

    def wrap(self, category: str, function: Callable[..., Any]) -> Callable[..., Any]:
        if category not in CATEGORIES or getattr(function, "_coarse_cpu_region", False):
            raise ArithmeticError("fresh known source boundary required")

        @functools.wraps(function)
        def selected(*args: Any, **kwargs: Any) -> Any:
            if not self.active:
                return function(*args, **kwargs)
            self.owner()
            if category != ROOT and not self.stack:
                return function(*args, **kwargs)
            if (
                self.emitting
                or self.total >= self.maximum
                or category == ROOT
                and self.stack
                or category != ROOT
                and (
                    len(self.stack) != 1 or self.rows[self.stack[0]]["category"] != ROOT
                )
            ):
                self.errors += 1
                raise ArithmeticError("source recursion/reentrancy/cap unsupported")
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
            try:
                self.publish(row)
                return function(*args, **kwargs)
            except BaseException as error:
                primary = error
                row["failure_kind"] = type(error).__name__
                raise
            finally:
                try:
                    row.update(
                        status="complete" if primary is None else "primary_failed",
                        after=self.stamp(),
                    )
                    self.publish(row)
                    if not self.stack or self.stack[-1] != index:
                        raise ArithmeticError("source phase stack changed")
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


def targets() -> tuple[tuple[str, Any, str, Any], ...]:
    from compact_suit import cli

    from poker_ai.evaluation import compact_opponent_boundaries as boundaries
    from poker_ai.evaluation import compact_opponent_contexts as contexts
    from poker_ai.evaluation import compact_opponent_sources as source

    return (
        (ROOT, cli, "load", source.load),
        ("compact_game", source, "build_game", contexts.build_game),
        ("original_contexts", source, "load_contexts", boundaries.load_contexts),
        ("original_boundaries", source, "boundaries", boundaries.boundaries),
    )


def module_targets() -> tuple[tuple[str, ModuleType, str, ModuleType, str], ...]:
    from poker_ai.evaluation import compact_fixed_inputs as sampled
    from poker_ai.evaluation import compact_opponent_sources as source
    from poker_ai.evaluation import opponent_learning_sources as previous

    return (
        ("previous_sources", source, "old_sources", previous, "load"),
        ("parent_replay", source, "sampled_parent", sampled, "replay_sources"),
    )


class Observer(prior.Observer):
    """Reuse read clocks and cleanup; scope observations to the named root."""

    def __init__(
        self,
        *,
        enabled: bool,
        maximum: int = 32,
        read_clock: prior.Clock = coarse.clock,
        event_sink: Callable[[int, dict[str, Any]], None] | None = None,
        read_sink: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        super().__init__(
            enabled=enabled,
            maximum=maximum,
            read_clock=read_clock,
            event_sink=event_sink,
            read_sink=read_sink,
        )
        self.regions = Regions(maximum, read_clock=read_clock)
        self.module_aliases_restored = False

    @contextmanager
    def hooks(self) -> Iterator[None]:
        global BUSY
        self.regions.owner()
        if (
            self.started
            or self.installed
            or BUSY
            or threading.current_thread() is not threading.main_thread()
        ):
            raise ArithmeticError("fresh main-thread source observer required")
        declared, modules = targets(), module_targets()
        if any(
            getattr(owner, name) is not original
            for _, owner, name, original in declared
        ) or any(
            getattr(owner, name) is not original
            for _, owner, name, original, _ in modules
        ):
            raise ArithmeticError(
                "unchanged source callsite and module aliases required"
            )
        originals = [
            (module, member, getattr(module, member))
            for _, _, _, module, member in modules
        ]
        self.started = True
        BUSY = True
        bindings = prior.Bindings(self.cleanup_failures)
        primary: BaseException | None = None
        try:
            if self.enabled:
                for category, owner, name, original in declared:
                    bindings.install(
                        owner,
                        name,
                        self.regions.wrap(category, original),
                        aliases=False,
                    )
                for category, owner, name, original, member in modules:
                    proxy = ModuleAlias(
                        original,
                        member,
                        self.regions.wrap(category, getattr(original, member)),
                    )
                    # The common restorer handles identity aliases and late imports
                    # for these module objects too; no defining module is patched.
                    bindings.saved.append((owner, name, original, original, proxy))
                    setattr(owner, name, proxy)
            self.installed = True
            yield
        except BaseException as error:
            primary = error
            raise
        finally:
            self.installed = False
            self.regions.active = False
            bindings.restore()
            BUSY = False
            self.remaining = bindings.remaining
            self.module_aliases_restored = all(
                getattr(o, n) is original for _, o, n, original, _ in modules
            )
            self.original_root_unchanged = all(
                original is now[3]
                for (_, _, _, original), now in zip(declared, targets(), strict=True)
            ) and all(
                getattr(module, member) is function
                for module, member, function in originals
            )
            self.restored = (
                bindings.restored
                and self.module_aliases_restored
                and self.original_root_unchanged
                and all(getattr(o, n) is original for _, o, n, original in declared)
            )
            if not self.restored and primary is None:
                raise ArithmeticError("source phase restoration incomplete")

    def state(self) -> dict[str, Any]:
        result = super().state()
        result["original_functions_unchanged"] = result.pop("original_root_unchanged")
        result["module_aliases_restored"] = self.module_aliases_restored
        result["categories"] = list(CATEGORIES)
        return result


def validate_read(row: Any, index: int, *, enabled: bool) -> dict[str, Any]:
    """Check exact two-level nesting and disjoint CPU from saved data only."""
    if type(index) is not int or not 0 <= index < 3 or type(enabled) is not bool:
        raise ArithmeticError("typed index and explicit observation mode required")
    if (
        type(row) is not dict
        or set(row) != {"index", "status", "before", "after", "ledger", "events"}
        or type(row["index"]) is not int
        or row["index"] != index
        or row["status"] != "complete"
    ):
        raise ArithmeticError("complete ordered source read required")
    before, after, ledger = row["before"], row["after"], row["ledger"]
    for clock in (before, after):
        prior.check_clock(clock)
    if any(after[k] < before[k] for k in ("cpu", "wall")) or any(
        before[k] != after[k] for k in ("pid", "thread")
    ):
        raise ArithmeticError("one monotone serial read producer required")
    expected = (ROOT, *CHILDREN) if enabled and index else ()
    if (
        type(ledger) is not dict
        or set(ledger) != {"status", "errors", "rows", "pid", "thread"}
        or ledger["status"] != "complete"
        or type(ledger["errors"]) is not int
        or ledger["errors"] != 0
        or any(
            type(ledger[k]) is not int or ledger[k] != before[k]
            for k in ("pid", "thread")
        )
        or type(ledger["rows"]) is not list
        or len(ledger["rows"]) != len(expected)
        or type(row["events"]) is not list
        or len(row["events"]) != 2 * len(expected)
    ):
        raise ArithmeticError("complete source phase inventory required")
    for item in [*ledger["rows"], *row["events"]]:
        if type(item) is not dict:
            raise ArithmeticError("typed source boundary required")
        keys = {"index", "read", "parent", "category", "status", "before"}
        if item.get("status") == "complete":
            keys.add("after")
        if (
            set(item) != keys
            or item.get("status") not in ("running", "complete")
            or type(item["index"]) is not int
            or type(item["read"]) is not int
            or item["parent"] is not None
            and type(item["parent"]) is not int
        ):
            raise ArithmeticError("typed source event schema required")
        for clock in (
            (item["before"], item["after"]) if "after" in item else (item["before"],)
        ):
            prior.check_clock(clock)
            if any(clock[k] != before[k] for k in ("pid", "thread")):
                raise ArithmeticError("source event producer changed")
    if any(item["status"] != "complete" for item in ledger["rows"]):
        raise ArithmeticError("complete retained source boundaries required")
    cpu = dict.fromkeys(dict.fromkeys(CHILDREN), 0.0)
    root_cpu = 0.0
    if expected:
        root = ledger["rows"][0]
        root_cpu = root["after"]["cpu"] - root["before"]["cpu"]
        previous = root["before"]
        events = []
        for i, (item, category) in enumerate(
            zip(ledger["rows"], expected, strict=True)
        ):
            if (
                item["index"] != i
                or item["read"] != index
                or item["category"] != category
                or item["status"] != "complete"
                or item["parent"] != (None if i == 0 else 0)
            ):
                raise ArithmeticError(
                    "one root and six ordered source children required"
                )
            lower, upper = (before, after) if i == 0 else (previous, root["after"])
            if not all(
                lower[k] <= item["before"][k] <= item["after"][k] <= upper[k]
                for k in ("cpu", "wall")
            ):
                raise ArithmeticError("source boundary overlaps or escapes its parent")
            start = copy.deepcopy(item)
            del start["after"]
            start["status"] = "running"
            if i == 0:
                events.append(start)
            else:
                events.extend((start, item))
                cpu[category] += item["after"]["cpu"] - item["before"]["cpu"]
                previous = item["after"]
        events.append(root)
        if events != row["events"]:
            raise ArithmeticError("independent nested event stream changed")
    total = after["cpu"] - before["cpu"]
    remaining, outside = root_cpu - sum(cpu.values()), total - root_cpu
    if min(remaining, outside) < -1e-9:
        raise ArithmeticError("selected CPU exceeds enclosing source/read CPU")
    return dict(
        child_cpu_seconds=cpu,
        source_cpu_seconds=root_cpu,
        remaining_source_cpu_seconds=remaining,
        read_cpu_seconds=total,
        outside_source_cpu_seconds=outside,
        selected_calls=len(expected),
    )


def validate_state(
    state: Any, reads: Any, *, enabled: bool, pid: int, thread: int
) -> list[dict[str, Any]]:
    wanted = dict(
        enabled=enabled,
        pid=pid,
        thread=thread,
        active=False,
        restored=True,
        aliases_remaining=0,
        original_functions_unchanged=True,
        module_aliases_restored=True,
        errors=0,
        cleanup_failures=[],
        selected_calls=14 if enabled else 0,
        maximum=32,
        read_count=3,
        categories=list(CATEGORIES),
    )
    if (
        type(enabled) is not bool
        or type(pid) is not int
        or type(thread) is not int
        or min(pid, thread) <= 0
        or type(state) is not dict
        or set(state) != set(wanted)
        or any(
            type(state[k]) is not type(v) or state[k] != v for k, v in wanted.items()
        )
        or type(reads) is not list
        or len(reads) != 3
    ):
        raise ArithmeticError("complete restored source observer state required")
    results = []
    for index, row in enumerate(reads):
        results.append(validate_read(row, index, enabled=enabled))
        if (
            row["before"]["pid"] != pid
            or row["before"]["thread"] != thread
            or index
            and any(
                reads[index - 1]["after"][k] > row["before"][k] for k in ("cpu", "wall")
            )
        ):
            raise ArithmeticError("ordered actual read producer required")
    return results
