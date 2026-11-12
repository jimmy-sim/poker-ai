"""Standalone instrumentation of an unchanged, complete compact cost replay.

Kept outside src deliberately: its own source binds this script while the old
runner's all-src aggregate and original strict historical guards stay intact.
The supervisor is stdlib-only and charges startup/imports/extraction/writes.
"""

import argparse
import gzip
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/compact-replay-profile.json"
CONFIG_SHA = "d9c43f528aa47ed1faa08cd82a4d882f4b9046340d17c3ae38a3da61bbef6d76"
ENTRY = "scripts/profile_compact_replay.py"
FOLDER = "results/compact-replay-profile"


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, allow_nan=False).encode()


def atomic(path: Path, value: Any) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective replay-profile contract changed")
    saved: dict[str, Any] = json.loads((root / CONFIG).read_text())
    return saved


def preflight(root: Path) -> tuple[dict[str, Any], dict[str, Any]]:
    """Check old named source AND every published archive/report member."""
    from poker_ai.evaluation.compact_opponent_source import source as old_source
    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.postflop.learning_artifacts import sha
    from poker_ai.validation.five_card import source_provenance

    c = contract(root)
    original = old_source(root, clean=True)
    if (
        original["fingerprint"] != c["original_source_sha256"]
        or original["sha256"] != c["original_named_source"]
        or digest(root / c["own"]) != c["own_sha256"]
        or any(digest(root / p) != h for p, h in c["published_input_sha256"].items())
    ):
        raise ArithmeticError(
            "complete frozen replay corpus or original source changed"
        )
    current: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=(ENTRY,))
    )
    current["sha256"].update(c["original_named_source"])
    current["fingerprint"] = sha(current["sha256"])
    commit_sources(root, current["git_commit"], current["sha256"])
    return c, current


def checked(root: Path, source: dict[str, Any]) -> None:
    from poker_ai.evaluation.compact_opponent_admission import published
    from poker_ai.evaluation.diagnostic_receipts import checks

    path = root / FOLDER / "checks.json"
    checks(root, path, source)
    published(root, path)
    receipt = json.loads(path.read_text())
    for row in receipt["checks"]:
        published(root, root / row["log"]["file"])


def identity(own: dict[str, Any], c: dict[str, Any]) -> dict[str, Any]:
    replay = own["own_replay"]
    if (
        own["scope"] != "OLD_OWN_OPPONENT_COST_STANDINS_NO_NEW_TRAINING"
        or own["poker_training_performed"] is not False
        or own["reference_constructed"] is not False
        or own["actual_poker_training_work"] != 0
        or any(replay[k] != v for k, v in c["expected"].items())
        or replay["unique_profiles"] != 432
        or replay["policy_and_ledger_bits_exact"] is not True
    ):
        raise ArithmeticError("complete cost-only replay identity required")
    return dict(
        complete_own_sha256=hashlib.sha256(canonical(own)).hexdigest(),
        own_replay=replay,
        source_sha256=own["source_sha256"],
        poker_training_performed=False,
        reference_constructed=False,
    )


def profile_read(root: Path, own: Path, deadline: Any, output: Path) -> dict[str, Any]:
    """Keep every raw code object/caller, not lossy pstats label aggregates."""
    import cProfile

    from poker_ai.evaluation.batch_cost_stats import extract
    from poker_ai.evaluation.compact_opponent_cli import read

    profiler = cProfile.Profile()
    try:
        return profiler.runcall(read, root, own, deadline)
    finally:
        profiler.disable()
        profiler.dump_stats(str(output / "replay.prof"))
        stats = extract(profiler, root)
        with (output / "functions-callers.json.gz").open("xb") as raw:
            with gzip.GzipFile(filename="", mode="wb", fileobj=raw, mtime=0) as stream:
                stream.write(canonical(stats) + b"\n")


def child(root: Path, mode: str, output: Path, origin: float) -> int:
    """Only the exact frozen reader can supply the replay result."""
    saved: dict[str, Any] = dict(
        status="running",
        mode=mode,
        training_performed=False,
        reference_constructed=False,
        admission_evidence=False,
    )
    receipt = output / "child.json"
    atomic(receipt, saved)
    try:
        from poker_ai.evaluation.compact_opponent_cli import read
        from poker_ai.evaluation.compact_opponent_publication import publication
        from poker_ai.postflop.river_study import Deadline

        c, source = preflight(root)
        import numpy as np

        if (
            sys.version.split()[0] != c["runtime"]["python"]
            or np.__version__ != c["runtime"]["numpy"]
        ):
            raise ArithmeticError(
                "original Python/NumPy runtime required for real archive replay"
            )
        checked(root, source)
        deadline = Deadline(c["maximum_child_seconds"])
        deadline.started = origin
        own_path = root / c["own"]
        saved.update(
            scope=c["scope"], source=source, config_sha256=digest(root / CONFIG)
        )
        saved["publication"] = publication(
            root, own_path, json.loads(own_path.read_text())
        )
        deadline.check()
        own = (
            profile_read(root, own_path, deadline, output)
            if mode == "profile"
            else read(root, own_path, deadline)
        )
        saved["identity"] = identity(own, c)
        after_c, after_source = preflight(root)
        if after_c != c or after_source["sha256"] != source["sha256"]:
            raise ArithmeticError(
                "profile source or complete inputs changed during replay"
            )
        if mode == "profile":
            saved["profile_files"] = {
                p: digest(output / p)
                for p in ("replay.prof", "functions-callers.json.gz")
            }
        saved.update(
            status="complete_read_only_replay", seconds=time.perf_counter() - origin
        )
        atomic(receipt, saved)
        deadline.check()
        return 0
    except BaseException as exc:
        saved.update(
            status="failed_retained",
            failure=dict(type=type(exc).__name__, message=str(exc)),
        )
        atomic(receipt, saved)
        raise


def supervise(command: list[str], output: Path, cap: float) -> dict[str, Any]:
    """Retain hard timeouts and incomplete children; no same-destination retry."""
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain complete/partial replay profile output")
    output.mkdir(parents=True)
    started = time.perf_counter()
    env = dict(os.environ, POKER_COMPACT_REPLAY_PROFILE_STARTED=repr(started))
    with (output / "command.log").open("x") as log:
        process = subprocess.Popen(
            command,
            env=env,
            stdout=log,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
        interrupted = None
        try:
            code = process.wait(timeout=cap)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as exc:
            interrupted = type(exc).__name__
            os.killpg(process.pid, signal.SIGTERM)
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
            code = 124 if isinstance(exc, subprocess.TimeoutExpired) else 130
    result = dict(
        command=command,
        returncode=code,
        interrupted=interrupted,
        seconds=time.perf_counter() - started,
        child_sha256=digest(output / "child.json")
        if (output / "child.json").is_file()
        else None,
        scope=(
            "Whole child startup/imports/checks/replay/extraction/writes; "
            "excludes this measurement receipt"
        ),
    )
    atomic(output / "measurement.json", result)
    return result


def pair_identity(plain: dict[str, Any], profiled: dict[str, Any]) -> dict[str, Any]:
    if (
        plain["status"] != "complete_read_only_replay"
        or profiled["status"] != "complete_read_only_replay"
        or plain["mode"] != "plain"
        or profiled["mode"] != "profile"
        or canonical(plain["identity"]) != canonical(profiled["identity"])
        or plain["source"]["sha256"] != profiled["source"]["sha256"]
        or plain["config_sha256"] != profiled["config_sha256"]
    ):
        raise ArithmeticError("plain/profile complete replay identity changed")
    return dict(status="same_complete_cost_replay", **plain["identity"])


def authenticate_source(root: Path, saved: dict[str, Any]) -> None:
    """Named historical bytes stay checkable after unrelated source additions."""
    from poker_ai.postflop.compact_full_artifacts import commit_sources
    from poker_ai.postflop.learning_artifacts import sha

    if saved["fingerprint"] != sha(saved["sha256"]) or any(
        digest(root / name) != expected for name, expected in saved["sha256"].items()
    ):
        raise ArithmeticError("profile viewer named scientific source changed")
    commit_sources(root, saved["git_commit"], saved["sha256"])


def show(output: Path) -> None:
    """Authenticate retained children/profile bytes before printing costs."""
    from poker_ai.evaluation.batch_cost_stats import validate

    saved = json.loads((output / "pair.json").read_text())
    if saved["status"] != "same_complete_cost_replay" or saved["order"] != [
        "plain",
        "profile",
    ]:
        raise ArithmeticError("complete ordered profile pair required")
    children = []
    for mode, measurement in zip(saved["order"], saved["measurements"], strict=True):
        folder = output / mode
        actual = json.loads((folder / "measurement.json").read_text())
        if (
            actual != measurement
            or actual["returncode"] != 0
            or actual["interrupted"] is not None
            or digest(folder / "child.json") != actual["child_sha256"]
        ):
            raise ArithmeticError("profile child measurement changed")
        children.append(json.loads((folder / "child.json").read_text()))
    identity = pair_identity(*children)
    authenticate_source(ROOT, children[0]["source"])
    if any(saved[k] != value for k, value in identity.items()):
        raise ArithmeticError("saved pair identity changed")
    for name, expected in children[1]["profile_files"].items():
        if (
            name not in ("replay.prof", "functions-callers.json.gz")
            or digest(output / "profile" / name) != expected
        ):
            raise ArithmeticError("raw profile bytes changed")
    if set(children[1]["profile_files"]) != {
        "replay.prof",
        "functions-callers.json.gz",
    }:
        raise ArithmeticError("complete raw profiler inventory required")
    with gzip.open(output / "profile/functions-callers.json.gz", "rt") as stream:
        stats = json.load(stream)
    validate(stats)
    print("Complete cost replay; identical plain/profile results; no new learning")
    for mode, measurement in zip(saved["order"], saved["measurements"], strict=True):
        print(f"{mode}: {measurement['seconds']:.6f} whole-child seconds")
    print(f"Raw functions: {stats['frame_count']}; caller edges: {stats['edge_count']}")
    for metric in ("self_seconds", "cumulative_seconds"):
        print(
            metric
            + (" (inclusive times overlap):" if metric == "cumulative_seconds" else ":")
        )
        for row in sorted(stats["functions"], key=lambda r: r[metric], reverse=True)[
            :12
        ]:
            print(
                f"  {row[metric]:.6f}s  {row['total_calls']} calls  "
                f"{row['file']}:{row['line']} {row['qualname']}"
            )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/compact-replay-profile/profile"),
    )
    parser.add_argument("--stop-at")
    parser.add_argument("--show", type=Path)
    parser.add_argument("--_mode", choices=("plain", "profile"), help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.show is not None:
        show(ROOT / args.show)
        return 0
    if args.stop_at is None:
        parser.error("--stop-at is required for the fixed profile pair")
    if args._mode:
        return child(
            ROOT,
            args._mode,
            args.output,
            float(os.environ["POKER_COMPACT_REPLAY_PROFILE_STARTED"]),
        )
    c = contract(ROOT)
    cutoff = datetime.fromisoformat(args.stop_at.replace("Z", "+00:00"))
    if (
        cutoff.tzinfo is None
        or (cutoff - datetime.now(UTC)).total_seconds()
        < c["maximum_pair_seconds"] + c["save_reserve_seconds"]
    ):
        raise TimeoutError(
            "full fixed replay pair plus save reserve does not fit cutoff"
        )
    output = ROOT / args.output
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain previous complete/partial profile pair")
    output.mkdir(parents=True)
    started = time.perf_counter()
    saved: dict[str, Any] = dict(
        status="running", order=c["order"], measurements=[], admission_evidence=False
    )
    atomic(output / "pair.json", saved)
    try:
        for mode in c["order"]:
            destination = output / mode
            m = supervise(
                [
                    sys.executable,
                    str(ROOT / ENTRY),
                    "--output",
                    str(destination),
                    "--stop-at",
                    args.stop_at,
                    "--_mode",
                    mode,
                ],
                destination,
                min(
                    c["maximum_child_seconds"],
                    c["maximum_pair_seconds"] - (time.perf_counter() - started),
                ),
            )
            saved["measurements"].append(m)
            atomic(output / "pair.json", saved)
            if (
                m["returncode"] != 0
                or not 0 < m["seconds"] < c["maximum_child_seconds"]
            ):
                raise ArithmeticError(
                    "complete fixed replay child did not finish under cap"
                )
        plain, profiled = [
            json.loads((output / mode / "child.json").read_text())
            for mode in c["order"]
        ]
        saved.update(
            pair_identity(plain, profiled), seconds=time.perf_counter() - started
        )
        if saved["seconds"] >= c["maximum_pair_seconds"]:
            raise TimeoutError("complete replay pair exceeded its fixed cap")
        atomic(output / "pair.json", saved)
    except BaseException as exc:
        saved.update(
            status="failed_retained",
            failure=dict(type=type(exc).__name__, message=str(exc)),
        )
        atomic(output / "pair.json", saved)
        raise
    print(saved["status"] + "; no learning, reference construction or admission")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
