"""Source-bound exact private-minimum suit factorization; no training admission."""

import argparse
import copy
import hashlib
import json
import os
import re
import sys
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import check_suit_lookup as predecessor
import collect_complete_reader_helpers as helpers
import grouped_depth_support as fields
import profile_reader_loads as prior
import suit_candidates_support as kernel
import suit_lookup_support as lookup
import trace_card_audit as original
from profile_compact_replay import atomic, canonical, digest, supervise

ROOT = Path(__file__).resolve().parents[1]
ENTRY = "scripts/compare_suit_candidates.py"
SUPPORT = "scripts/suit_candidates_support.py"
CONFIG = "configs/suit-candidates.json"
CONFIG_SHA = "593072acc4d94403378675dc7550131e75373a1f159c5f04a9337edbf007cb09"
FOLDER = "results/suit-candidates"


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective suit-candidate contract changed")
    c: dict[str, Any] = json.loads((root / CONFIG).read_text())
    for name, checksum in c["input_sha256"].items():
        p = root / name
        if (
            p.is_symlink()
            or not p.resolve().is_relative_to(root.resolve())
            or digest(p) != checksum
        ):
            raise ArithmeticError("suit-candidate retained input changed")
    return c


def binding(root: Path, *, clean: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.validation.five_card import source_provenance

    if (
        Path(__file__).resolve() != root.resolve() / ENTRY
        or Path(kernel.__file__).resolve() != root.resolve() / SUPPORT
        or Path(prior.__file__).resolve() != root.resolve() / prior.ENTRY
    ):
        raise ArithmeticError("suit-candidate imports outside stated checkout")
    c = contract(root)
    _, previous = predecessor.binding(root, clean=clean)
    anchor = json.loads((root / c["preserved_source_anchor"]).read_text())["source"][
        "sha256"
    ]
    if len(anchor) != 415 or previous["sha256"] != anchor:
        raise ArithmeticError("preserve all415 prior source files")
    source: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=(ENTRY, SUPPORT))
    )
    source["sha256"].update(anchor)
    source["fingerprint"] = sha(source["sha256"])
    if len(source["sha256"]) != 418 or (clean and source["dirty"] is not False):
        raise ArithmeticError("publish clean418-file suit-candidate source")
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
    return predecessor.phase_ledgers(output, child, old, c, root=root)


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


def software_cases(c: dict[str, Any]) -> list[dict[str, Any]]:
    """Sealed software-only inputs, unrelated to historical trajectory RNG."""
    import itertools

    import numpy as np

    rows = [
        dict(kind="ordered_preflop", hole=list(h), board=[])
        for h in itertools.permutations(range(52), 2)
    ]
    rng = np.random.Generator(np.random.PCG64(c["software_fixture_seed"]))
    for length in c["software_board_lengths"]:
        for _ in range(c["software_cases_per_board"]):
            cards = [int(x) for x in rng.choice(52, 2 + length, replace=False)]
            rows.append(dict(kind="generated", hole=cards[:2], board=cards[2:]))
    if len(rows) != c["software_valid_cases"]:
        raise ArithmeticError("complete sealed card case inventory required")
    return rows


def fixed_arguments(label: str) -> tuple[tuple[Any, ...], dict[str, Any]]:
    catalog: dict[str, tuple[tuple[Any, ...], dict[str, Any]]] = {
        "wrong_hole_empty": (((), ()), {}),
        "wrong_hole_one": (((0,), ()), {}),
        "wrong_hole_three": (((0, 1, 2), ()), {}),
        "wrong_board_one": (((0, 1), (2,)), {}),
        "wrong_board_two": (((0, 1), (2, 3)), {}),
        "wrong_board_six": (((0, 1), (2, 3, 4, 5, 6, 7)), {}),
        "duplicate_hole": (((0, 0), ()), {}),
        "duplicate_board": (((0, 1), (2, 2, 3)), {}),
        "overlap": (((0, 1), (0, 2, 3)), {}),
        "negative_card": (((-1, 1), ()), {}),
        "high_card": (((0, 52), ()), {}),
        "bool_card": (((False, 1), ()), {}),
        "float_card": (((0, 1), (2.0, 3, 4)), {}),
        "valid_lists": (([0, 1], [2, 3, 4]), {}),
        "tuple_list_concat": (((0, 1), [2, 3, 4]), {}),
        "keyword_valid": ((), dict(hole=(0, 1), board=())),
        "unknown_keyword": ((), dict(hole=(0, 1), board=(), extra=True)),
    }
    if label not in catalog:
        raise ArithmeticError("unknown fixed software call")
    return catalog[label]


def card_value(value: Any) -> dict[str, Any]:
    if (
        type(value) is not tuple
        or len(value) != 2
        or any(
            type(x) is not tuple or any(type(card) is not int for card in x)
            for x in value
        )
    ):
        raise ArithmeticError("original builtin tuple-of-integer result required")
    return dict(
        value=[list(x) for x in value], types="tuple(tuple(int),tuple(int))", error=None
    )


def pinned_constructors(root: Path, c: dict[str, Any], vector: list[str]) -> None:
    folder = root / c["constructor_baseline"]
    row = json.loads((folder / "constructor.json").read_text())
    wanted = fields.read_constructors(
        folder,
        "original",
        c["maximum_builder_calls_per_child"],
        row["pid"],
        row["thread"],
    )
    if len(vector) != c["expected_constructors"] or vector != wanted:
        raise ArithmeticError("all184 original constructor field fingerprints required")


def capture_cards(
    output: Path,
    cases: list[dict[str, Any]],
    call: Callable[..., Any],
    saved: dict[str, Any],
    mode: str,
) -> None:
    saved["valid_completed"][mode] = 0
    with (output / (mode + "-cards.jsonl")).open("x") as stream:
        for i, case in enumerate(cases):
            hole, board = tuple(case["hole"]), tuple(case["board"])
            before = (hole, board)
            value = card_value(call(hole, board))
            if (hole, board) != before:
                raise ArithmeticError("software card input mutated")
            stream.write(
                canonical(dict(index=i, **value, inputs_unchanged=True)).decode() + "\n"
            )
            stream.flush()
            saved["valid_completed"][mode] += 1


def fixed_outcome(call: Callable[..., Any], label: str) -> dict[str, Any]:
    args, kwargs = fixed_arguments(label)
    before = copy.deepcopy((args, kwargs))
    try:
        result = card_value(call(*args, **kwargs))
    except (TypeError, ValueError) as error:
        result = dict(
            value=None,
            types=None,
            error=dict(kind=type(error).__name__, message=str(error)),
        )
    if (args, kwargs) != before:
        raise ArithmeticError("fixed software input mutated")
    return result


def software_child(root: Path, output: Path, origin: float) -> int:
    saved: dict[str, Any] = dict(
        status="starting",
        execution_root=str(root.resolve()),
        execution_output=str(output.resolve()),
        executable=sys.executable,
        pid=os.getpid(),
        thread=threading.get_ident(),
        scope="EXACT_SUIT_CANDIDATE_SOFTWARE_NOT_TRAINING_OR_NATIVE",
        admission_evidence=False,
        poker_training_performed=False,
        reference_constructed=False,
        reference_output_used_in_training=False,
        valid_completed={},
        fixed_completed={},
    )
    atomic(output / "child.json", saved)
    try:
        from poker_ai.abstraction import potential
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
        kernel.check_geometry(c["lookup_table_sha256"], c["geometry_sha256"])
        atomic(
            output / "table.json",
            dict(
                rows=kernel.TABLE,
                sha256=lookup.table_sha(),
                entries=c["software_table_entries"],
            ),
        )
        atomic(
            output / "geometry.json",
            dict(
                rows=kernel.GEOMETRY,
                sha256=c["geometry_sha256"],
                slots=c["geometry_slots"],
                valid=c["geometry_valid_ordered_holes"],
                duplicate_sentinels=c["geometry_duplicate_sentinels"],
                tie_counts=c["geometry_tie_counts"],
            ),
        )
        cases = software_cases(c)
        atomic(output / "card-inputs.json", dict(cases=cases))
        fixture = SpotTree.build(load_spot(root / c["proof_spot"]))
        vectors: dict[str, Any] = {}
        fixed: dict[str, Any] = {}
        counters: dict[str, Any] = {}
        owner_before = potential.canonical_cards is kernel.BASE
        if owner_before is not True:
            raise ArithmeticError("unhooked own original baseline required")
        capture_cards(output, cases, kernel.BASE, saved, "original")
        model = CardAbstraction.load(root / c["proof_model"])
        with fields.constructor_scope(
            "original", output / "original", c["maximum_builder_calls_per_child"]
        ):
            for encoding in c["proof_encodings"]:
                MatrixTree.build(fixture, encoding, model)
        vectors["original"] = fields.read_constructors(
            output / "original",
            "original",
            c["maximum_builder_calls_per_child"],
            saved["pid"],
            saved["thread"],
        )
        fixed["original"] = {}
        saved["fixed_completed"]["original"] = 0
        for label in c["software_fixed_calls"]:
            fixed["original"][label] = fixed_outcome(kernel.BASE, label)
            saved["fixed_completed"]["original"] += 1
        owner_after = potential.canonical_cards is kernel.BASE
        if owner_after is not True:
            raise ArithmeticError("own original baseline owner changed")
        atomic(
            output / "original-direct.json",
            dict(
                method="unhooked own original canonicalization",
                valid_calls=saved["valid_completed"]["original"],
                fixed_calls=saved["fixed_completed"]["original"],
                constructor_calls=len(vectors["original"]),
                owner_before_unchanged=owner_before,
                owner_after_unchanged=owner_after,
                inputs_unchanged=True,
            ),
        )
        for mode in c["order"]:
            saved["fixed_completed"][mode] = 0
            model = CardAbstraction.load(root / c["proof_model"])
            with kernel.kernel_scope(
                mode,
                output / (mode + "-kernel.json"),
                c["maximum_kernel_requests"],
                c["lookup_table_sha256"],
                c["geometry_sha256"],
            ):
                capture_cards(output, cases, potential.canonical_cards, saved, mode)
                with fields.constructor_scope(
                    "original", output / mode, c["maximum_builder_calls_per_child"]
                ):
                    for encoding in c["proof_encodings"]:
                        MatrixTree.build(fixture, encoding, model)
            vectors[mode] = fields.read_constructors(
                output / mode,
                "original",
                c["maximum_builder_calls_per_child"],
                saved["pid"],
                saved["thread"],
            )
            counters[mode] = kernel.read_kernel(
                output / (mode + "-kernel.json"),
                mode,
                c["maximum_kernel_requests"],
                c["lookup_table_sha256"],
                c["geometry_sha256"],
                saved["pid"],
                saved["thread"],
                require_reduced=mode == "reduced",
            )
            fixed[mode] = {}
            for label in c["software_fixed_calls"]:
                args, kwargs = fixed_arguments(label)
                before = copy.deepcopy((args, kwargs))
                try:
                    with kernel.kernel_scope(
                        mode,
                        output / "fixed" / (mode + "-" + label + ".json"),
                        c["maximum_kernel_requests"],
                        c["lookup_table_sha256"],
                        c["geometry_sha256"],
                    ):
                        result = card_value(potential.canonical_cards(*args, **kwargs))
                except (TypeError, ValueError) as error:
                    result = dict(
                        value=None,
                        types=None,
                        error=dict(kind=type(error).__name__, message=str(error)),
                    )
                if (args, kwargs) != before:
                    raise ArithmeticError("fixed variant input mutated")
                fixed[mode][label] = result
                saved["fixed_completed"][mode] += 1
        if (
            any(
                (output / (mode + "-cards.jsonl")).read_bytes()
                != (output / "original-cards.jsonl").read_bytes()
                or vectors[mode] != vectors["original"]
                or fixed[mode] != fixed["original"]
                for mode in c["order"]
            )
            or len(vectors["original"]) != 5
        ):
            raise ArithmeticError("original/all/reduced software outputs differ")
        atomic(output / "fixed-results.json", fixed)
        validate_fixed(output, c, saved["pid"], saved["thread"])
        after_c, after = binding(root, clean=False)
        if (
            c != after_c
            or source["sha256"] != after["sha256"]
            or saved["qualification_sha256"] != digest(root / FOLDER / "checks.json")
        ):
            raise ArithmeticError("software source/qualification changed")
        saved.update(
            status="complete",
            seconds=time.perf_counter() - origin,
            constructor_fingerprints=vectors,
            kernel_counters=counters,
            successful_constructor_fields_per_implementation=5,
            table_entries=1248,
            geometry_slots=2704,
            fixed_inputs_unchanged=True,
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


def validate_fixed(
    output: Path, c: dict[str, Any], pid: int, thread: int
) -> dict[str, Any]:
    data: dict[str, Any] = json.loads((output / "fixed-results.json").read_text())
    if (
        set(data) != set(c["software_order"])
        or any(data[mode] != data["original"] for mode in c["order"])
        or set(data["original"]) != set(c["software_fixed_calls"])
    ):
        raise ArithmeticError("complete original/all/reduced fixed inventory required")
    for label in c["software_fixed_calls"]:
        result = data["original"][label]
        if set(result) != {"value", "types", "error"}:
            raise ArithmeticError("fixed software outcome schema changed")
        expected_error = label not in ("valid_lists", "keyword_valid")
        if expected_error:
            if (
                result["value"] is not None
                or result["types"] is not None
                or type(result["error"]) is not dict
                or set(result["error"]) != {"kind", "message"}
                or result["error"]["kind"] not in ("TypeError", "ValueError")
                or type(result["error"]["message"]) is not str
                or not result["error"]["message"]
            ):
                raise ArithmeticError(
                    "precise expected original software exception missing"
                )
        else:
            validate_card_record(dict(index=0, **result, inputs_unchanged=True), 0)
        for mode in c["order"]:
            row = json.loads(
                (output / "fixed" / (mode + "-" + label + ".json")).read_text()
            )
            args, kwargs = fixed_arguments(label)
            eligible = (
                not kwargs
                and len(args) == 2
                and kernel.primitive(args[0])
                and kernel.primitive(args[1])
            )
            wanted = dict(
                status="failed_retained" if expected_error else "complete",
                mode=mode,
                maximum=c["maximum_kernel_requests"],
                pid=pid,
                thread=thread,
                requests=1,
                original_evaluations=int(not eligible),
                all_evaluations=int(mode == "all" and eligible),
                reduced_evaluations=int(mode == "reduced" and eligible),
                fallbacks=int(not eligible),
                errors=int(expected_error),
                restored=True,
                aliases_remaining=0,
                table_sha256=c["lookup_table_sha256"],
                geometry_sha256=c["geometry_sha256"],
                scope=kernel.SCOPE,
            )
            integer_fields = (
                "maximum",
                "pid",
                "thread",
                "requests",
                "original_evaluations",
                "all_evaluations",
                "reduced_evaluations",
                "fallbacks",
                "errors",
                "aliases_remaining",
            )
            if (
                row != wanted
                or row["restored"] is not True
                or any(type(row[k]) is not int for k in integer_fields)
            ):
                raise ArithmeticError(
                    "precise typed expected fixed kernel receipt required"
                )
    return data


def validate_card_record(
    row: dict[str, Any], index: int, case: dict[str, Any] | None = None
) -> None:
    if (
        set(row) != {"index", "value", "types", "error", "inputs_unchanged"}
        or type(row["index"]) is not int
        or row["index"] != index
        or row["types"] != "tuple(tuple(int),tuple(int))"
        or row["error"] is not None
        or row["inputs_unchanged"] is not True
        or type(row["value"]) is not list
        or len(row["value"]) != 2
        or any(
            type(x) is not list
            or any(type(card) is not int or not 0 <= card < 52 for card in x)
            for x in row["value"]
        )
    ):
        raise ArithmeticError("complete typed canonical-card output required")

    value = row["value"]
    if (
        len(value[0]) != 2
        or len(value[1]) not in (0, 3, 4, 5)
        or len(set(value[0] + value[1])) != len(value[0]) + len(value[1])
        or any(x != sorted(x) for x in value)
    ):
        raise ArithmeticError("valid sorted canonical card geometry required")
    if case is not None and (
        len(value[1]) != len(case["board"])
        or sorted(c // 4 for c in value[0]) != sorted(c // 4 for c in case["hole"])
        or sorted(c // 4 for c in value[1]) != sorted(c // 4 for c in case["board"])
    ):
        raise ArithmeticError("canonicalization changed known ranks or board length")


def registered_origin() -> float:
    """The published operator starts this clock before launching Python."""
    import math

    raw = os.environ.get("POKER_SUIT_CANDIDATES_COMMAND_STARTED")
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
        raise ArithmeticError("complete qualified suit-candidate child required")
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
        or child["scope"] != "EXACT_SUIT_CANDIDATE_SOFTWARE_NOT_TRAINING_OR_NATIVE"
    ):
        raise ArithmeticError("complete bounded own-only factorization proof required")
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
    kernel.check_geometry(c["lookup_table_sha256"], c["geometry_sha256"])
    table = json.loads((output / "child/table.json").read_text())
    geometry = json.loads((output / "child/geometry.json").read_text())
    if (
        canonical(table)
        != canonical(
            dict(
                rows=[list(x) for x in kernel.TABLE],
                sha256=c["lookup_table_sha256"],
                entries=1248,
            )
        )
        or child["table_entries"] != 1248
        or canonical(geometry)
        != canonical(
            dict(
                rows=kernel.GEOMETRY,
                sha256=c["geometry_sha256"],
                slots=2704,
                valid=2652,
                duplicate_sentinels=52,
                tie_counts=c["geometry_tie_counts"],
            )
        )
        or child["geometry_slots"] != 2704
    ):
        raise ArithmeticError("all fixed translation/ordered-hole slots required")
    cases = json.loads((output / "child/card-inputs.json").read_text())["cases"]
    if canonical(cases) != canonical(software_cases(c)) or len(cases) != 5724:
        raise ArithmeticError("all5724 original/variant software cases required")
    direct = json.loads((output / "child/original-direct.json").read_text())
    wanted = dict(
        method="unhooked own original canonicalization",
        valid_calls=5724,
        fixed_calls=17,
        constructor_calls=5,
        owner_before_unchanged=True,
        owner_after_unchanged=True,
        inputs_unchanged=True,
    )
    if (
        direct != wanted
        or any(
            type(direct[k]) is not int
            for k in ("valid_calls", "fixed_calls", "constructor_calls")
        )
        or any(
            direct[k] is not True
            for k in (
                "owner_before_unchanged",
                "owner_after_unchanged",
                "inputs_unchanged",
            )
        )
    ):
        raise ArithmeticError("typed unhooked original baseline inventory required")
    vectors, records, counters = {}, {}, {}
    for mode in c["software_order"]:
        vectors[mode] = fields.read_constructors(
            output / "child" / mode,
            "original",
            c["maximum_builder_calls_per_child"],
            child["pid"],
            child["thread"],
        )
        records[mode] = [
            json.loads(x)
            for x in (output / "child" / (mode + "-cards.jsonl"))
            .read_text()
            .splitlines()
        ]
        if (
            len(records[mode]) != 5724
            or type(child["valid_completed"][mode]) is not int
            or child["valid_completed"][mode] != 5724
            or type(child["fixed_completed"][mode]) is not int
            or child["fixed_completed"][mode] != 17
        ):
            raise ArithmeticError("complete typed software inventory required")
        for i, row in enumerate(records[mode]):
            validate_card_record(row, i, cases[i])
        if mode in c["order"]:
            counters[mode] = kernel.read_kernel(
                output / "child" / (mode + "-kernel.json"),
                mode,
                c["maximum_kernel_requests"],
                c["lookup_table_sha256"],
                c["geometry_sha256"],
                child["pid"],
                child["thread"],
                require_reduced=mode == "reduced",
            )
            if (
                counters[mode]["requests"] < 5724
                or counters[mode][
                    "all_evaluations" if mode == "all" else "reduced_evaluations"
                ]
                < 5724
            ):
                raise ArithmeticError("complete variant software coverage required")
    fixed = validate_fixed(output / "child", c, child["pid"], child["thread"])
    if (
        any(
            vectors[mode] != vectors["original"] or records[mode] != records["original"]
            for mode in c["order"]
        )
        or len(vectors["original"]) != 5
        or child["constructor_fingerprints"] != vectors
        or child["kernel_counters"] != counters
        or child["successful_constructor_fields_per_implementation"] != 5
        or child["fixed_inputs_unchanged"] is not True
    ):
        raise ArithmeticError("all original/all/reduced software outputs required")
    if {str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()} != {
        "proof.json",
        *("child/" + n for n in raw_files(output / "child", child)),
    }:
        raise ArithmeticError("software outer inventory changed")
    checked(root, current)
    return dict(
        proof=proof,
        child=child,
        constructors=vectors,
        kernels=counters,
        valid_cases=5724,
        table_entries=1248,
        geometry_slots=2704,
        fixed=fixed,
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
            raise ValueError("unknown suit-candidate arm")
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
        with kernel.kernel_scope(
            mode,
            output / "kernel.json",
            c["maximum_kernel_requests"],
            c["lookup_table_sha256"],
            c["geometry_sha256"],
        ):
            with fields.constructor_scope(
                "original",
                output / "constructors",
                c["maximum_builder_calls_per_child"],
            ):
                with prior.reader_observer(root, c, output):
                    code = original.child(root, "uncached", output / "old", origin)
        if code != 0:
            raise ArithmeticError("original complete audit child failed")
        old = prior.original_result(root, output, c)
        phase_ledgers(output, saved, old, c, root=root)
        constructors = fields.read_constructors(
            output / "constructors",
            "original",
            c["maximum_builder_calls_per_child"],
            saved["pid"],
            saved["thread"],
        )
        pinned_constructors(root, c, constructors)
        counter = kernel.read_kernel(
            output / "kernel.json",
            mode,
            c["maximum_kernel_requests"],
            c["lookup_table_sha256"],
            c["geometry_sha256"],
            saved["pid"],
            saved["thread"],
            require_reduced=mode == "reduced",
        )
        if mode == "all" and counter["all_evaluations"] == 0:
            raise ArithmeticError("positive all-candidate control coverage required")
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
            kernel_requests=counter["requests"],
            kernel_sha256=digest(output / "kernel.json"),
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
        raise ArithmeticError("complete capped suit-candidate pair required")
    children, originals, ledgers, constructors, kernels = [], [], {}, {}, {}
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
        constructors[mode] = fields.read_constructors(
            folder / "constructors",
            "original",
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
        pinned_constructors(root, c, constructors[mode])
        kernels[mode] = kernel.read_kernel(
            folder / "kernel.json",
            mode,
            c["maximum_kernel_requests"],
            c["lookup_table_sha256"],
            c["geometry_sha256"],
            row["pid"],
            row["thread"],
            require_reduced=mode == "reduced",
        )
        if mode == "all" and kernels[mode]["all_evaluations"] == 0:
            raise ArithmeticError("all-candidate control was not exercised")
        if row["kernel_requests"] != kernels[mode]["requests"] or row[
            "kernel_sha256"
        ] != digest(folder / "kernel.json"):
            raise ArithmeticError("kernel request receipt binding changed")
        children.append(row)
        originals.append(old)
    if (
        children[0]["pid"] == children[1]["pid"]
        or children[0]["source"] != children[1]["source"]
        or originals[0]["identity"] != originals[1]["identity"]
        or originals[0]["card_cache"] != originals[1]["card_cache"]
        or constructors["all"] != constructors["reduced"]
        or kernels["all"]["requests"] != kernels["reduced"]["requests"]
        or kernels["all"]["fallbacks"] != kernels["reduced"]["fallbacks"]
        or sum(x["summary"]["calls"] for mode in c["order"] for x in ledgers[mode])
        != c["expected_combined_calls"]
        or c["expected_combined_calls"] >= c["maximum_selected_calls_pair"]
        or expected
        != {str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()}
        or any(p.is_symlink() for p in output.rglob("*"))
    ):
        raise ArithmeticError(
            "complete equal all/reduced audit/fields/capture required"
        )
    checked(root, current)
    published_proof(root)
    return dict(
        pair=pair,
        children=children,
        originals=originals,
        ledgers=ledgers,
        constructors=constructors,
        kernels=kernels,
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
    for mode in ("all", "reduced"):
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
    all_wall, reduced_wall = [x["seconds"] for x in verified["pair"]["measurements"]]
    gates = dict(
        complete_correctness_and_coverage=True,
        lower_complete_command_wall=reduced_wall < all_wall,
        lower_selected_exclusive_matrix_cpu=cpu["reduced"] < cpu["all"],
    )
    return dict(
        scope="ONE_ORDERED_ALL_REDUCED_SUIT_DIAGNOSTIC_NOT_TRAINING_ADMISSION",
        measurements=verified["pair"]["measurements"],
        rows=rows,
        constructor_calls={m: len(v) for m, v in verified["constructors"].items()},
        all_constructor_fingerprints_equal=True,
        original_identity_exact=True,
        kernel_counters=verified["kernels"],
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
    parser.add_argument("--child", choices=("all", "reduced"), help=argparse.SUPPRESS)
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
            "results/runs/suit-candidates/software"
            if args.prove or args.show_proof
            else "results/runs/suit-candidates/pair"
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
