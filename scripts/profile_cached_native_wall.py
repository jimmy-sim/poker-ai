"""Complete cached native-audit elapsed-stack profile; never a study permit.

Frames include blocked waits; CPU is sampled only at body/read boundaries.
The unchanged complete child includes initial/final own replays and three native
workers. This standalone instrumentation source preserves every old kernel.
"""

import argparse
import cProfile
import gzip
import hashlib
import json
import os
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from unittest.mock import patch

from profile_cached_native import preflight as base_preflight
from profile_compact_replay import atomic, canonical, digest, supervise

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/compact-native-wall-profile.json"
CONFIG_SHA = "4a9947aaff1e9a717efeed865264a3f9c448464689df99049e8d3524bea7753f"
ENTRY = "scripts/profile_cached_native_wall.py"
FOLDER = "results/compact-native-wall-profile"


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective native-profile contract changed")
    result: dict[str, Any] = json.loads((root / CONFIG).read_text())
    return result


def preflight(
    root: Path, *, clean: bool = True
) -> tuple[dict[str, Any], dict[str, Any]]:

    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.validation.five_card import source_provenance

    c = contract(root)
    _, original = base_preflight(root, clean=clean)
    if original["fingerprint"] != c["historical_profile_source_sha256"] or any(
        digest(root / p) != h for p, h in c["input_sha256"].items()
    ):
        raise ArithmeticError("complete frozen native-profile source or inputs changed")
    current: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=(ENTRY,))
    )
    current["sha256"].update(original["sha256"])
    current["fingerprint"] = sha(current["sha256"])
    commit_sources(root, current["git_commit"], current["sha256"])
    return c, current


def checked(root: Path, current: dict[str, Any]) -> None:
    from compact_cached.admission import published

    from poker_ai.evaluation.diagnostic_receipts import checks

    path = root / FOLDER / "checks.json"
    saved = checks(root, path, current)
    published(root, path)
    # checks returns a bound file record; read the authenticated six raw logs.
    receipt = json.loads((root / saved["file"]).read_text())
    for row in receipt["checks"]:
        published(root, root / row["log"]["file"])


def identity(saved: dict[str, Any], replays: list[dict[str, Any]]) -> dict[str, Any]:
    """All scalar rows/computed replay results, not rounded or selected metrics."""
    from compact_cached.cache import check_counters
    from compact_cached.contract import CONFIG_SHA as BASE_CONFIG_SHA

    from poker_ai.evaluation.opponent_learning_design import COST, TOY

    if (
        saved["status"] != "completed_scalar_comparison"
        or saved["failure"] is not None
        or saved["scope"] != COST
        or type(saved["repetition"]) is not int
        or saved["repetition"] != 0
        or saved["poker_training_performed"] is not False
        or saved["reference_constructed"] is not True
        or saved["reference_output_used_in_training"] is not False
        or any(
            saved[k] is not False
            for k in (
                "long_run_admitted",
                "new_agent_default",
                "fresh_global_admission",
            )
        )
        or len(saved["profiles"]) != 432
        or len(saved["fixed_conditions"]) != 1152
        or len(replays) != 3
        or [r["scope"] for r in replays] != [TOY, COST, COST]
        or replays[1] != replays[2]
        or any(r["computed"]["unique_profiles"] != 432 for r in replays)
        or any(
            r["computed"]["policy_and_ledger_bits_exact"] is not True for r in replays
        )
    ):
        raise ArithmeticError(
            "complete unchanged scalar and computed-replay inventory required"
        )
    check_counters(saved["validation_cache"])
    workers = saved["native_batch"]["workers"]
    if len(workers) != 3 or saved["native_batch"]["status"] != "completed":
        raise ArithmeticError("complete three native workers required")
    summaries = []
    for slot, worker in enumerate(workers):
        done = [m for m in worker["messages"] if m.get("kind") == "done"]
        if worker["slot"] != slot or worker["exitcode"] != 0 or len(done) != 1:
            raise ArithmeticError("complete fixed worker summary required")
        summary = done[0]["summary"]
        if summary["implementation_sha256"] != BASE_CONFIG_SHA:
            raise ArithmeticError("worker effective implementation changed")
        check_counters(summary["validation_cache"])
        summaries.append(summary)
    return dict(
        own_sha256=saved["own_sha256"],
        base_source_sha256=saved["source_sha256"],
        implementation_config=saved["implementation_config"],
        profiles=saved["profiles"],
        fixed_conditions=saved["fixed_conditions"],
        verification=saved["verification"],
        validation_cache=saved["validation_cache"],
        worker_summaries=summaries,
        computed_replays=replays,
        training_performed=False,
        reference_actions_exported=False,
    )


def execute_child(root: Path, output: Path, c: dict[str, Any]) -> dict[str, Any]:
    """Transparent observation of all three mandatory mathematical reads."""
    from compact_cached import cli

    original = cli.read
    replays = []
    phases = []

    def observe(*args: Any, **kwargs: Any) -> dict[str, Any]:
        if "observed" in kwargs or len(args) != 3:
            raise ArithmeticError("native reads must keep original complete call shape")
        actual: list[dict[str, Any]] = []
        wall, cpu = time.perf_counter(), time.process_time()
        saved = original(*args, **kwargs, observed=actual)
        phases.append(
            dict(
                scope=saved["scope"],
                whole_read_wall_seconds=time.perf_counter() - wall,
                parent_read_cpu_seconds=time.process_time() - cpu,
            )
        )
        if len(actual) != 1:
            raise ArithmeticError("one actual mathematical replay per read required")
        replays.append(dict(scope=saved["scope"], computed=actual[0]))
        return saved

    with patch.object(cli, "read", observe):
        code = cli.child_main(
            root,
            [
                "cost-audit",
                "--repetition",
                "0",
                "--own",
                c["own"],
                "--output",
                str(output / "native.json"),
            ],
        )
    if code != 0:
        raise ArithmeticError("complete native child failed")
    raw = output / "native.json"
    saved = json.loads(raw.read_text())
    from compact_cached.cache import check_execution

    check_execution(root, saved)
    result = identity(saved, replays)
    atomic(
        output / "read-phases.json",
        dict(
            phases=phases,
            scope=(
                "unchanged complete mathematical reads; "
                "timings excluded from exact identity"
            ),
        ),
    )
    # Explicitly invalidate base-family admission: instrumentation is effective
    # parent source, even though all numerical/worker implementations are old.
    saved["base_implementation_config"] = saved["implementation_config"]
    saved["implementation_config"] = dict(
        instrumentation_config=CONFIG,
        instrumentation_sha256=CONFIG_SHA,
        admission_evidence=False,
    )
    saved["instrumentation_scope"] = c["scope"]
    atomic(raw, saved)
    return result


def child(root: Path, mode: str, output: Path, origin: float) -> int:
    saved: dict[str, Any] = dict(status="running", mode=mode, admission_evidence=False)
    receipt = output / "child.json"
    atomic(receipt, saved)
    profile: cProfile.Profile | None = None
    try:
        c, current = preflight(root)
        checked(root, current)
        import numpy

        if (
            sys.version.split()[0] != c["runtime"]["python"]
            or numpy.__version__ != c["runtime"]["numpy"]
        ):
            raise ArithmeticError("original real-archive Python/NumPy runtime required")
        saved.update(source=current, scope=c["scope"], config_sha256=CONFIG_SHA)
        os.environ["POKER_COMPACT_OPPONENT_STARTED"] = repr(origin)
        if mode == "profile":
            profile = cProfile.Profile()
        cpu = time.process_time()
        try:
            result = (
                profile.runcall(execute_child, root, output, c)
                if profile
                else execute_child(root, output, c)
            )
        finally:
            saved["parent_body_cpu_seconds"] = time.process_time() - cpu
            if profile is not None:
                from poker_ai.evaluation.batch_cost_stats import extract

                profile.disable()
                profile.dump_stats(str(output / "native-parent.prof"))
                stats = extract(profile, root)
                with (output / "functions-callers.json.gz").open("xb") as raw:
                    with gzip.GzipFile(
                        filename="", mode="wb", fileobj=raw, mtime=0
                    ) as stream:
                        stream.write(canonical(stats) + b"\n")
                saved["profile_files"] = {
                    p: digest(output / p)
                    for p in ("native-parent.prof", "functions-callers.json.gz")
                }
        after_c, after_source = preflight(root, clean=False)
        if after_c != c or after_source["sha256"] != current["sha256"]:
            raise ArithmeticError(
                "complete profile source/input changed during command"
            )
        from compact_cached.cache import check_execution

        native = json.loads((output / "native.json").read_text())
        try:
            check_execution(root, native)
        except ArithmeticError:
            saved["base_admission_rejected"] = True
        else:
            raise ArithmeticError(
                "instrumented native receipt must fail base admission"
            )
        saved.update(
            identity=result,
            status="complete_native_parent_profile",
            seconds=time.perf_counter() - origin,
        )
        saved["raw_files"] = {
            p.name: digest(p)
            for p in output.iterdir()
            if p.is_file() and p.name not in ("child.json", "command.log")
        }
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


def pair_identity(plain: dict[str, Any], profiled: dict[str, Any]) -> dict[str, Any]:
    if (
        any(
            x["status"] != "complete_native_parent_profile"
            or x.get("base_admission_rejected") is not True
            for x in (plain, profiled)
        )
        or [plain["mode"], profiled["mode"]] != ["plain", "profile"]
        or canonical(plain["identity"]) != canonical(profiled["identity"])
        or plain["source"]["sha256"] != profiled["source"]["sha256"]
        or plain["config_sha256"] != profiled["config_sha256"]
    ):
        raise ArithmeticError("complete native plain/profile identity changed")
    return dict(
        status="same_complete_native_scalar_and_replay_results",
        identity_sha256=hashlib.sha256(canonical(plain["identity"])).hexdigest(),
    )


def show(output: Path) -> None:
    from profile_compact_replay import authenticate_source

    from poker_ai.evaluation.batch_cost_stats import validate

    pair = json.loads((output / "pair.json").read_text())
    children = []
    if pair["order"] != ["plain", "profile"] or len(pair["measurements"]) != 2:
        raise ArithmeticError("fixed complete profile pair required")
    for mode, measurement in zip(pair["order"], pair["measurements"], strict=True):
        folder = output / mode
        if digest(folder / "command.log") != pair["command_log_sha256"][mode]:
            raise ArithmeticError("raw command log changed")
        if (
            measurement != json.loads((folder / "measurement.json").read_text())
            or measurement["returncode"] != 0
            or digest(folder / "child.json") != measurement["child_sha256"]
        ):
            raise ArithmeticError("complete profile measurement changed")
        saved = json.loads((folder / "child.json").read_text())
        authenticate_source(ROOT, saved["source"])
        for name, checksum in saved["raw_files"].items():
            if digest(folder / name) != checksum:
                raise ArithmeticError("profile raw scalar/journal data changed")
        children.append(saved)
        print(
            f"{mode}: {measurement['seconds']:.6f}s whole wall; "
            f"{saved['parent_body_cpu_seconds']:.6f}s parent body CPU"
        )
    if any(pair[k] != v for k, v in pair_identity(*children).items()):
        raise ArithmeticError("saved complete pair identity changed")
    with gzip.open(output / "profile/functions-callers.json.gz", "rt") as stream:
        stats = json.load(stream)
    validate(stats)
    print(
        "Identical complete native scalar and computed replay results; "
        "no new training or admission"
    )
    print(
        f"Parent elapsed-stack profile: {stats['frame_count']} raw functions, "
        f"{stats['edge_count']} caller edges; worker CPU is separate"
    )
    for metric in ("self_seconds", "cumulative_seconds"):
        print(
            metric
            + (" (inclusive costs overlap)" if metric == "cumulative_seconds" else "")
        )
        for row in sorted(stats["functions"], key=lambda x: x[metric], reverse=True)[
            :12
        ]:
            print(
                f"  {row[metric]:.6f}s {row['total_calls']} calls "
                f"{row['file']}:{row['line']} {row['qualname']}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/compact-native-wall-profile/pair"),
    )
    parser.add_argument("--stop-at")
    parser.add_argument("--show", type=Path)
    parser.add_argument("--_mode", choices=("plain", "profile"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.show is not None:
        show(ROOT / args.show)
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
    cutoff = datetime.fromisoformat(args.stop_at.replace("Z", "+00:00"))
    if (
        cutoff.tzinfo is None
        or (cutoff - datetime.now(UTC)).total_seconds()
        < c["maximum_pair_seconds"] + c["save_reserve_seconds"]
    ):
        raise TimeoutError("full native pair and save reserve do not fit cutoff")
    output = ROOT / args.output
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain previous complete/partial native pair")
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
                    "complete native profile child failed or exceeded cap"
                )
        children = [
            json.loads((output / mode / "child.json").read_text())
            for mode in c["order"]
        ]
        saved.update(pair_identity(*children), seconds=time.perf_counter() - started)
        if saved["seconds"] >= c["maximum_pair_seconds"]:
            raise TimeoutError("complete native profile pair exceeded cap")
        atomic(output / "pair.json", saved)
    except BaseException as error:
        saved.update(
            status="failed_retained",
            failure=dict(type=type(error).__name__, message=str(error)),
        )
        atomic(output / "pair.json", saved)
        raise
    show(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
