"""Saved range-mass response diagnosis across every final seed and full control."""

import gzip
import json
import math
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.range_admission_report import checked_audit as check_full_audit
from poker_ai.postflop.range_protocol import CONTROLS, build_representation_control
from poker_ai.postflop.range_replay import replay as full_replay
from poker_ai.postflop.range_sampled import replay as sampled_replay
from poker_ai.postflop.range_sampled_report import checked_audit as check_sampled_audit
from poker_ai.postflop.reply_diagnosis import analyse
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

FORMAT = "poker-ai-range-reply-diagnosis-v1"
DETAIL_FORMAT = "poker-ai-range-reply-details-v1"
IDENTITY = ("spot_file", "representation", "training", "seed")
ENTRYPOINTS = (
    "scripts/diagnose_range_replies.py",
    "scripts/audit_range_replies.py",
    "scripts/report_range_replies.py",
    "scripts/inspect_range_reply.py",
)


def validate_config(config: dict[str, Any]) -> None:
    if (
        type(config["schema_version"]) is not int
        or config["schema_version"] != 1
        or len(config["inputs_sha256"]) != 6
        or not {
            config[k]
            for k in ("sampled_report", "sampled_audit", "full_report", "full_audit")
        }.issubset(config["inputs_sha256"])
        or config["representations"] != CONTROLS
        or not config["spot_files"]
        or len(set(config["spot_files"])) != len(config["spot_files"])
        or not config["sampled_seeds"]
        or config["sampled_seeds"] != sorted(set(config["sampled_seeds"]))
        or any(type(v) is not int or v < 1 for v in config["sampled_seeds"])
        or any(
            type(config[k]) is not int or config[k] < 1
            for k in ("sampled_node_work", "full_iteration", "maximum_seconds")
        )
        or type(config["top_groups"]) is not int
        or not 1 <= config["top_groups"] <= 20
        or type(config["examples_per_group"]) is not int
        or not 2 <= config["examples_per_group"] <= 8
        or type(config["tolerance_chips"]) not in (int, float)
        or not math.isfinite(config["tolerance_chips"])
        or not 0 < config["tolerance_chips"] <= 1e-9
        or config["tie_rule"]
        != "first legal maximizer, no approximate tie substitution"
        or config["aggregation"]
        != (
            "arithmetic means of additive components; every seed retained; "
            "median total separate"
        )
    ):
        raise ValueError("invalid fixed range-reply diagnosis")


def expected_grid(config: dict[str, Any]) -> set[tuple[Any, ...]]:
    return {
        (p, e, t, s)
        for p in config["spot_files"]
        for e in config["representations"]
        for t, seeds in (("full", [None]), ("sampled", config["sampled_seeds"]))
        for s in seeds
    }


def check_source(root: Path, source: dict[str, Any]) -> None:
    if source["dirty"] is not False:
        raise ArithmeticError("diagnosis/audit requires originally clean source")
    for name, sha in source["sha256"].items():
        if digest(root / name) != sha:
            raise ArithmeticError("range-reply source/config changed")


def compare(actual: Any, saved: Any) -> float:
    """Compare complete nested receipts; float roundoff only, exact typed IDs."""
    if isinstance(actual, float):
        if (
            type(saved) not in (int, float)
            or not math.isfinite(actual)
            or not math.isfinite(saved)
        ):
            raise ArithmeticError("nonfinite/invalid diagnosis float")
        return float(abs(actual - saved))
    if isinstance(actual, dict):
        if not isinstance(saved, dict) or actual.keys() != saved.keys():
            raise ArithmeticError("diagnosis fields changed")
        return max((compare(v, saved[k]) for k, v in actual.items()), default=0.0)
    if isinstance(actual, (list, tuple)):
        if not isinstance(saved, (list, tuple)) or len(actual) != len(saved):
            raise ArithmeticError("diagnosis sequence changed")
        return max(
            (compare(a, b) for a, b in zip(actual, saved, strict=True)), default=0.0
        )
    if type(actual) is not type(saved) or actual != saved:
        raise ArithmeticError("diagnosis identity/count changed")
    return 0.0


def check_bound_inputs(root: Path, config: dict[str, Any]) -> None:
    for name, sha in config["inputs_sha256"].items():
        if digest(root / name) != sha:
            raise ArithmeticError("pinned diagnosis input changed")


def load_inputs(
    root: Path, config: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    validate_config(config)
    check_bound_inputs(root, config)
    records = []
    original: dict[str, Any] = {}
    for training, loader, checker in (
        ("sampled", sampled_replay, check_sampled_audit),
        ("full", full_replay, check_full_audit),
    ):
        path = root / config[training + "_report"]
        report, policies, _ = loader(root, path)
        if original and report["config"] != original["config"]:
            raise ArithmeticError("full/sample protocol mismatch")
        bundle_key = (
            "own_receipts_file" if training == "sampled" else "own_policies_file"
        )
        hash_key = (
            "own_receipts_sha256" if training == "sampled" else "own_policies_sha256"
        )
        bundle = str(Path(config[training + "_report"]).parent / report[bundle_key])
        if config["inputs_sha256"].get(bundle) != report[hash_key]:
            raise ArithmeticError("own bundle not pinned in diagnosis config")
        audit = json.loads((root / config[training + "_audit"]).read_text())
        checker(path, report, audit)
        check_source(root, audit["source"])
        if audit["reference"] != {
            "name": "OpenSpiel",
            "version": "2.0.2",
            "license": "Apache-2.0",
        }:
            raise ArithmeticError("input reference changed")
        if (
            report["config"]["representations"] != config["representations"]
            or report["config"]["spot_files"] != config["spot_files"]
        ):
            raise ArithmeticError("diagnosis game/control selection changed")
        if training == "sampled":
            later = report["config"]["later_sampled"]
            if (
                later["seeds"] != config["sampled_seeds"]
                or later["node_work_checkpoints"][-1] != config["sampled_node_work"]
            ):
                raise ArithmeticError("diagnosis sampled selection changed")
        elif report["config"]["full_tree_checkpoints"][-1] != config["full_iteration"]:
            raise ArithmeticError("diagnosis full iteration changed")
        for snapshot in policies:
            if (
                training == "sampled"
                and snapshot["node_work_checkpoint"] != config["sampled_node_work"]
            ) or (
                training == "full" and snapshot["iteration"] != config["full_iteration"]
            ):
                continue
            row = next(
                r
                for r in report["rows"]
                if r["spot_file"] == snapshot["spot_file"]
                and r["representation"] == snapshot["representation"]
                and (
                    training == "full"
                    and r["iteration"] == config["full_iteration"]
                    or training == "sampled"
                    and r["seed"] == snapshot["seed"]
                    and r["node_work_checkpoint"] == config["sampled_node_work"]
                )
            )
            records.append(
                {
                    "spot_file": snapshot["spot_file"],
                    "representation": snapshot["representation"],
                    "training": training,
                    "seed": snapshot["seed"] if training == "sampled" else None,
                    "range_context_sha256": snapshot["range_context_sha256"],
                    "policy": snapshot["policy"],
                    "exploitability_chips": row["exploitability_chips"],
                }
            )
        original = report
    ids = [tuple(r[k] for k in IDENTITY) for r in records]
    if len(ids) != len(set(ids)) or set(ids) != expected_grid(config):
        raise ArithmeticError("incomplete input diagnosis grid")
    return original, records


def compute(
    root: Path, config: dict[str, Any], deadline: Deadline | None = None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    original, policies = load_inputs(root, config)
    model = CardAbstraction.load(root / original["config"]["model"])
    cases, details = [], []
    for filename in config["spot_files"]:
        if deadline is not None:
            deadline.check()
        source = SpotTree.build(load_spot(root / filename))
        exact = MatrixTree.build(source)
        for name in config["representations"]:
            abstract = build_representation_control(source, name, model)
            for saved in policies:
                if saved["spot_file"] != filename or saved["representation"] != name:
                    continue
                if deadline is not None:
                    deadline.check()
                policy = exact.dense_exact(tuple(tuple(r) for r in saved["policy"]))
                case, detail = analyse(
                    exact,
                    abstract,
                    policy,
                    top=config["top_groups"],
                    examples=config["examples_per_group"],
                    tolerance=config["tolerance_chips"],
                )
                if (
                    abs(
                        case["exact_exploitability_chips"]
                        - saved["exploitability_chips"]
                    )
                    > config["tolerance_chips"]
                ):
                    raise ArithmeticError("diagnosis changes saved exploitability")
                identity = {
                    **{k: saved[k] for k in IDENTITY},
                    "range_context_sha256": saved["range_context_sha256"],
                }
                cases.append({**identity, **case})
                details.append({**identity, **detail})
                print(
                    f"range reply: {source.spot.name}/{name}/"
                    f"{saved['training']}/{saved['seed']}",
                    flush=True,
                )
    return cases, details


def diagnose(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    started = time.perf_counter()
    config = json.loads(config_path.read_text())
    validate_config(config)
    deadline = Deadline(config["maximum_seconds"])
    deadline.started = started
    sidecar = output.with_name(output.stem + "-details.json.gz")
    if output.exists() or sidecar.exists():
        raise FileExistsError("retain previous diagnosis")
    source = source_provenance(root, config_path, entrypoints=ENTRYPOINTS)
    if source["dirty"] is not False:
        raise ValueError("publish checked code; use clean source")
    started_at = datetime.now(UTC).isoformat()
    cases, details = compute(root, config, deadline)
    deadline.check()
    check_source(root, source)
    check_bound_inputs(root, config)
    output.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_bytes(
        gzip.compress(
            json.dumps(
                {"format": DETAIL_FORMAT, "cases": details}, allow_nan=False
            ).encode(),
            mtime=0,
        )
    )
    elapsed = time.perf_counter() - started
    result = {
        "format": FORMAT,
        "status": "completed"
        if elapsed <= config["maximum_seconds"]
        else "over_budget",
        "config": config,
        "source": source,
        "environment": runtime_environment(),
        "started_at_utc": started_at,
        "seconds": elapsed,
        "cases": cases,
        "details_file": sidecar.name,
        "details_sha256": digest(sidecar),
        "training_performed": False,
        "fresh_global_admission": False,
        "scope": config["scope"],
    }
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return result


def checked_details(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report: dict[str, Any] = json.loads(path.read_text())
    validate_config(report["config"])
    json.dumps(report, allow_nan=False)
    if (
        report["format"] != FORMAT
        or report["status"] != "completed"
        or type(report["seconds"]) not in (int, float)
        or not 0 <= report["seconds"] <= report["config"]["maximum_seconds"]
        or report["training_performed"] is not False
        or report["fresh_global_admission"] is not False
    ):
        raise ArithmeticError("incomplete/changed diagnosis stage")
    sidecar = path.parent / report["details_file"]
    if digest(sidecar) != report["details_sha256"]:
        raise ArithmeticError("diagnosis details hash changed")
    payload = json.loads(gzip.decompress(sidecar.read_bytes()))
    json.dumps(payload, allow_nan=False)
    ids = [tuple(c[k] for k in IDENTITY) for c in report["cases"]]
    other = [tuple(c[k] for k in IDENTITY) for c in payload["cases"]]
    if (
        payload["format"] != DETAIL_FORMAT
        or len(ids) != len(set(ids))
        or ids != other
        or set(ids) != expected_grid(report["config"])
    ):
        raise ArithmeticError("incomplete/duplicate diagnosis grid")
    for c in report["cases"]:
        if c["training"] == "sampled" and type(c["seed"]) is not int:
            raise ArithmeticError("invalid diagnosis seed")
    return report, payload["cases"]


def replay(
    root: Path, path: Path
) -> tuple[dict[str, Any], list[dict[str, Any]], float]:
    report, details = checked_details(path)
    check_source(root, report["source"])
    cases, actual = compute(root, report["config"])
    error = max(compare(cases, report["cases"]), compare(actual, details))
    if error > report["config"]["tolerance_chips"]:
        raise ArithmeticError("nested response replay changed")
    check_source(root, report["source"])
    check_bound_inputs(root, report["config"])
    return report, details, error
