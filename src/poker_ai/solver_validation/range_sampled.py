"""Independent post-training value/BR audit for own range-mass sampled study."""

import json
import math
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

from poker_ai.postflop.game import load_spot
from poker_ai.postflop.range_sampled import IDENTITY, replay, verify_inputs
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.reference import Reference
from poker_ai.validation.five_card import source_provenance


def audit(root: Path, config_path: Path, path: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain existing sampled audit")
    source = source_provenance(
        root, config_path, entrypoints=("scripts/audit_range_sampled.py",)
    )
    if source["dirty"] is not False:
        raise ValueError(
            "publish own evidence before native audit; use a clean worktree"
        )
    started = time.perf_counter()
    report, policies, own_error = replay(root, path)
    if json.loads(config_path.read_text()) != report["config"]:
        raise ArithmeticError("sampled audit config changed")
    by_id = {tuple(r[k] for k in IDENTITY): r for r in report["rows"]}
    rows = []
    for filename in report["config"]["spot_files"]:
        tree = SpotTree.build(load_spot(root / filename))
        reference = Reference(tree)
        for snapshot in policies:
            if snapshot["spot_file"] != filename:
                continue
            recorded = by_id[tuple(snapshot[k] for k in IDENTITY)]
            policy = tuple(tuple(float(v) for v in p) for p in snapshot["policy"])
            value, epsilon = reference.value(policy), reference.exploitability(policy)
            rows.append(
                {
                    **{k: snapshot[k] for k in IDENTITY},
                    "range_context_sha256": snapshot["range_context_sha256"],
                    "native_value_chips": value,
                    "native_exploitability_chips": epsilon,
                    "value_error_chips": abs(
                        value - recorded["value_player_zero_chips"]
                    ),
                    "exploitability_error_chips": abs(
                        epsilon - recorded["exploitability_chips"]
                    ),
                }
            )
        print(f"range-mass sampled native audit: {tree.spot.name}", flush=True)
    tolerance = report["config"]["full_limits"]["independent_tolerance_chips"]
    passed = len(rows) == len(policies) and all(
        math.isfinite(r[k]) and 0 <= r[k] <= tolerance
        for r in rows
        for k in ("value_error_chips", "exploitability_error_chips")
    )
    verify_inputs(root, report)
    result = {
        "status": "passed" if passed else "failed",
        "input_sha256": digest(path),
        "comparisons": rows,
        "tolerance_chips": tolerance,
        "maximum_own_replay_error_chips": own_error,
        "reference": {
            "name": "OpenSpiel",
            "version": version("open-spiel"),
            "license": "Apache-2.0",
        },
        "seconds": time.perf_counter() - started,
        "environment": runtime_environment(),
        "source": source,
        "scope": (
            "native value/BR on shared own exported mechanics; "
            "comparison-only, never learner input"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return result
