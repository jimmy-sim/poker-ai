"""Independent fixed-policy values and response checks; no native actions exported."""

import json
import math
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.policy_swaps import CROSS, HYBRID, replay
from poker_ai.postflop.range_protocol import build_representation_control
from poker_ai.postflop.range_reply import check_source
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.reference import Reference
from poker_ai.solver_validation.reply_diagnosis import partition_source
from poker_ai.validation.five_card import source_provenance


def audit(root: Path, config_path: Path, path: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain native policy-swap audit")
    started = time.perf_counter()
    source_record = source_provenance(
        root, config_path, entrypoints=("scripts/audit_policy_swaps.py",)
    )
    if source_record["dirty"] is not False:
        raise ValueError("publish own swaps before audit")
    report, details, error = replay(root, path)
    config = report["config"]
    if json.loads(config_path.read_text()) != config:
        raise ArithmeticError("swap audit config changed")
    previous = json.loads((root / config["previous_config"]).read_text())
    full = json.loads((root / previous["full_report"]).read_text())
    model = CardAbstraction.load(root / full["config"]["model"])
    cross_rows, reply_rows = [], []
    for filename in config["spot_files"]:
        tree = SpotTree.build(load_spot(root / filename))
        exact = Reference(tree)
        # Match policy arrays by exact decision infos; native exporter is independent.
        from poker_ai.postflop.matrix import MatrixTree

        matrix = MatrixTree.build(tree)
        for name in config["representations"]:
            abstract = build_representation_control(tree, name, model)
            limited = Reference(partition_source(abstract))
            first = np.unique(abstract.exact_to_abstract, return_index=True)[1]
            selected = [
                d
                for d in details
                if d["spot_file"] == filename and d["representation"] == name
            ]
            policies = {
                "full": next(
                    d["baseline_policy"] for d in selected if d["combination"] == "FF"
                ),
                **{
                    str(s): next(
                        d["baseline_policy"]
                        for d in selected
                        if d["seed"] == s and d["combination"] == "SS"
                    )
                    for s in config["seeds"]
                },
            }
            for row in report["crossplay"]:
                if row["spot_file"] != filename or row["representation"] != name:
                    continue
                # Use source ownership and raw tuple rows, not own seat_policy/value.
                baseline = tuple(
                    tuple(
                        float(v)
                        for v in policies[
                            row["first"] if owner == 0 else row["second"]
                        ][i]
                    )
                    for i, owner in enumerate(tree.owners)
                )
                value = exact.value(baseline)
                cross_rows.append(
                    {
                        **{k: row[k] for k in CROSS},
                        "range_context_sha256": row["range_context_sha256"],
                        "native_value_player_zero_chips": value,
                        "value_error_chips": abs(
                            value - row["value_player_zero_chips"]
                        ),
                    }
                )
            for detail in selected:
                baseline = tuple(
                    tuple(float(v) for v in r) for r in detail["baseline_policy"]
                )
                dense = matrix.dense_exact(baseline)
                restricted = tuple(
                    tuple(float(v) for v in dense[i, : len(menu)])
                    for i, menu in zip(first, abstract.actions, strict=True)
                )
                own = next(
                    c
                    for c in report["hybrids"]
                    if all(c[k] == detail[k] for k in HYBRID)
                )
                native_baseline = exact.value(baseline)
                for target in (0, 1):
                    row = {
                        **{k: detail[k] for k in HYBRID},
                        "target": target,
                        "range_context_sha256": detail["range_context_sha256"],
                        "native_baseline_value_chips": (1 if target == 0 else -1)
                        * native_baseline,
                    }
                    row["baseline_error_chips"] = abs(
                        row["native_baseline_value_chips"]
                        - own["responses"][target]["baseline_value_chips"]
                    )
                    for label, reference, policy in (
                        ("exact", exact, baseline),
                        ("restricted", limited, restricted),
                    ):
                        native_policy = reference.native_policy(policy)
                        response = reference.pyspiel.TabularBestResponse(
                            reference.game, target, native_policy
                        )
                        value = float(response.value(""))
                        profile = tuple(
                            tuple(float(v) for v in r)
                            for r in detail["responses"][target][
                                label + "_reply_profile"
                            ]
                        )
                        achieved = (1 if target == 0 else -1) * exact.value(profile)
                        row.update(
                            {
                                label + "_native_value_chips": value,
                                label + "_achieved_value_chips": achieved,
                                label + "_root_error_chips": abs(
                                    value
                                    - own["responses"][target][
                                        label + "_reply_value_chips"
                                    ]
                                ),
                                label + "_achieved_error_chips": abs(value - achieved),
                            }
                        )
                    reply_rows.append(row)
            print(f"native policy swaps: {tree.spot.name}/{name}", flush=True)
    errors = [r["value_error_chips"] for r in cross_rows] + [
        v for r in reply_rows for k, v in r.items() if k.endswith("error_chips")
    ]
    tolerance = config["tolerance_chips"]
    passed = (
        len(cross_rows) == len(report["crossplay"])
        and len(reply_rows) == 2 * len(report["hybrids"])
        and all(math.isfinite(v) and 0 <= v <= tolerance for v in errors)
    )
    check_source(root, source_record)
    result = {
        "status": "passed" if passed else "failed",
        "input_sha256": digest(path),
        "crossplay": cross_rows,
        "responses": reply_rows,
        "maximum_native_error_chips": max(errors),
        "maximum_own_replay_error_chips": error,
        "reference": {
            "name": "OpenSpiel",
            "version": version("open-spiel"),
            "license": "Apache-2.0",
        },
        "source": source_record,
        "environment": runtime_environment(),
        "seconds": time.perf_counter() - started,
        "scope": (
            "native crossed/hybrid values and exact/restricted roots/achieved "
            "own profiles; shared mechanics; no reference actions exported"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return result
