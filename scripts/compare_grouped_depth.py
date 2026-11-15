"""Source-bound grouped matrix-depth comparison, never a training admission."""

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
import grouped_depth_support as depth
import profile_reader_loads as prior
import trace_card_audit as original
from profile_compact_replay import atomic, canonical, digest, supervise

ROOT = Path(__file__).resolve().parents[1]
ENTRY = "scripts/compare_grouped_depth.py"
SUPPORT = "scripts/grouped_depth_support.py"
CONFIG = "configs/grouped-depth-check.json"
CONFIG_SHA = "8e627b4c8b9dc4a4a2346374a240dc3ed57836ed59c9190c0031cc1be70d03f8"
FOLDER = "results/grouped-depth-check"


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective grouped-depth contract changed")
    c: dict[str, Any] = json.loads((root / CONFIG).read_text())
    for name, checksum in c["input_sha256"].items():
        p = root / name
        if (
            p.is_symlink()
            or not p.resolve().is_relative_to(root.resolve())
            or digest(p) != checksum
        ):
            raise ArithmeticError("grouped-depth retained input changed")
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
        raise ArithmeticError("grouped-depth imports outside stated checkout")
    c = contract(root)
    _, previous = prior.binding(root, clean=clean)
    anchor = json.loads((root / c["preserved_source_anchor"]).read_text())["source"][
        "sha256"
    ]
    if len(anchor) != 406 or previous["sha256"] != anchor:
        raise ArithmeticError("preserve all406 prior source files")
    source: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=(ENTRY, SUPPORT))
    )
    source["sha256"].update(anchor)
    source["fingerprint"] = sha(source["sha256"])
    if len(source["sha256"]) != 409 or (clean and source["dirty"] is not False):
        raise ArithmeticError("publish clean409-file grouped-depth source")
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
    expected = [x for x in baseline["rows"] if x["mode"] == "profiled"]
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


def software_cases(c: dict[str, Any]) -> list[dict[str, Any]]:
    """New fixed integer fixtures only; never a historical poker RNG stream."""
    import numpy as np

    rng = np.random.Generator(np.random.PCG64(c["software_fixture_seed"]))
    cases: list[dict[str, Any]] = []
    for index in range(c["software_fixture_cases"]):
        groups = int(rng.integers(0, 17))
        size = max(groups, int(rng.integers(0, 65)))
        information = rng.integers(-2, groups + 2, size, dtype=np.int64)
        depths = rng.integers(0, 16, size, dtype=np.int64)
        if index % 2 == 0:
            information[:groups] = np.arange(groups, dtype=np.int64)
            group_depths = rng.integers(0, 16, groups, dtype=np.int64)
            valid = (information >= 0) & (information < groups)
            depths[valid] = group_depths[information[valid]]
        cases.append(
            dict(
                kind="generated",
                information=information.tolist(),
                depths=depths.tolist(),
                groups=groups,
            )
        )
    edge_cases = [
        ([], [], 0),
        ([], [], 1),
        ([0], [3], 2),
        ([0, 0], [3, 5], 1),
        ([0, 0, 1], [-(2**63), -(2**63), 2**63 - 1], 2),
        ([0, 0], [-(2**63), 2**63 - 1], 1),
        ([-(2**63), 0, 2**63 - 1], [7, 3, 8], 1),
        ([0, 0], [2**63 - 1, 2**63 - 1], 1),
    ]
    cases.extend(
        dict(kind="edge", information=a, depths=b, groups=n) for a, b, n in edge_cases
    )
    return cases


def integer_decision(case: dict[str, Any]) -> dict[str, Any]:
    """Independent direct-set predicate versus the candidate, with exact inputs."""
    import numpy as np

    a, b, count = case["information"], case["depths"], case["groups"]
    expected = all(
        len({d for info, d in zip(a, b, strict=True) if info == group}) == 1
        for group in range(count)
    )
    information, depths = np.array(a, dtype=np.int64), np.array(b, dtype=np.int64)
    before = information.tobytes(), depths.tobytes()
    try:
        depth.grouped_depths(information, depths, count)
    except ValueError as error:
        if str(error) != depth.MESSAGE:
            raise
        actual = False
    else:
        actual = True
    if expected is not actual or (information.tobytes(), depths.tobytes()) != before:
        raise ArithmeticError("grouped predicate differs from independent integer sets")
    return dict(**case, expected=expected, actual=actual, inputs_unchanged=True)


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


def software_child(root: Path, output: Path, origin: float) -> int:
    """Formal source-bound constructor proof only, after published six-role checks."""
    saved: dict[str, Any] = dict(
        status="starting",
        execution_root=str(root.resolve()),
        execution_output=str(output.resolve()),
        executable=sys.executable,
        pid=os.getpid(),
        thread=threading.get_ident(),
        scope="GROUPED_DEPTH_SOFTWARE_CONSTRUCTION_NOT_TRAINING_OR_NATIVE",
        admission_evidence=False,
        poker_training_performed=False,
        reference_constructed=False,
        reference_output_used_in_training=False,
        integer_completed=0,
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
        cases = software_cases(c)
        atomic(output / "integer-inputs.json", dict(cases=cases))
        with (output / "integer-results.jsonl").open("x") as stream:
            for case in cases:
                row = integer_decision(case)
                stream.write(canonical(row).decode() + "\n")
                stream.flush()
                saved["integer_completed"] += 1
        fixture = SpotTree.build(load_spot(root / c["proof_spot"]))
        model = CardAbstraction.load(root / c["proof_model"])
        witnesses = {}
        for mode in c["order"]:
            with depth.constructor_scope(
                mode, output / mode, c["maximum_builder_calls_per_child"]
            ):
                for encoding in c["proof_encodings"]:
                    MatrixTree.build(fixture, encoding, model)
            witnesses[mode] = depth.read_constructors(
                output / mode,
                mode,
                c["maximum_builder_calls_per_child"],
                saved["pid"],
                saved["thread"],
            )
        if witnesses["original"] != witnesses["grouped"] or len(
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
            integer_generated=c["software_fixture_cases"],
            integer_edges=len(cases) - c["software_fixture_cases"],
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

    raw = os.environ.get("POKER_GROUPED_COMMAND_STARTED")
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
        raise ArithmeticError("complete qualified grouped-depth child required")
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
        != "GROUPED_DEPTH_SOFTWARE_CONSTRUCTION_NOT_TRAINING_OR_NATIVE"
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
    inputs = json.loads((output / "child/integer-inputs.json").read_text())["cases"]
    results = [
        json.loads(x)
        for x in (output / "child/integer-results.jsonl").read_text().splitlines()
    ]
    if (
        inputs != software_cases(c)
        or len(inputs) != c["software_fixture_cases"] + 8
        or len(results) != len(inputs)
        or child["integer_completed"] != len(inputs)
        or child["integer_generated"] != c["software_fixture_cases"]
        or child["integer_edges"] != 8
    ):
        raise ArithmeticError("complete fixed integer case inventory required")
    for case, row in zip(inputs, results, strict=True):
        if (
            row != integer_decision(case)
            or type(row["actual"]) is not bool
            or type(row["expected"]) is not bool
            or row["inputs_unchanged"] is not True
        ):
            raise ArithmeticError("independent integer proof changed")
    vectors = {
        mode: depth.read_constructors(
            output / "child" / mode,
            mode,
            c["maximum_builder_calls_per_child"],
            child["pid"],
            child["thread"],
        )
        for mode in c["order"]
    }
    if (
        vectors["original"] != vectors["grouped"]
        or len(vectors["original"]) != len(c["proof_encodings"])
        or child["constructor_fingerprints"] != vectors
        or child["successful_constructor_fields_per_arm"] != len(c["proof_encodings"])
    ):
        raise ArithmeticError(
            "all five original/grouped constructor witnesses required"
        )
    if {str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()} != {
        "proof.json",
        *("child/" + n for n in raw_files(output / "child", child)),
    }:
        raise ArithmeticError("software proof outer inventory changed")
    checked(root, current)
    return dict(
        proof=proof, child=child, constructors=vectors, integer_cases=len(inputs)
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
            raise ValueError("unknown grouped-depth arm")
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
            mode, output / "constructors", c["maximum_builder_calls_per_child"]
        ):
            with prior.reader_observer(root, c, output):
                code = original.child(root, "uncached", output / "old", origin)
        if code != 0:
            raise ArithmeticError("original complete audit child failed")
        old = prior.original_result(root, output, c)
        phase_ledgers(output, saved, old, c, root=root)
        constructors = depth.read_constructors(
            output / "constructors",
            mode,
            c["maximum_builder_calls_per_child"],
            saved["pid"],
            saved["thread"],
        )
        if len(constructors) < 184:
            raise ArithmeticError("whole-child constructor coverage missing real reads")
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
        or len(pair["measurements"]) != 2
    ):
        raise ArithmeticError("complete capped grouped-depth pair required")
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
        constructors[mode] = depth.read_constructors(
            folder / "constructors",
            mode,
            c["maximum_builder_calls_per_child"],
            row["pid"],
            row["thread"],
        )
        if (
            not 184 <= len(constructors[mode]) == row["constructor_calls"]
            or row["constructors_sha256"]
            != hashlib.sha256(canonical(constructors[mode])).hexdigest()
        ):
            raise ArithmeticError("whole-child constructor binding/count changed")
        children.append(row)
        originals.append(old)
    if (
        children[0]["pid"] == children[1]["pid"]
        or children[0]["source"] != children[1]["source"]
        or originals[0]["identity"] != originals[1]["identity"]
        or originals[0]["card_cache"] != originals[1]["card_cache"]
        or constructors["original"] != constructors["grouped"]
        or sum(x["summary"]["calls"] for mode in c["order"] for x in ledgers[mode])
        >= c["maximum_selected_calls_pair"]
        or expected
        != {str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()}
        or any(p.is_symlink() for p in output.rglob("*"))
    ):
        raise ArithmeticError(
            "complete equal original/grouped audit/fields/capture required"
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
    rows = []
    cpu = {}
    for mode in ("original", "grouped"):
        outer = json.loads(
            (output / mode / "old/parent-resource-reads.json").read_text()
        )["reads"]
        inner = json.loads((output / mode / "inner-reads.json").read_text())["reads"]
        for i in range(3):
            summary = verified["ledgers"][mode][i]["summary"]
            interval = inner[i]["observation"]["interval"]
            rows.append(
                dict(
                    mode=mode,
                    read=i,
                    scope=outer[i]["scope"],
                    outer=outer[i]["observation"]["interval"],
                    inner=interval,
                    selected=summary,
                    outside_selected_cpu=interval["clocks"]["process_cpu_seconds"]
                    - summary["selected_union_cpu"],
                    exclusive_minus_union_cpu=math.fsum(
                        g["exclusive_selected_cpu"] for g in summary["groups"].values()
                    )
                    - summary["selected_union_cpu"],
                )
            )
        cpu[mode] = math.fsum(
            x["summary"]["groups"]["matrix_build"]["exclusive_selected_cpu"]
            for x in verified["ledgers"][mode]
        )
    original_wall, grouped_wall = [
        x["seconds"] for x in verified["pair"]["measurements"]
    ]
    gates = dict(
        complete_correctness_and_coverage=True,
        lower_complete_command_wall=grouped_wall < original_wall,
        lower_selected_exclusive_matrix_cpu=cpu["grouped"] < cpu["original"],
    )
    return dict(
        scope="ONE_ORDERED_GROUPED_DEPTH_DIAGNOSTIC_NOT_TRAINING_ADMISSION",
        measurements=verified["pair"]["measurements"],
        rows=rows,
        constructor_calls={m: len(v) for m, v in verified["constructors"].items()},
        all_constructor_fingerprints_equal=True,
        original_identity_exact=True,
        matrix_cpu=cpu,
        diagnostic_cost_checks=gates,
        diagnostic_cost_passed=all(gates.values()),
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
        "--child", choices=("original", "grouped"), help=argparse.SUPPRESS
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
            "results/runs/grouped-depth-check/software"
            if args.prove or args.show_proof
            else "results/runs/grouped-depth-check/pair"
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
