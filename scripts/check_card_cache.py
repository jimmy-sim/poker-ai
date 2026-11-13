"""One complete saved native audit pair with parent-only pure-card memoization."""

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

import profile_cached_native_wall as base
from card_cache_support import check_summary, hooks
from profile_compact_replay import atomic, canonical, digest, supervise

ROOT = Path(__file__).resolve().parents[1]
CONFIG = "configs/card-computation-cache.json"
CONFIG_SHA = "9e9b088e02665e725f873209a9801874df33b7fcf39908363d7eadab6b634704"
ENTRY = "scripts/check_card_cache.py"
SUPPORT = "scripts/card_cache_support.py"
FOLDER = "results/card-computation-cache"


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
    _, historical = base.preflight(root, clean=clean)
    if historical["fingerprint"] != c["historical_source"]:
        raise ArithmeticError("frozen complete historical source changed")
    current: dict[str, Any] = dict(
        source_provenance(root, root / CONFIG, entrypoints=(ENTRY, SUPPORT))
    )
    current["sha256"].update(historical["sha256"])
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


def child(root: Path, mode: str, output: Path, origin: float) -> int:
    saved: dict[str, Any] = dict(status="running", mode=mode, admission_evidence=False)
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
        saved.update(source=current, scope=c["scope"], config_sha256=CONFIG_SHA)
        atomic(receipt, saved)
        os.environ["POKER_COMPACT_OPPONENT_STARTED"] = repr(origin)
        # Import all entry aliases before replacing loaded poker_ai bindings;
        # subsequent defining-module imports see wrappers. Native uses spawn.
        from compact_cached import cli  # noqa: F401

        cpu = time.process_time()
        with hooks(c, enabled=mode == "cached") as stores:
            try:
                identity = base.execute_child(root, output, c)
            finally:
                saved["parent_body_cpu_seconds"] = time.process_time() - cpu
                saved["card_cache"] = {k: v.summary() for k, v in stores.items()}
                atomic(receipt, saved)
        check_summary(saved["card_cache"], c, mode == "cached")
        after_c, after = preflight(root, clean=False)
        if c != after_c or current["sha256"] != after["sha256"]:
            raise ArithmeticError("complete card-cache source/input changed")
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
        saved.update(
            identity=identity,
            status="complete_card_cache_audit",
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


def pair_identity(
    a: dict[str, Any], b: dict[str, Any], c: dict[str, Any]
) -> dict[str, Any]:
    if (
        [a["mode"], b["mode"]] != ["uncached", "cached"]
        or any(
            x["status"] != "complete_card_cache_audit"
            or x.get("base_admission_rejected") is not True
            for x in (a, b)
        )
        or a["source"]["sha256"] != b["source"]["sha256"]
        or a["config_sha256"] != b["config_sha256"]
        or a["config_sha256"] != CONFIG_SHA
        or canonical(a["identity"]) != canonical(b["identity"])
    ):
        raise ArithmeticError(
            "complete card-cache scalar/replay/worker/source identity changed"
        )
    for x, enabled in ((a, False), (b, True)):
        check_summary(x["card_cache"], c, enabled)
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
    return dict(
        status="same_complete_audit_with_parent_card_reuse",
        identity_sha256=hashlib.sha256(canonical(a["identity"])).hexdigest(),
    )


def show(root: Path, output: Path) -> None:
    from profile_compact_replay import authenticate_source

    pair = json.loads((output / "pair.json").read_text())
    c = contract(root)
    children = []
    if pair["order"] != c["order"] or len(pair["measurements"]) != 2:
        raise ArithmeticError("fixed two-command complete pair required")
    for mode, measurement in zip(pair["order"], pair["measurements"], strict=True):
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
        if any(digest(folder / name) != h for name, h in saved["raw_files"].items()):
            raise ArithmeticError("card-cache raw numerical evidence changed")
        children.append(saved)
        print(
            f"{mode}: {measurement['seconds']:.6f}s whole wall; "
            f"{saved['parent_body_cpu_seconds']:.6f}s parent body CPU"
        )
        print(json.dumps(saved["card_cache"], sort_keys=True))
    if any(pair[k] != v for k, v in pair_identity(children[0], children[1], c).items()):
        raise ArithmeticError("saved complete card-cache identity changed")
    print(
        "Exact complete scalar/replay/worker identity; "
        "ONE ordered saved case, no new training or admission"
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path("results/runs/card-computation-cache/pair")
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
                    "complete card-cache child failed or exceeded cap"
                )
        children = [
            json.loads((output / mode / "child.json").read_text())
            for mode in c["order"]
        ]
        saved.update(
            pair_identity(children[0], children[1], c),
            seconds=time.perf_counter() - started,
        )
        saved["narrow_wall_time_pass"] = (
            saved["measurements"][1]["seconds"] < saved["measurements"][0]["seconds"]
        )
        if saved["seconds"] >= c["maximum_pair_seconds"]:
            raise TimeoutError("complete card-cache pair exceeded shared cap")
        atomic(output / "pair.json", saved)
    except BaseException as error:
        saved.update(
            status="failed_retained",
            failure=dict(type=type(error).__name__, message=str(error)),
        )
        atomic(output / "pair.json", saved)
        raise
    show(ROOT, output)
    return 0 if saved["narrow_wall_time_pass"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
