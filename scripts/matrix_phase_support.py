"""Private phase-localized original constructor; historical source stays unchanged."""

import ast
import functools
import hashlib
import inspect
import json
import math
import os
import textwrap
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from pathlib import Path
from types import MethodType
from typing import Any

import grouped_depth_support as previous
import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.matrix import Encoding, MatrixTree, observation_key
from poker_ai.postflop.tree import SpotTree

BASE_DESCRIPTOR = previous.BASE_DESCRIPTOR
BASE_FUNCTION = previous.BASE_FUNCTION
PHASES = (
    "information_keys",
    "array_setup",
    "depth_validation",
    "instantiate",
    "field_witness",
)
CURRENT: ContextVar["PhaseRecorder | None"] = ContextVar(
    "matrix_phase_recorder", default=None
)


def build(
    cls: type[MatrixTree],
    source: SpotTree,
    encoding: Encoding = "exact",
    model: CardAbstraction | None = None,
) -> "MatrixTree":
    with phase("information_keys"):
        keys: list[str] = []
        menus: list[tuple[int, ...]] = []
        owners: list[int] = []
        lookup: dict[str, int] = {}
        mapping = np.zeros(len(source.keys), dtype=np.int64)
        for exact, node in enumerate(source.representatives):
            state = source.states[node]
            assert state.dealer is not None
            key = observation_key(state.dealer.observe(state.actor), encoding, model)
            if key not in lookup:
                lookup[key] = len(keys)
                keys.append(key)
                menus.append(source.menus[exact])
                owners.append(state.actor)
            info = lookup[key]
            if menus[info] != source.menus[exact] or owners[info] != state.actor:
                raise ValueError("representation merges incompatible owners/actions")
            mapping[exact] = info
    with phase("array_setup"):
        n = len(source.states)
        width = max(map(len, source.children))
        children = np.zeros((n, width), dtype=np.int64)
        valid = np.zeros((n, width), dtype=np.bool_)
        chance_edges = np.zeros((n, width))
        chance_reach = np.ones(n)
        depths = np.zeros(n, dtype=np.int64)
        information = np.full(n, -1, dtype=np.int64)
        players = np.full(n, -2, dtype=np.int64)
        for node, state in enumerate(source.states):
            group = source.children[node]
            children[node, : len(group)] = group
            valid[node, : len(group)] = True
            if state.chance:
                players[node] = -1
                chance_edges[node, : len(group)] = source.chance_probabilities[node]
            elif not state.terminal:
                players[node] = state.actor
                information[node] = mapping[source.information[node]]
            for column, child in enumerate(group):
                depths[child] = depths[node] + 1
                chance_reach[child] = chance_reach[node] * (
                    chance_edges[node, column] if state.chance else 1.0
                )
        legal = np.zeros((len(keys), width))
        for info, menu in enumerate(menus):
            legal[info, : len(menu)] = 1
        levels = tuple(
            np.flatnonzero((depths == d) & (players != -2))
            for d in range(int(depths.max()) + 1)
        )
    with phase("depth_validation"):
        for info in range(len(keys)):
            if len(set(depths[information == info].tolist())) != 1:
                raise ValueError("information set merges different depths")
    with phase("instantiate"):
        return cls(
            children=children,
            valid=valid,
            player=players,
            information=information,
            keys=tuple(keys),
            actions=tuple(menus),
            owners=np.array(owners, dtype=np.int64),
            legal=legal,
            chance_edges=chance_edges,
            chance_reach=chance_reach,
            terminal_values=np.array(source.payoffs),
            levels=levels,
            source=source,
            exact_to_abstract=mapping,
            encoding=encoding,
            node_actions=tuple(state.actions for state in source.states),
        )


def ast_equivalence() -> None:
    """Removing only declared timing contexts must recover the entire original."""
    old = ast.parse(textwrap.dedent(inspect.getsource(BASE_FUNCTION))).body[0]
    new = ast.parse(textwrap.dedent(inspect.getsource(build))).body[0]
    if not isinstance(old, ast.FunctionDef) or not isinstance(new, ast.FunctionDef):
        raise ArithmeticError("ordinary matrix constructors required")
    expected = ast.dump(ast.parse("type[MatrixTree]", mode="eval").body)
    if (
        len(old.decorator_list) != 1
        or ast.dump(old.decorator_list[0])
        != ast.dump(ast.Name(id="classmethod", ctx=ast.Load()))
        or new.decorator_list
        or old.args.args[0].annotation is not None
        or new.args.args[0].annotation is None
        or ast.dump(new.args.args[0].annotation) != expected
        or len(new.body) != 4
    ):
        raise ArithmeticError("original constructor signature/phase layout changed")
    array_index = next(
        (
            i
            for i, n in enumerate(old.body)
            if isinstance(n, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == "n" for t in n.targets)
        ),
        None,
    )
    if array_index is None:
        raise ArithmeticError("original array boundary changed")
    boundaries = (
        old.body[:array_index],
        old.body[array_index:-2],
        old.body[-2:-1],
        old.body[-1:],
    )
    expanded = []
    expanded_blocks: list[bool] = []
    for node, name in zip(new.body, PHASES[:4], strict=True):
        target = ast.parse(f'with phase("{name}"):\n    pass').body[0]
        if (
            not isinstance(node, ast.With)
            or not isinstance(target, ast.With)
            or ast.dump(
                ast.Tuple(elts=[x.context_expr for x in node.items], ctx=ast.Load())
            )
            != ast.dump(
                ast.Tuple(elts=[x.context_expr for x in target.items], ctx=ast.Load())
            )
            or any(x.optional_vars is not None for x in node.items)
        ):
            raise ArithmeticError("declared phase boundaries changed")
        expected_block = boundaries[len(expanded_blocks)]
        if [ast.dump(x) for x in node.body] != [ast.dump(x) for x in expected_block]:
            raise ArithmeticError("constructor phase statement boundaries changed")
        expanded_blocks.append(True)
        expanded.extend(node.body)
    old.decorator_list = []
    new.args.args[0].annotation = None
    new.body = expanded
    if ast.dump(old) != ast.dump(new):
        raise ArithmeticError("constructor changed beyond explicit phase contexts")
    for name in BASE_FUNCTION.__code__.co_names:
        if (
            name in BASE_FUNCTION.__globals__
            and build.__globals__.get(name) is not BASE_FUNCTION.__globals__[name]
        ):
            raise ArithmeticError("copied constructor global dependency changed")


def clock() -> dict[str, float]:
    result = dict(wall=time.perf_counter(), cpu=time.process_time())
    if any(not math.isfinite(x) or x < 0 for x in result.values()):
        raise ArithmeticError("finite nonnegative phase clocks required")
    return result


class PhaseRecorder:
    """Five serial disjoint phases; retained failures stay failures."""

    def __init__(self, output: Path, maximum: int) -> None:
        self.output = output
        self.maximum = maximum
        self.pid, self.thread = os.getpid(), threading.get_ident()
        self.events: list[dict[str, Any]] = []
        self.index: int | None = None
        self.ordinal = 0
        self.in_phase = False
        self.completed = 0
        self.errors = 0
        self.rows = output / "phase-events.jsonl"
        self.stream = self.rows.open("x")

    def guard(self) -> None:
        if os.getpid() != self.pid or threading.get_ident() != self.thread:
            self.errors += 1
            raise ArithmeticError("phase process/thread changed")

    def emit(self, event: str, **payload: Any) -> None:
        row = dict(
            event=event,
            sequence=len(self.events),
            pid=self.pid,
            thread=self.thread,
            index=self.index,
            **payload,
        )
        self.stream.write(previous.canonical(row).decode() + "\n")
        self.stream.flush()
        self.events.append(row)

    def begin(self, index: int) -> None:
        self.guard()
        if (
            self.index is not None
            or type(index) is not int
            or index != self.completed
            or index >= self.maximum
        ):
            self.errors += 1
            raise ArithmeticError("phase nesting/order/capacity changed")
        self.index, self.ordinal = index, 0
        self.emit("constructor_begin", clocks=clock())

    def end(self, primary: bool) -> None:
        self.guard()
        if (
            self.index is None
            or self.in_phase
            or (not primary and self.ordinal != len(PHASES))
        ):
            self.errors += 1
            raise ArithmeticError("incomplete constructor phases")
        self.emit(
            "constructor_failed" if primary else "constructor_end", clocks=clock()
        )
        if not primary:
            self.completed += 1
        self.index = None

    @contextmanager
    def interval(self, name: str) -> Iterator[None]:
        self.guard()
        if (
            self.index is None
            or self.in_phase
            or self.ordinal >= len(PHASES)
            or name != PHASES[self.ordinal]
        ):
            self.errors += 1
            raise ArithmeticError("phase inventory/nesting/order changed")
        ordinal = self.ordinal
        before = clock()
        self.emit("phase_begin", phase=name, ordinal=ordinal, clocks=before)
        self.in_phase = True
        primary: BaseException | None = None
        try:
            yield
        except BaseException as error:
            primary = error
            raise
        finally:
            self.in_phase = False
            try:
                self.guard()
                after = clock()
                if any(not math.isfinite(v) or v < 0 for v in after.values()) or any(
                    after[k] < before[k] for k in before
                ):
                    raise ArithmeticError("phase clock moved backward")
                self.emit(
                    "phase_failed" if primary else "phase_end",
                    phase=name,
                    ordinal=ordinal,
                    clocks=after,
                    failure_kind=type(primary).__name__ if primary else None,
                )
                self.ordinal += 1
            except BaseException:
                self.errors += 1
                if primary is None:
                    raise

    def close(self, primary: bool) -> None:
        self.stream.close()
        receipt = dict(
            status="failed_retained"
            if primary or self.errors or self.index is not None
            else "complete",
            pid=self.pid,
            thread=self.thread,
            maximum=self.maximum,
            completed=self.completed,
            errors=self.errors,
            phases=list(PHASES),
            events_sha256=hashlib.sha256(self.rows.read_bytes()).hexdigest(),
        )
        (self.output / "phases.json").write_bytes(previous.canonical(receipt) + b"\n")


def phase(name: str) -> Any:
    """Direct calls retain behavior; scoped calls collect intervals."""
    recorder = CURRENT.get()
    return nullcontext() if recorder is None else recorder.interval(name)


@contextmanager
def constructor_scope(
    mode: str, output: Path, maximum: int
) -> Iterator[dict[str, Any]]:
    """Whole-child field witnesses, with original-only private phase instrumentation."""
    if (
        mode not in ("original", "phased")
        or type(maximum) is not int
        or maximum <= 0
        or vars(MatrixTree)["build"] is not BASE_DESCRIPTOR
        or threading.current_thread() is not threading.main_thread()
        or CURRENT.get() is not None
    ):
        raise ArithmeticError("unsupported constructor scope or changed baseline")
    ast_equivalence()
    output.mkdir(parents=True, exist_ok=False)
    events = output / "constructor-events.jsonl"
    receipt: dict[str, Any] = dict(
        status="running",
        mode=mode,
        pid=os.getpid(),
        thread=threading.get_ident(),
        maximum=maximum,
        calls=0,
        completed=0,
        primary_failures=0,
        errors=0,
        restored=False,
        aliases_remaining=None,
        scope=(
            "whole original child main-process constructor field witnesses; "
            "native spawned workers unchanged"
        ),
    )
    initial: list[Any] = []
    primary = False
    recorder = PhaseRecorder(output, maximum) if mode == "phased" else None
    (output / "constructor.json").write_bytes(previous.canonical(receipt) + b"\n")
    with events.open("x") as stream:

        def emit(row: dict[str, Any]) -> None:
            stream.write(previous.canonical(row).decode() + "\n")
            stream.flush()

        @functools.wraps(BASE_FUNCTION)
        def observed(*args: Any, **kwargs: Any) -> Any:
            if (
                os.getpid() != receipt["pid"]
                or threading.get_ident() != receipt["thread"]
                or receipt["calls"] >= maximum
                or CURRENT.get() is not None
            ):
                receipt["errors"] += 1
                raise ArithmeticError(
                    "constructor process/thread/call capacity or nesting changed"
                )
            index = receipt["calls"]
            receipt["calls"] += 1
            emit(dict(index=index, status="running"))
            token = None
            failed = False
            try:
                if recorder is not None:
                    recorder.begin(index)
                    token = CURRENT.set(recorder)
                result = (BASE_FUNCTION if mode == "original" else build)(
                    *args, **kwargs
                )
                source = kwargs["source"] if "source" in kwargs else args[1]
                with phase("field_witness"):
                    witness = previous.matrix_witness(result, source)
                emit(dict(index=index, status="complete", witness=witness))
                receipt["completed"] += 1
                return result
            except BaseException as error:
                failed = True
                receipt["primary_failures"] += 1
                try:
                    emit(
                        dict(
                            index=index,
                            status="primary_failed",
                            failure_kind=type(error).__name__,
                        )
                    )
                except BaseException:
                    receipt["errors"] += 1
                raise
            finally:
                if token is not None:
                    CURRENT.reset(token)
                    try:
                        assert recorder is not None
                        recorder.end(failed)
                    except BaseException:
                        receipt["errors"] += 1
                        if not failed:
                            raise

        attribute = "build"
        descriptor = classmethod(observed)
        try:
            setattr(MatrixTree, attribute, descriptor)
            previous.aliases(BASE_FUNCTION, observed, initial)
            yield receipt
        except BaseException:
            primary = True
            raise
        finally:
            try:
                if vars(MatrixTree)["build"] is not descriptor:
                    receipt["errors"] += 1
                setattr(MatrixTree, attribute, BASE_DESCRIPTOR)
                previous.aliases(observed, BASE_FUNCTION)
                for mod, name, value in initial:
                    setattr(mod, name, value)
                remaining = sum(
                    value is observed
                    or (isinstance(value, MethodType) and value.__func__ is observed)
                    for mod in previous.owned_modules()
                    for value in vars(mod).values()
                )
                receipt.update(
                    aliases_remaining=remaining,
                    restored=vars(MatrixTree)["build"] is BASE_DESCRIPTOR
                    and remaining == 0,
                    status="complete"
                    if not primary
                    and receipt["errors"] == receipt["primary_failures"] == 0
                    and receipt["completed"] == receipt["calls"]
                    else "failed_retained",
                )
                stream.flush()
                receipt["events_sha256"] = hashlib.sha256(
                    events.read_bytes()
                ).hexdigest()
                (output / "constructor.json").write_bytes(
                    previous.canonical(receipt) + b"\n"
                )
                if recorder is not None:
                    recorder.close(primary or receipt["status"] != "complete")
            except BaseException:
                if not primary:
                    raise


def read_phases(
    output: Path, count: int, maximum: int, pid: int, thread: int
) -> list[dict[str, Any]]:
    """Authenticate exact serial coverage and non-overlapping clocks from saved data."""
    receipt = json.loads((output / "phases.json").read_text())
    raw = (output / "phase-events.jsonl").read_bytes()
    expected = dict(
        status="complete",
        pid=pid,
        thread=thread,
        maximum=maximum,
        completed=count,
        errors=0,
        phases=list(PHASES),
        events_sha256=hashlib.sha256(raw).hexdigest(),
    )
    if (
        receipt != expected
        or any(
            type(receipt[k]) is not int
            for k in ("pid", "thread", "maximum", "completed", "errors")
        )
        or type(count) is not int
        or not 0 < count <= maximum
    ):
        raise ArithmeticError("complete exact phase receipt required")
    rows = [json.loads(x) for x in raw.splitlines()]
    if len(rows) != count * 12:
        raise ArithmeticError("complete five-phase event inventory required")
    summaries = []
    last: dict[str, float] | None = None
    for index in range(count):
        events = rows[index * 12 : (index + 1) * 12]
        for offset, row in enumerate(events):
            kind = (
                "constructor_begin"
                if offset == 0
                else "constructor_end"
                if offset == 11
                else "phase_begin"
                if offset % 2
                else "phase_end"
            )
            expected_keys = {"event", "sequence", "pid", "thread", "index", "clocks"}
            if 0 < offset < 11:
                expected_keys.update(("phase", "ordinal"))
                if offset % 2 == 0:
                    expected_keys.add("failure_kind")
                if (
                    row.get("phase") != PHASES[(offset - 1) // 2]
                    or type(row.get("ordinal")) is not int
                    or row["ordinal"] != (offset - 1) // 2
                    or (offset % 2 == 0 and row.get("failure_kind") is not None)
                ):
                    raise ArithmeticError("phase order/failure changed")
            if (
                set(row) != expected_keys
                or row["event"] != kind
                or any(
                    type(row[k]) is not int
                    for k in ("sequence", "pid", "thread", "index")
                )
                or (row["sequence"], row["pid"], row["thread"], row["index"])
                != (index * 12 + offset, pid, thread, index)
            ):
                raise ArithmeticError("phase event schema/context changed")
            clocks = row["clocks"]
            if (
                type(clocks) is not dict
                or set(clocks) != {"cpu", "wall"}
                or any(
                    type(v) not in (int, float) or not math.isfinite(v) or v < 0
                    for v in clocks.values()
                )
                or (last is not None and any(clocks[k] < last[k] for k in clocks))
            ):
                raise ArithmeticError("phase clock missing/nonfinite/backward")
            last = clocks
        phases = {
            name: {
                key: events[2 * i + 2]["clocks"][key] - events[2 * i + 1]["clocks"][key]
                for key in ("cpu", "wall")
            }
            for i, name in enumerate(PHASES)
        }
        total = {
            k: events[-1]["clocks"][k] - events[0]["clocks"][k] for k in ("cpu", "wall")
        }
        remainder = {
            k: total[k] - math.fsum(x[k] for x in phases.values()) for k in total
        }
        if any(x < -1e-9 for x in remainder.values()):
            raise ArithmeticError("phase clocks exceed constructor boundary")
        summaries.append(
            dict(
                index=index,
                before=events[0]["clocks"],
                after=events[-1]["clocks"],
                phases=phases,
                total=total,
                remainder=remainder,
            )
        )
    return summaries


def depth_error_fixture(source: SpotTree) -> SpotTree:
    """Synthetic software-only shape: same observed decision at depths one and two.

    This is not a valid played poker trajectory or experimental poker data.
    Reuse one acting observation solely to exercise the original rejection.
    """
    from types import SimpleNamespace
    from typing import cast

    decision = source.states[source.representatives[0]]
    actions = decision.actions
    if len(actions) != 2:
        raise ArithmeticError("negative fixture requires pinned two-action decision")
    chance = SimpleNamespace(
        chance=True, terminal=False, actor=0, dealer=None, actions=(0, 1)
    )
    terminal = SimpleNamespace(
        chance=False, terminal=True, actor=0, dealer=None, actions=()
    )
    return cast(
        SpotTree,
        SimpleNamespace(
            states=(
                chance,
                decision,
                chance,
                terminal,
                terminal,
                decision,
                terminal,
                terminal,
            ),
            children=((1, 2), (3, 4), (5,), (), (), (6, 7), (), ()),
            chance_probabilities=((0.5, 0.5), (), (1.0,), (), (), (), (), ()),
            keys=("synthetic-first-depth", "synthetic-second-depth"),
            representatives=(1, 5),
            menus=(actions, actions),
            information=(-1, 0, -1, -1, -1, 1, -1, -1),
            payoffs=(0.0,) * 8,
        ),
    )
