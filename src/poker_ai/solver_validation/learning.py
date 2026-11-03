"""Independent numerical checks of frozen OWN postflop training outputs only."""

import gzip
import hashlib
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning import POLICY_FORMAT
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.reference import Reference
from poker_ai.validation.five_card import source_provenance


def validate_report(root: Path, path: Path, output: Path) -> dict[str, Any]:
    report = json.loads(path.read_text())
    if report["status"] != "completed":
        raise ValueError("cannot validate a partial own training report")
    policy_path = path.parent / report["own_policies_file"]
    if (
        hashlib.sha256(policy_path.read_bytes()).hexdigest()
        != report["own_policies_sha256"]
    ):
        raise ArithmeticError("own frozen policy artifact changed")
    policies = json.loads(gzip.decompress(policy_path.read_bytes()))
    if policies.get("format") != POLICY_FORMAT:
        raise ValueError("requires an own postflop policy format")

    def identity(row: dict[str, Any]) -> tuple[Any, ...]:
        return tuple(
            row[k] for k in ("spot", "encoding", "method", "seed", "iteration")
        )

    own = {identity(r): r for r in report["rows"]}
    frozen = {identity(p): p for p in policies["policies"]}
    if (
        own.keys() != frozen.keys()
        or len(own) != len(report["rows"])
        or len(frozen) != len(policies["policies"])
    ):
        raise ArithmeticError("missing/duplicate own policy snapshot")
    tolerance = report["config"]["independent_tolerance"]
    if not 0 < tolerance <= 1e-8:
        raise ValueError("invalid independent-check tolerance")
    started = time.perf_counter()
    comparisons = []
    for filename, digest in report["spot_sha256"].items():
        spot_path = root / filename
        if hashlib.sha256(spot_path.read_bytes()).hexdigest() != digest:
            raise ArithmeticError("own game definition changed before validation")
        tree = SpotTree.build(load_spot(spot_path))
        reference = Reference(tree)
        for key, snapshot in frozen.items():
            if snapshot["spot"] != tree.spot.name:
                continue
            policy = tuple(tuple(float(p) for p in row) for row in snapshot["policy"])
            value = reference.value(policy)
            epsilon = reference.exploitability(policy)
            row = own[key]
            comparison = {
                k: snapshot[k]
                for k in ("spot", "encoding", "method", "seed", "iteration")
            }
            comparison.update(
                {
                    "own_native_value_error": abs(
                        row["value_player_zero_chips"] - value
                    ),
                    "own_native_exploitability_error": abs(
                        row["exploitability_chips"] - epsilon
                    ),
                    "native_exploitability_chips": epsilon,
                }
            )
            if (
                snapshot["encoding"] == "exact"
                and snapshot["method"] == "full_cfr_plus"
            ):
                reference.train_to(snapshot["iteration"])
                other = reference.policy()
                reference_epsilon = reference.exploitability(other)
                comparison.update(
                    {
                        "matched_reference_exploitability_chips": reference_epsilon,
                        "matched_exploitability_error_chips": abs(
                            epsilon - reference_epsilon
                        ),
                        "matched_policy_mean_row_l1": float(
                            np.mean(
                                [
                                    sum(abs(a - b) for a, b in zip(x, y, strict=True))
                                    for x, y in zip(policy, other, strict=True)
                                ]
                            )
                        ),
                    }
                )
            comparisons.append(comparison)
        print(
            f"independently checked: {tree.spot.name}, frozen own snapshots", flush=True
        )

    def passed(row: dict[str, Any]) -> bool:
        return bool(
            row["own_native_value_error"] <= tolerance
            and row["own_native_exploitability_error"] <= tolerance
            and row.get("matched_exploitability_error_chips", 0) <= tolerance
        )

    status = (
        "passed" if comparisons and all(passed(r) for r in comparisons) else "failed"
    )
    result = {
        "status": status,
        "format": "poker-ai-reference-comparison-v1",
        "input_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "source": source_provenance(
            root,
            root / "configs/holdem-learning.json",
            entrypoints=("scripts/validate_postflop_learning.py",),
        ),
        "environment": runtime_environment(),
        "seconds": time.perf_counter() - started,
        "tolerance_chips": tolerance,
        "comparisons": comparisons,
        "limits": (
            "independent native solver/value/BR, shared own game "
            "mechanics/export; comparison-only numbers, "
            "never an agent strategy input"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return result
