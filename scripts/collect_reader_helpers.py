"""One unchanged complete own reader, with transparent helper accounting."""

import argparse
import csv
import gzip
import hashlib
import json
import os
import re
import sys
import time
from collections import Counter
from collections.abc import Callable
from pathlib import Path
from typing import Any

from card_clock_support import check_record, record, snapshot
from collect_source_helpers import Census, validate_ledger
from helper_call_accounting import Recorder, hooks
from profile_compact_replay import atomic, canonical, digest, supervise

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/reader-helper-trace.json"
CONFIG_SHA = "0de2cf79f5f6849d50ca41ace1e878bdacb08e642a463c23de295f7642d8a489"
ENTRY = "scripts/collect_reader_helpers.py"
FOLDER = "results/reader-helper-trace"


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective complete-reader helper contract changed")
    c: dict[str, Any] = json.loads((root / CONFIG).read_text())
    for name, expected in c["input_sha256"].items():
        p = root / name
        if (
            p.is_symlink()
            or not p.resolve().is_relative_to(root.resolve())
            or digest(p) != expected
        ):
            raise ArithmeticError("frozen reader input changed")
    return c


def binding(root: Path, *, clean: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    from collect_source_helpers import binding as prior_binding

    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.validation.five_card import source_provenance

    c = contract(root)
    _, prior = prior_binding(root, clean=clean)
    anchor = json.loads((root / c["historical_anchor"]).read_text())["source"]["sha256"]
    if len(anchor) != c["historical_source_count"] or prior["sha256"] != anchor:
        raise ArithmeticError("historical 394-file source changed")
    current: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=(ENTRY,))
    )
    current["sha256"].update(anchor)
    current["fingerprint"] = sha(current["sha256"])
    if len(current["sha256"]) != c["effective_source_count"] or (
        clean and current["dirty"] is not False
    ):
        raise ArithmeticError("publish clean complete reader collector source first")
    commit_sources(root, current["git_commit"], current["sha256"])
    return c, current


def control(c: dict[str, Any]) -> dict[str, Any]:
    from trace_card_audit import control as original_control

    return original_control(c)


def target(root: Path, c: dict[str, Any], origin: float) -> dict[str, Any]:
    from compact_cached.cache import cached
    from compact_cached.cli import read

    from poker_ai.postflop.river_study import Deadline

    deadline = Deadline(c["maximum_child_seconds"])
    deadline.started = origin
    actual: list[dict[str, Any]] = []
    with cached(root) as cache:
        own = read(root, root / c["own"], deadline, observed=actual)
    if len(actual) != 1:
        raise ArithmeticError("one actual complete mathematical replay required")
    deadline.check()
    return dict(
        own_sha256=digest(root / c["own"]),
        complete_own_sha256=hashlib.sha256(canonical(own)).hexdigest(),
        source_sha256=own["source_sha256"],
        reader_scope=own["scope"],
        computed_replay=actual[0],
        validation_cache=cache.summary(),
    )


def validate_witness(
    witness: dict[str, Any], c: dict[str, Any], source: dict[str, Any]
) -> None:
    from compact_cached.cache import check_counters

    if set(witness) != {
        "own_sha256",
        "complete_own_sha256",
        "source_sha256",
        "reader_scope",
        "computed_replay",
        "validation_cache",
    } or (
        witness["own_sha256"] != c["input_sha256"][c["own"]]
        or witness["complete_own_sha256"] != c["original_own_canonical_sha256"]
        or witness["source_sha256"] != c["expected_source_sha256"]
        or witness["reader_scope"] != c["reader_scope"]
        or canonical(witness["computed_replay"]) != canonical(c["expected_replay"])
    ):
        raise ArithmeticError(
            "complete original reader return or computed replay changed"
        )
    check_counters(witness["validation_cache"])
    if witness["validation_cache"]["requests"] <= 0:
        raise ArithmeticError("actual enabled validation cache required")


def compressed(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as stream:
            stream.write(canonical(value) + b"\n")
    temporary.replace(path)


def load_compressed(path: Path) -> Any:
    with gzip.open(path, "rb") as stream:
        return json.load(stream)


def observe(
    root: Path, c: dict[str, Any], output: Path, call: Callable[[], dict[str, Any]]
) -> dict[str, Any]:
    with (output / "events.jsonl.gz").open("xb") as raw:
        with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as stream:

            def emit(row: dict[str, Any]) -> None:
                stream.write(canonical(row) + b"\n")
                stream.flush()
                raw.flush()

            recorder = Recorder(root, tuple(c["commands"]), emit=emit)
            census = Census(recorder)
            try:
                with hooks(recorder), census.counting():
                    result = call()
            finally:
                ledger = dict(
                    rows=recorder.rows,
                    summary=recorder.summary(),
                    census=census.saved(),
                )
                compressed(output / "ledger.json.gz", ledger)
    with gzip.open(output / "events.jsonl.gz", "rt") as events_stream:
        events = [json.loads(line) for line in events_stream]
    validate_ledger(ledger, events, os.getpid(), c["commands"])
    return result


def checked(root: Path, source: dict[str, Any]) -> None:
    from compact_cached.admission import published
    from trace_card_audit import actual_host_runtime

    from poker_ai.evaluation.diagnostic_receipts import checks

    p = root / FOLDER / "checks.json"
    checks(root, p, source)
    published(root, p)
    for row in json.loads(p.read_text())["checks"]:
        name = root / row["log"]["file"]
        published(root, name)
        log = name.read_text(encoding="utf-8-sig")
        python, numpy = (
            ("3.11.17", "2.4.6") if row["minor"] == "311" else ("3.12.15", "2.5.4")
        )
        if row["numpy"] != numpy:
            raise ArithmeticError("qualified NumPy version changed")
        if row["role"] == "hosted":
            actual_host_runtime(log, python, numpy)
        elif set(re.findall(r"ACTUAL_PYTHON=([0-9]+\.[0-9]+\.[0-9]+)", log)) != {
            python
        } or set(re.findall(r"ACTUAL_NUMPY=([0-9]+\.[0-9]+\.[0-9]+)", log)) != {numpy}:
            raise ArithmeticError("actual local runtime markers required")


def child(root: Path, mode: str, output: Path, origin: float) -> int:
    saved: dict[str, Any] = dict(
        status="starting",
        mode=mode,
        pid=os.getpid(),
        execution_root=str(root.resolve()),
        execution_output=str(output.resolve()),
        executable=sys.executable,
        poker_training_performed=False,
        reference_constructed=False,
        admission_evidence=False,
    )
    atomic(output / "child.json", saved)
    try:
        if mode not in ("control", "observed"):
            raise ValueError("unknown observation mode")
        c, source = binding(root)
        checked(root, source)
        import numpy

        from poker_ai.reproducibility import runtime_environment

        if (
            sys.version.split()[0] != c["runtime"]["python"]
            or numpy.__version__ != c["runtime"]["numpy"]
        ):
            raise ArithmeticError("original qualified runtime required")
        qualification = digest(root / FOLDER / "checks.json")
        saved["environment"] = runtime_environment()
        saved["idle_control"] = control(c)
        saved.update(
            source=source, config_sha256=CONFIG_SHA, qualification_sha256=qualification
        )
        atomic(output / "child.json", saved)
        before = snapshot()
        saved["target_before"] = before
        atomic(output / "child.json", saved)

        def call() -> dict[str, Any]:
            return target(root, c, origin)

        result = observe(root, c, output, call) if mode == "observed" else call()
        saved["target_observation"] = record(before, snapshot())
        after_c, after = binding(root, clean=False)
        if (
            c != after_c
            or source["sha256"] != after["sha256"]
            or qualification != digest(root / FOLDER / "checks.json")
        ):
            raise ArithmeticError("collector source or reader inputs changed")
        validate_witness(result, c, source)
        saved.update(
            status="complete", witness=result, seconds=time.perf_counter() - origin
        )
        if mode == "observed":
            saved["ledger_sha256"] = digest(output / "ledger.json.gz")
            saved["events_sha256"] = digest(output / "events.jsonl.gz")
        atomic(output / "child.json", saved)
        return 0
    except BaseException as error:
        saved.update(status="failed_retained", failure_kind=type(error).__name__)
        atomic(output / "child.json", saved)
        return 130 if isinstance(error, KeyboardInterrupt) else 1


def verify_pair(root: Path, output: Path) -> dict[str, Any]:
    c = contract(root)
    _, current = binding(root, clean=False)
    pair = json.loads((output / "pair.json").read_text())
    if (
        pair["status"] != "complete"
        or pair.get("admission_evidence") is not False
        or type(pair["seconds"]) not in (int, float)
        or not 0 < pair["seconds"] < c["maximum_pair_seconds"]
        or len(pair["measurements"]) != len(c["order"])
    ):
        raise ArithmeticError("complete capped pair required; retain partial failures")
    names = {"pair.json"}
    for mode in c["order"]:
        names.update(
            f"{mode}/{p}" for p in ("child.json", "measurement.json", "command.log")
        )
    names.update(("observed/ledger.json.gz", "observed/events.jsonl.gz"))
    actual = {str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()}
    if actual != names or any(p.is_symlink() for p in output.rglob("*")):
        raise ArithmeticError("complete fixed raw file inventory required")
    children = []
    for mode, measurement in zip(c["order"], pair["measurements"], strict=True):
        folder = output / mode
        if (
            measurement != json.loads((folder / "measurement.json").read_text())
            or measurement["returncode"] != 0
            or measurement["interrupted"] is not None
            or type(measurement["seconds"]) not in (int, float)
            or not 0 < measurement["seconds"] < c["maximum_child_seconds"]
            or measurement["child_sha256"] != digest(folder / "child.json")
            or digest(folder / "command.log") != pair["command_log_sha256"][mode]
        ):
            raise ArithmeticError("complete child/raw measurement binding changed")
        row = json.loads((folder / "child.json").read_text())
        environment = row["environment"]
        if (
            environment["python"] != c["runtime"]["python"]
            or environment["numpy"] != c["runtime"]["numpy"]
            or not {"platform", "cpu", "cpu_query_status", "logical_cpus"}.issubset(
                environment
            )
        ):
            raise ArithmeticError("recorded runtime/hardware context changed")
        execution_root = Path(row["execution_root"])
        execution_output = Path(row["execution_output"])
        expected_command = [
            c["idle_control"]["path"],
            *c["idle_control"]["arguments"],
            row["executable"],
            str(execution_root / ENTRY),
            "--child",
            mode,
            "--output",
            str(execution_output),
        ]
        if measurement[
            "command"
        ] != expected_command or not execution_output.is_relative_to(
            execution_root / "results/runs"
        ):
            raise ArithmeticError("supervised command or original output scope changed")
        if (
            row["idle_control"]
            != dict(
                c["idle_control"],
                requested=True,
                assertion_state_independently_audited=False,
            )
            or row["status"] != "complete"
            or row["mode"] != mode
            or row["config_sha256"] != CONFIG_SHA
            or any(
                row[k] is not False
                for k in (
                    "poker_training_performed",
                    "reference_constructed",
                    "admission_evidence",
                )
            )
        ):
            raise ArithmeticError("collector completion/scope changed")
        if (
            row["source"]["sha256"] != current["sha256"]
            or row["source"]["fingerprint"] != current["fingerprint"]
            or row["qualification_sha256"] != digest(root / FOLDER / "checks.json")
        ):
            raise ArithmeticError("collector source or qualification changed")
        check_record(row["target_observation"])
        if (
            row["target_observation"]["before"]["pid"] != row["pid"]
            or row["target_before"] != row["target_observation"]["before"]
        ):
            raise ArithmeticError("target producer/raw start changed")
        validate_witness(row["witness"], c, row["source"])
        children.append(row)
    if (
        children[0]["source"] != children[1]["source"]
        or children[0]["witness"] != children[1]["witness"]
    ):
        raise ArithmeticError(
            "complete reader returns/replay/cache/source must match exactly"
        )
    if children[0]["pid"] == children[1]["pid"]:
        raise ArithmeticError("separate supervised children required")
    from poker_ai.postflop.compact_full_artifacts import commit_sources

    commit_sources(
        root, children[0]["source"]["git_commit"], children[0]["source"]["sha256"]
    )
    checked(root, children[0]["source"])
    observed = output / "observed"
    if (
        digest(observed / "ledger.json.gz") != children[1]["ledger_sha256"]
        or digest(observed / "events.jsonl.gz") != children[1]["events_sha256"]
    ):
        raise ArithmeticError("raw helper ledger/event hash changed")
    ledger = load_compressed(observed / "ledger.json.gz")
    with gzip.open(observed / "events.jsonl.gz", "rt") as stream:
        events = [json.loads(line) for line in stream]
    validate_ledger(ledger, events, children[1]["pid"], c["commands"])
    return dict(pair=pair, children=children, ledger=ledger)


def pair(root: Path, output: Path) -> int:
    started = time.perf_counter()
    output = output.resolve()
    if (
        output.exists()
        or output.is_symlink()
        or not output.resolve().is_relative_to(root.resolve() / "results/runs")
    ):
        raise ValueError("fresh ignored run destination required")
    output.mkdir(parents=True)
    saved: dict[str, Any] = dict(
        status="running", measurements=[], admission_evidence=False
    )
    atomic(output / "pair.json", saved)
    try:
        c = contract(root)
        control(c)
        for mode in c["order"]:
            cap = min(
                c["maximum_child_seconds"],
                started + c["maximum_pair_seconds"] - time.perf_counter(),
            )
            if cap <= 0:
                raise TimeoutError("shared diagnostic cap")
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
                raise ArithmeticError("child failed; raw partial evidence retained")
        saved.update(status="complete", seconds=time.perf_counter() - started)
        atomic(output / "pair.json", saved)
        verify_pair(root, output)
        saved["seconds"] = time.perf_counter() - started
        if saved["seconds"] >= c["maximum_pair_seconds"]:
            raise TimeoutError("shared cap includes final verification")
        atomic(output / "pair.json", saved)
        return 0
    except BaseException as error:
        saved.update(
            status="failed_retained",
            seconds=time.perf_counter() - started,
            failure_kind=type(error).__name__,
        )
        atomic(output / "pair.json", saved)
        return 130 if isinstance(error, KeyboardInterrupt) else 1


def report(root: Path, output: Path, destination: Path | None = None) -> dict[str, Any]:
    if destination is not None and destination.resolve().is_relative_to(
        output.resolve()
    ):
        raise ValueError("posthoc report must stay outside frozen raw folder")
    checked_pair = verify_pair(root, output)
    groups: dict[str, dict[str, Any]] = {}
    for row in checked_pair["ledger"]["rows"]:
        group = groups.setdefault(
            row["category"],
            dict(
                category=row["category"],
                calls=0,
                interval_wall_seconds=0.0,
                parent_cpu_seconds=0.0,
                reaped_child_user_seconds=0.0,
                reaped_child_system_seconds=0.0,
            ),
        )
        interval = row["observation"]["interval"]
        delta = interval["resources"]["reaped_child_usage"]["delta"]
        group["calls"] += 1
        group["interval_wall_seconds"] += interval["clocks"]["perf_seconds"]
        group["parent_cpu_seconds"] += interval["clocks"]["process_cpu_seconds"]
        group["reaped_child_user_seconds"] += delta["ru_utime"]
        group["reaped_child_system_seconds"] += delta["ru_stime"]
    for category, group in groups.items():
        counts = Counter(
            row["argv_sha256"]
            for row in checked_pair["ledger"]["rows"]
            if row["category"] == category
        )
        group["distinct_argument_fingerprints"] = len(counts)
        group["maximum_argument_repeats"] = max(counts.values())
    summary = dict(
        scope="ONE_COMPLETE_OWN_READER_ONLY_NOT_FULL_NATIVE_AUDIT_OR_PER_PID_CPU",
        groups=sorted(groups.values(), key=lambda v: v["category"]),
        witness=checked_pair["children"][0]["witness"],
        original_witness_exact=True,
        helpers=len(checked_pair["ledger"]["rows"]),
        complete_children=checked_pair["pair"]["measurements"],
        target_intervals=[r["target_observation"] for r in checked_pair["children"]],
        environments=[r["environment"] for r in checked_pair["children"]],
        input_sha256={
            str(p.relative_to(output)): digest(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
        },
    )
    if destination is not None:
        if destination.exists():
            raise FileExistsError("retain earlier posthoc report")
        destination.mkdir(parents=True)
        atomic(destination / "summary.json", summary)
        with (destination / "helpers.csv").open("x", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=list(summary["groups"][0]))
            writer.writeheader()
            writer.writerows(summary["groups"])
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--child", choices=("control", "observed"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--show", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    if args.show or args.report is not None:
        saved = report(ROOT, args.output, args.report)
        print(
            "Exact complete own read/replay/cache; one saved pair, "
            "no full-audit forecast or new training"
        )
        for row in saved["groups"]:
            print(
                f"{row['category']:18} {row['calls']:4} calls; "
                f"observed interval {row['interval_wall_seconds']:.6f}s; "
                f"child user/system {row['reaped_child_user_seconds']:.6f}/"
                f"{row['reaped_child_system_seconds']:.6f}s"
            )
        return 0
    if args.child:
        origin = float(os.environ["POKER_COMPACT_REPLAY_PROFILE_STARTED"])
        return child(ROOT, args.child, args.output, origin)
    return pair(ROOT, args.output)


if __name__ == "__main__":
    raise SystemExit(main())
