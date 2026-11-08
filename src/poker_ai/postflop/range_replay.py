"""Portable numerical replay adapter; frozen historical source is unchanged."""

import math
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning import decision_mass, score
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.public_metrics import collision_summary
from poker_ai.postflop.range_admission import IDENTITY, checked_artifacts, verify_inputs
from poker_ai.postflop.range_protocol import build_representation_control
from poker_ai.postflop.tree import SpotTree

# Probabilities from BLAS reductions may differ in final bits across architectures.
# Counts, row/key/table bytes and contexts must still match exactly, including type.
REACH_FIELDS = {
    "uniform_decision_reach_any_collision",
    "uniform_decision_reach_public_collision",
    "uniform_decision_reach_private_collision",
}
REACH_TOLERANCE = 1e-12


def check_diagnostics(actual: dict[str, Any], saved: dict[str, Any]) -> None:
    for name, value in actual.items():
        expected = saved[name]
        if name in REACH_FIELDS:
            if (
                type(expected) not in (int, float)
                or not math.isfinite(expected)
                or not math.isfinite(value)
                or abs(value - expected) > REACH_TOLERANCE
            ):
                raise ArithmeticError(f"reach diagnostic changed: {name}")
        elif type(expected) is not type(value) or expected != value:
            raise ArithmeticError(f"exact diagnostic changed: {name}")


def replay(
    root: Path, path: Path
) -> tuple[dict[str, Any], list[dict[str, Any]], float]:
    report, policies = checked_artifacts(path)
    verify_inputs(root, report)
    model = CardAbstraction.load(root / report["config"]["model"])
    lookup = {tuple(r[k] for k in IDENTITY): r for r in report["rows"]}
    maximum = 0.0
    for filename in report["config"]["spot_files"]:
        source = SpotTree.build(load_spot(root / filename))
        exact = MatrixTree.build(source)
        weights = decision_mass(exact, exact.normalize(exact.legal))
        for name in report["config"]["representations"]:
            tree = build_representation_control(source, name, model)
            diag = {**collision_summary(tree, weights), "tree_nodes": len(tree.player)}
            recorded = next(
                d
                for d in report["diagnostics"]
                if d["spot_file"] == filename and d["representation"] == name
            )
            check_diagnostics(diag, recorded)
            first = np.unique(tree.exact_to_abstract, return_index=True)[1]
            for snapshot in policies:
                if (
                    snapshot["spot_file"] != filename
                    or snapshot["representation"] != name
                ):
                    continue
                row = lookup[tuple(snapshot[k] for k in IDENTITY)]
                dense = exact.dense_exact(
                    tuple(tuple(v for v in r) for r in snapshot["policy"])
                )
                policy = dense[first]
                if not np.array_equal(
                    exact.dense_exact(tree.exact_policy(policy)), dense
                ):
                    raise ArithmeticError("admission policy violates shared rows")
                active = np.asarray(snapshot["average_active"], dtype=np.float64)
                if active.shape != (len(tree.keys),) or not np.all(
                    np.isin(active, (0, 1))
                ):
                    raise ArithmeticError("admission active-row mask invalid")
                actual = score(exact, tree, policy, active, weights)
                maximum = max(maximum, *[abs(actual[k] - row[k]) for k in actual])
                if row["total_node_work"] != 2 * row["iteration"] * len(tree.player):
                    raise ArithmeticError("admission work receipt invalid")
    if maximum > report["config"]["full_limits"]["independent_tolerance_chips"]:
        raise ArithmeticError("admission frozen-policy replay mismatch")
    verify_inputs(root, report)
    return report, policies, maximum
