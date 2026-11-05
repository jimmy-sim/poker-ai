"""Independent post-training value/BR checks of frozen fresh-game policies."""

import json
import math
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

from poker_ai.postflop.fresh_cohort import verify_freeze
from poker_ai.postflop.fresh_learning import IDENTITY, checked_artifacts
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.reference import Reference
from poker_ai.validation.five_card import source_provenance


def audit(root: Path, config_path: Path, path: Path, output: Path) -> dict[str, Any]:
    config, freeze = verify_freeze(root, config_path)
    report, policies = checked_artifacts(path)
    if (
        report["config"] != config
        or report["spot_sha256"] != freeze["spot_sha256"]
        or report["freeze_sha256"] != digest(root / config["freeze_file"])
    ):
        raise ArithmeticError("fresh report differs from frozen procedure/inputs")
    started = time.perf_counter()
    comparisons = []
    for filename in report["spot_sha256"]:
        tree = SpotTree.build(load_spot(root / filename))
        reference = Reference(tree)
        for snapshot in policies:
            if snapshot["spot_file"] != filename:
                continue
            row = next(
                r for r in report["rows"] if all(r[k] == snapshot[k] for k in IDENTITY)
            )
            policy = tuple(tuple(float(v) for v in p) for p in snapshot["policy"])
            value, epsilon = reference.value(policy), reference.exploitability(policy)
            comparisons.append(
                {
                    **{k: row[k] for k in IDENTITY},
                    "native_value_chips": value,
                    "native_exploitability_chips": epsilon,
                    "value_error_chips": abs(value - row["value_player_zero_chips"]),
                    "exploitability_error_chips": abs(
                        epsilon - row["exploitability_chips"]
                    ),
                }
            )
        print(f"fresh native audit: {tree.spot.name}", flush=True)
    tolerance = config["independent_tolerance_chips"]
    passed = len(comparisons) == len(policies) and all(
        math.isfinite(r[k]) and 0 <= r[k] <= tolerance
        for r in comparisons
        for k in ("value_error_chips", "exploitability_error_chips")
    )
    result = {
        "status": "passed" if passed else "failed",
        "input_sha256": digest(path),
        "freeze_sha256": report["freeze_sha256"],
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
            root, config_path, entrypoints=("scripts/audit_fresh_games.py",)
        ),
        "limits": (
            "post-training native value/BR only, own shared exported mechanics; "
            "never learner input"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    )
    return result
