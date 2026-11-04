"""Post-training native value/BR audit; never feeds a strategy into training."""

import gzip
import json
import math
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

from poker_ai.postflop.game import load_spot
from poker_ai.postflop.river_study import FORMAT, POLICY_FORMAT, acceptance, digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.reference import Reference
from poker_ai.validation.five_card import source_provenance

IDENTITY = ("spot_file", "method", "seed", "iteration", "node_threshold")


def checked_artifacts(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report: dict[str, Any] = json.loads(path.read_text())
    if report["format"] != FORMAT or report["status"] != "completed":
        raise ValueError(
            "requires a complete river study, retaining partial data separately"
        )
    if (
        report["acceptance"] != acceptance(report["rows"], report["config"])
        or not report["acceptance"]["complete"]
    ):
        raise ArithmeticError("missing/duplicate or changed learning grid")
    policy_path = path.parent / report["own_policies_file"]
    if digest(policy_path) != report["own_policies_sha256"]:
        raise ArithmeticError("own policy artifact hash mismatch")
    frozen = json.loads(gzip.decompress(policy_path.read_bytes()))
    if frozen["format"] != POLICY_FORMAT:
        raise ValueError("expected own river policy artifact")
    rows = {tuple(r[k] for k in IDENTITY) for r in report["rows"]}
    policies = {tuple(r[k] for k in IDENTITY) for r in frozen["policies"]}
    if rows != policies or len(policies) != len(frozen["policies"]):
        raise ArithmeticError("missing/duplicate frozen own policy")
    return report, frozen["policies"]


def validate_study(root: Path, path: Path, output: Path) -> dict[str, Any]:
    """Evaluate every frozen policy with independent native value/best response.

    The EFG game mechanics remain this project's own; this cross-check concerns
    value/BR arithmetic and information-set alignment, not independent mechanics.
    OpenSpiel 2.0.2, Apache-2.0, is pinned/licensed in solver_validation.md.
    No reference solving or training is performed by this audit.
    """
    report, snapshots = checked_artifacts(path)
    started = time.perf_counter()
    tolerance = report["config"]["independent_tolerance_chips"]
    comparisons = []
    for filename, expected in report["spot_sha256"].items():
        if digest(root / filename) != expected:
            raise ArithmeticError("own spot changed before native audit")
        tree = SpotTree.build(load_spot(root / filename))
        reference = Reference(tree)
        for snapshot in snapshots:
            if snapshot["spot_file"] != filename:
                continue
            row = next(
                r for r in report["rows"] if all(r[k] == snapshot[k] for k in IDENTITY)
            )
            policy = tuple(tuple(float(v) for v in r) for r in snapshot["policy"])
            value, epsilon = reference.value(policy), reference.exploitability(policy)
            comparison = {k: row[k] for k in IDENTITY}
            comparison.update(
                native_value_chips=value,
                native_exploitability_chips=epsilon,
                value_error_chips=abs(value - row["value_player_zero_chips"]),
                exploitability_error_chips=abs(epsilon - row["exploitability_chips"]),
            )
            comparisons.append(comparison)
        print(f"native audit: {tree.spot.name}", flush=True)
    passed = all(
        math.isfinite(r[k]) and 0 <= r[k] <= tolerance
        for r in comparisons
        for k in ("value_error_chips", "exploitability_error_chips")
    ) and len(comparisons) == len(snapshots)
    result = {
        "status": "passed" if passed else "failed",
        "input_sha256": digest(path),
        "comparisons": comparisons,
        "tolerance_chips": tolerance,
        "seconds": time.perf_counter() - started,
        "environment": runtime_environment(),
        "reference": {
            "name": "OpenSpiel",
            "version": version("open-spiel"),
            "license": "Apache-2.0",
        },
        "source": source_provenance(
            root,
            root / "configs/river-integration-study.json",
            entrypoints=("scripts/audit_river_study.py",),
        ),
        "limits": (
            "comparison-only native value/BR, shared own game/export; "
            "no reference training input"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return result
