"""Bounded, mutation-isolated context graphs for one archive validation root.

Research-only caller hooks are installed below; defining factories stay intact.
Graph copies preserve exact scalar/array bits and internal object aliases. Unknown
layouts reject rather than silently dropping data or weakening a check.
"""

import functools
import hashlib
import os
import struct
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, fields
from enum import Enum
from pathlib import Path
from types import ModuleType
from typing import Any, Literal

import numpy as np
import profile_coarse_reader as clocks


def graph_types() -> tuple[type[Any], ...]:
    """The complete prospective dataclass whitelist, including nested state."""
    from poker_ai.abstraction.actions import ActionAbstraction
    from poker_ai.cards import Deck
    from poker_ai.engine import Action, ActionRecord, HoldemState, Pot
    from poker_ai.finite import ArrayTree
    from poker_ai.postflop.compact_full_context import Context
    from poker_ai.postflop.controlled_scoring import ScoringContext
    from poker_ai.postflop.game import RangeHand, Spot, SpotState
    from poker_ai.postflop.matrix import MatrixTree
    from poker_ai.postflop.tree import SpotTree
    from poker_ai.toy.games import ToyState
    from poker_ai.toy.tree import Tree
    from poker_ai.training.no_limit import NoLimitRules

    return (
        Context,
        ScoringContext,
        ArrayTree,
        MatrixTree,
        SpotTree,
        Spot,
        SpotState,
        RangeHand,
        NoLimitRules,
        ActionAbstraction,
        HoldemState,
        Action,
        ActionRecord,
        Pot,
        Deck,
        Tree,
        ToyState,
    )


def array_layout(value: Any) -> tuple[Any, ...]:
    """Only exactly supported contiguous primitive layouts may be copied."""
    if type(value) is not np.ndarray or value.dtype not in (
        np.dtype(np.bool_),
        np.dtype(np.int64),
        np.dtype(np.float64),
    ):
        raise ArithmeticError("unsupported context array type/dtype")
    if (
        not (value.flags.c_contiguous or value.flags.f_contiguous)
        or not value.flags.aligned
        or value.flags.writebackifcopy
    ):
        raise ArithmeticError("unsupported context array layout")
    return (
        value.dtype.str,
        value.shape,
        value.strides,
        bool(value.flags.writeable),
        bool(value.flags.owndata),
        bool(value.flags.c_contiguous),
        bool(value.flags.f_contiguous),
        bool(value.flags.aligned),
    )


class Graph:
    """One traversal memo; witnesses include alias topology and every field.

    Cycles and distinct overlapping ndarray views reject. Immutable scalar
    identities are irrelevant; all container/dataclass/array aliases are retained.
    Arrays do not share storage across successful clones, including readonly ones.
    """

    def __init__(self, *, copying: bool = False) -> None:
        self.copying = copying
        self.allowed = graph_types()
        self.memo: dict[int, tuple[int, Any]] = {}
        self.active: set[int] = set()
        self.arrays: list[Any] = []
        self.mutables: set[int] = set()
        self.hash = hashlib.sha256()

    def emit(self, value: bytes) -> None:
        self.hash.update(struct.pack(">Q", len(value)))
        self.hash.update(value)

    def visit(self, value: Any) -> Any:
        from poker_ai.engine import ActionKind, Street

        kind = type(value)
        if kind in (type(None), bool, int, str, bytes, float):
            self.emit(kind.__name__.encode())
            self.emit(
                struct.pack(">d", value)
                if kind is float
                else value
                if kind is bytes
                else str(value).encode("utf-8")
            )
            return value
        if kind in (ActionKind, Street):
            self.emit(kind.__name__.encode())
            self.emit(value.name.encode())
            return value
        if isinstance(value, Enum):
            raise ArithmeticError("unsupported context enum")
        if kind in (np.bool_, np.int64, np.float64):
            self.emit(kind.__name__.encode())
            self.emit(value.tobytes())
            return value.copy() if self.copying else value
        if kind not in (*self.allowed, tuple, list, dict, np.ndarray):
            raise ArithmeticError("unsupported context graph object")
        identity = id(value)
        if identity in self.active:
            raise ArithmeticError("cyclic context graph unsupported")
        if identity in self.memo:
            self.emit(b"reference")
            self.emit(str(self.memo[identity][0]).encode())
            return self.memo[identity][1]
        self.active.add(identity)
        self.emit((kind.__module__ + "." + kind.__qualname__).encode())
        self.memo[identity] = len(self.memo), value
        try:
            if kind is np.ndarray:
                result = self.array(value)
            elif kind in (tuple, list, dict):
                result = self.container(value)
            else:
                result = self.dataclass(value)
            self.memo[identity] = self.memo[identity][0], result
            return result
        finally:
            self.active.remove(identity)

    def array(self, value: Any) -> Any:
        layout = array_layout(value)
        if any(np.shares_memory(value, other) for other in self.arrays):
            raise ArithmeticError("distinct overlapping context arrays unsupported")
        self.arrays.append(value)
        self.mutables.add(id(value))
        self.emit(repr(layout).encode())
        self.emit(value.tobytes(order="A"))
        if not self.copying:
            return value
        order: Literal["C", "F"] = "F" if value.flags.f_contiguous else "C"
        if value.flags.owndata:
            result = np.empty(value.shape, dtype=value.dtype, order=order)
        else:
            storage = np.empty(value.nbytes, dtype=np.uint8)
            result = np.ndarray(
                value.shape, dtype=value.dtype, buffer=storage, strides=value.strides
            )
        result[...] = value
        result.setflags(write=bool(value.flags.writeable))
        if array_layout(result) != layout:
            raise ArithmeticError("isolated array copy changed exact layout/flags")
        return result

    def container(self, value: Any) -> Any:
        kind = type(value)
        self.emit(str(len(value)).encode())
        if kind is dict:
            self.mutables.add(id(value))
            pairs = [(self.visit(k), self.visit(v)) for k, v in value.items()]
            return dict(pairs) if self.copying else value
        if kind is list:
            self.mutables.add(id(value))
        result = [self.visit(v) for v in value]
        return (tuple(result) if kind is tuple else result) if self.copying else value

    def dataclass(self, value: Any) -> Any:
        declared = fields(value)
        if hasattr(value, "__dict__") and set(vars(value)) != {
            f.name for f in declared
        }:
            raise ArithmeticError("extra/missing context instance attributes")
        # Treat frozen dataclasses as mutable graph nodes too: object.__setattr__
        # can change them, and their fields may contain mutable arrays/dicts.
        self.mutables.add(id(value))
        result = object.__new__(type(value)) if self.copying else value
        for field in declared:
            self.emit(field.name.encode())
            item = self.visit(getattr(value, field.name))
            if self.copying:
                object.__setattr__(result, field.name, item)
        return result


def witness(value: Any) -> str:
    graph = Graph()
    graph.visit(value)
    return graph.hash.hexdigest()


def isolated_clone(value: Any) -> Any:
    """Copy a supported graph, independently compare it and prove isolation."""
    original = Graph(copying=True)
    result = original.visit(value)
    copied = Graph()
    copied.visit(result)
    if original.hash.digest() != copied.hash.digest() or original.mutables & (
        copied.mutables
    ):
        raise ArithmeticError("clone changed graph or shared mutable objects")
    if any(np.shares_memory(a, b) for a in original.arrays for b in copied.arrays):
        raise ArithmeticError("clone shares array storage")
    return result


# Caller hooks are intentionally separate from the exact graph primitive above.
# No original scientific function, learner, or reference output is modified.
Clock = Callable[[], dict[str, Any]]

BUSY = False


@dataclass(frozen=True)
class Alias:
    delegate: ModuleType
    member: str
    selected: Callable[..., Any]

    def __getattr__(self, name: str) -> Any:
        return self.selected if name == self.member else getattr(self.delegate, name)


def guard_inputs(root: Path) -> None:
    from poker_ai.postflop.public_range_definition import check_inputs, contract

    check_inputs(root, contract(root))


def expected_keys(root: Path, software: bool) -> tuple[tuple[str, str], ...]:
    from poker_ai.postflop.public_range_definition import contract

    design = contract(root)
    spots = (
        ("software-kuhn-1", "software-kuhn--1") if software else design["spot_files"]
    )
    return tuple((spot, rep) for spot in spots for rep in design["representations"])


class Session:
    """Serial root-local lifetime and complete measured request inventory.

    Ordinary mode forwards the original factories; reuse mode guards every
    request and stores one complete isolated template. No file verdict, policy,
    score, reference answer, or context across roots is reused.
    """

    def __init__(
        self,
        *,
        enabled: bool,
        maximum: int = 32,
        clock: Clock = clocks.clock,
        sink: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        from poker_ai.evaluation import compact_sampled_inputs as inputs
        from poker_ai.postflop.compact_full_context import contexts

        if type(enabled) is not bool or type(maximum) is not int or maximum != 32:
            raise ArithmeticError(
                "explicit reuse mode and fixed32 boundary cap required"
            )
        self.enabled, self.maximum = enabled, maximum
        self.clock, self.sink = clock, sink
        self.pid, self.thread = os.getpid(), threading.get_ident()
        self.factory, self.iterator_factory = inputs.game_contexts, contexts
        self.guard = guard_inputs
        self.guard_original = guard_inputs
        self.rows: list[dict[str, Any]] = []
        self.events: list[dict[str, Any]] = []
        self.cleanup_failures: list[str] = []
        self.facts = dict(
            roots=0,
            requests=0,
            materializations=0,
            original_iterators=0,
            misses=0,
            hits=0,
            input_guards=0,
            template_clones=0,
            return_clones=0,
        )
        self.token: object | None = None
        self.root_path: Path | None = None
        self.software: bool | None = None
        self.keys: tuple[tuple[str, str], ...] = ()
        self.template: dict[tuple[str, str], Any] | None = None
        self.template_sha: str | None = None
        self.inflight = False
        self.emitting = False
        self.request_kinds: list[str] = []
        self.installed = False
        self.used = False
        self.restored = False
        self.bindings: list[tuple[Any, str, Any, Any]] = []

    def owner(self) -> None:
        if self.emitting:
            raise ArithmeticError("context observer callback reentrancy refused")
        if (os.getpid(), threading.get_ident()) != (self.pid, self.thread):
            raise ArithmeticError("one serial context-reuse PID/thread required")

    def boundaries(self) -> None:
        self.owner()
        if (
            self.guard is not self.guard_original
            or guard_inputs is not self.guard_original
        ):
            raise ArithmeticError("context input guard binding changed")
        if self.installed:
            from poker_ai.evaluation import compact_sampled_inputs as inputs
            from poker_ai.postflop import compact_full_context as full

            if (
                vars(inputs)["contexts"] is not self.iterator_factory
                or inputs.game_contexts is not self.factory
                or full.contexts is not (self.iterator_factory)
            ):
                raise ArithmeticError("defining context factory changed")
            if any(getattr(o, n) is not proxy for o, n, _, proxy in self.bindings):
                raise ArithmeticError("installed caller binding changed")

    def publish(self, row: dict[str, Any], phase: str) -> None:
        # Snapshot the row; an event never aliases the mutable running ledger.
        event = dict(index=row["index"], phase=phase, clock=self.clock())
        if phase == "end":
            event.update(status=row["status"], facts=dict(self.facts))
        self.events.append(event)
        if self.sink is not None:
            self.emitting = True
            try:
                self.sink(event)
            finally:
                self.emitting = False

    @contextmanager
    def region(self, kind: str) -> Iterator[dict[str, Any]]:
        self.boundaries()
        if len(self.rows) >= self.maximum:
            raise ArithmeticError("context-reuse boundary cap exhausted")
        row: dict[str, Any] = dict(
            index=len(self.rows),
            kind=kind,
            root=self.facts["roots"] - 1,
            status="running",
            before=self.clock(),
        )
        self.rows.append(row)
        primary: BaseException | None = None
        try:
            self.publish(row, "start")
            yield row
        except BaseException as error:
            primary = error
            row.update(status="primary_failed", failure_kind=type(error).__name__)
            raise
        finally:
            try:
                row["after"] = self.clock()
                if primary is None:
                    row["status"] = "complete"
                self.publish(row, "end")
            except BaseException as error:
                self.cleanup_failures.append(type(error).__name__)
                row["status"] = "cleanup_failed"
                if primary is None:
                    raise

    def check_template(self) -> None:
        if self.template is not None and witness(self.template) != self.template_sha:
            raise ArithmeticError("cached context template mutated")

    @contextmanager
    def root(self, root: Path, software: bool) -> Iterator[None]:
        self.boundaries()
        if (
            self.token is not None
            or self.inflight
            or self.cleanup_failures
            or type(software) is not bool
        ):
            raise ArithmeticError("fresh non-nested typed archive root required")
        if not isinstance(root, Path) or root != root.resolve():
            raise ArithmeticError("resolved archive root required")
        self.root_path, self.software = root, software
        self.token = object()
        self.request_kinds = []
        self.facts["roots"] += 1
        try:
            with self.region("archive_root"):
                primary: BaseException | None = None
                try:
                    self.keys = expected_keys(root, software)
                    self.rows[-1].update(
                        software=software,
                        root_path=str(root),
                        keys=[list(k) for k in self.keys],
                    )
                    yield
                except BaseException as error:
                    primary = error
                    raise
                finally:
                    try:
                        self.boundaries()
                        self.check_template()
                        if self.inflight:
                            raise ArithmeticError(
                                "partial context iterator at root exit"
                            )
                        if self.cleanup_failures:
                            raise ArithmeticError("context cleanup already failed")
                    except BaseException as error:
                        self.cleanup_failures.append(type(error).__name__)
                        if primary is None:
                            raise
                    finally:
                        # Include releasing the cached graph in the root clock.
                        self.template = None
                        self.template_sha = None
        finally:
            self.template = None
            self.template_sha = None
            self.root_path = None
            self.software = None
            self.token = None
            self.keys = ()
            self.inflight = False

    @contextmanager
    def request(
        self, kind: str, root: Path, software: bool
    ) -> Iterator[dict[str, Any]]:
        self.boundaries()
        if (
            self.token is None
            or self.inflight
            or root != self.root_path
            or type(software) is not bool
            or software is not self.software
            or kind not in ("sampled_dictionary", "full_dictionary", "prior_iterator")
            or len(self.request_kinds) >= 3
            or kind
            != ("sampled_dictionary", "full_dictionary", "prior_iterator")[
                len(self.request_kinds)
            ]
        ):
            raise ArithmeticError("ordered same-root/scope serial request required")
        token = self.token
        self.inflight = True
        self.request_kinds.append(kind)
        self.facts["requests"] += 1
        try:
            with self.region(kind) as row:
                if self.enabled:
                    self.guard(root)
                    self.facts["input_guards"] += 1
                    self.check_template()
                yield row
                self.boundaries()
                self.check_template()
        finally:
            if self.token is token:
                self.inflight = False

    def validate_collection(self, result: Any) -> None:
        from poker_ai.postflop.compact_full_context import Context

        if (
            type(result) is not dict
            or tuple(result) != self.keys
            or any(
                type(c) is not Context or (c.spot_file, c.representation) != key
                for key, c in result.items()
            )
        ):
            raise ArithmeticError(
                "complete original ordered12-context inventory required"
            )

    def cached(self) -> dict[tuple[str, str], Any]:
        if self.template is None:
            raise ArithmeticError("complete first context collection required")
        self.check_template()
        result: dict[tuple[str, str], Any] = isolated_clone(self.template)
        self.facts["return_clones"] += 1
        self.check_template()
        self.validate_collection(result)
        self.facts["hits"] += 1
        return result

    def dictionary(self, kind: str, *args: Any, **kwargs: Any) -> Any:
        if self.emitting:
            self.owner()
        if self.token is None:
            return self.factory(*args, **kwargs)
        if len(args) != 2 or kwargs or args[1] not in ("software", "real"):
            raise ArithmeticError("original typed positional context call required")
        with self.request(kind, args[0], args[1] == "software") as row:
            if self.enabled and self.template is not None:
                result = self.cached()
                row["collection_sha256"] = witness(result)
                return result
            self.facts["materializations"] += 1
            result = self.factory(*args, **kwargs)
            self.validate_collection(result)
            if self.enabled:
                self.template = isolated_clone(result)
                self.facts["template_clones"] += 1
                self.template_sha = witness(self.template)
                self.facts["misses"] += 1
            row["collection_sha256"] = witness(result)
            return result

    def iterator(self, *args: Any, **kwargs: Any) -> Iterator[Any]:
        if self.emitting:
            self.owner()
        if self.token is None:
            return self.iterator_factory(*args, **kwargs)
        token = self.token

        def consumed() -> Iterator[Any]:
            if self.token is not token:
                raise ArithmeticError("deferred context iterator outlived archive root")
            if len(args) != 1 or set(kwargs) != {"software"}:
                raise ArithmeticError("original positional-root keyword-scope required")
            complete = False
            try:
                with self.request("prior_iterator", args[0], kwargs["software"]) as row:
                    if self.enabled:
                        sequence: Iterator[Any] = iter(self.cached().values())
                    else:
                        self.facts["original_iterators"] += 1
                        sequence = self.iterator_factory(*args, **kwargs)
                    keys = []
                    collected = {}
                    for context in sequence:
                        self.boundaries()
                        if self.token is not token:
                            raise ArithmeticError("iterator outlived its root")
                        keys.append((context.spot_file, context.representation))
                        collected[keys[-1]] = context
                        yield context
                        if self.token is not token:
                            raise ArithmeticError("iterator outlived its root")
                    if tuple(keys) != self.keys:
                        raise ArithmeticError(
                            "complete original ordered iterator required"
                        )
                    row["collection_sha256"] = witness(collected)
                    complete = True
            finally:
                if not complete:
                    self.cleanup_failures.append("incomplete_iterator")

        return consumed()

    def state(self) -> dict[str, Any]:
        return dict(
            enabled=self.enabled,
            facts=dict(self.facts),
            rows=self.rows,
            events=self.events,
            final_entries=int(self.template is not None),
            root_active=self.token is not None,
            inflight=self.inflight,
            emitting=self.emitting,
            cleanup_failures=list(self.cleanup_failures),
            restored=self.restored,
        )

    @contextmanager
    def hooks(self) -> Iterator[None]:
        """Patch only declared callers; remove late aliases, including this script."""
        global BUSY
        import sys

        from poker_ai.evaluation import compact_fixed_inputs as full
        from poker_ai.evaluation import compact_opponent_sources as source
        from poker_ai.evaluation import compact_sampled_inputs as inputs
        from poker_ai.evaluation import compact_sampled_own as own
        from poker_ai.evaluation import compact_sampled_prior as prior
        from poker_ai.postflop import compact_full_context as defining

        self.owner()
        if (
            self.used
            or BUSY
            or threading.current_thread() is not threading.main_thread()
        ):
            raise ArithmeticError("fresh main-thread context session required")
        if (
            inputs.game_contexts is not self.factory
            or defining.contexts is not self.iterator_factory
            or vars(source)["sampled_parent"] is not full
            or vars(own)["inputs"] is not inputs
            or vars(full)["old_inputs"] is not inputs
            or vars(prior)["contexts"] is not self.iterator_factory
        ):
            raise ArithmeticError("unchanged declared context caller bindings required")
        original_root = full.replay_sources

        @functools.wraps(original_root)
        def selected(*args: Any, **kwargs: Any) -> Any:
            if not self.installed:
                return original_root(*args, **kwargs)
            if len(args) != 2 or kwargs:
                raise ArithmeticError(
                    "unchanged positional archive call shape required"
                )
            with self.root(*args):
                return original_root(*args, **kwargs)

        self.bindings = [
            (source, "sampled_parent", full, Alias(full, "replay_sources", selected)),
            (
                own,
                "inputs",
                inputs,
                Alias(
                    inputs,
                    "game_contexts",
                    functools.partial(self.dictionary, "sampled_dictionary"),
                ),
            ),
            (
                full,
                "old_inputs",
                inputs,
                Alias(
                    inputs,
                    "game_contexts",
                    functools.partial(self.dictionary, "full_dictionary"),
                ),
            ),
            (prior, "contexts", self.iterator_factory, self.iterator),
        ]
        primary: BaseException | None = None
        self.used, BUSY = True, True
        try:
            for owner, name, _, proxy in self.bindings:
                setattr(owner, name, proxy)
            self.installed = True
            yield
        except BaseException as error:
            primary = error
            raise
        finally:
            self.installed = False
            try:
                # Restore direct imports and any proxy/selected-call aliases made
                # during the session. Never scan/patch arbitrary external modules.
                replacements = [
                    (proxy, original) for _, _, original, proxy in self.bindings
                ]
                replacements.append((selected, original_root))
                for _, _, original, proxy in self.bindings:
                    if isinstance(proxy, Alias):
                        replacements.append(
                            (proxy.selected, getattr(original, proxy.member))
                        )
                for module in tuple(sys.modules.values()):
                    if module is None or not (
                        module.__name__.startswith("poker_ai.")
                        or module.__name__ in {__name__, "compare_context_reuse"}
                    ):
                        continue
                    for name, value in tuple(vars(module).items()):
                        for proxy, original in replacements:
                            if value is proxy:
                                setattr(module, name, original)
                for owner, name, original, _ in reversed(self.bindings):
                    setattr(owner, name, original)
                self.restored = (
                    all(
                        getattr(o, n) is original for o, n, original, _ in self.bindings
                    )
                    and full.replay_sources is original_root
                    and inputs.game_contexts is self.factory
                    and defining.contexts is self.iterator_factory
                )
                if not self.restored:
                    raise ArithmeticError("context-reuse caller restoration incomplete")
            except BaseException as error:
                self.cleanup_failures.append(type(error).__name__)
                if primary is None:
                    raise
            finally:
                BUSY = False
                self.template = None
                self.template_sha = None
                self.token = None


def expected_facts(enabled: bool, roots: int = 2) -> dict[str, int]:
    """Complete prospective request/factory/copy counts, never inferred from time."""
    return dict(
        roots=roots,
        requests=3 * roots,
        materializations=roots if enabled else 2 * roots,
        original_iterators=0 if enabled else roots,
        misses=roots if enabled else 0,
        hits=2 * roots if enabled else 0,
        input_guards=3 * roots if enabled else 0,
        template_clones=roots if enabled else 0,
        return_clones=2 * roots if enabled else 0,
    )


def validate_session(
    state: Any,
    *,
    enabled: bool,
    pid: int,
    thread: int,
    keys: list[list[str]],
    roots: int = 2,
    software: bool = False,
) -> list[dict[str, Any]]:
    """Check saved complete serial boundaries; no graph/factory/solver execution."""
    import math
    import re

    from checkpoint_cpu_support import check_clock

    if (
        type(roots) is not int
        or roots not in (0, 1, 2)
        or type(pid) is not int
        or pid <= 0
        or type(thread) is not int
        or thread <= 0
        or type(software) is not bool
        or type(state) is not dict
        or set(state)
        != {
            "enabled",
            "facts",
            "rows",
            "events",
            "final_entries",
            "root_active",
            "inflight",
            "emitting",
            "cleanup_failures",
            "restored",
        }
        or type(enabled) is not bool
        or state["enabled"] is not enabled
        or state["root_active"] is not False
        or state["inflight"] is not False
        or state["emitting"] is not False
        or state["restored"] is not True
        or type(state["final_entries"]) is not int
        or state["final_entries"] != 0
        or state["cleanup_failures"] != []
        or type(state["facts"]) is not dict
        or state["facts"] != expected_facts(enabled, roots)
        or any(type(v) is not int for v in state["facts"].values())
        or type(state["rows"]) is not list
        or len(state["rows"]) != 4 * roots
        or type(state["events"]) is not list
        or len(state["events"]) != 8 * roots
    ):
        raise ArithmeticError("complete typed context-reuse inventory required")
    expected_kinds = (
        "archive_root",
        "sampled_dictionary",
        "full_dictionary",
        "prior_iterator",
    )
    hashes: set[str] = set()
    summaries = []
    for index, row in enumerate(state["rows"]):
        root, offset = divmod(index, 4)
        common = {"index", "root", "kind", "status", "before", "after"}
        expected = common | (
            {"software", "root_path", "keys"} if offset == 0 else {"collection_sha256"}
        )
        if (
            type(row) is not dict
            or set(row) != expected
            or type(row["index"]) is not int
            or row["index"] != index
            or type(row["root"]) is not int
            or row["root"] != root
            or row["kind"] != expected_kinds[offset]
            or row["status"] != "complete"
        ):
            raise ArithmeticError("complete ordered context boundary required")
        for stamp in (row["before"], row["after"]):
            check_clock(stamp)
            if stamp["pid"] != pid or stamp["thread"] != thread:
                raise ArithmeticError("same serial context producer required")
        if any(row["after"][k] < row["before"][k] for k in ("cpu", "wall")):
            raise ArithmeticError("monotone context clocks required")
        if offset:
            parent = state["rows"][4 * root]
            if any(
                not parent["before"][k]
                <= row["before"][k]
                <= row["after"][k]
                <= parent["after"][k]
                for k in ("cpu", "wall")
            ):
                raise ArithmeticError("context request outside archive root")
            if offset > 1 and any(
                state["rows"][index - 1]["after"][k] > row["before"][k]
                for k in ("cpu", "wall")
            ):
                raise ArithmeticError("serial context requests overlap")
            checksum = row["collection_sha256"]
            if (
                type(checksum) is not str
                or re.fullmatch("[0-9a-f]{64}", checksum) is None
            ):
                raise ArithmeticError("complete exact graph witness required")
            hashes.add(checksum)
        elif (
            row["software"] is not software
            or row["keys"] != keys
            or type(row["root_path"]) is not str
            or not Path(row["root_path"]).is_absolute()
        ):
            raise ArithmeticError("original archive context key/scope binding required")
        summaries.append(
            dict(
                index=index,
                root=root,
                kind=row["kind"],
                cpu_seconds=row["after"]["cpu"] - row["before"]["cpu"],
                wall_seconds=row["after"]["wall"] - row["before"]["wall"],
            )
        )
    if roots and len(hashes) != 1:
        raise ArithmeticError("fresh/reused complete context graph witnesses differ")
    order = []
    for root in range(roots):
        base = 4 * root
        order.append((base, "start"))
        for child in (base + 1, base + 2, base + 3):
            order.extend(((child, "start"), (child, "end")))
        order.append((base, "end"))
    previous: dict[str, Any] | None = None
    for event, (index, phase) in zip(state["events"], order, strict=True):
        if (
            type(event) is not dict
            or set(event)
            != (
                {"index", "phase", "clock"}
                | ({"status", "facts"} if phase == "end" else set())
            )
            or type(event["index"]) is not int
            or event["index"] != index
            or event["phase"] != phase
        ):
            raise ArithmeticError("ordered complete context events required")
        stamp = event["clock"]
        check_clock(stamp)
        row = state["rows"][index]
        if (
            stamp["pid"] != pid
            or stamp["thread"] != thread
            or any(
                not math.isfinite(stamp[k])
                or stamp[k] < row["before" if phase == "start" else "after"][k]
                for k in ("cpu", "wall")
            )
        ):
            raise ArithmeticError("context event producer/clock changed")
        if phase == "start" and any(
            stamp[k] > row["after"][k] for k in ("cpu", "wall")
        ):
            raise ArithmeticError("context start event outside boundary")
        if previous is not None and any(
            stamp[k] < previous[k] for k in ("cpu", "wall")
        ):
            raise ArithmeticError("context event clock reversed")
        if phase == "end" and (
            event["status"] != "complete"
            or type(event["facts"]) is not dict
            or set(event["facts"]) != set(state["facts"])
            or any(
                type(v) is not int or v < 0 or v > state["facts"][k]
                for k, v in event["facts"].items()
            )
        ):
            raise ArithmeticError("complete typed bounded context event facts required")
        if phase == "end":
            root, offset = divmod(index, 4)
            wanted = progress_facts(enabled, root + 1, offset or 3)
            if event["facts"] != wanted:
                raise ArithmeticError("context event factory/copy progress differs")
        previous = stamp
    if roots and state["events"][-1]["facts"] != state["facts"]:
        raise ArithmeticError("final context event inventory differs")
    return summaries


def progress_facts(
    enabled: bool, roots_started: int, current_requests: int
) -> dict[str, int]:
    """Expected completed work at each end event, including the root end."""
    facts = expected_facts(enabled, roots_started - 1)
    facts["roots"] = roots_started
    facts["requests"] += current_requests
    if current_requests >= 1:
        facts["materializations"] += 1
        if enabled:
            facts["misses"] += 1
            facts["template_clones"] += 1
    if current_requests >= 2:
        facts["materializations"] += int(not enabled)
    if current_requests >= 3:
        facts["original_iterators"] += int(not enabled)
    if enabled:
        facts["hits"] += max(0, current_requests - 1)
        facts["return_clones"] += max(0, current_requests - 1)
        facts["input_guards"] += current_requests
    return facts
