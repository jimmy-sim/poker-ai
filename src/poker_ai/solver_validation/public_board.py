"""Post-training native value/BR and cross-play audit, never own learner input."""

import json
import math
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

from poker_ai.postflop.game import load_spot
from poker_ai.postflop.public_evidence import final_snapshots, policy_label, replay
from poker_ai.postflop.public_metrics import IDENTITY
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.reference import Reference
from poker_ai.validation.five_card import source_provenance


def audit(root: Path, config_path: Path, path: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain previous native audit; choose a new output")
    started = time.perf_counter()
    report, snapshots, own = replay(root, path, check_checkpoints=True)
    if json.loads(config_path.read_text()) != report["config"]:
        raise ArithmeticError("audit config differs from own study")
    by_id = {tuple(r[k] for k in IDENTITY): r for r in report["rows"]}
    comparisons = []
    crossplays = []
    for filename in report["config"]["development_spots"]:
        tree = SpotTree.build(load_spot(root / filename))
        reference = Reference(tree)
        selected = [p for p in snapshots if p["spot_file"] == filename]
        for snapshot in selected:
            row = by_id[tuple(snapshot[k] for k in IDENTITY)]
            policy = tuple(tuple(float(v) for v in p) for p in snapshot["policy"])
            value, epsilon = reference.value(policy), reference.exploitability(policy)
            comparisons.append(
                {
                    **{k: snapshot[k] for k in IDENTITY},
                    "native_value_chips": value,
                    "native_exploitability_chips": epsilon,
                    "value_error_chips": abs(value - row["value_player_zero_chips"]),
                    "exploitability_error_chips": abs(
                        epsilon - row["exploitability_chips"]
                    ),
                }
            )
        final = {
            policy_label(p): p["policy"]
            for p in final_snapshots(selected, report["config"])
        }
        game_crossplay = [r for r in own["crossplay"] if r["spot_file"] == filename]
        values = {}
        for row in game_crossplay:
            first, second = final[row["first"]], final[row["second"]]
            mixed = tuple(
                tuple(a if owner == 0 else b)
                for a, b, owner in zip(first, second, tree.owners, strict=True)
            )
            values[row["first"], row["second"]] = reference.value(mixed)
        for row in game_crossplay:
            value = values[row["first"], row["second"]]
            balanced = (value - values[row["second"], row["first"]]) / 2
            crossplays.append(
                {
                    "spot_file": filename,
                    "first": row["first"],
                    "second": row["second"],
                    "native_value_player_zero_chips": value,
                    "native_seat_balanced_first_chips": balanced,
                    "value_error_chips": abs(value - row["value_player_zero_chips"]),
                    "balanced_error_chips": abs(
                        balanced - row["seat_balanced_first_chips"]
                    ),
                }
            )
        print(f"public-board native audit: {tree.spot.name}", flush=True)
    tolerance = report["config"]["limits"]["independent_value_br_tolerance_chips"]
    errors = [
        r[k]
        for r in comparisons
        for k in ("value_error_chips", "exploitability_error_chips")
    ]
    errors += [
        r[k] for r in crossplays for k in ("value_error_chips", "balanced_error_chips")
    ]
    passed = (
        len(comparisons) == len(snapshots)
        and len(crossplays) == len(own["crossplay"])
        and all(math.isfinite(v) and 0 <= v <= tolerance for v in errors)
    )
    result = {
        "status": "passed" if passed else "failed",
        "input_sha256": digest(path),
        "tolerance_chips": tolerance,
        "comparisons": comparisons,
        "crossplay": crossplays,
        "checkpoint_receipts_checked": own["checkpoint_receipts_checked"],
        "maximum_own_replay_error_chips": own["maximum_own_replay_error_chips"],
        "seconds": time.perf_counter() - started,
        "environment": runtime_environment(),
        "reference": {
            "name": "OpenSpiel",
            "version": version("open-spiel"),
            "license": "Apache-2.0",
        },
        "source": source_provenance(
            root, config_path, entrypoints=("scripts/audit_public_boards.py",)
        ),
        "limits": (
            "native solver math on shared own EFG mechanics; "
            "comparison-only output, never own training input"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    )
    return result
