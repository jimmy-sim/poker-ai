"""Three-level archive boundaries; scientific functions remain unchanged."""

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

ROOT = "parent_archive"
PARENTS = {
    ROOT: None,
    "sampled_gather": ROOT,
    "sampled_contexts": "sampled_gather",
    "sampled_decode": "sampled_gather",
    "sampled_scores": "sampled_gather",
    "full_contexts": ROOT,
    "full_decode": ROOT,
    "prior_full": ROOT,
    "prior_decode": "prior_full",
}
CATEGORIES = tuple(PARENTS)
BUSY = False


def inventory() -> tuple[tuple[str, int | None], ...]:
    """Predeclared preorder: 36 warm states, 108 saved states, two full archives."""
    rows: list[tuple[str, int | None]] = [
        (ROOT, None),
        ("sampled_gather", 0),
        ("sampled_contexts", 1),
    ]
    for _ in range(36):
        rows.append(("sampled_decode", 1))
        for _ in range(3):
            rows.extend((("sampled_decode", 1), ("sampled_scores", 1)))
    rows.append(("full_contexts", 0))
    rows.extend(("full_decode", 0) for _ in range(72))
    parent = len(rows)
    rows.append(("prior_full", 0))
    rows.extend(("prior_decode", parent) for _ in range(72))
    return tuple(rows)


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
    """A root owns nested serial children; calls outside the root pass through."""

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
                    not self.stack
                    or self.rows[self.stack[-1]]["category"] != PARENTS[category]
                )
            ):
                self.errors += 1
                raise ArithmeticError(
                    "archive recursion/reentrancy/parent/cap unsupported"
                )
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
    from poker_ai.evaluation import compact_fixed_inputs as full
    from poker_ai.evaluation import compact_sampled_own as own
    from poker_ai.evaluation import compact_sampled_prior as prior_full
    from poker_ai.postflop import compact_sampled_state as state

    return (
        ("sampled_decode", own, "decode", state.decode),
        ("sampled_scores", own, "scores", state.scores),
        ("prior_full", full, "prior_full", prior_full.verify),
    )


def module_targets() -> tuple[tuple[str, ModuleType, str, ModuleType, str], ...]:
    from poker_ai.evaluation import compact_fixed_inputs as full
    from poker_ai.evaluation import compact_opponent_sources as source
    from poker_ai.evaluation import compact_sampled_inputs as inputs
    from poker_ai.evaluation import compact_sampled_own as own
    from poker_ai.evaluation import compact_sampled_prior as prior_full
    from poker_ai.postflop import compact_full_artifacts as files

    return (
        (ROOT, source, "sampled_parent", full, "replay_sources"),
        ("sampled_gather", full, "old_own", own, "gather"),
        ("sampled_contexts", own, "inputs", inputs, "game_contexts"),
        ("full_contexts", full, "old_inputs", inputs, "game_contexts"),
        ("full_decode", full, "files", files, "decode"),
        ("prior_decode", prior_full, "old", files, "decode"),
    )


class Observer(prior.Observer):
    """Reuse read clocks and cleanup; scope observations to the named root."""

    def __init__(
        self,
        *,
        enabled: bool,
        maximum: int = 1024,
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
            raise ArithmeticError("fresh main-thread archive observer required")
        declared, modules = targets(), module_targets()
        if any(
            getattr(owner, name) is not original
            for _, owner, name, original in declared
        ) or any(
            getattr(owner, name) is not original
            for _, owner, name, original, _ in modules
        ):
            raise ArithmeticError(
                "unchanged archive callsite and module aliases required"
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
                raise ArithmeticError("archive observer restoration incomplete")

    def state(self) -> dict[str, Any]:
        result = super().state()
        result["original_functions_unchanged"] = result.pop("original_root_unchanged")
        result["module_aliases_restored"] = self.module_aliases_restored
        result["categories"] = list(CATEGORIES)
        return result


def validate_read(row: Any, index: int, *, enabled: bool) -> dict[str, Any]:
    """Reconstruct the complete serial tree from saved clocks, without replay."""
    if type(index) is not int or not 0 <= index < 3 or type(enabled) is not bool:
        raise ArithmeticError("typed index and explicit observation mode required")
    if (
        type(row) is not dict
        or set(row) != {"index", "status", "before", "after", "ledger", "events"}
        or type(row["index"]) is not int
        or row["index"] != index
        or row["status"] != "complete"
    ):
        raise ArithmeticError("complete ordered archive read required")
    before, after, ledger = row["before"], row["after"], row["ledger"]
    for clock in (before, after):
        prior.check_clock(clock)
    if any(after[k] < before[k] for k in ("cpu", "wall")) or any(
        before[k] != after[k] for k in ("pid", "thread")
    ):
        raise ArithmeticError("one monotone serial read producer required")
    expected = inventory() if enabled and index else ()
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
        raise ArithmeticError("complete archive boundary inventory required")
    rows = ledger["rows"]
    for item in [*rows, *row["events"]]:
        if type(item) is not dict:
            raise ArithmeticError("typed archive boundary required")
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
            raise ArithmeticError("typed archive event schema required")
        for clock in (
            (item["before"], item["after"]) if "after" in item else (item["before"],)
        ):
            prior.check_clock(clock)
            if any(clock[k] != before[k] for k in ("pid", "thread")):
                raise ArithmeticError("archive event producer changed")
    inclusive = dict.fromkeys(CATEGORIES, 0.0)
    residual = dict.fromkeys(CATEGORIES, 0.0)
    children: dict[int | None, list[int]] = {}
    for i, (item, (category, parent)) in enumerate(zip(rows, expected, strict=True)):
        if (
            item["index"] != i
            or item["read"] != index
            or item["category"] != category
            or item["parent"] != parent
            or item["status"] != "complete"
        ):
            raise ArithmeticError("exact ordered archive hierarchy required")
        children.setdefault(parent, []).append(i)
        inclusive[category] += item["after"]["cpu"] - item["before"]["cpu"]
    events = []

    def visit(parent: int | None) -> None:
        lower = before if parent is None else rows[parent]["before"]
        upper = after if parent is None else rows[parent]["after"]
        previous = lower
        child_cpu = 0.0
        for i in children.get(parent, []):
            item = rows[i]
            if not all(
                previous[k] <= item["before"][k] <= item["after"][k] <= upper[k]
                for k in ("cpu", "wall")
            ):
                raise ArithmeticError("archive boundary overlaps or escapes parent")
            start = copy.deepcopy(item)
            del start["after"]
            start["status"] = "running"
            events.append(start)
            visit(i)
            events.append(item)
            previous = item["after"]
            child_cpu += item["after"]["cpu"] - item["before"]["cpu"]
        if parent is not None:
            item = rows[parent]
            own = item["after"]["cpu"] - item["before"]["cpu"] - child_cpu
            if own < -1e-9:
                raise ArithmeticError("children exceed archive parent CPU")
            residual[item["category"]] += own

    visit(None)
    if events != row["events"]:
        raise ArithmeticError("independent nested archive event stream changed")
    total = after["cpu"] - before["cpu"]
    outside = total - inclusive[ROOT]
    if outside < -1e-9 or abs(sum(residual.values()) - inclusive[ROOT]) > 1e-9:
        raise ArithmeticError("disjoint archive CPU reconciliation failed")
    return dict(
        inclusive_cpu_seconds=inclusive,
        residual_cpu_seconds=residual,
        archive_cpu_seconds=inclusive[ROOT],
        outside_archive_cpu_seconds=outside,
        read_cpu_seconds=total,
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
        selected_calls=802 if enabled else 0,
        maximum=1024,
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
        raise ArithmeticError("complete restored archive observer state required")
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
            raise ArithmeticError("ordered actual archive read producer required")
    return results
