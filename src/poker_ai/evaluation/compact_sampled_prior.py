"""Authenticate unchanged historical full-control evidence under added source.

The original full runner's aggregate-fingerprint rule stays untouched. This new
adapter checks EVERY named historical dependency as an unchanged subset and Git
blob, then replays all raw states/metrics and the independent scalar audit.
"""

import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation.compact_sampled_inputs import protocol
from poker_ai.postflop import compact_full_artifacts as old
from poker_ai.postflop.compact_full_clock import measurement
from poker_ai.postflop.compact_full_context import contexts
from poker_ai.postflop.compact_full_native_checks import validate
from poker_ai.postflop.learning_artifacts import canonical, sha
from poker_ai.postflop.public_range_acceptance import assess_full
from poker_ai.postflop.public_range_definition import contract
from poker_ai.postflop.river_study import digest

FOLDER = "results/compact-full-control"


def historical_source(root: Path, saved: dict[str, Any], fingerprint: str) -> None:
    if saved["fingerprint"] != fingerprint or sha(saved["sha256"]) != fingerprint:
        raise ArithmeticError("historical full source map/fingerprint changed")
    old.commit_sources(root, saved["git_commit"], saved["sha256"])


def verify(root: Path) -> dict[str, Any]:
    config = protocol(root)
    folder = root / FOLDER
    own_path, native_path = folder / "own.json", folder / "native.json"
    own = json.loads(own_path.read_text())
    native = json.loads(native_path.read_text())
    result = json.loads((folder / "result.json").read_text())
    fingerprint = config["prior_source_fingerprint"]
    for saved in (own, native, result):
        historical_source(root, saved["source"], fingerprint)
    old.inventory(own, contract(root))
    if own["software_only"] is not False:
        raise ArithmeticError("actual prior full-control study required")
    own_clock = measurement(own_path, "own")
    native_clock = measurement(native_path, "native")
    measurement(folder / "result.json", "report")
    validate(own, native, digest(own_path))
    layouts = {(r["spot_file"], r["representation"]): r for r in own["partitions"]}
    checked = 0
    for context in contexts(root, software=False):
        key = context.spot_file, context.representation
        if canonical(layouts[key]) != canonical(
            dict(**context.binding, **context.diagnostics)
        ):
            raise ArithmeticError("historical full layout changed")
        for row in own["rows"]:
            if (row["spot_file"], row["representation"]) != key:
                continue
            saved = old.load_snapshot(folder / "snapshots", row["snapshot"])
            actual = old.decode(context, saved)
            scalar = {
                k: v
                for k, v in actual.items()
                if k not in {"format", "actions", "policy", "regrets", "strategy_sum"}
            }
            if canonical(scalar) != canonical(
                {k: v for k, v in row.items() if k != "snapshot"}
            ):
                raise ArithmeticError(
                    "historical full manifest/raw checkpoint mismatch"
                )
            checked += 1
    rows = [
        dict(
            **{k: r[k] for k in (*old.IDENTITY, "context_sha256", "total_node_work")},
            **r["metrics"],
        )
        for r in own["rows"]
    ]
    assessment = assess_full(
        rows,
        own["partitions"],
        native["comparisons"],
        contract(root),
        elapsed_seconds=own_clock["seconds"],
        audit_seconds=native_clock["seconds"],
    )
    if (
        checked != 72
        or canonical(assessment) != canonical(result["assessment"])
        or assessment["thresholds_passed"] is not True
        or result["full_control_admission_passed"] is not True
        or result["actual_admission"] is not True
        or result["fresh_global_admission"] is not False
        or result["own_sha256"] != digest(own_path)
        or result["native_sha256"] != digest(native_path)
    ):
        raise ArithmeticError("authenticated full-control prerequisite failed")
    check_receipt = json.loads((folder / "checks.json").read_text())
    ids = [(r["role"], r["minor"]) for r in check_receipt["checks"]]
    if (
        len(ids) != 6
        or len(set(ids)) != 6
        or set(ids)
        != {(r, v) for r in ("base", "optional", "hosted") for v in ("311", "312")}
        or check_receipt["source_fingerprint"] != fingerprint
    ):
        raise ArithmeticError("historical checked-source cohort incomplete")
    for row in check_receipt["checks"]:
        path = root / row["log"]["file"]
        if (
            not path.resolve().is_relative_to(root.resolve())
            or digest(path) != row["log"]["sha256"]
            or row["status"] != "passed"
            or row["source_fingerprint"] != fingerprint
        ):
            raise ArithmeticError("historical source-check log/receipt changed")
        old.commit_sources(root, row["checked_commit"], own["source"]["sha256"])
    return dict(
        status="authenticated_full_control_pass_unchanged_dependencies",
        historical_source_fingerprint=fingerprint,
        profiles_checked=checked,
        own_sha256=digest(own_path),
        native_sha256=digest(native_path),
        result_sha256=digest(folder / "result.json"),
        assessment=assessment,
        sampled_training_performed=False,
        scope=(
            "Prior full stage only; new sampled source/proof/forecast/"
            "admission still required"
        ),
    )
