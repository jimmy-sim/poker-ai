"""Private grouped matrix-depth check and exact constructor witnesses.

Historical source is unchanged. The explicit copied constructor differs only in
its final integer depth predicate; ast_equivalence authenticates that boundary.
"""

import ast
import functools
import hashlib
import inspect
import json
import os
import textwrap
import threading
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import fields
from pathlib import Path
from types import MethodType, ModuleType
from typing import Any

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.finite import IntArray
from poker_ai.postflop.matrix import Encoding, MatrixTree, observation_key
from poker_ai.postflop.tree import SpotTree

BASE_DESCRIPTOR = vars(MatrixTree)["build"]
BASE_FUNCTION = BASE_DESCRIPTOR.__func__
MESSAGE = "information set merges different depths"


def grouped_depths(information: IntArray, depths: IntArray, groups: int) -> None:
    """Exactly one integer depth per in-range group; never mutate either input.

    Two integer scatter reductions cost O(nodes + groups), instead of rescanning
    all nodes for every group. Missing groups have unequal extrema and fail too.
    """
    if (
        type(groups) is not int
        or groups < 0
        or not isinstance(information, np.ndarray)
        or not isinstance(depths, np.ndarray)
        or information.ndim != 1
        or depths.ndim != 1
        or information.shape != depths.shape
        or information.dtype != np.dtype(np.int64)
        or depths.dtype != np.dtype(np.int64)
    ):
        raise ValueError("canonical matching one-dimensional int64 arrays required")
    valid = (information >= 0) & (information < groups)
    index, values = information[valid], depths[valid]
    limits = np.iinfo(np.int64)
    minimum = np.full(groups, limits.max, dtype=np.int64)
    maximum = np.full(groups, limits.min, dtype=np.int64)
    np.minimum.at(minimum, index, values)
    np.maximum.at(maximum, index, values)
    if np.any(minimum != maximum):
        raise ValueError(MESSAGE)


def build(
    cls: type[MatrixTree],
    source: SpotTree,
    encoding: Encoding = "exact",
    model: CardAbstraction | None = None,
) -> "MatrixTree":
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
    grouped_depths(information, depths, len(keys))
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
    """Authenticate the literal copied body, not a runtime code transformation."""
    old = ast.parse(textwrap.dedent(inspect.getsource(BASE_FUNCTION))).body[0]
    new = ast.parse(textwrap.dedent(inspect.getsource(build))).body[0]
    if not isinstance(old, ast.FunctionDef) or not isinstance(new, ast.FunctionDef):
        raise ArithmeticError("ordinary matrix constructors required")
    if (
        [ast.dump(x) for x in old.decorator_list]
        != [ast.dump(ast.Name(id="classmethod", ctx=ast.Load()))]
        or new.decorator_list
        or old.args.args[0].annotation is not None
        or new.args.args[0].annotation is None
        or ast.dump(new.args.args[0].annotation)
        != ast.dump(ast.parse("type[MatrixTree]", mode="eval").body)
        or not isinstance(old.body[-2], ast.For)
    ):
        raise ArithmeticError("original matrix constructor layout changed")
    expected = ast.parse(
        "for info in range(len(keys)):\n"
        "    if len(set(depths[information == info].tolist())) != 1:\n"
        '        raise ValueError("information set merges different depths")'
    ).body[0]
    if ast.dump(old.body[-2]) != ast.dump(expected):
        raise ArithmeticError("original depth predicate changed")
    old.decorator_list = []
    new.args.args[0].annotation = None
    old.body[-2] = ast.parse("grouped_depths(information, depths, len(keys))").body[0]
    if ast.dump(old) != ast.dump(new):
        raise ArithmeticError("constructor changed beyond the grouped depth check")
    for name in BASE_FUNCTION.__code__.co_names:
        if (
            name in BASE_FUNCTION.__globals__
            and build.__globals__.get(name) is not BASE_FUNCTION.__globals__[name]
        ):
            raise ArithmeticError("copied constructor global dependency changed")


def canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode()


def field_value(value: Any) -> Any:
    """Hash full array bits and preserve container/type/geometry metadata."""
    if isinstance(value, np.ndarray):
        if value.dtype.hasobject:
            raise ArithmeticError("object arrays cannot witness constructor bits")
        return dict(
            kind="ndarray",
            dtype=value.dtype.str,
            shape=list(value.shape),
            strides=list(value.strides),
            flags=dict(
                C_CONTIGUOUS=bool(value.flags.c_contiguous),
                F_CONTIGUOUS=bool(value.flags.f_contiguous),
                OWNDATA=bool(value.flags.owndata),
                WRITEABLE=bool(value.flags.writeable),
                ALIGNED=bool(value.flags.aligned),
                WRITEBACKIFCOPY=bool(value.flags.writebackifcopy),
            ),
            sha256=hashlib.sha256(value.tobytes(order="C")).hexdigest(),
        )
    if isinstance(value, tuple):
        scalar = (type(None), bool, int, float, str)
        payload: Any
        if all(type(x) in scalar for x in value):
            layout, payload = "scalars", value
        elif all(type(x) is tuple and all(type(y) in scalar for y in x) for x in value):
            layout, payload = "tuples_of_scalars", value
        else:
            layout, payload = "typed_children", [field_value(x) for x in value]
        return dict(
            kind="tuple",
            layout=layout,
            length=len(value),
            sha256=hashlib.sha256(canonical(payload)).hexdigest(),
        )
    if value is None or type(value) in (bool, int, float, str):
        return dict(kind=type(value).__name__, value=value)
    raise ArithmeticError("unsupported constructed dataclass field")


def matrix_witness(matrix: MatrixTree, source: SpotTree) -> dict[str, Any]:
    if matrix.source is not source:
        raise ArithmeticError("constructor replaced the source object")
    payload = dict(
        matrix_class=type(matrix).__module__ + "." + type(matrix).__qualname__,
        source_is_exact_input=True,
        fields={
            f.name: field_value(getattr(matrix, f.name))
            for f in fields(matrix)
            if f.name != "source"
        },
    )
    return dict(**payload, fingerprint=hashlib.sha256(canonical(payload)).hexdigest())


def owned_modules() -> Iterator[ModuleType]:
    from profile_reader_loads import modules

    yield from modules()


def aliases(
    old: Callable[..., Any],
    new: Callable[..., Any],
    saved: list[tuple[ModuleType, str, Any]] | None = None,
) -> None:
    for mod in owned_modules():
        for name, value in list(vars(mod).items()):
            if value is old:
                if saved is not None:
                    saved.append((mod, name, value))
                setattr(mod, name, new)
            elif isinstance(value, MethodType) and value.__func__ is old:
                if saved is not None:
                    saved.append((mod, name, value))
                setattr(mod, name, MethodType(new, value.__self__))


@contextmanager
def constructor_scope(
    mode: str, output: Path, maximum: int
) -> Iterator[dict[str, Any]]:
    """Same field observer in both arms; candidate affects this main process only."""
    if (
        mode not in ("original", "grouped")
        or type(maximum) is not int
        or maximum <= 0
        or vars(MatrixTree)["build"] is not BASE_DESCRIPTOR
        or threading.current_thread() is not threading.main_thread()
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
    initial: list[tuple[ModuleType, str, Any]] = []
    primary = False
    (output / "constructor.json").write_bytes(canonical(receipt) + b"\n")
    with events.open("x") as stream:

        def emit(row: dict[str, Any]) -> None:
            stream.write(canonical(row).decode() + "\n")
            stream.flush()

        @functools.wraps(BASE_FUNCTION)
        def observed(*args: Any, **kwargs: Any) -> Any:
            if (
                os.getpid() != receipt["pid"]
                or threading.get_ident() != receipt["thread"]
                or receipt["calls"] >= maximum
            ):
                receipt["errors"] += 1
                raise ArithmeticError(
                    "constructor process/thread/call capacity changed"
                )
            index = receipt["calls"]
            receipt["calls"] += 1
            row: dict[str, Any] = dict(index=index, status="running")
            emit(row)
            try:
                result = (BASE_FUNCTION if mode == "original" else build)(
                    *args, **kwargs
                )
            except BaseException as error:
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
            try:
                source = kwargs["source"] if "source" in kwargs else args[1]
                witness = matrix_witness(result, source)
                emit(dict(index=index, status="complete", witness=witness))
                receipt["completed"] += 1
            except BaseException:
                receipt["errors"] += 1
                raise
            return result

        descriptor = classmethod(observed)
        attribute = "build"
        try:
            setattr(MatrixTree, attribute, descriptor)
            aliases(BASE_FUNCTION, observed, initial)
            yield receipt
        except BaseException:
            primary = True
            raise
        finally:
            try:
                if vars(MatrixTree)["build"] is not descriptor:
                    receipt["errors"] += 1
                setattr(MatrixTree, attribute, BASE_DESCRIPTOR)
                aliases(observed, BASE_FUNCTION)
                for mod, name, value in initial:
                    setattr(mod, name, value)
                remaining = sum(
                    value is observed
                    or (isinstance(value, MethodType) and value.__func__ is observed)
                    for mod in owned_modules()
                    for value in vars(mod).values()
                )
                receipt.update(
                    aliases_remaining=remaining,
                    restored=vars(MatrixTree)["build"] is BASE_DESCRIPTOR
                    and remaining == 0,
                    status="complete"
                    if not primary
                    and receipt["errors"] == 0
                    and receipt["primary_failures"] == 0
                    and receipt["completed"] == receipt["calls"]
                    else "failed_retained",
                )
                stream.flush()
                receipt["events_sha256"] = hashlib.sha256(
                    events.read_bytes()
                ).hexdigest()
                (output / "constructor.json").write_bytes(canonical(receipt) + b"\n")
            except BaseException:
                if not primary:
                    raise


def read_constructors(
    output: Path, mode: str, maximum: int, pid: int, thread: int
) -> list[str]:
    """Validate complete retained witnesses; never reconstruct a poker matrix."""
    receipt = json.loads((output / "constructor.json").read_text())
    data = (output / "constructor-events.jsonl").read_bytes()
    integers = (
        "maximum",
        "pid",
        "thread",
        "calls",
        "completed",
        "errors",
        "primary_failures",
        "aliases_remaining",
    )
    if (
        set(receipt)
        != {
            "status",
            "mode",
            "pid",
            "thread",
            "maximum",
            "calls",
            "completed",
            "primary_failures",
            "errors",
            "restored",
            "aliases_remaining",
            "scope",
            "events_sha256",
        }
        or any(type(receipt[k]) is not int for k in integers)
        or receipt["status"] != "complete"
        or receipt["mode"] != mode
        or receipt["maximum"] != maximum
        or receipt["pid"] != pid
        or receipt["thread"] != thread
        or receipt["restored"] is not True
        or receipt["aliases_remaining"] != 0
        or receipt["errors"] != 0
        or receipt["primary_failures"] != 0
        or not 0 < receipt["calls"] <= maximum
        or receipt["completed"] != receipt["calls"]
        or receipt["events_sha256"] != hashlib.sha256(data).hexdigest()
    ):
        raise ArithmeticError("complete same-context constructor witnesses required")
    rows = [json.loads(x) for x in data.splitlines()]
    if len(rows) != 2 * receipt["calls"]:
        raise ArithmeticError("constructor witness inventory incomplete")
    fingerprints = []
    expected_fields = {f.name for f in fields(MatrixTree)} - {"source"}
    for index in range(receipt["calls"]):
        before, after = rows[2 * index : 2 * index + 2]
        if (
            before != dict(index=index, status="running")
            or set(after) != {"index", "status", "witness"}
            or after["index"] != index
            or after["status"] != "complete"
        ):
            raise ArithmeticError("constructor witness ordering/status changed")
        witness = after["witness"]
        if (
            set(witness)
            != {"matrix_class", "source_is_exact_input", "fields", "fingerprint"}
            or witness["matrix_class"] != "poker_ai.postflop.matrix.MatrixTree"
            or witness["source_is_exact_input"] is not True
            or set(witness["fields"]) != expected_fields
            or type(witness["fingerprint"]) is not str
            or witness["fingerprint"]
            != hashlib.sha256(
                canonical({k: v for k, v in witness.items() if k != "fingerprint"})
            ).hexdigest()
        ):
            raise ArithmeticError("constructed fields/class/fingerprint changed")
        for value in witness["fields"].values():
            validate_field(value)
        fingerprints.append(witness["fingerprint"])
    return fingerprints


def validate_field(value: Any) -> None:
    """Check recorded metadata, not unretained array contents or a fresh game."""
    if type(value) is not dict or type(value.get("kind")) is not str:
        raise ArithmeticError("typed field metadata required")
    kind = value["kind"]
    if kind == "ndarray":
        flags = {
            "C_CONTIGUOUS",
            "F_CONTIGUOUS",
            "OWNDATA",
            "WRITEABLE",
            "ALIGNED",
            "WRITEBACKIFCOPY",
        }
        if (
            set(value) != {"kind", "dtype", "shape", "strides", "flags", "sha256"}
            or type(value["dtype"]) is not str
            or np.dtype(value["dtype"]).hasobject
            or type(value["shape"]) is not list
            or type(value["strides"]) is not list
            or len(value["shape"]) != len(value["strides"])
            or any(type(n) is not int or n < 0 for n in value["shape"])
            or any(type(n) is not int for n in value["strides"])
            or type(value["flags"]) is not dict
            or set(value["flags"]) != flags
            or any(type(b) is not bool for b in value["flags"].values())
        ):
            raise ArithmeticError("array field metadata changed")
    elif kind == "tuple":
        if (
            set(value) != {"kind", "layout", "length", "sha256"}
            or value["layout"] not in {"scalars", "tuples_of_scalars", "typed_children"}
            or type(value["length"]) is not int
            or value["length"] < 0
        ):
            raise ArithmeticError("tuple field metadata changed")
    elif kind in {"NoneType", "bool", "int", "float", "str"}:
        if set(value) != {"kind", "value"} or type(value["value"]).__name__ != kind:
            raise ArithmeticError("scalar field metadata changed")
        return
    else:
        raise ArithmeticError("unsupported field metadata kind")
    sha = value["sha256"]
    if (
        type(sha) is not str
        or len(sha) != 64
        or any(c not in "0123456789abcdef" for c in sha)
    ):
        raise ArithmeticError("field digest changed")
