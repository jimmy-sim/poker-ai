"""Source-bound complete audit resource trace; both timing directions descriptive."""

import argparse
import hashlib
import json
import os
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

import check_card_cache as historical
import profile_cached_native_wall as base
from card_cache_support import check_summary, hooks
from card_clock_support import check_record, record, snapshot, worker
from profile_compact_replay import atomic, canonical, digest, supervise

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/card-audit-clock-trace.json"
CONFIG_SHA = "9c18736b94d823e58b1bf6ad1c08b0e6d75bc760c038dde90aee31dba248b149"
ENTRY = "scripts/trace_card_audit.py"
SUPPORT = "scripts/card_clock_support.py"
FOLDER = "results/card-audit-clock-trace"


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective card-cache contract changed")
    result: dict[str, Any] = json.loads((root / CONFIG).read_text())
    return result


def preflight(
    root: Path, *, clean: bool = True
) -> tuple[dict[str, Any], dict[str, Any]]:
    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.validation.five_card import source_provenance

    c = contract(root)
    _, original_source = historical.preflight(root, clean=clean)
    if original_source["fingerprint"] != c["historical_source"]:
        raise ArithmeticError("frozen complete historical source changed")
    failure = json.loads((root / c["failure_pair"]).read_text())
    if (
        digest(root / c["failure_pair"]) != c["failure_pair_sha256"]
        or failure.get("narrow_wall_time_pass") is not False
    ):
        raise ArithmeticError("original registered timing failure must stay unchanged")
    current: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=(ENTRY, SUPPORT))
    )
    current["sha256"].update(original_source["sha256"])
    current["fingerprint"] = sha(current["sha256"])
    commit_sources(root, current["git_commit"], current["sha256"])
    return c, current


def checked(root: Path, current: dict[str, Any]) -> None:
    from compact_cached.admission import published

    from poker_ai.evaluation.diagnostic_receipts import checks

    path = root / FOLDER / "checks.json"
    receipt = checks(root, path, current)
    published(root, path)
    saved = json.loads((root / receipt["file"]).read_text())
    for row in saved["checks"]:
        published(root, root / row["log"]["file"])
        if row["role"] == "hosted":
            log = (root / row["log"]["file"]).read_text(encoding="utf-8-sig")
            actual_host_runtime(log, row["python"], row["numpy"])


def actual_host_runtime(log: str, python: str, numpy: str) -> None:
    guards = set(re.findall(r"ACTUAL_PYTHON=([0-9]+\.[0-9]+\.[0-9]+)", log))
    uv = set(re.findall(r"Using CPython ([0-9]+\.[0-9]+\.[0-9]+)", log))
    arrays = set(re.findall(r"ACTUAL_NUMPY=([0-9]+\.[0-9]+\.[0-9]+)", log))
    if guards != {python} or uv != {python} or arrays != {numpy}:
        raise ArithmeticError("actual hosted runtime markers and uv selection required")


def control(c: dict[str, Any]) -> dict[str, Any]:
    idle = c["idle_control"]
    if (
        sys.platform != "darwin"
        or digest(Path(idle["path"])) != idle["sha256"]
        or idle["arguments"] != ["-i"]
    ):
        raise ArithmeticError("registered Darwin idle-control binary required")
    return dict(idle, requested=True, assertion_state_independently_audited=False)


def execute_child(root: Path, output: Path, c: dict[str, Any]) -> dict[str, Any]:
    from compact_cached import cli

    original = cli.read
    reads = []

    def observe(*args: Any, **kwargs: Any) -> dict[str, Any]:
        before = snapshot()
        row: dict[str, Any] = dict(status="running", before=before)
        reads.append(row)
        atomic(output / "parent-resource-reads.json", dict(reads=reads))
        try:
            saved = original(*args, **kwargs)
        except BaseException as error:
            row.update(
                status="failed_retained",
                after_failure=snapshot(),
                failure=dict(type=type(error).__name__, message=str(error)),
            )
            atomic(output / "parent-resource-reads.json", dict(reads=reads))
            raise
        row.update(
            status="complete",
            scope=saved["scope"],
            observation=record(before, snapshot()),
        )
        atomic(output / "parent-resource-reads.json", dict(reads=reads))
        return saved

    folder = output / "worker-telemetry"
    folder.mkdir()
    old = os.environ.get("POKER_CARD_CLOCK_DIR")
    os.environ["POKER_CARD_CLOCK_DIR"] = str(folder)
    try:
        with (
            patch.object(cli, "read", observe),
            patch.object(cli, "independent", worker),
        ):
            return base.execute_child(root, output, c)
    finally:
        if old is None:
            os.environ.pop("POKER_CARD_CLOCK_DIR", None)
        else:
            os.environ["POKER_CARD_CLOCK_DIR"] = old


def validate_resources(
    root: Path, output: Path, source: dict[str, Any], identity: dict[str, Any]
) -> dict[str, Any]:
    from profile_compact_replay import authenticate_source

    reads = json.loads((output / "parent-resource-reads.json").read_text())["reads"]
    if len(reads) != 3 or [r["scope"] for r in reads] != [
        r["scope"] for r in identity["computed_replays"]
    ]:
        raise ArithmeticError("all three actual resource read boundaries required")
    if any(
        row.get("status") != "complete"
        or row.get("before") != row["observation"]["before"]
        for row in reads
    ):
        raise ArithmeticError("only complete matching raw read boundaries qualify")
    for row in reads:
        check_record(row["observation"])
    workers = json.loads((output / "native.json").read_text())["native_batch"][
        "workers"
    ]
    if len(workers) != 3 or len({w["pid"] for w in workers}) != 3:
        raise ArithmeticError("three actual distinct spawned worker PIDs required")
    for slot in range(3):
        saved = json.loads(
            (output / "worker-telemetry" / f"worker-{slot}.json").read_text()
        )
        if (
            saved["status"] != "complete_worker_resource_trace"
            or saved["slot"] != slot
            or saved["indices"] != list(range(slot, 6, 3))
            or saved["config_sha256"] != CONFIG_SHA
            or saved["source"]["sha256"] != source["sha256"]
            or saved["numeric_summary"] != identity["worker_summaries"][slot]
            or saved["observation"]["before"]["pid"] != workers[slot]["pid"]
            or saved.get("before") != saved["observation"]["before"]
            or saved["runtime"]
            != dict(contract(root)["runtime"], module_is_under_checked_source_root=True)
        ):
            raise ArithmeticError(
                "complete source-bound unchanged worker trace required"
            )
        authenticate_source(root, saved["source"])
        check_record(saved["observation"])
    return dict(reads=3, workers=3, source_bound=True)


def child(root: Path, mode: str, output: Path, origin: float) -> int:
    saved: dict[str, Any] = dict(
        status="running", mode=mode, admission_evidence=False, child_before=snapshot()
    )
    receipt = output / "child.json"
    atomic(receipt, saved)
    try:
        c, current = preflight(root)
        checked(root, current)
        import numpy

        if (
            sys.version.split()[0] != c["runtime"]["python"]
            or numpy.__version__ != c["runtime"]["numpy"]
        ):
            raise ArithmeticError("original real-archive Python/NumPy required")
        saved["idle_control"] = control(c)
        saved.update(source=current, scope=c["scope"], config_sha256=CONFIG_SHA)
        atomic(receipt, saved)
        os.environ["POKER_COMPACT_OPPONENT_STARTED"] = repr(origin)
        # Import all entry aliases before replacing loaded poker_ai bindings;
        # subsequent defining-module imports see wrappers. Native uses spawn.
        from compact_cached import cli  # noqa: F401

        saved["body_before"] = snapshot()
        cpu = time.process_time()
        with hooks(c, enabled=mode == "cached") as stores:
            try:
                identity = execute_child(root, output, c)
            finally:
                saved["parent_body_cpu_seconds"] = time.process_time() - cpu
                saved["body_observation"] = record(saved["body_before"], snapshot())
                saved["card_cache"] = {k: v.summary() for k, v in stores.items()}
                atomic(receipt, saved)
        check_summary(saved["card_cache"], c, mode == "cached")
        after_c, after = preflight(root, clean=False)
        if (
            c != after_c
            or current["sha256"] != after["sha256"]
            or control(c) != saved["idle_control"]
        ):
            raise ArithmeticError("complete clock-trace source/input changed")
        raw = output / "native.json"
        native = json.loads(raw.read_text())
        native["implementation_config"] = dict(
            diagnostic_config=CONFIG,
            diagnostic_sha256=CONFIG_SHA,
            admission_evidence=False,
        )
        native["card_cache"] = saved["card_cache"]
        native["instrumentation_scope"] = c["scope"]
        atomic(raw, native)
        from compact_cached.cache import check_execution

        try:
            check_execution(root, native)
        except ArithmeticError:
            saved["base_admission_rejected"] = True
        else:
            raise ArithmeticError("diagnostic must fail base admission")
        check_record(saved["body_observation"])
        resources = validate_resources(root, output, current, identity)
        saved["resource_validation"] = resources
        saved.update(
            identity=identity,
            status="complete_card_clock_trace",
            seconds=time.perf_counter() - origin,
        )
        saved["raw_files"] = {
            str(p.relative_to(output)): digest(p)
            for p in output.rglob("*")
            if p.is_file() and p.name not in ("child.json", "command.log")
        }
        saved["child_observation"] = record(saved["child_before"], snapshot())
        saved["child_observation_scope"] = (
            "after imports/argument dispatch through final prewrite; "
            "supervisor alone supplies complete command clock"
        )
        atomic(receipt, saved)
        return 0
    except BaseException as error:
        saved.update(
            status="failed_retained",
            failure=dict(type=type(error).__name__, message=str(error)),
            seconds=time.perf_counter() - origin,
        )
        atomic(receipt, saved)
        raise


def pair_identity(
    a: dict[str, Any], b: dict[str, Any], c: dict[str, Any]
) -> dict[str, Any]:
    if (
        [a["mode"], b["mode"]] != ["uncached", "cached"]
        or any(
            x["status"] != "complete_card_clock_trace"
            or x.get("base_admission_rejected") is not True
            for x in (a, b)
        )
        or a["source"]["sha256"] != b["source"]["sha256"]
        or a["config_sha256"] != b["config_sha256"]
        or a["config_sha256"] != CONFIG_SHA
        or canonical(a["identity"]) != canonical(b["identity"])
    ):
        raise ArithmeticError(
            "complete clock-trace scalar/replay/worker/source identity changed"
        )
    for x, enabled in ((a, False), (b, True)):
        check_summary(x["card_cache"], c, enabled)
        if x.get("idle_control") != dict(
            c["idle_control"],
            requested=True,
            assertion_state_independently_audited=False,
        ):
            raise ArithmeticError("registered idle-control request evidence required")
    for name in ("canonical", "rank"):
        x, y = a["card_cache"][name], b["card_cache"][name]
        if (
            x["requests"] != y["requests"]
            or y["hits"] <= 0
            or y["original_calls"] >= x["original_calls"]
            or x["errors"]
            or y["errors"]
        ):
            raise ArithmeticError(
                "actual card requests, hits or original calls fail gate"
            )
    if any(
        x.get("resource_validation") != dict(reads=3, workers=3, source_bound=True)
        for x in (a, b)
    ):
        raise ArithmeticError("complete resource observations required")
    return dict(
        status="same_complete_audit_with_resource_trace",
        identity_sha256=hashlib.sha256(canonical(a["identity"])).hexdigest(),
    )


def controlled_command(command: list[str], mode: str, c: dict[str, Any]) -> None:
    if (
        len(command) != 8
        or command[:2] != [c["idle_control"]["path"], "-i"]
        or Path(command[3]).name != Path(ENTRY).name
        or command[4] != "--output"
        or Path(command[5]).name != mode
        or command[6:] != ["--_mode", mode]
    ):
        raise ArithmeticError("exact utility-duration idle-control command required")


def show(root: Path, output: Path) -> None:
    from profile_compact_replay import authenticate_source

    pair = json.loads((output / "pair.json").read_text())
    c = contract(root)
    children = []
    if pair["order"] != c["order"] or len(pair["measurements"]) != 2:
        raise ArithmeticError("fixed two-command complete pair required")
    for mode, measurement in zip(pair["order"], pair["measurements"], strict=True):
        controlled_command(measurement["command"], mode, c)
        if (
            type(measurement["seconds"]) not in (int, float)
            or not 0 < measurement["seconds"] < c["maximum_child_seconds"]
        ):
            raise ArithmeticError("original complete command cap required")
        folder = output / mode
        if (
            measurement != json.loads((folder / "measurement.json").read_text())
            or measurement["returncode"] != 0
            or digest(folder / "command.log") != pair["command_log_sha256"][mode]
            or digest(folder / "child.json") != measurement["child_sha256"]
        ):
            raise ArithmeticError("complete raw card-cache command changed")
        saved = json.loads((folder / "child.json").read_text())
        authenticate_source(root, saved["source"])
        check_record(saved["body_observation"])
        check_record(saved["child_observation"])
        if saved["resource_validation"] != validate_resources(
            root, folder, saved["source"], saved["identity"]
        ):
            raise ArithmeticError("saved resource validation changed")
        if any(digest(folder / name) != h for name, h in saved["raw_files"].items()):
            raise ArithmeticError("card-cache raw numerical evidence changed")
        children.append(saved)
        print(
            f"{mode}: {measurement['seconds']:.6f}s whole wall; "
            f"{saved['parent_body_cpu_seconds']:.6f}s parent body CPU"
        )
        print(json.dumps(saved["card_cache"], sort_keys=True))
    if any(pair[k] != v for k, v in pair_identity(children[0], children[1], c).items()):
        raise ArithmeticError("saved complete clock-trace identity changed")
    print(
        "Exact complete scalar/replay/worker identity; "
        "ONE ordered saved case, no new training or admission"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("results/runs/card-audit-clock-trace/pair")
    )
    parser.add_argument("--stop-at")
    parser.add_argument("--show", type=Path)
    parser.add_argument(
        "--_mode", choices=("uncached", "cached"), help=argparse.SUPPRESS
    )
    args = parser.parse_args()
    if args.show is not None:
        show(ROOT, ROOT / args.show)
        return 0
    if args._mode:
        return child(
            ROOT,
            args._mode,
            ROOT / args.output,
            float(os.environ["POKER_COMPACT_REPLAY_PROFILE_STARTED"]),
        )
    if args.stop_at is None:
        parser.error("--stop-at required")
    c = contract(ROOT)
    control(c)
    cutoff = datetime.fromisoformat(args.stop_at.replace("Z", "+00:00"))
    reserve = sum(
        c[k]
        for k in (
            "maximum_pair_seconds",
            "final_ci_reserve_seconds",
            "save_reserve_seconds",
        )
    )
    if cutoff.tzinfo is None or (cutoff - datetime.now(UTC)).total_seconds() < reserve:
        raise TimeoutError("full pair/finalCI/save reserves do not fit cutoff")
    output = ROOT / args.output
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain previous complete/partial card-cache pair")
    if not output.resolve().is_relative_to(ROOT.resolve() / "results/runs"):
        raise ArithmeticError("formal resource traces need a fresh run folder")
    output.mkdir(parents=True)
    started = time.perf_counter()
    saved: dict[str, Any] = dict(
        status="running", order=c["order"], measurements=[], admission_evidence=False
    )
    atomic(output / "pair.json", saved)
    try:
        for mode in c["order"]:
            m = supervise(
                [
                    c["idle_control"]["path"],
                    *c["idle_control"]["arguments"],
                    sys.executable,
                    str(ROOT / ENTRY),
                    "--output",
                    str(output / mode),
                    "--_mode",
                    mode,
                ],
                output / mode,
                min(
                    c["maximum_child_seconds"],
                    c["maximum_pair_seconds"] - (time.perf_counter() - started),
                ),
            )
            saved["measurements"].append(m)
            saved.setdefault("command_log_sha256", {})[mode] = digest(
                output / mode / "command.log"
            )
            atomic(output / "pair.json", saved)
            if (
                m["returncode"] != 0
                or not 0 < m["seconds"] < c["maximum_child_seconds"]
            ):
                raise ArithmeticError(
                    "complete clock-trace child failed or exceeded cap"
                )
        children = [
            json.loads((output / mode / "child.json").read_text())
            for mode in c["order"]
        ]
        saved.update(
            pair_identity(children[0], children[1], c),
            seconds=time.perf_counter() - started,
        )
        saved["cached_elapsed_lower_in_this_pair"] = (
            saved["measurements"][1]["seconds"] < saved["measurements"][0]["seconds"]
        )
        if saved["seconds"] >= c["maximum_pair_seconds"]:
            raise TimeoutError("complete clock-trace pair exceeded shared cap")
        atomic(output / "pair.json", saved)
    except BaseException as error:
        saved.update(
            status="failed_retained",
            failure=dict(type=type(error).__name__, message=str(error)),
        )
        atomic(output / "pair.json", saved)
        raise
    show(ROOT, output)
    return 0  # Both directions descriptive; no performance admission in this step.


if __name__ == "__main__":
    raise SystemExit(main())
