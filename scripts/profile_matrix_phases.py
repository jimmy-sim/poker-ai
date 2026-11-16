"""Source-bound original matrix phases; never a cost or training admission."""

import argparse
import hashlib
import json
import os
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any

import collect_complete_reader_helpers as helpers
import compare_grouped_depth as predecessor
import grouped_depth_support as previous
import matrix_phase_support as depth
import profile_reader_loads as prior
import trace_card_audit as original
from profile_compact_replay import atomic, canonical, digest, supervise

ROOT = Path(__file__).resolve().parents[1]
ENTRY = "scripts/profile_matrix_phases.py"
SUPPORT = "scripts/matrix_phase_support.py"
CONFIG = "configs/matrix-phases.json"
CONFIG_SHA = "7d3b5f2b23e4df7f28b95e45639be4603d38cb044593b71eba492e77438129ad"
FOLDER = "results/matrix-phases"


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective matrix-phase contract changed")
    c: dict[str, Any] = json.loads((root / CONFIG).read_text())
    for name, checksum in c["input_sha256"].items():
        p = root / name
        if (
            p.is_symlink()
            or not p.resolve().is_relative_to(root.resolve())
            or digest(p) != checksum
        ):
            raise ArithmeticError("matrix-phase retained input changed")
    return c


def binding(root: Path, *, clean: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.validation.five_card import source_provenance

    if (
        Path(__file__).resolve() != root.resolve() / ENTRY
        or Path(depth.__file__).resolve() != root.resolve() / SUPPORT
        or Path(prior.__file__).resolve() != root.resolve() / prior.ENTRY
    ):
        raise ArithmeticError("matrix-phase imports outside stated checkout")
    c = contract(root)
    _, previous = predecessor.binding(root, clean=clean)
    anchor = json.loads((root / c["preserved_source_anchor"]).read_text())["source"][
        "sha256"
    ]
    if len(anchor) != 409 or previous["sha256"] != anchor:
        raise ArithmeticError("preserve all409 prior source files")
    source: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=(ENTRY, SUPPORT))
    )
    source["sha256"].update(anchor)
    source["fingerprint"] = sha(source["sha256"])
    if len(source["sha256"]) != 412 or (clean and source["dirty"] is not False):
        raise ArithmeticError("publish clean412-file matrix-phase source")
    commit_sources(root, source["git_commit"], source["sha256"])
    return c, source


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


def phase_ledgers(
    output: Path,
    child: dict[str, Any],
    old: dict[str, Any],
    c: dict[str, Any],
    *,
    root: Path = ROOT,
) -> list[dict[str, Any]]:
    data = prior.phase_ledgers(output, child, old, c, root=root)
    baseline = json.loads((root / c["full_capture_baseline"]).read_text())
    expected = [x for x in baseline["rows"] if x["mode"] == "original"]
    if len(expected) != 3:
        raise ArithmeticError("complete three-read baseline required")
    for i, (actual, wanted) in enumerate(zip(data, expected, strict=True)):
        counts = {k: v["calls"] for k, v in actual["summary"]["groups"].items()}
        previous = {k: v["calls"] for k, v in wanted["selected"]["groups"].items()}
        if (
            wanted["read"] != i
            or counts != previous
            or set(counts) != set(prior.CATEGORIES)
        ):
            raise ArithmeticError("original six-category inventory changed")
    if sum(x["summary"]["calls"] for x in data) != 1538:
        raise ArithmeticError("complete1538 selected calls required per arm")
    return data


def runtime(c: dict[str, Any]) -> dict[str, Any]:
    import numpy

    from poker_ai.reproducibility import runtime_environment

    if (
        sys.version.split()[0] != c["runtime"]["python"]
        or numpy.__version__ != c["runtime"]["numpy"]
    ):
        raise ArithmeticError("original archive runtime required")
    return dict(
        requirements=helpers.runtime_requirements(c),
        environment=runtime_environment(),
        idle_control=original.control(c),
    )


def verify_negative(
    output: Path, c: dict[str, Any], pid: int, thread: int
) -> dict[str, Any]:
    """Explicit expected software failures; never usable successful real evidence."""
    expected = {
        mode: dict(
            expected_failure="ValueError",
            message=previous.MESSAGE,
            synthetic_software_only=True,
        )
        for mode in c["proof_modes"]
    }
    if json.loads((output / "expected-negative.json").read_text()) != expected:
        raise ArithmeticError("declared negative software inventory changed")
    for mode in c["proof_modes"]:
        folder = output / (mode + "-negative")
        receipt = json.loads((folder / "constructor.json").read_text())
        raw = (folder / "constructor-events.jsonl").read_bytes()
        rows = [json.loads(x) for x in raw.splitlines()]
        wanted = dict(
            status="failed_retained",
            mode=mode,
            pid=pid,
            thread=thread,
            maximum=c["maximum_builder_calls_per_child"],
            calls=1,
            completed=0,
            primary_failures=1,
            errors=0,
            restored=True,
            aliases_remaining=0,
            scope=(
                "whole original child main-process constructor field witnesses; "
                "native spawned workers unchanged"
            ),
            events_sha256=hashlib.sha256(raw).hexdigest(),
        )
        if (
            receipt != wanted
            or any(
                type(receipt[k]) is not int
                for k in (
                    "pid",
                    "thread",
                    "maximum",
                    "calls",
                    "completed",
                    "primary_failures",
                    "errors",
                    "aliases_remaining",
                )
            )
            or rows
            != [
                dict(index=0, status="running"),
                dict(index=0, status="primary_failed", failure_kind="ValueError"),
            ]
        ):
            raise ArithmeticError("expected original depth rejection not retained")
        if mode == "phased":
            raw_phase = (folder / "phase-events.jsonl").read_bytes()
            state = json.loads((folder / "phases.json").read_text())
            if state != dict(
                status="failed_retained",
                pid=pid,
                thread=thread,
                maximum=c["maximum_builder_calls_per_child"],
                completed=0,
                errors=0,
                phases=list(depth.PHASES),
                events_sha256=hashlib.sha256(raw_phase).hexdigest(),
            ) or any(
                type(state[k]) is not int
                for k in ("pid", "thread", "maximum", "completed", "errors")
            ):
                raise ArithmeticError("expected failed depth phase receipt changed")
            events = [json.loads(x) for x in raw_phase.splitlines()]
            if len(events) != 8:
                raise ArithmeticError(
                    "expected depth rejection phase inventory changed"
                )
            previous_clock: dict[str, float] | None = None
            for i, event in enumerate(events):
                keys = {"event", "sequence", "pid", "thread", "index", "clocks"}
                kind = (
                    "constructor_begin"
                    if i == 0
                    else "constructor_failed"
                    if i == 7
                    else "phase_begin"
                    if i % 2
                    else "phase_failed"
                    if i == 6
                    else "phase_end"
                )
                if 0 < i < 7:
                    keys.update(("phase", "ordinal"))
                    if (
                        event.get("phase") != depth.PHASES[(i - 1) // 2]
                        or type(event.get("ordinal")) is not int
                        or event["ordinal"] != (i - 1) // 2
                    ):
                        raise ArithmeticError(
                            "expected depth rejection phase order changed"
                        )
                    if i % 2 == 0:
                        keys.add("failure_kind")
                        if event.get("failure_kind") != (
                            "ValueError" if i == 6 else None
                        ):
                            raise ArithmeticError(
                                "unexpected negative fixture exception"
                            )
                clocks = event.get("clocks")
                if (
                    set(event) != keys
                    or event["event"] != kind
                    or any(
                        type(event[k]) is not int
                        for k in ("sequence", "pid", "thread", "index")
                    )
                    or (
                        event["sequence"],
                        event["pid"],
                        event["thread"],
                        event["index"],
                    )
                    != (i, pid, thread, 0)
                    or type(clocks) is not dict
                    or set(clocks) != {"wall", "cpu"}
                ):
                    raise ArithmeticError(
                        "expected negative phase schema/context changed"
                    )
                import math

                if any(
                    type(v) not in (int, float) or not math.isfinite(v) or v < 0
                    for v in clocks.values()
                ) or (
                    previous_clock is not None
                    and any(clocks[k] < previous_clock[k] for k in clocks)
                ):
                    raise ArithmeticError("expected negative fixture clock changed")
                previous_clock = clocks
    return expected


def constructor_phases(
    root: Path,
    output: Path,
    c: dict[str, Any],
    child: dict[str, Any],
    fingerprints: list[str],
) -> list[dict[str, Any]]:
    """Require all original fingerprints, exact phase counts and outer containment."""
    baseline = root / c["constructor_baseline"]
    state = json.loads((baseline / "constructor.json").read_text())
    wanted = previous.read_constructors(
        baseline,
        "original",
        c["maximum_builder_calls_per_child"],
        state["pid"],
        state["thread"],
    )
    if len(fingerprints) != c["expected_constructors"] or fingerprints != wanted:
        raise ArithmeticError("all184 pinned original constructor fields required")
    rows = depth.read_phases(
        output / "constructors",
        c["expected_constructors"],
        c["maximum_builder_calls_per_child"],
        child["pid"],
        child["thread"],
    )
    outer: list[dict[str, Any]] = []
    for index in range(3):
        ledger = helpers.load_compressed(
            output / "reads" / str(index) / "ledger.json.gz"
        )
        outer.extend(
            dict(region, read=index)
            for region in ledger["rows"]
            if region["category"] == "matrix_build"
        )
    if len(outer) != len(rows):
        raise ArithmeticError("constructor/matrix boundary inventory mismatch")
    for inner, region in zip(rows, outer, strict=True):
        if region["status"] != "complete" or any(
            not (
                region["before"][k]
                <= inner["before"][k]
                <= inner["after"][k]
                <= region["after"][k]
            )
            for k in ("cpu", "wall")
        ):
            raise ArithmeticError("constructor phases outside original matrix boundary")
        inner["read"] = region["read"]
        inner["matrix_boundary"] = region
    return rows


def software_child(root: Path, output: Path, origin: float) -> int:
    """Formal source-bound constructor proof only, after published six-role checks."""
    saved: dict[str, Any] = dict(
        status="starting",
        execution_root=str(root.resolve()),
        execution_output=str(output.resolve()),
        executable=sys.executable,
        pid=os.getpid(),
        thread=threading.get_ident(),
        scope="ORIGINAL_MATRIX_PHASE_SOFTWARE_ONLY_NOT_TRAINING_OR_NATIVE",
        admission_evidence=False,
        poker_training_performed=False,
        reference_constructed=False,
        reference_output_used_in_training=False,
    )
    atomic(output / "child.json", saved)
    try:
        from poker_ai.abstraction.model import CardAbstraction
        from poker_ai.postflop.game import load_spot
        from poker_ai.postflop.matrix import MatrixTree
        from poker_ai.postflop.tree import SpotTree

        c, source = binding(root)
        checked(root, source)
        saved.update(
            source=source,
            config_sha256=CONFIG_SHA,
            qualification_sha256=digest(root / FOLDER / "checks.json"),
            runtime=runtime(c),
        )
        atomic(output / "child.json", saved)
        fixture = SpotTree.build(load_spot(root / c["proof_spot"]))
        model = CardAbstraction.load(root / c["proof_model"])
        witnesses = {}
        negative = {}
        for mode in c["proof_modes"]:
            with depth.constructor_scope(
                mode, output / mode, c["maximum_builder_calls_per_child"]
            ):
                for encoding in c["proof_encodings"]:
                    MatrixTree.build(fixture, encoding, model)
            witnesses[mode] = previous.read_constructors(
                output / mode,
                mode,
                c["maximum_builder_calls_per_child"],
                saved["pid"],
                saved["thread"],
            )
            if mode == "phased":
                depth.read_phases(
                    output / mode,
                    len(c["proof_encodings"]),
                    c["maximum_builder_calls_per_child"],
                    saved["pid"],
                    saved["thread"],
                )
            synthetic = depth.depth_error_fixture(fixture)
            try:
                with depth.constructor_scope(
                    mode,
                    output / (mode + "-negative"),
                    c["maximum_builder_calls_per_child"],
                ):
                    MatrixTree.build(synthetic)
            except ValueError as error:
                if str(error) != previous.MESSAGE:
                    raise
                negative[mode] = dict(
                    expected_failure="ValueError",
                    message=str(error),
                    synthetic_software_only=True,
                )
            else:
                raise ArithmeticError(
                    "negative software fixture was incorrectly accepted"
                )
        atomic(output / "expected-negative.json", negative)
        if witnesses["original"] != witnesses["phased"] or len(
            witnesses["original"]
        ) != len(c["proof_encodings"]):
            raise ArithmeticError("all software constructor fields must match exactly")
        after_c, after = binding(root, clean=False)
        if (
            c != after_c
            or source["sha256"] != after["sha256"]
            or saved["qualification_sha256"] != digest(root / FOLDER / "checks.json")
        ):
            raise ArithmeticError("software proof source/input/qualification changed")
        saved.update(
            status="complete",
            seconds=time.perf_counter() - origin,
            constructor_fingerprints=witnesses,
            expected_negative_fixtures=negative,
            successful_constructor_fields_per_arm=len(c["proof_encodings"]),
        )
        saved["raw_sha256"] = {
            str(p.relative_to(output)): digest(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
            and p.name not in ("child.json", "measurement.json", "command.log")
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


def registered_origin() -> float:
    """The published operator starts this clock before launching Python."""
    import math

    raw = os.environ.get("POKER_MATRIX_PHASES_COMMAND_STARTED")
    if raw is None:
        raise ArithmeticError(
            "formal collection requires the published launch operator"
        )
    origin = float(raw)
    if not math.isfinite(origin) or not 0 < origin <= time.perf_counter():
        raise ArithmeticError("invalid registered command origin")
    return origin


def fresh(root: Path, output: Path) -> Path:
    if output.is_symlink():
        raise ValueError("fresh ignored destination required; retain every attempt")
    output = output.resolve()
    if (
        output.exists()
        or output.is_symlink()
        or not output.is_relative_to(root.resolve() / "results/runs")
    ):
        raise ValueError("fresh ignored destination required; retain every attempt")
    output.mkdir(parents=True)
    return output


def raw_files(folder: Path, child: dict[str, Any]) -> set[str]:
    expected = {"child.json", "measurement.json", "command.log"}
    for name, checksum in child["raw_sha256"].items():
        path = folder / name
        if (
            path.is_symlink()
            or not path.resolve().is_relative_to(folder.resolve())
            or digest(path) != checksum
        ):
            raise ArithmeticError("retained child raw bytes changed")
        expected.add(name)
    if expected != {
        str(p.relative_to(folder)) for p in folder.rglob("*") if p.is_file()
    } or any(p.is_symlink() for p in folder.rglob("*")):
        raise ArithmeticError("retained child inventory changed")
    return expected


def supervised(
    c: dict[str, Any],
    folder: Path,
    child: dict[str, Any],
    measurement: dict[str, Any],
    flag: list[str],
    cap: float,
) -> None:
    expected_command = [
        c["idle_control"]["path"],
        *c["idle_control"]["arguments"],
        child["executable"],
        str(Path(child["execution_root"]) / ENTRY),
        *flag,
        "--output",
        child["execution_output"],
    ]
    if (
        measurement != json.loads((folder / "measurement.json").read_text())
        or measurement["returncode"] != 0
        or measurement["interrupted"] is not None
        or type(measurement["seconds"]) not in (int, float)
        or not 0 < measurement["seconds"] < cap
        or measurement["child_sha256"] != digest(folder / "child.json")
        or measurement["command"] != expected_command
        or not Path(child["execution_output"]).is_relative_to(
            Path(child["execution_root"]) / "results/runs"
        )
    ):
        raise ArithmeticError("complete original supervised command required")


def child_identity(
    root: Path, c: dict[str, Any], child: dict[str, Any], current: dict[str, Any]
) -> None:
    if (
        child["status"] != "complete"
        or child["source"]["sha256"] != current["sha256"]
        or child["source"]["dirty"] is not False
        or child["config_sha256"] != CONFIG_SHA
        or child["qualification_sha256"] != digest(root / FOLDER / "checks.json")
        or any(
            child[k] is not False
            for k in (
                "admission_evidence",
                "poker_training_performed",
                "reference_output_used_in_training",
            )
        )
    ):
        raise ArithmeticError("complete qualified matrix-phase child required")
    metadata = child["runtime"]
    if (
        metadata["requirements"]
        != dict(
            distributions=c["required_distributions"],
            metadata_probe=c["metadata_probe"],
        )
        or any(metadata["environment"][k] != v for k, v in c["runtime"].items())
        or metadata["idle_control"]
        != dict(
            c["idle_control"],
            requested=True,
            assertion_state_independently_audited=False,
        )
    ):
        raise ArithmeticError("actual child runtime/metadata/control changed")


def verify_software(root: Path, output: Path) -> dict[str, Any]:
    c, current = binding(root, clean=False)
    proof = json.loads((output / "proof.json").read_text())
    child = json.loads((output / "child/child.json").read_text())
    measurement = proof["measurement"]
    if (
        proof["status"] != "complete"
        or proof["admission_evidence"] is not False
        or type(proof["seconds"]) not in (int, float)
        or not 0 < proof["seconds"] < c["maximum_software_proof_seconds"]
        or proof["command_log_sha256"] != digest(output / "child/command.log")
        or child["reference_constructed"] is not False
        or child["scope"]
        != "ORIGINAL_MATRIX_PHASE_SOFTWARE_ONLY_NOT_TRAINING_OR_NATIVE"
    ):
        raise ArithmeticError("complete capped own-only software proof required")
    supervised(
        c,
        output / "child",
        child,
        measurement,
        ["--proof-child"],
        c["maximum_software_proof_seconds"],
    )
    child_identity(root, c, child, current)
    raw_files(output / "child", child)
    vectors = {
        mode: previous.read_constructors(
            output / "child" / mode,
            mode,
            c["maximum_builder_calls_per_child"],
            child["pid"],
            child["thread"],
        )
        for mode in c["proof_modes"]
    }
    phases = depth.read_phases(
        output / "child/phased",
        len(c["proof_encodings"]),
        c["maximum_builder_calls_per_child"],
        child["pid"],
        child["thread"],
    )
    negative = verify_negative(output / "child", c, child["pid"], child["thread"])
    if (
        vectors["original"] != vectors["phased"]
        or len(vectors["original"]) != len(c["proof_encodings"])
        or child["constructor_fingerprints"] != vectors
        or child["expected_negative_fixtures"] != negative
        or child["successful_constructor_fields_per_arm"] != len(c["proof_encodings"])
    ):
        raise ArithmeticError(
            "all five original/phased witnesses and expected failures required"
        )
    if {str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()} != {
        "proof.json",
        *("child/" + n for n in raw_files(output / "child", child)),
    }:
        raise ArithmeticError("software proof outer inventory changed")
    checked(root, current)
    return dict(
        proof=proof,
        child=child,
        constructors=vectors,
        phases=phases,
        expected_negative=negative,
    )


def proof_run(root: Path, output: Path) -> int:
    started = registered_origin()
    output = fresh(root, output)
    saved: dict[str, Any] = dict(status="running", admission_evidence=False)
    atomic(output / "proof.json", saved)
    try:
        c, source = binding(root)
        checked(root, source)
        original.control(c)
        cap = c["maximum_software_proof_seconds"] - (time.perf_counter() - started)
        if cap <= 0:
            raise TimeoutError("software proof preconditions exhausted complete cap")
        measurement = supervise(
            [
                c["idle_control"]["path"],
                *c["idle_control"]["arguments"],
                sys.executable,
                str(root / ENTRY),
                "--proof-child",
                "--output",
                str(output / "child"),
            ],
            output / "child",
            cap,
        )
        saved["measurement"] = measurement
        log = output / "child/command.log"
        saved["command_log_sha256"] = digest(log) if log.exists() else None
        if measurement["returncode"] != 0:
            raise ArithmeticError(
                "software proof child failed; retain partial evidence"
            )
        saved.update(status="complete", seconds=time.perf_counter() - started)
        atomic(output / "proof.json", saved)
        verify_software(root, output)
        saved["seconds"] = time.perf_counter() - started
        atomic(output / "proof.json", saved)
        if time.perf_counter() - started >= c["maximum_software_proof_seconds"]:
            raise TimeoutError("complete software proof exceeded shared cap")
        return 0
    except BaseException as error:
        saved.update(
            status="failed_retained",
            failure_kind=type(error).__name__,
            seconds=time.perf_counter() - started,
        )
        atomic(output / "proof.json", saved)
        return 130 if isinstance(error, KeyboardInterrupt) else 1


def published_proof(root: Path) -> str:
    from compact_cached.admission import published

    output = root / FOLDER / "software"
    verify_software(root, output)
    for p in sorted(output.rglob("*")):
        if p.is_file():
            published(root, p)
    return digest(output / "proof.json")


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
        c, source = binding(root)
        if mode not in c["order"]:
            raise ValueError("unknown matrix-phase arm")
        checked(root, source)
        saved.update(
            source=source,
            config_sha256=CONFIG_SHA,
            qualification_sha256=digest(root / FOLDER / "checks.json"),
            proof_sha256=published_proof(root),
            runtime=runtime(c),
        )
        atomic(output / "child.json", saved)
        prior.targets()  # Same preload before original card hooks in both arms.
        (output / "old").mkdir()
        with depth.constructor_scope(
            "phased", output / "constructors", c["maximum_builder_calls_per_child"]
        ):
            with prior.reader_observer(root, c, output):
                code = original.child(root, "uncached", output / "old", origin)
        if code != 0:
            raise ArithmeticError("original complete audit child failed")
        old = prior.original_result(root, output, c)
        phase_ledgers(output, saved, old, c, root=root)
        constructors = previous.read_constructors(
            output / "constructors",
            "phased",
            c["maximum_builder_calls_per_child"],
            saved["pid"],
            saved["thread"],
        )
        constructor_phases(root, output, c, saved, constructors)
        after_c, after = binding(root, clean=False)
        if (
            c != after_c
            or source["sha256"] != after["sha256"]
            or saved["qualification_sha256"] != digest(root / FOLDER / "checks.json")
            or saved["proof_sha256"] != digest(root / FOLDER / "software/proof.json")
        ):
            raise ArithmeticError("comparison prerequisites changed during child")
        saved.update(
            status="complete",
            reference_constructed=True,
            original_identity_sha256=hashlib.sha256(
                canonical(old["identity"])
            ).hexdigest(),
            constructor_calls=len(constructors),
            constructors_sha256=hashlib.sha256(canonical(constructors)).hexdigest(),
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
        or len(pair["measurements"]) != 1
    ):
        raise ArithmeticError("complete capped matrix-phase pair required")
    children, originals, ledgers, constructors = [], [], {}, {}
    expected = {"pair.json"}
    for mode, measurement in zip(c["order"], pair["measurements"], strict=True):
        folder = output / mode
        row = json.loads((folder / "child.json").read_text())
        supervised(
            c, folder, row, measurement, ["--child", mode], c["maximum_child_seconds"]
        )
        child_identity(root, c, row, current)
        if (
            row["mode"] != mode
            or row["reference_constructed"] is not True
            or row["proof_sha256"] != digest(root / FOLDER / "software/proof.json")
            or pair["command_log_sha256"][mode] != digest(folder / "command.log")
        ):
            raise ArithmeticError("arm/mathematical proof/log changed")
        expected.update(mode + "/" + n for n in raw_files(folder, row))
        old = prior.original_result(root, folder, c)
        if (
            row["pid"] != old["child_before"]["pid"]
            or row["original_identity_sha256"]
            != hashlib.sha256(canonical(old["identity"])).hexdigest()
        ):
            raise ArithmeticError("original audit process or computed identity changed")
        ledgers[mode] = phase_ledgers(folder, row, old, c, root=root)
        constructors[mode] = previous.read_constructors(
            folder / "constructors",
            "phased",
            c["maximum_builder_calls_per_child"],
            row["pid"],
            row["thread"],
        )
        if (
            not 184 == len(constructors[mode]) == row["constructor_calls"]
            or row["constructors_sha256"]
            != hashlib.sha256(canonical(constructors[mode])).hexdigest()
        ):
            raise ArithmeticError("whole-child constructor binding/count changed")
        constructor_phases(root, folder, c, row, constructors[mode])
        children.append(row)
        originals.append(old)
    if (
        sum(x["summary"]["calls"] for mode in c["order"] for x in ledgers[mode])
        + c["expected_phase_calls"]
        != c["expected_combined_calls"]
        or c["expected_combined_calls"] >= c["maximum_selected_calls_total"]
        or expected
        != {str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()}
        or any(p.is_symlink() for p in output.rglob("*"))
    ):
        raise ArithmeticError(
            "complete original-only audit/fields/phase capture required"
        )
    checked(root, current)
    published_proof(root)
    return dict(
        pair=pair,
        children=children,
        originals=originals,
        ledgers=ledgers,
        constructors=constructors,
    )


def pair_run(root: Path, output: Path) -> int:
    started = registered_origin()
    output = fresh(root, output)
    saved: dict[str, Any] = dict(
        status="running", measurements=[], admission_evidence=False
    )
    atomic(output / "pair.json", saved)
    try:
        c, source = binding(root)
        checked(root, source)
        published_proof(root)
        original.control(c)
        for mode in c["order"]:
            cap = min(
                c["maximum_child_seconds"],
                c["maximum_pair_seconds"] - (time.perf_counter() - started),
            )
            if cap <= 0:
                raise TimeoutError("shared complete comparison cap")
            measurement = supervise(
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
            saved["measurements"].append(measurement)
            log = output / mode / "command.log"
            saved.setdefault("command_log_sha256", {})[mode] = (
                digest(log) if log.exists() else None
            )
            atomic(output / "pair.json", saved)
            if measurement["returncode"] != 0:
                raise ArithmeticError(
                    "comparison child failed; retain partial evidence"
                )
        saved.update(status="complete", seconds=time.perf_counter() - started)
        atomic(output / "pair.json", saved)
        verify_pair(root, output)
        saved["seconds"] = time.perf_counter() - started
        atomic(output / "pair.json", saved)
        if time.perf_counter() - started >= c["maximum_pair_seconds"]:
            raise TimeoutError("final verification exceeded shared cap")
        return 0
    except BaseException as error:
        saved.update(
            status="failed_retained",
            failure_kind=type(error).__name__,
            seconds=time.perf_counter() - started,
        )
        atomic(output / "pair.json", saved)
        return 130 if isinstance(error, KeyboardInterrupt) else 1


def report(root: Path, output: Path) -> dict[str, Any]:
    import math

    verified = verify_pair(root, output)
    mode = "original_profiled"
    folder = output / mode
    row = verified["children"][0]
    phases = constructor_phases(
        root, folder, contract(root), row, verified["constructors"][mode]
    )
    return dict(
        scope="ONE_ORIGINAL_ONLY_PHASE_LOCALIZATION_NOT_COST_OR_TRAINING_ADMISSION",
        measurements=verified["pair"]["measurements"],
        ledgers=verified["ledgers"],
        constructor_phases=phases,
        phase_cpu={
            name: math.fsum(x["phases"][name]["cpu"] for x in phases)
            for name in depth.PHASES
        },
        phase_wall={
            name: math.fsum(x["phases"][name]["wall"] for x in phases)
            for name in depth.PHASES
        },
        constructor_remainder_cpu=math.fsum(x["remainder"]["cpu"] for x in phases),
        original_identity_exact=True,
        all_constructor_fingerprints_equal=True,
        global_selected_calls=1538,
        phase_calls=920,
        combined_selected_calls=2458,
        diagnostic_cost_pass_claim_permitted=False,
        poker_training_performed=False,
        long_run_admitted=False,
        input_sha256={
            str(p.relative_to(root)): digest(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--prove", action="store_true")
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--show-proof", action="store_true")
    parser.add_argument(
        "--child", choices=("original_profiled",), help=argparse.SUPPRESS
    )
    parser.add_argument("--proof-child", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    if (
        sum(
            bool(x)
            for x in (
                args.prove,
                args.show,
                args.show_proof,
                args.child,
                args.proof_child,
            )
        )
        > 1
    ):
        parser.error("choose exactly one operation")
    destination = ROOT / (
        args.output
        or Path(
            "results/runs/matrix-phases/software"
            if args.prove or args.show_proof
            else "results/runs/matrix-phases/pair"
        )
    )
    if args.show:
        print(json.dumps(report(ROOT, destination), sort_keys=True, indent=2))
        return 0
    if args.show_proof:
        print(json.dumps(verify_software(ROOT, destination), sort_keys=True, indent=2))
        return 0
    if args.child or args.proof_child:
        if args.output is None:
            parser.error("child output required")
        origin = float(os.environ["POKER_COMPACT_REPLAY_PROFILE_STARTED"])
        return (
            child(ROOT, args.child, destination, origin)
            if args.child
            else software_child(ROOT, destination, origin)
        )
    return proof_run(ROOT, destination) if args.prove else pair_run(ROOT, destination)


if __name__ == "__main__":
    raise SystemExit(main())
