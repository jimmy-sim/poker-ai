"""Coarse selected-call process CPU boundaries; never a training admission."""

import argparse
import copy
import functools
import gzip
import hashlib
import json
import math
import os
import re
import sys
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from types import MethodType, ModuleType
from typing import Any
from unittest.mock import patch

import collect_complete_reader_helpers as helpers
import measure_original_audit as prior
import trace_card_audit as original
from card_clock_support import check_record, record, snapshot
from profile_compact_replay import atomic, canonical, digest, supervise

original_result = prior.original_result
ROOT = Path(__file__).resolve().parents[1]
ENTRY = "scripts/profile_coarse_reader.py"
CONFIG = "configs/coarse-reader-cpu.json"
CONFIG_SHA = "dde1b9be75ef5c81b1ca0e91d75eca37378799772d5498437236fad8ab46a101"
FOLDER = "results/coarse-reader-cpu"
CATEGORIES = ("matrix_build", "spot_tree_build", "checkpoint_replay")


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective coarse CPU contract changed")
    c: dict[str, Any] = json.loads((root / CONFIG).read_text())
    for n, h in c["input_sha256"].items():
        p = root / n
        if (
            p.is_symlink()
            or not p.resolve().is_relative_to(root.resolve())
            or digest(p) != h
        ):
            raise ArithmeticError("coarse CPU retained input changed")
    return c


def binding(root: Path, *, clean: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.validation.five_card import source_provenance

    c = contract(root)
    _, old = prior.binding(root, clean=clean)
    anchor = json.loads((root / c["historical_helper_anchor"]).read_text())["source"][
        "sha256"
    ]
    if len(anchor) != 402 or old["sha256"] != anchor:
        raise ArithmeticError("preserve all402 prior source files")
    s: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=(ENTRY,))
    )
    s["sha256"].update(anchor)
    s["fingerprint"] = sha(s["sha256"])
    if len(s["sha256"]) != 404 or (clean and s["dirty"] is not False):
        raise ArithmeticError("publish clean404-file coarse CPU source")
    commit_sources(root, s["git_commit"], s["sha256"])
    return c, s


def clock() -> dict[str, Any]:
    return dict(
        wall=time.perf_counter(),
        cpu=time.process_time(),
        pid=os.getpid(),
        thread=threading.get_ident(),
    )


class Regions:
    """Time only selected serial call boundaries, never every Python frame."""

    def __init__(
        self,
        maximum: int,
        emit: Callable[[dict[str, Any]], None] | None = None,
        read_clock: Callable[[], dict[str, Any]] = clock,
    ) -> None:
        if type(maximum) is not int or maximum <= 0:
            raise ValueError("positive selected-call cap required")
        self.maximum = maximum
        self.emit = emit
        self.read_clock = read_clock
        self.pid = os.getpid()
        self.thread = threading.get_ident()
        self.active = False
        self.emitting = False
        self.total = 0
        self.rows: list[dict[str, Any]] = []
        self.stack: list[int] = []
        self.errors = 0
        self.read_index = -1

    def publish(self, row: dict[str, Any]) -> None:
        self.emitting = True
        try:
            if self.emit is not None:
                self.emit(copy.deepcopy(row))
        finally:
            self.emitting = False

    def wrap(self, category: str, function: Callable[..., Any]) -> Callable[..., Any]:
        if category not in CATEGORIES:
            raise ValueError("unknown selected boundary")

        @functools.wraps(function)
        def selected(*args: Any, **kwargs: Any) -> Any:
            if not self.active:
                return function(*args, **kwargs)
            if (
                os.getpid() != self.pid
                or threading.get_ident() != self.thread
                or self.total >= self.maximum
                or self.emitting
            ):
                self.errors += 1
                raise ArithmeticError(
                    "serial main-thread selected-call coverage/cap failed"
                )
            before = self.read_clock()
            index = len(self.rows)
            row: dict[str, Any] = dict(
                index=index,
                read=self.read_index,
                parent=self.stack[-1] if self.stack else None,
                category=category,
                status="running",
                before=before,
            )
            self.rows.append(row)
            self.stack.append(index)
            self.total += 1
            try:
                self.publish(row)
            except BaseException:
                self.errors += 1
                self.stack.pop()
                raise

            def finish(status: str) -> None:
                row.update(status=status, after=self.read_clock())
                self.publish(row)

            try:
                result = function(*args, **kwargs)
            except BaseException as error:
                row["failure_kind"] = type(error).__name__
                try:
                    finish("primary_failed")
                except BaseException:
                    self.errors += 1
                    row["status"] = "primary_with_observer_failure"
                raise
            else:
                try:
                    finish("complete")
                except BaseException:
                    self.errors += 1
                    raise
                return result
            finally:
                if not self.stack or self.stack[-1] != index:
                    self.errors += 1
                    raise ArithmeticError("selected stack changed")
                self.stack.pop()

        marker = "_coarse_cpu_region"
        setattr(selected, marker, True)
        return selected


def modules() -> Iterator[ModuleType]:
    for name, mod in list(sys.modules.items()):
        if name.startswith("poker_ai.") and isinstance(mod, ModuleType):
            yield mod


def targets() -> tuple[tuple[str, Any, str], ...]:
    import poker_ai.postflop.learning_training as training
    from poker_ai.postflop.matrix import MatrixTree
    from poker_ai.postflop.tree import SpotTree

    return (
        ("matrix_build", MatrixTree, "build"),
        ("spot_tree_build", SpotTree, "build"),
        ("checkpoint_replay", training, "replay_snapshot"),
    )


def aliases(
    old: Callable[..., Any],
    new: Callable[..., Any],
    saved: list[tuple[ModuleType, str, Any]] | None = None,
) -> int:
    count = 0
    for mod in modules():
        for name, value in list(vars(mod).items()):
            if value is old:
                if saved is not None:
                    saved.append((mod, name, value))
                setattr(mod, name, new)
                count += 1
            elif isinstance(value, MethodType) and value.__func__ is old:
                if saved is not None:
                    saved.append((mod, name, value))
                setattr(mod, name, MethodType(new, value.__self__))
                count += 1
    return count


@contextmanager
def selected_hooks(
    regions: Regions,
    receipt: dict[str, Any],
    bindings: tuple[tuple[str, Any, str], ...] | None = None,
) -> Iterator[None]:
    bindings = targets() if bindings is None else bindings
    saved = []
    initial_aliases: list[tuple[ModuleType, str, Any]] = []
    receipt.update(
        categories=[x[0] for x in bindings], restored=False, aliases_remaining=None
    )
    try:
        for category, owner, name in bindings:
            descriptor = vars(owner)[name]
            function = (
                descriptor.__func__
                if isinstance(descriptor, classmethod)
                else descriptor
            )
            if not callable(function) or getattr(function, "_coarse_cpu_region", False):
                raise ArithmeticError("nested/unknown selected hook")
            wrapper = regions.wrap(category, function)
            saved.append((owner, name, descriptor, function, wrapper))
            setattr(
                owner,
                name,
                classmethod(wrapper)
                if isinstance(descriptor, classmethod)
                else wrapper,
            )
            aliases(function, wrapper, initial_aliases)
        yield
    finally:
        for owner, name, descriptor, function, wrapper in reversed(saved):
            setattr(owner, name, descriptor)
            aliases(wrapper, function)
        for mod, name, value in initial_aliases:
            setattr(mod, name, value)
        remaining = sum(
            1
            for mod in modules()
            for value in vars(mod).values()
            if any(
                value is w or (isinstance(value, MethodType) and value.__func__ is w)
                for _, _, _, _, w in saved
            )
        )
        receipt.update(
            restored=all(vars(o)[n] is d for o, n, d, _, _ in saved) and remaining == 0,
            aliases_remaining=remaining,
        )


def validate_regions(
    saved: dict[str, Any],
    events: list[dict[str, Any]],
    pid: int,
    thread: int,
    read: int,
) -> dict[str, Any]:
    rows = saved["rows"]
    stack: list[int] = []
    seen: set[int] = set()
    starts = {}
    totals = {
        c: dict(calls=0, inclusive_cpu=0.0, exclusive_selected_cpu=0.0)
        for c in CATEGORIES
    }
    previous = -math.inf
    previous_cpu = -math.inf
    if (
        saved["status"] != "complete"
        or saved["errors"] != 0
        or len(events) != 2 * len(rows)
    ):
        raise ArithmeticError("complete selected-boundary ledger required")
    for event in events:
        index = event["index"]
        v = event["before"] if event["status"] == "running" else event.get("after")
        if (
            type(index) is not int
            or not 0 <= index < len(rows)
            or event["category"] not in CATEGORIES
            or event["read"] != read
            or v is None
            or set(v) != {"wall", "cpu", "pid", "thread"}
            or v["pid"] != pid
            or v["thread"] != thread
            or any(
                type(v[k]) not in (int, float) or not math.isfinite(v[k]) or v[k] < 0
                for k in ("wall", "cpu")
            )
            or v["wall"] < previous
            or v["cpu"] < previous_cpu
        ):
            raise ArithmeticError("selected event clock/identity/order changed")
        previous = v["wall"]
        previous_cpu = v["cpu"]
        if event["status"] == "running":
            if (
                index in seen
                or index != len(seen)
                or event["parent"] != (stack[-1] if stack else None)
            ):
                raise ArithmeticError("selected event parent/order changed")
            seen.add(index)
            starts[index] = event
            stack.append(index)
        elif event["status"] == "complete":
            if not stack or stack.pop() != index or event != rows[index]:
                raise ArithmeticError("selected final event/stack changed")
            start = copy.deepcopy(event)
            start.pop("after")
            start["status"] = "running"
            if start != starts[index]:
                raise ArithmeticError("selected start/final mismatch")
        else:
            raise ArithmeticError("failed selected call is not complete coverage")
    if stack or len(seen) != len(rows):
        raise ArithmeticError("missing selected calls")
    children: dict[int, list[int]] = {i: [] for i in range(len(rows))}
    for i, row in enumerate(rows):
        if row["index"] != i:
            raise ArithmeticError("selected ordinal changed")
        before, after = row["before"], row["after"]
        if after["cpu"] < before["cpu"]:
            raise ArithmeticError("CPU decreased")
        if row["parent"] is not None:
            p = row["parent"]
            parent = rows[p]
            if not (
                parent["before"]["wall"]
                <= before["wall"]
                <= after["wall"]
                <= parent["after"]["wall"]
            ) or not (
                parent["before"]["cpu"]
                <= before["cpu"]
                <= after["cpu"]
                <= parent["after"]["cpu"]
            ):
                raise ArithmeticError("selected interval not nested")
            children[p].append(i)
        x = totals[row["category"]]
        x["calls"] += 1
        x["inclusive_cpu"] += after["cpu"] - before["cpu"]
    union = 0.0
    for i, row in enumerate(rows):
        amount = row["after"]["cpu"] - row["before"]["cpu"]
        exclusive = amount - sum(
            rows[j]["after"]["cpu"] - rows[j]["before"]["cpu"] for j in children[i]
        )
        if exclusive < -1e-9:
            raise ArithmeticError("selected children exceed parent CPU")
        totals[row["category"]]["exclusive_selected_cpu"] += exclusive
        if row["parent"] is None:
            union += amount
    return dict(calls=len(rows), groups=totals, selected_union_cpu=union)


@contextmanager
def reader_observer(root: Path, c: dict[str, Any], output: Path) -> Iterator[None]:
    from compact_cached import cli

    underlying = cli.read
    regions = Regions(c["maximum_selected_calls"])
    rows: list[dict[str, Any]] = []
    state: dict[str, Any] = {}

    def observe(*args: Any, **kwargs: Any) -> dict[str, Any]:
        if (
            len(args) != 3
            or set(kwargs) != {"observed"}
            or type(kwargs["observed"]) is not list
            or kwargs["observed"]
            or len(rows) >= 3
        ):
            raise ArithmeticError("original actual read shape required")
        index = len(rows)
        folder = output / "reads" / str(index)
        folder.mkdir(parents=True)
        before = snapshot()
        row: dict[str, Any] = dict(index=index, status="running", before=before)
        rows.append(row)
        atomic(output / "inner-reads.json", dict(reads=rows))
        try:
            with (folder / "events.jsonl.gz").open("xb") as raw:
                with gzip.GzipFile(
                    filename="", mode="wb", fileobj=raw, mtime=0
                ) as stream:

                    def emit(value: dict[str, Any]) -> None:
                        stream.write(canonical(value) + b"\n")
                        stream.flush()
                        raw.flush()

                    regions.rows = []
                    regions.stack = []
                    regions.read_index = index
                    regions.emit = emit
                    regions.active = True
                    complete = False
                    try:
                        result = underlying(*args, **kwargs)
                        complete = True
                    finally:
                        regions.active = False
                        helpers.compressed(
                            folder / "ledger.json.gz",
                            dict(
                                status="complete"
                                if complete and not regions.stack and not regions.errors
                                else "partial",
                                rows=regions.rows,
                                errors=regions.errors,
                                pid=regions.pid,
                                thread=regions.thread,
                            ),
                        )
            if len(kwargs["observed"]) != 1:
                raise ArithmeticError("one actual read witness required")
            row.update(
                status="complete",
                scope=result["scope"],
                computed=kwargs["observed"][0],
                observation=record(before, snapshot()),
            )
            atomic(output / "inner-reads.json", dict(reads=rows))
            return result
        except BaseException as error:
            row.update(status="failed_retained", failure_kind=type(error).__name__)
            atomic(output / "inner-reads.json", dict(reads=rows))
            raise

    try:
        with selected_hooks(regions, state), patch.object(cli, "read", observe):
            yield
    finally:
        atomic(
            output / "hook-state.json",
            dict(state, total_selected_calls=regions.total, errors=regions.errors),
        )


def phase_ledgers(
    output: Path, child: dict[str, Any], old: dict[str, Any], c: dict[str, Any]
) -> list[dict[str, Any]]:
    inner = json.loads((output / "inner-reads.json").read_text())["reads"]
    outer = json.loads((output / "old/parent-resource-reads.json").read_text())["reads"]
    state = json.loads((output / "hook-state.json").read_text())
    if (
        len(inner) != 3
        or state["categories"] != list(CATEGORIES)
        or state["restored"] is not True
        or state["aliases_remaining"] != 0
        or state["errors"] != 0
    ):
        raise ArithmeticError("complete restored three-region hooks required")
    ledgers = []
    categories = set()
    total = 0
    for i, row in enumerate(inner):
        check_record(row["observation"])
        if (
            row["index"] != i
            or row["status"] != "complete"
            or row["scope"] != outer[i]["scope"]
            or row["computed"] != old["identity"]["computed_replays"][i]["computed"]
            or row["before"] != row["observation"]["before"]
            or row["before"]["pid"] != child["pid"]
        ):
            raise ArithmeticError("selected reader identity changed")
        if not (
            outer[i]["observation"]["before"]["perf_seconds"]
            <= row["before"]["perf_seconds"]
            <= row["observation"]["after"]["perf_seconds"]
            <= outer[i]["observation"]["after"]["perf_seconds"]
        ):
            raise ArithmeticError("selected read outside original boundary")
        folder = output / "reads" / str(i)
        ledger = helpers.load_compressed(folder / "ledger.json.gz")
        with gzip.open(folder / "events.jsonl.gz", "rt") as stream:
            events = [json.loads(x) for x in stream]
        summary = validate_regions(ledger, events, child["pid"], child["thread"], i)
        if ledger["pid"] != child["pid"] or ledger["thread"] != child["thread"]:
            raise ArithmeticError("selected producer changed")
        for region in ledger["rows"]:
            if not (
                row["before"]["perf_seconds"]
                <= region["before"]["wall"]
                <= region["after"]["wall"]
                <= row["observation"]["after"]["perf_seconds"]
            ) or not (
                row["before"]["process_cpu_seconds"]
                <= region["before"]["cpu"]
                <= region["after"]["cpu"]
                <= row["observation"]["after"]["process_cpu_seconds"]
            ):
                raise ArithmeticError("selected region outside reader")
            categories.add(region["category"])
        read_cpu = row["observation"]["interval"]["clocks"]["process_cpu_seconds"]
        if summary["selected_union_cpu"] > read_cpu + 1e-9:
            raise ArithmeticError("selected union exceeds read CPU")
        total += summary["calls"]
        ledgers.append(dict(ledger=ledger, summary=summary))
    if (
        categories != set(CATEGORIES)
        or total != state["total_selected_calls"]
        or not 0 < total <= c["maximum_selected_calls"]
    ):
        raise ArithmeticError("complete bounded region inventory required")
    return ledgers


def checked(root: Path, source: dict[str, Any]) -> None:
    from compact_cached.admission import published

    from poker_ai.evaluation.diagnostic_receipts import checks

    path = root / FOLDER / "checks.json"
    checks(root, path, source)
    published(root, path)
    for row in json.loads(path.read_text())["checks"]:
        p = root / row["log"]["file"]
        published(root, p)
        log = p.read_text(encoding="utf-8-sig")
        py, np = ("3.11.17", "2.4.6") if row["minor"] == "311" else ("3.12.15", "2.5.4")
        if row["numpy"] != np:
            raise ArithmeticError("actual qualified NumPy required")
        if row["role"] == "hosted":
            original.actual_host_runtime(log, py, np)
        elif set(re.findall(r"ACTUAL_PYTHON=([0-9.]+)", log)) != {py} or set(
            re.findall(r"ACTUAL_NUMPY=([0-9.]+)", log)
        ) != {np}:
            raise ArithmeticError("actual qualified local runtime required")


def child(root: Path, mode: str, output: Path, origin: float) -> int:
    saved: dict[str, Any] = dict(
        status="starting",
        mode=mode,
        pid=os.getpid(),
        thread=threading.get_ident(),
        execution_root=str(root.resolve()),
        execution_output=str(output.resolve()),
        executable=sys.executable,
        admission_evidence=False,
        poker_training_performed=False,
        reference_output_used_in_training=False,
    )
    atomic(output / "child.json", saved)
    try:
        if mode not in ("control", "profiled"):
            raise ValueError("unknown observation mode")
        c, source = binding(root)
        checked(root, source)
        saved["runtime_requirements"] = helpers.runtime_requirements(c)
        import numpy

        # Both arms import the same original entry alias before original card hooks.
        from compact_cached import cli  # noqa: F401

        from poker_ai.reproducibility import runtime_environment

        if (
            sys.version.split()[0] != c["runtime"]["python"]
            or numpy.__version__ != c["runtime"]["numpy"]
        ):
            raise ArithmeticError("original real-archive runtime required")
        saved.update(
            source=source,
            config_sha256=CONFIG_SHA,
            qualification_sha256=digest(root / FOLDER / "checks.json"),
            environment=runtime_environment(),
            idle_control=original.control(c),
        )
        atomic(output / "child.json", saved)
        targets()  # Common preloading in both halves, before original card hooks.
        (output / "old").mkdir()
        if mode == "profiled":
            with reader_observer(root, c, output):
                code = original.child(root, "uncached", output / "old", origin)
        else:
            code = original.child(root, "uncached", output / "old", origin)
        if code != 0:
            raise ArithmeticError("original audit child did not complete")
        old = original_result(root, output, c)
        if mode == "profiled":
            phase_ledgers(output, saved, old, c)
        after_c, after = binding(root, clean=False)
        if (
            c != after_c
            or source["sha256"] != after["sha256"]
            or saved["qualification_sha256"] != digest(root / FOLDER / "checks.json")
        ):
            raise ArithmeticError("measurement source/input/qualification changed")
        saved.update(
            status="complete",
            original_identity_sha256=hashlib.sha256(
                canonical(old["identity"])
            ).hexdigest(),
            reference_constructed=True,
            seconds=time.perf_counter() - origin,
        )
        saved["raw_sha256"] = {
            str(p.relative_to(output)): digest(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
            and (
                p.parent != output
                or p.name not in ("child.json", "measurement.json", "command.log")
            )
        }
        atomic(output / "child.json", saved)
        return 0
    except BaseException as error:
        saved.update(
            status="failed_retained",
            failure_kind=type(error).__name__,
            seconds=time.perf_counter() - origin,
        )
        atomic(output / "child.json", saved)
        return 130 if isinstance(error, KeyboardInterrupt) else 1


def verify_pair(root: Path, output: Path) -> dict[str, Any]:
    c, current = binding(root, clean=False)
    pair = json.loads((output / "pair.json").read_text())
    if (
        pair["status"] != "complete"
        or pair["admission_evidence"] is not False
        or type(pair["seconds"]) not in (int, float)
        or not 0 < pair["seconds"] < c["maximum_pair_seconds"]
        or len(pair["measurements"]) != 2
    ):
        raise ArithmeticError("complete capped original-context pair required")
    children, olds, data = [], [], []
    expected_files = {"pair.json"}
    for mode, m in zip(c["order"], pair["measurements"], strict=True):
        folder = output / mode
        row = json.loads((folder / "child.json").read_text())
        if (
            m != json.loads((folder / "measurement.json").read_text())
            or m["returncode"] != 0
            or m["interrupted"] is not None
            or type(m["seconds"]) not in (int, float)
            or not 0 < m["seconds"] < c["maximum_child_seconds"]
            or m["child_sha256"] != digest(folder / "child.json")
            or digest(folder / "command.log") != pair["command_log_sha256"][mode]
        ):
            raise ArithmeticError(
                "complete supervised measurement/raw binding required"
            )
        command = [
            c["idle_control"]["path"],
            *c["idle_control"]["arguments"],
            row["executable"],
            str(Path(row["execution_root"]) / ENTRY),
            "--child",
            mode,
            "--output",
            row["execution_output"],
        ]
        if (
            m["command"] != command
            or not Path(row["execution_output"]).is_relative_to(
                Path(row["execution_root"]) / "results/runs"
            )
            or row["mode"] != mode
            or row["status"] != "complete"
            or row["config_sha256"] != CONFIG_SHA
            or row["source"]["sha256"] != current["sha256"]
            or row["qualification_sha256"] != digest(root / FOLDER / "checks.json")
            or any(
                row[k] is not False
                for k in (
                    "admission_evidence",
                    "poker_training_performed",
                    "reference_output_used_in_training",
                )
            )
            or row["reference_constructed"] is not True
        ):
            raise ArithmeticError("measurement scope/source/command changed")
        if (
            row["runtime_requirements"]
            != dict(
                distributions=c["required_distributions"],
                metadata_probe=c["metadata_probe"],
            )
            or any(row["environment"][k] != v for k, v in c["runtime"].items())
            or row["idle_control"]
            != dict(
                c["idle_control"],
                requested=True,
                assertion_state_independently_audited=False,
            )
        ):
            raise ArithmeticError("actual runtime/metadata/control context changed")
        for name, sha in row["raw_sha256"].items():
            p = folder / name
            if (
                p.is_symlink()
                or not p.resolve().is_relative_to(folder.resolve())
                or digest(p) != sha
            ):
                raise ArithmeticError("retained raw original-context file changed")
            expected_files.add(f"{mode}/{name}")
        expected_files.update(
            f"{mode}/{n}" for n in ("child.json", "measurement.json", "command.log")
        )
        old = original_result(root, folder, c)
        if (
            row["pid"] != old["child_before"]["pid"]
            or row["original_identity_sha256"]
            != hashlib.sha256(canonical(old["identity"])).hexdigest()
        ):
            raise ArithmeticError("original child process or identity changed")
        if mode == "profiled":
            data = phase_ledgers(folder, row, old, c)
        elif (folder / "inner-reads.json").exists() or (folder / "reads").exists():
            raise ArithmeticError("control must not install the added read observer")
        children.append(row)
        olds.append(old)
    if expected_files != {
        str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()
    } or any(p.is_symlink() for p in output.rglob("*")):
        raise ArithmeticError("raw file inventory changed")
    if (
        children[0]["pid"] == children[1]["pid"]
        or children[0]["source"] != children[1]["source"]
        or olds[0]["identity"] != olds[1]["identity"]
        or olds[0]["card_cache"] != olds[1]["card_cache"]
    ):
        raise ArithmeticError(
            "separate children with exact original audit identity required"
        )
    checked(root, children[0]["source"])
    return dict(pair=pair, children=children, originals=olds, ledgers=data)


def pair(root: Path, output: Path) -> int:
    started = time.perf_counter()
    output = output.resolve()
    if (
        output.exists()
        or output.is_symlink()
        or not output.is_relative_to(root.resolve() / "results/runs")
    ):
        raise ValueError("fresh ignored destination required; retain every attempt")
    output.mkdir(parents=True)
    saved: dict[str, Any] = dict(
        status="running", measurements=[], admission_evidence=False
    )
    atomic(output / "pair.json", saved)
    try:
        c = contract(root)
        original.control(c)
        for mode in c["order"]:
            cap = min(
                c["maximum_child_seconds"],
                started + c["maximum_pair_seconds"] - time.perf_counter(),
            )
            if cap <= 0:
                raise TimeoutError("shared complete diagnostic cap")
            m = supervise(
                [
                    c["idle_control"]["path"],
                    *c["idle_control"]["arguments"],
                    sys.executable,
                    str(root / ENTRY),
                    "--child",
                    mode,
                    "--output",
                    str(output / mode),
                ],
                output / mode,
                cap,
            )
            saved["measurements"].append(m)
            log = output / mode / "command.log"
            saved.setdefault("command_log_sha256", {})[mode] = (
                digest(log) if log.is_file() else None
            )
            atomic(output / "pair.json", saved)
            if m["returncode"] != 0:
                raise ArithmeticError("child failed; partial evidence retained")
        saved.update(status="complete", seconds=time.perf_counter() - started)
        atomic(output / "pair.json", saved)
        verify_pair(root, output)
        saved["seconds"] = time.perf_counter() - started
        if saved["seconds"] >= c["maximum_pair_seconds"]:
            raise TimeoutError("final verification exceeds shared cap")
        atomic(output / "pair.json", saved)
        return 0
    except BaseException as error:
        saved.update(
            status="failed_retained",
            failure_kind=type(error).__name__,
            seconds=time.perf_counter() - started,
        )
        atomic(output / "pair.json", saved)
        return 130 if isinstance(error, KeyboardInterrupt) else 1


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--output", type=Path, default=Path("results/runs/coarse-reader-cpu/pair")
    )
    p.add_argument("--child", choices=("control", "profiled"), help=argparse.SUPPRESS)
    p.add_argument("--show", action="store_true")
    args = p.parse_args()
    if args.show:
        print(json.dumps(report(ROOT, ROOT / args.output), sort_keys=True, indent=2))
        return 0
    if args.child:
        return child(
            ROOT,
            args.child,
            ROOT / args.output,
            float(os.environ["POKER_COMPACT_REPLAY_PROFILE_STARTED"]),
        )
    return pair(ROOT, ROOT / args.output)


def report(root: Path, output: Path) -> dict[str, Any]:
    verified = verify_pair(root, output)
    rows = []
    for mode in ("control", "profiled"):
        outer = json.loads(
            (output / mode / "old/parent-resource-reads.json").read_text()
        )["reads"]
        for i, row in enumerate(outer):
            v: dict[str, Any] = dict(
                mode=mode,
                read=i,
                scope=row["scope"],
                outer=row["observation"]["interval"],
                selected=None,
            )
            if mode == "profiled":
                x = verified["ledgers"][i]["summary"]
                inner = json.loads((output / mode / "inner-reads.json").read_text())[
                    "reads"
                ][i]["observation"]["interval"]
                v.update(
                    selected=x,
                    inner=inner,
                    outside_selected_cpu=inner["clocks"]["process_cpu_seconds"]
                    - x["selected_union_cpu"],
                )
            rows.append(v)
    return dict(
        scope="ONE_ORDERED_COARSE_READER_PROCESS_CPU_NOT_INSTRUCTION_SAMPLES_OR_ADMISSION",
        rows=rows,
        measurements=verified["pair"]["measurements"],
        original_identity_exact=True,
        poker_training_performed=False,
        long_run_admitted=False,
        input_sha256={
            str(p.relative_to(output)): digest(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
        },
    )


if __name__ == "__main__":
    raise SystemExit(main())
