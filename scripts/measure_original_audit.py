"""One original-context audit pair; helper boundaries are not exclusive PID CPU."""

import argparse
import gzip
import hashlib
import json
import os
import re
import sys
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import collect_complete_reader_helpers as helpers
import trace_card_audit as original
from card_clock_support import check_record, record, snapshot
from profile_compact_replay import atomic, canonical, digest, supervise

ROOT = Path(__file__).resolve().parents[1]
ENTRY = "scripts/measure_original_audit.py"
CONFIG = "configs/original-audit-helpers.json"
CONFIG_SHA = "4f0f56715482cd81fdbf5ee9a9686f7cac0960304d9b285ea70a77afc0fd979c"
FOLDER = "results/original-audit-helpers"
EXTRA = (
    ENTRY,
    "scripts/reconcile_reader_boundaries.py",
    "configs/reader-boundary-reconciliation.json",
)


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective original-context contract changed")
    c: dict[str, Any] = json.loads((root / CONFIG).read_text())
    for name, sha in c["input_sha256"].items():
        path = root / name
        if (
            path.is_symlink()
            or not path.resolve().is_relative_to(root.resolve())
            or digest(path) != sha
        ):
            raise ArithmeticError("original-context retained input changed")
    return c


def binding(root: Path, *, clean: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.validation.five_card import source_provenance

    c = contract(root)
    _, prior = helpers.binding(root, clean=clean)
    anchor = json.loads((root / c["historical_helper_anchor"]).read_text())["source"][
        "sha256"
    ]
    if prior["sha256"] != anchor or len(anchor) != 398:
        raise ArithmeticError("all prior measurement source must remain unchanged")
    current: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=EXTRA)
    )
    current["sha256"].update(anchor)
    current["fingerprint"] = sha(current["sha256"])
    if len(current["sha256"]) != c["effective_source_count"] or (
        clean and current["dirty"] is not False
    ):
        raise ArithmeticError("publish complete clean original-context source")
    # The reconciliation utility is preserved as source, not executed by this run.
    reconciliation = json.loads(
        (root / "results/reader-boundary-reconciliation/summary.json").read_text()
    )
    if (
        digest(root / EXTRA[1]) != reconciliation["implementation_sha256"]
        or digest(root / EXTRA[2]) != reconciliation["config_sha256"]
    ):
        raise ArithmeticError("PR71 source must remain unchanged")
    commit_sources(root, current["git_commit"], current["sha256"])
    return c, current


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


@contextmanager
def reader_observer(root: Path, c: dict[str, Any], output: Path) -> Iterator[None]:
    """Forward the original read unchanged, inside both frozen outer observers."""
    from compact_cached import cli

    underlying = cli.read
    rows: list[dict[str, Any]] = []

    def observe(*args: Any, **kwargs: Any) -> dict[str, Any]:
        if (
            len(args) != 3
            or set(kwargs) != {"observed"}
            or type(kwargs["observed"]) is not list
            or kwargs["observed"]
        ):
            raise ArithmeticError(
                "unchanged three-argument read and actual witness list required"
            )
        index = len(rows)
        if index >= 3:
            raise ArithmeticError("only the original three reads are allowed")
        folder = output / "reads" / str(index)
        folder.mkdir(parents=True)
        before = snapshot()
        row: dict[str, Any] = dict(index=index, status="running", before=before)
        rows.append(row)
        atomic(output / "inner-reads.json", dict(reads=rows))
        try:
            result = helpers.observe(
                root, c, folder, lambda: underlying(*args, **kwargs)
            )
            if len(kwargs["observed"]) != 1:
                raise ArithmeticError("one actual complete computed summary per read")
            row.update(
                status="complete",
                scope=result["scope"],
                return_sha256=hashlib.sha256(canonical(result)).hexdigest(),
                computed=kwargs["observed"][0],
                observation=record(before, snapshot()),
            )
            atomic(output / "inner-reads.json", dict(reads=rows))
            return result
        except BaseException as error:
            row.update(status="failed_retained", failure_kind=type(error).__name__)
            atomic(output / "inner-reads.json", dict(reads=rows))
            raise

    with patch.object(cli, "read", observe):
        yield


def original_result(root: Path, output: Path, c: dict[str, Any]) -> dict[str, Any]:
    """Validate original telemetry, scalar identity and disabled pure-card reuse."""
    from profile_compact_replay import authenticate_source

    row: dict[str, Any] = json.loads((output / "old/child.json").read_text())
    old = json.loads((root / c["historical_original"]).read_text())
    if (
        row["status"] != "complete_card_clock_trace"
        or row["mode"] != "uncached"
        or row.get("base_admission_rejected") is not True
        or row["identity"] != old["identity"]
        or row["card_cache"] != old["card_cache"]
        or row["source"]["sha256"] != old["source"]["sha256"]
        or len(row["source"]["sha256"]) != 390
    ):
        raise ArithmeticError("complete original audit/card/scalar identity required")
    authenticate_source(root, row["source"])
    check_record(row["body_observation"])
    check_record(row["child_observation"])
    if row["resource_validation"] != original.validate_resources(
        root, output / "old", row["source"], row["identity"]
    ):
        raise ArithmeticError("all original read and worker telemetry required")
    if set(row["raw_files"]) != set(old["raw_files"]):
        raise ArithmeticError("complete original raw inventory required")
    for name, sha in row["raw_files"].items():
        if digest(output / "old" / name) != sha:
            raise ArithmeticError("original numerical or telemetry raw file changed")
    return row


def ledgers(
    output: Path, child: dict[str, Any], old: dict[str, Any], c: dict[str, Any]
) -> list[dict[str, Any]]:
    rows = json.loads((output / "inner-reads.json").read_text())["reads"]
    outer = json.loads((output / "old/parent-resource-reads.json").read_text())["reads"]
    if len(rows) != 3:
        raise ArithmeticError("all three inner reader records required")
    result = []
    for i, row in enumerate(rows):
        check_record(row["observation"])
        if (
            row["index"] != i
            or row["status"] != "complete"
            or row["scope"] != outer[i]["scope"]
            or row["computed"] != old["identity"]["computed_replays"][i]["computed"]
            or row["before"] != row["observation"]["before"]
            or row["before"]["pid"] != child["pid"]
        ):
            raise ArithmeticError("inner read process/scope/computed identity changed")
        # Saving/validation is charged; nested counters need not be identical.
        if not (
            outer[i]["observation"]["before"]["perf_seconds"]
            <= row["before"]["perf_seconds"]
            <= row["observation"]["after"]["perf_seconds"]
            <= outer[i]["observation"]["after"]["perf_seconds"]
        ):
            raise ArithmeticError("inner read must remain within its original boundary")
        folder = output / "reads" / str(i)
        ledger = helpers.load_compressed(folder / "ledger.json.gz")
        with gzip.open(folder / "events.jsonl.gz", "rt") as stream:
            events = [json.loads(line) for line in stream]
        helpers.validate_ledger(ledger, events, child["pid"], c["commands"])
        for helper in ledger["rows"]:
            if not (
                row["before"]["perf_seconds"]
                <= helper["before"]["perf_seconds"]
                <= helper["observation"]["after"]["perf_seconds"]
                <= row["observation"]["after"]["perf_seconds"]
            ):
                raise ArithmeticError("helper outside selected read boundary")
        result.append(ledger)
    return result


def child(root: Path, mode: str, output: Path, origin: float) -> int:
    saved: dict[str, Any] = dict(
        status="starting",
        mode=mode,
        pid=os.getpid(),
        execution_root=str(root.resolve()),
        execution_output=str(output.resolve()),
        executable=sys.executable,
        admission_evidence=False,
        poker_training_performed=False,
        reference_output_used_in_training=False,
    )
    atomic(output / "child.json", saved)
    try:
        if mode not in ("control", "observed"):
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
        (output / "old").mkdir()
        if mode == "observed":
            with reader_observer(root, c, output):
                code = original.child(root, "uncached", output / "old", origin)
        else:
            code = original.child(root, "uncached", output / "old", origin)
        if code != 0:
            raise ArithmeticError("original audit child did not complete")
        old = original_result(root, output, c)
        if mode == "observed":
            ledgers(output, saved, old, c)
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
        if mode == "observed":
            data = ledgers(folder, row, old, c)
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


def report(root: Path, output: Path) -> dict[str, Any]:
    verified = verify_pair(root, output)
    rows = []
    for mode in ("control", "observed"):
        reads = json.loads(
            (output / mode / "old/parent-resource-reads.json").read_text()
        )["reads"]
        for i, read in enumerate(reads):
            interval = read["observation"]["interval"]
            row: dict[str, Any] = dict(
                mode=mode,
                read=i,
                scope=read["scope"],
                outer=interval,
                helper_count=None,
                helper_totals=None,
            )
            if mode == "observed":
                helpers_rows = verified["ledgers"][i]["rows"]
                row["helper_count"] = len(helpers_rows)
                row["helper_totals"] = {
                    k: sum(
                        h["observation"]["interval"]["resources"]["reaped_child_usage"][
                            "delta"
                        ][k]
                        for h in helpers_rows
                    )
                    for k in ("ru_utime", "ru_stime")
                }
                row["inner"] = json.loads(
                    (output / mode / "inner-reads.json").read_text()
                )["reads"][i]["observation"]["interval"]
                row["categories"] = {
                    k: sum(h["category"] == k for h in helpers_rows)
                    for k in sorted({h["category"] for h in helpers_rows})
                }
            rows.append(row)
    return dict(
        scope="ONE_ORDERED_ORIGINAL_AUDIT_PAIR_NOT_CAUSAL_FACTOR_ISOLATION_OR_PERFORMANCE_ADMISSION",
        rows=rows,
        measurements=verified["pair"]["measurements"],
        body_intervals=[
            x["body_observation"]["interval"] for x in verified["originals"]
        ],
        workers=[x["resource_validation"] for x in verified["originals"]],
        original_identity_exact=True,
        input_sha256={
            str(p.relative_to(output)): digest(p)
            for p in sorted(output.rglob("*"))
            if p.is_file()
        },
        poker_training_performed=False,
        long_run_admitted=False,
    )


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--output", type=Path, default=Path("results/runs/original-audit-helpers/pair")
    )
    p.add_argument("--child", choices=("control", "observed"), help=argparse.SUPPRESS)
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


if __name__ == "__main__":
    raise SystemExit(main())
