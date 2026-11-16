"""Seven named parent-reader phases; no changes to reusable scientific functions.

The checkpoint observer supplies its tested clock, read lifecycle and restoration
machinery. This observer uses disjoint phases instead of nested checkpoints.
"""

import copy
import functools
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

import checkpoint_cpu_support as prior
import profile_coarse_reader as coarse

CATEGORIES = ("source_load", "standin_load", "own_replay")
INVENTORIES = (("own_replay",), CATEGORIES, CATEGORIES)
BUSY = False


class Phases(prior.ScopedRegions):
    """Observe only sequential named calls inside an active complete read."""

    def wrap(self, category: str, function: Callable[..., Any]) -> Callable[..., Any]:
        if category not in CATEGORIES or getattr(function, "_coarse_cpu_region", False):
            raise ArithmeticError("fresh named reader phase required")

        @functools.wraps(function)
        def selected(*args: Any, **kwargs: Any) -> Any:
            if not self.active:
                return function(*args, **kwargs)
            self.owner()
            if self.stack or self.emitting or self.total >= self.maximum:
                self.errors += 1
                raise ArithmeticError("serial disjoint reader phase/cap required")
            index = len(self.rows)
            row: dict[str, Any] = dict(
                index=index,
                read=self.read_index,
                parent=None,
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
                    if self.stack != [index]:
                        raise ArithmeticError("reader phase stack changed")
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

    from poker_ai.evaluation import compact_opponent_sources as sources
    from poker_ai.evaluation import opponent_learning_own as own

    return (
        ("source_load", cli, "load", sources.load),
        ("standin_load", cli, "load_standins", sources.standins),
        ("own_replay", cli, "replay", own.replay),
    )


class Observer(prior.Observer):
    """Reuse the proven three-read lifecycle with three callsite-only bindings."""

    def __init__(
        self,
        *,
        enabled: bool,
        maximum: int = 16,
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
        self.regions = Phases(maximum, read_clock=read_clock)

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
            raise ArithmeticError("fresh reader observer scope required")
        declared = targets()
        if any(
            getattr(owner, name) is not original
            for _, owner, name, original in declared
        ):
            raise ArithmeticError("unchanged named reader phase callsites required")
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
            self.original_root_unchanged = all(
                original is target[3]
                for (_, _, _, original), target in zip(declared, targets(), strict=True)
            )
            self.restored = (
                bindings.restored
                and self.original_root_unchanged
                and all(
                    getattr(owner, name) is original
                    for _, owner, name, original in declared
                )
            )
            if not self.restored and primary is None:
                raise ArithmeticError("reader phase restoration incomplete")

    def state(self) -> dict[str, Any]:
        result = super().state()
        result["original_functions_unchanged"] = result.pop("original_root_unchanged")
        result["categories"] = list(CATEGORIES)
        return result


def validate_read(row: Any, index: int, *, enabled: bool) -> dict[str, Any]:
    """Validate saved disjoint intervals without constructing or replaying games."""
    if type(index) is not int or not 0 <= index < 3 or type(enabled) is not bool:
        raise ArithmeticError("typed read index and explicit observation mode required")
    if (
        type(row) is not dict
        or set(row) != {"index", "status", "before", "after", "ledger", "events"}
        or type(row["index"]) is not int
        or row["index"] != index
        or row["status"] != "complete"
    ):
        raise ArithmeticError("complete ordered reader phase record required")
    before, after = row["before"], row["after"]
    for clock in (before, after):
        prior.check_clock(clock)
    if any(after[k] < before[k] for k in ("cpu", "wall")) or any(
        before[k] != after[k] for k in ("pid", "thread")
    ):
        raise ArithmeticError("one monotone serial read producer required")
    ledger = row["ledger"]
    expected = INVENTORIES[index] if enabled else ()
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
        raise ArithmeticError("complete typed reader phase inventory required")
    previous = before
    cpu: dict[str, float] = dict.fromkeys(CATEGORIES, 0.0)
    for event in row["events"]:
        keys = {"index", "read", "parent", "category", "status", "before"}
        if type(event) is not dict:
            raise ArithmeticError("typed reader phase event required")
        if event.get("status") == "complete":
            keys.add("after")
        if (
            set(event) != keys
            or event.get("status") not in ("running", "complete")
            or type(event["index"]) is not int
            or type(event["read"]) is not int
            or event["parent"] is not None
        ):
            raise ArithmeticError("typed reader phase event schema required")
        prior.check_clock(event["before"])
        if event["status"] == "complete":
            prior.check_clock(event["after"])
    for i, (item, category) in enumerate(zip(ledger["rows"], expected, strict=True)):
        keys = {"index", "read", "parent", "category", "status", "before", "after"}
        if (
            type(item) is not dict
            or set(item) != keys
            or type(item["index"]) is not int
            or type(item["read"]) is not int
            or item["index"] != i
            or item["read"] != index
            or item["parent"] is not None
            or item["category"] != category
            or item["status"] != "complete"
        ):
            raise ArithmeticError("ordered disjoint complete phase required")
        for clock in (item["before"], item["after"]):
            prior.check_clock(clock)
            if any(clock[k] != before[k] for k in ("pid", "thread")):
                raise ArithmeticError("reader phase producer changed")
        if not all(
            previous[k] <= item["before"][k] <= item["after"][k] <= after[k]
            for k in ("wall", "cpu")
        ):
            raise ArithmeticError("reader phases overlap or escape whole read")
        start = copy.deepcopy(item)
        del start["after"]
        start["status"] = "running"
        if row["events"][2 * i : 2 * i + 2] != [start, item]:
            raise ArithmeticError("reader phase start/end events changed")
        cpu[category] += item["after"]["cpu"] - item["before"]["cpu"]
        previous = item["after"]
    total = after["cpu"] - before["cpu"]
    residual = total - sum(cpu.values())
    if residual < -1e-9:
        raise ArithmeticError("selected phase CPU exceeds whole read")
    return dict(
        phase_cpu_seconds=cpu,
        read_cpu_seconds=total,
        remaining_read_cpu_seconds=residual,
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
        errors=0,
        cleanup_failures=[],
        selected_calls=7 if enabled else 0,
        maximum=16,
        read_count=3,
        categories=list(CATEGORIES),
    )
    if (
        type(enabled) is not bool
        or type(pid) is not int
        or type(thread) is not int
        or pid <= 0
        or thread <= 0
        or type(state) is not dict
        or set(state) != set(wanted)
        or any(
            type(state[k]) is not type(v) or state[k] != v for k, v in wanted.items()
        )
        or type(reads) is not list
        or len(reads) != 3
    ):
        raise ArithmeticError("complete restored reader phase state required")
    results = []
    for index, row in enumerate(reads):
        results.append(validate_read(row, index, enabled=enabled))
        if row["before"]["pid"] != pid or row["before"]["thread"] != thread:
            raise ArithmeticError("complete actual reader producer required")
        if index and any(
            reads[index - 1]["after"][k] > row["before"][k] for k in ("cpu", "wall")
        ):
            raise ArithmeticError("complete reader intervals overlap")
    return results
