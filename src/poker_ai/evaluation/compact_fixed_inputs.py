"""Frozen source/selector binding and unchanged-dependency historical replay."""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation import compact_sampled_inputs as old_inputs
from poker_ai.evaluation import compact_sampled_own as old_own
from poker_ai.evaluation.compact_sampled_clock import measurement as sampled_clock
from poker_ai.evaluation.compact_sampled_prior import verify as prior_full
from poker_ai.finite import FloatArray
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.compact_full_clock import measurement as full_clock
from poker_ai.postflop.compact_full_context import Context
from poker_ai.postflop.compact_full_native_checks import validate as full_native
from poker_ai.postflop.compact_full_run import check_runtime
from poker_ai.postflop.compact_sampled_native_checks import validate as sampled_native
from poker_ai.postflop.compact_sampled_state import decode
from poker_ai.postflop.learning_artifacts import canonical, sha
from poker_ai.postflop.public_range_definition import contract
from poker_ai.postflop.river_study import digest
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/compact-fixed-opponents.json"
CONFIG_SHA = "35b9a1956c90400018ffe22fbafdcb9ab994876e812e43fdc03f4250d632f82c"
ENTRY = "scripts/diagnose_compact_fixed.py"
FOLDER = "results/compact-fixed-opponents"
FIELDS = ("spot_file", "representation", "seed", "mixture")


def config(root: Path) -> dict[str, Any]:
    path = root / CONFIG
    if digest(path) != CONFIG_SHA:
        raise ArithmeticError("published diagnostic design changed")
    value: dict[str, Any] = json.loads(path.read_text())
    for name, expected in value["input_sha256"].items():
        if digest(root / name) != expected:
            raise ArithmeticError("diagnostic source evidence changed")
    old_inputs.protocol(root)
    return value


def source(root: Path, *, clean: bool = True) -> dict[str, Any]:
    if not Path(__file__).resolve().is_relative_to(root / "src"):
        raise ArithmeticError("diagnostic imports outside stated checkout")
    saved = source_provenance(root, root / CONFIG, entrypoints=(ENTRY,))
    saved["fingerprint"] = sha(saved["sha256"])
    if clean and saved["dirty"] is not False:
        raise ValueError("publish checked source first")
    return saved


def historical(root: Path, saved: dict[str, Any], fingerprint: str) -> None:
    if saved["fingerprint"] != fingerprint or sha(saved["sha256"]) != fingerprint:
        raise ArithmeticError("original source map/fingerprint changed")
    files.commit_sources(root, saved["git_commit"], saved["sha256"])


def check_source(root: Path, saved: dict[str, Any]) -> None:
    if source(root, clean=False)["fingerprint"] != saved["fingerprint"]:
        raise ArithmeticError("diagnostic source/config changed")
    historical(root, saved, saved["fingerprint"])
    config(root)


def bound(root: Path, path: Path) -> dict[str, Any]:
    return dict(
        file=str(path.resolve().relative_to(root.resolve())), sha256=digest(path)
    )


def checked(root: Path, item: dict[str, Any]) -> Path:
    path: Path = root / str(item["file"])
    if (
        path.is_symlink()
        or not path.resolve().is_relative_to(root.resolve())
        or digest(path) != item["sha256"]
    ):
        raise ArithmeticError("diagnostic prerequisite path/bytes changed")
    return path


def checks(root: Path, path: Path) -> dict[str, Any]:
    saved = json.loads(path.read_text())
    current = source(root, clean=False)
    rows = saved["checks"]
    ids = [(r["role"], r["minor"]) for r in rows]
    if (
        len(ids) != 6
        or set(ids)
        != {(r, v) for r in ("base", "optional", "hosted") for v in ("311", "312")}
        or saved["source_fingerprint"] != current["fingerprint"]
        or len({r["checked_commit"] for r in rows}) != 1
    ):
        raise ArithmeticError("complete exact-source six-role checks required")
    files.commit_sources(root, rows[0]["checked_commit"], current["sha256"])
    for row in rows:
        log = checked(root, row["log"]).read_text(encoding="utf-8-sig")
        if (
            row["status"] != "passed"
            or row["source_fingerprint"] != current["fingerprint"]
            or row["checked_commit"] not in log
            or "passed" not in log
            or row["python"] != ("3.11.17" if row["minor"] == "311" else "3.12.15")
        ):
            raise ArithmeticError("source check execution/runtime/log mismatch")
        if row["role"] == "hosted" and (
            row["conclusion"] != "success"
            or row["head_sha"] != row["checked_commit"]
            or type(row["run_id"]) is not int
            or type(row["job_id"]) is not int
        ):
            raise ArithmeticError("both exact-head hosted passes required")
    return bound(root, path)


def identity(row: dict[str, Any]) -> tuple[Any, ...]:
    if (
        any(
            type(row[k]) is not str or not row[k]
            for k in ("spot_file", "representation", "mixture")
        )
        or type(row["seed"]) is not int
    ):
        raise ValueError("strict diagnostic identity required")
    return tuple(row[k] for k in FIELDS)


def expected(root: Path, software: bool) -> set[tuple[Any, ...]]:
    design = config(root)
    return {
        tuple(c[k] for k in old_inputs.PATH) + (m,)
        for c in old_inputs.cases(root, "software" if software else "real")
        for m in design["mixtures"]
    }


def paths(root: Path, software: bool) -> tuple[Path, Path]:
    suffix = "software" if software else "real"
    return root / f"results/compact-sampled/{suffix}/own.json", root / (
        "results/compact-full-control/" + ("software/" if software else "") + "own.json"
    )


def replay_sources(root: Path, software: bool) -> dict[str, Any]:
    """All historical named code unchanged; old aggregate checkers stay intact."""
    c = config(root)
    sp, fp = paths(root, software)
    s = json.loads(sp.read_text())
    f = json.loads(fp.read_text())
    for original, fingerprint in (
        (s, c["sampled_source_fingerprint"]),
        (f, c["full_source_fingerprint"]),
    ):
        historical(root, original["source"], fingerprint)
        check_runtime(original["runtime"], real=not software)
    if (
        s["format"] != old_own.FORMAT
        or s["status"] != "completed"
        or s["failure"] is not None
        or s["scope"] != ("software" if software else "real")
        or s["protocol_sha256"] != old_inputs.SPEC_SHA
        or s["actual_admission"] is not False
        or s["fresh_global_admission"] is not False
        or s["new_agent_default"] is not False
        or s["sampled_training_performed"] is not True
        or s["new_holdem_training_performed"] is not (not software)
        or s["trajectory_collection"] != "completed_36_paths"
    ):
        raise ArithmeticError("complete original sampled collection required")
    sampled_clock(sp, "software-own" if software else "study")
    captured = old_own.gather(root, sp.parent, s, score=True)
    if any(canonical(value) != canonical(s[k]) for k, value in captured.items()):
        raise ArithmeticError(
            "original sampled raw-state/journal/metric replay changed"
        )
    old_own.check_batch(s, captured)
    sn = sp.with_name("native.json")
    native = json.loads(sn.read_text())
    historical(root, native["source"], c["sampled_source_fingerprint"])
    sampled_clock(sn, "software-native" if software else "audit")
    sampled_native(s, native, digest(sp))
    files.inventory(f, contract(root))
    full_clock(fp, "software-own" if software else "own")
    lookup = old_inputs.game_contexts(root, "software" if software else "real")
    count = 0
    for row in f["rows"]:
        context = lookup[row["spot_file"], row["representation"]]
        raw = files.load_snapshot(fp.parent / "snapshots", row["snapshot"])
        actual = files.decode(context, raw)
        scalar = {
            k: v
            for k, v in actual.items()
            if k not in {"format", "actions", "policy", "regrets", "strategy_sum"}
        }
        if canonical(scalar) != canonical(
            {k: v for k, v in row.items() if k != "snapshot"}
        ):
            raise ArithmeticError("original full checkpoint replay changed")
        count += 1
    fn = fp.with_name("native.json")
    n = json.loads(fn.read_text())
    historical(root, n["source"], c["full_source_fingerprint"])
    full_clock(fn, "software-native" if software else "native")
    full_native(f, n, digest(fp))
    if not software:
        prior_full(root)
        rp = sp.with_name("result.json")
        result = json.loads(rp.read_text())
        sampled_clock(rp, "report")
        historical(root, result["source"], c["sampled_source_fingerprint"])
        if (
            result["status"] != "completed"
            or result["failure"] is not None
            or result["actual_admission"] is not False
            or result["fresh_global_admission"] is not False
            or [k for k, v in result["assessment"]["checks"].items() if not v]
            != ["accuracy"]
            or any(
                digest(checked(root, item)) != item["sha256"]
                for item in result["inputs"]
            )
        ):
            raise ArithmeticError(
                "complete audited sampled failure must remain visible"
            )
    return dict(
        sampled_states=108,
        sampled_readouts=324,
        full_profiles=count,
        native_inputs_checked=True,
        source_files=[bound(root, p) for p in (sp, sn, fp, fn)],
        new_training=False,
    )


@dataclass(frozen=True)
class Pair:
    context: Context
    seed: int
    sampled: FloatArray
    full: FloatArray
    origins: dict[str, Any]
    sampled_metrics: dict[str, Any]
    full_metrics: dict[str, Any]


def pairs(root: Path, software: bool) -> list[Pair]:
    c = config(root)
    sp, fp = paths(root, software)
    s = json.loads(sp.read_text())
    f = json.loads(fp.read_text())
    lookup = old_inputs.game_contexts(root, "software" if software else "real")
    full = {}
    full_rows = {}
    for row in f["rows"]:
        if row["iteration"] != c["full_selector"]["iteration"]:
            continue
        key = row["spot_file"], row["representation"]
        raw = files.load_snapshot(fp.parent / "snapshots", row["snapshot"])
        policy = np.asarray(raw["policy"], dtype=np.float64)
        lookup[key].scoring.partition.validate_policy(policy)
        policy.flags.writeable = False
        full[key] = policy
        full_rows[key] = row
    originals = {
        (r["spot_file"], r["representation"], r["seed"]): r
        for r in s["rows"]
        if r["work_checkpoint"]
        == (10000 if software else c["sampled_selector"]["work_checkpoint"])
        and r["readout"] == "linear"
    }
    result = []
    for point in s["points"]:
        if point["work_checkpoint"] != (
            10000 if software else c["sampled_selector"]["work_checkpoint"]
        ):
            continue
        key = point["spot_file"], point["representation"]
        context = lookup[key]
        state = files.load_snapshot(sp.parent / "states", point["state_receipt"])
        warm = files.load_snapshot(sp.parent / "warms", point["warm_receipt"])
        _, policies = decode(
            context,
            state,
            warm,
            c["sampled_source_fingerprint"],
            "software" if software else "real",
        )
        policy = policies["linear"]
        policy.flags.writeable = False
        result.append(
            Pair(
                context,
                point["seed"],
                policy,
                full[key],
                dict(
                    sampled_state=point["state_receipt"],
                    warm=point["warm_receipt"],
                    full_state=full_rows[key]["snapshot"],
                ),
                originals[*key, point["seed"]],
                full_rows[key]["metrics"],
            )
        )
    if len(full) != 12 or len(result) != 36:
        raise ArithmeticError("all48 declared final sources required")
    return result
