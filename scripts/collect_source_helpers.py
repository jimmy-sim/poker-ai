"""One frozen own-publication check, never a learner or full-audit forecast."""

import argparse
import copy
import csv
import json
import os
import re
import sys
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

from card_clock_support import check_record, record, snapshot
from helper_call_accounting import Recorder, hooks
from profile_compact_replay import atomic, canonical, digest, supervise

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/source-helper-trace.json"
CONFIG_SHA = "3945034074484821989d1206d8e8c881115975bbbe460a665bf1f4ada463fba9"
ENTRY = "scripts/collect_source_helpers.py"
FOLDER = "results/source-helper-trace"
EXTRA = (
    ENTRY,
    "scripts/helper_call_accounting.py",
    "configs/helper-call-accounting.json",
)
MARKER = "poker_ai.source_helper_census.ready"


class Census:
    """Count documented CPython launches; retain none of their arguments.

    The installed hook lives until this dedicated child exits. Counting is
    active only inside the selected target. This is not a security boundary,
    a census of Git's children, or coverage of arbitrary native launch APIs.
    """

    def __init__(self, recorder: Recorder) -> None:
        self.recorder = recorder
        self.registered = False
        self.active = False
        self.counts: dict[str, int] = {}
        self.unassigned = 0

    def __call__(self, event: str, arguments: tuple[Any, ...]) -> None:
        if event == MARKER and arguments == (id(self),):
            self.registered = True
        if event != "subprocess.Popen" or not self.active:
            return
        # In particular, never inspect/store Popen arguments, cwd or env.
        if self.recorder.rows and self.recorder.rows[-1]["status"] == "running":
            key = str(self.recorder.rows[-1]["ordinal"])
            self.counts[key] = self.counts.get(key, 0) + 1
        else:
            self.unassigned += 1

    @contextmanager
    def counting(self) -> Iterator[None]:
        if self.active or self.registered:
            raise RuntimeError("one census installation per dedicated child")
        sys.addaudithook(self)
        sys.audit(MARKER, id(self))
        if not self.registered:
            raise ArithmeticError("process-event hook installation was suppressed")
        self.active = True
        try:
            yield
        finally:
            self.active = False

    def saved(self) -> dict[str, Any]:
        return dict(
            registered=self.registered,
            active=self.active,
            events_by_ordinal=dict(self.counts),
            unassigned=self.unassigned,
            audit_arguments_retained=False,
        )


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective publication-helper contract changed")
    c: dict[str, Any] = json.loads((root / CONFIG).read_text())
    for name, expected in c["input_sha256"].items():
        p = root / name
        if (
            p.is_symlink()
            or not p.resolve().is_relative_to(root.resolve())
            or digest(p) != expected
        ):
            raise ArithmeticError("frozen publication input changed")
    return c


def binding(root: Path, *, clean: bool = True) -> tuple[dict[str, Any], dict[str, Any]]:
    """Bind code without invoking the selected publication target."""
    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.validation.five_card import source_provenance

    c = contract(root)
    old = json.loads((root / c["historical_anchor"]).read_text())["source"]["sha256"]
    if len(old) != 390 or any(digest(root / p) != h for p, h in old.items()):
        raise ArithmeticError("historical 390-file scientific source changed")
    current: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=EXTRA)
    )
    current["sha256"].update(old)
    current["fingerprint"] = sha(current["sha256"])
    if len(current["sha256"]) != 394 or (clean and current["dirty"] is not False):
        raise ArithmeticError("publish clean complete collector source first")
    commit_sources(root, current["git_commit"], current["sha256"])
    return c, current


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


def target(root: Path, c: dict[str, Any]) -> dict[str, Any]:
    from compact_cached.publication import publication

    return publication(root, root / c["own"], json.loads((root / c["own"]).read_text()))


def validate_ledger(
    saved: dict[str, Any], events: list[dict[str, Any]], pid: int, commands: list[str]
) -> None:
    rows = saved["rows"]
    n = len(rows)
    expected_summary = dict(
        requests=n,
        recognized=n,
        unsupported=0,
        completed=n,
        retention_errors=0,
        observer_errors=0,
        exclusive_pid_attribution=False,
        collection_scope_not_inferred=True,
    )
    if not n or saved["summary"] != expected_summary or len(events) != 2 * n:
        raise ArithmeticError("complete successful recorded coverage required")
    for i, row in enumerate(rows):
        if (
            type(row["ordinal"]) is not int
            or row["ordinal"] != i
            or row["recognized"] is not True
            or row["status"] != "complete"
            or type(row["returncode"]) is not int
            or row["returncode"] != 0
            or row["category"] not in {"git " + c for c in commands}
            or re.fullmatch("[0-9a-f]{64}", row["argv_sha256"]) is None
        ):
            raise ArithmeticError("helper ordinal/category/status/fingerprint changed")
        check_record(row["observation"])
        if row["before"] != row["observation"]["before"] or row["before"]["pid"] != pid:
            raise ArithmeticError("helper raw start or producer PID changed")
        for field in ("stdout", "stderr"):
            v = row[field]
            if v["kind"] == "none":
                if v != dict(kind="none", encoded_bytes=0, sha256=None):
                    raise ArithmeticError("empty output fingerprint changed")
            elif (
                v["kind"] not in ("bytes", "text_utf8_surrogatepass")
                or type(v["encoded_bytes"]) is not int
                or v["encoded_bytes"] < 0
                or re.fullmatch("[0-9a-f]{64}", v["sha256"]) is None
            ):
                raise ArithmeticError("output fingerprint changed")
        start = copy.deepcopy(row)
        for name in ("returncode", "stdout", "stderr", "observation"):
            del start[name]
        start["status"] = "running"
        if events[2 * i : 2 * i + 2] != [start, row]:
            raise ArithmeticError("streamed helper starts/finals differ from ledger")
    census = dict(
        registered=True,
        active=False,
        events_by_ordinal={str(i): 1 for i in range(n)},
        unassigned=0,
        audit_arguments_retained=False,
    )
    if saved["census"] != census:
        raise ArithmeticError(
            "process launches bypassed or differed from recorded requests"
        )


def observe(
    root: Path, c: dict[str, Any], output: Path, call: Callable[[], dict[str, Any]]
) -> dict[str, Any]:
    with (output / "events.jsonl").open("x") as stream:

        def emit(row: dict[str, Any]) -> None:
            stream.write(canonical(row).decode() + "\n")
            stream.flush()

        recorder = Recorder(root, tuple(c["commands"]), emit=emit)
        census = Census(recorder)
        try:
            with hooks(recorder), census.counting():
                result = call()
        finally:
            ledger = dict(
                rows=recorder.rows, summary=recorder.summary(), census=census.saved()
            )
            atomic(output / "ledger.json", ledger)
        events = [
            json.loads(line)
            for line in (output / "events.jsonl").read_text().splitlines()
        ]
        validate_ledger(ledger, events, os.getpid(), c["commands"])
        return result


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

        if (
            sys.version.split()[0] != c["runtime"]["python"]
            or numpy.__version__ != c["runtime"]["numpy"]
        ):
            raise ArithmeticError("original qualified runtime required")
        qualification = digest(root / FOLDER / "checks.json")
        saved.update(
            source=source, config_sha256=CONFIG_SHA, qualification_sha256=qualification
        )
        atomic(output / "child.json", saved)
        before = snapshot()
        saved["target_before"] = before

        def call() -> dict[str, Any]:
            return target(root, c)

        result = observe(root, c, output, call) if mode == "observed" else call()
        saved["target_observation"] = record(before, snapshot())
        after_c, after = binding(root, clean=False)
        if (
            c != after_c
            or source["sha256"] != after["sha256"]
            or qualification != digest(root / FOLDER / "checks.json")
        ):
            raise ArithmeticError("collector source or publication inputs changed")
        validate_witness(result, c, source)
        saved.update(
            status="complete", witness=result, seconds=time.perf_counter() - origin
        )
        if mode == "observed":
            saved["ledger_sha256"] = digest(output / "ledger.json")
            saved["events_sha256"] = digest(output / "events.jsonl")
        atomic(output / "child.json", saved)
        return 0
    except BaseException as error:
        saved.update(status="failed_retained", failure_kind=type(error).__name__)
        atomic(output / "child.json", saved)
        return 130 if isinstance(error, KeyboardInterrupt) else 1


def validate_witness(
    witness: dict[str, Any], c: dict[str, Any], source: dict[str, Any]
) -> None:
    expected = {
        p: h for p, h in c["input_sha256"].items() if p != c["historical_anchor"]
    }
    if (
        witness["published_input_sha256"] != expected
        or witness["own_sha256"] != expected[c["own"]]
        or witness["source_sha256"] != c["original_source_fingerprint"]
        or witness["own_commit"] != source["git_commit"]
    ):
        raise ArithmeticError("original publication witness/input inventory changed")


def verify_pair(root: Path, output: Path) -> dict[str, Any]:
    c = contract(root)
    _, current = binding(root, clean=False)
    pair = json.loads((output / "pair.json").read_text())
    if (
        pair["status"] != "complete"
        or not 0 < pair["seconds"] < c["maximum_pair_seconds"]
    ):
        raise ArithmeticError("complete capped pair required; retain partial failures")
    names = {"pair.json"}
    for mode in c["order"]:
        names.update(
            f"{mode}/{p}" for p in ("child.json", "measurement.json", "command.log")
        )
    names.update(("observed/ledger.json", "observed/events.jsonl"))
    actual = {str(p.relative_to(output)) for p in output.rglob("*") if p.is_file()}
    if actual != names:
        raise ArithmeticError("complete fixed raw file inventory required")
    children = []
    for mode, measurement in zip(c["order"], pair["measurements"], strict=True):
        folder = output / mode
        if (
            measurement != json.loads((folder / "measurement.json").read_text())
            or measurement["returncode"] != 0
            or measurement["interrupted"] is not None
            or not 0 < measurement["seconds"] < c["maximum_child_seconds"]
            or measurement["child_sha256"] != digest(folder / "child.json")
        ):
            raise ArithmeticError("complete child/raw measurement binding changed")
        row = json.loads((folder / "child.json").read_text())
        execution_root = Path(row["execution_root"])
        execution_output = Path(row["execution_output"])
        expected_command = [
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
            row["status"] != "complete"
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
        raise ArithmeticError("original publication returns/source must match exactly")
    if children[0]["pid"] == children[1]["pid"]:
        raise ArithmeticError("separate supervised children required")
    from poker_ai.postflop.compact_full_artifacts import commit_sources

    commit_sources(
        root, children[0]["source"]["git_commit"], children[0]["source"]["sha256"]
    )
    checked(root, children[0]["source"])
    observed = output / "observed"
    if (
        digest(observed / "ledger.json") != children[1]["ledger_sha256"]
        or digest(observed / "events.jsonl") != children[1]["events_sha256"]
    ):
        raise ArithmeticError("raw helper ledger/event hash changed")
    ledger = json.loads((observed / "ledger.json").read_text())
    events = [
        json.loads(line)
        for line in (observed / "events.jsonl").read_text().splitlines()
    ]
    validate_ledger(ledger, events, children[1]["pid"], c["commands"])
    return dict(pair=pair, children=children, ledger=ledger)


def pair(root: Path, output: Path) -> int:
    started = time.perf_counter()
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
        for mode in c["order"]:
            cap = min(
                c["maximum_child_seconds"],
                started + c["maximum_pair_seconds"] - time.perf_counter(),
            )
            if cap <= 0:
                raise TimeoutError("shared diagnostic cap")
            m = supervise(
                [
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
    summary = dict(
        scope="ONE_PUBLICATION_CHECK_ONLY_NOT_FULL_AUDIT_OR_PER_PID_CPU",
        groups=sorted(groups.values(), key=lambda v: v["category"]),
        original_witness_exact=True,
        helpers=len(checked_pair["ledger"]["rows"]),
        complete_children=checked_pair["pair"]["measurements"],
        target_intervals=[r["target_observation"] for r in checked_pair["children"]],
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
            "Exact publication witness; one saved pair, "
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
