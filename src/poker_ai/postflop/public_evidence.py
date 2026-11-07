"""Offline replay of own strategies, collision diagnostics and cross-play values."""

from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning import (
    decision_mass,
    root_factory,
    sampled_average,
    score,
)
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.public_metrics import IDENTITY, collision_summary, mixed_value
from poker_ai.postflop.public_study import checked_artifacts, verify_inputs
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.sampling import load_learning_checkpoint
from poker_ai.postflop.tree import SpotTree


def policy_label(snapshot: dict[str, Any]) -> str:
    return f"{snapshot['encoding']}/{snapshot['method']}" + (
        "" if snapshot["seed"] is None else f"/{snapshot['seed']}"
    )


def final_snapshots(
    policies: list[dict[str, Any]], config: dict[str, Any]
) -> list[dict[str, Any]]:
    return [
        p
        for p in policies
        if (
            p["method"] == "full_cfr_plus"
            and p["iteration"] == config["full_tree_checkpoints"][-1]
        )
        or (
            p["method"] == "external"
            and p["node_threshold"] == config["sampled_node_checkpoints"][-1]
        )
    ]


def crossplay(
    tree: MatrixTree, snapshots: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    """All ordered final profiles, including self. Unit: net chips to player 0.

    Seat-balanced advantage of A over B is (V(A0,B1)-V(B0,A1))/2. This cancels
    seat advantage; it is antisymmetric and self-play is exactly zero by design.
    It measures matchups of frozen own policies, not best response strength.
    """
    arrays = [
        tree.dense_exact(tuple(tuple(v for v in row) for row in p["policy"]))
        for p in snapshots
    ]
    values = [[mixed_value(tree, a, b) for b in arrays] for a in arrays]
    return [
        {
            "spot_file": tree.source.spot.name,
            "first": policy_label(a),
            "second": policy_label(b),
            "value_player_zero_chips": values[i][j],
            "seat_balanced_first_chips": (values[i][j] - values[j][i]) / 2,
            "seat_balanced_first_pot": (values[i][j] - values[j][i])
            / (2 * tree.source.spot.pot),
        }
        for i, a in enumerate(snapshots)
        for j, b in enumerate(snapshots)
    ]


def replay(
    root: Path, path: Path, *, check_checkpoints: bool = False
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    """Recompute every policy/coverage/diagnostic; optionally verify core receipts.

    Saved exact policies must be constant on their original abstract rows. Saved
    active/visit masks permit coverage replay without ignored large checkpoints.
    The native audit additionally checks every local core/visits checkpoint pair.
    """
    report, snapshots = checked_artifacts(path)
    verify_inputs(root, report)
    config = report["config"]
    model = CardAbstraction.load(root / config["model"])
    tolerance = config["limits"]["independent_value_br_tolerance_chips"]
    by_id = {tuple(r[k] for k in IDENTITY): r for r in report["rows"]}
    maximum = 0.0
    receipts = 0
    crossplays = []
    for filename in config["development_spots"]:
        source = SpotTree.build(load_spot(root / filename))
        exact = MatrixTree.build(source)
        uniform_mass = decision_mass(exact, exact.normalize(exact.legal))
        game_snapshots = [p for p in snapshots if p["spot_file"] == filename]
        for encoding in config["encodings"]:
            tree = (
                exact
                if encoding == "exact"
                else MatrixTree.build(source, encoding, model)
            )
            current = collision_summary(tree, uniform_mass)
            diagnostic = next(
                r
                for r in report["diagnostics"]
                if r["spot_file"] == filename and r["encoding"] == encoding
            )
            if any(current[k] != diagnostic[k] for k in current):
                raise ArithmeticError("collision/recall/memory diagnostics changed")
            first_indices = np.unique(tree.exact_to_abstract, return_index=True)[1]
            for snapshot in game_snapshots:
                if snapshot["encoding"] != encoding:
                    continue
                row = by_id[tuple(snapshot[k] for k in IDENTITY)]
                deployed = exact.dense_exact(
                    tuple(tuple(v for v in p) for p in snapshot["policy"])
                )
                policy = deployed[first_indices]
                tree.validate_policy(policy)
                if not np.array_equal(
                    exact.dense_exact(tree.exact_policy(policy)), deployed
                ):
                    raise ArithmeticError(
                        "frozen policy violates abstract row consistency"
                    )
                active = np.asarray(snapshot["average_active"], dtype=np.float64)
                if active.shape != (len(tree.keys),) or not np.all(
                    np.isin(active, (0, 1))
                ):
                    raise ArithmeticError("invalid frozen average-coverage mask")
                actual = score(exact, tree, policy, active, uniform_mass)
                errors = [abs(actual[k] - row[k]) for k in actual]
                maximum = max(maximum, *errors)
                if max(errors) > tolerance:
                    raise ArithmeticError(
                        "frozen policy metrics/coverage replay mismatch"
                    )
                if snapshot["method"] == "full_cfr_plus":
                    if (
                        snapshot["sampled"] is not None
                        or row["seed"] is not None
                        or row["node_threshold"] is not None
                        or row["warm_node_equivalent"] != 0
                        or row["total_node_work"]
                        != 2 * row["iteration"] * len(tree.player)
                    ):
                        raise ArithmeticError("invalid full-tree work accounting")
                    continue
                visited = np.asarray(snapshot["sampled"], dtype=np.float64)
                if visited.shape != active.shape or not np.all(
                    np.isin(visited, (0, 1))
                ):
                    raise ArithmeticError("invalid frozen sampled-visit mask")
                own_mass = decision_mass(exact, deployed)
                for name, mass in (("uniform", uniform_mass), ("own", own_mass)):
                    value = float(mass @ visited[tree.exact_to_abstract] / mass.sum())
                    error = abs(
                        value - row[f"{name}_reach_subsequently_sampled_coverage"]
                    )
                    maximum = max(maximum, error)
                    if error > tolerance:
                        raise ArithmeticError("subsequent-visit coverage mismatch")
                if (
                    row["warm_node_equivalent"] != 2 * len(tree.player)
                    or row["recursive_visits"] < 0
                    or row["iteration"] < 2
                    or row["total_node_work"]
                    != row["recursive_visits"] + row["warm_node_equivalent"]
                    or row["overshoot"]
                    != row["total_node_work"] - row["node_threshold"]
                    or not 0 <= row["overshoot"] < 2 * len(tree.player)
                    or row["subsequently_sampled_information_sets"]
                    != int(visited.sum())
                    or row["initial_only_information_sets"]
                    != len(tree.keys) - int(visited.sum())
                    or row["sampled_regret_average_bytes"]
                    != current["unpadded_regret_average_bytes"]
                ):
                    raise ArithmeticError("invalid sampled work/row/memory accounting")
                if not check_checkpoints:
                    continue
                checkpoint = path.parent / row["checkpoint_file"]
                if (
                    digest(checkpoint) != row["checkpoint_sha256"]
                    or digest(checkpoint.with_suffix(".visits.json"))
                    != row["checkpoint_visits_sha256"]
                ):
                    raise ArithmeticError("checkpoint/visits receipt hash mismatch")
                solver = load_learning_checkpoint(
                    checkpoint,
                    root_factory(tree),
                    expected_config={
                        "learning": {
                            **config,
                            "sampler": "external",
                            "encoding": encoding,
                        },
                        "spot_file": filename,
                        "spot_sha256": report["spot_sha256"][filename],
                    },
                )
                restored, restored_active = sampled_average(solver, tree)
                restored_visits = np.array(
                    [k in solver.sampled_keys for k in tree.keys], dtype=np.float64
                )
                if (
                    solver.iteration != row["iteration"]
                    or solver.nodes_visited != row["recursive_visits"]
                    or solver.warm_node_equivalent != row["warm_node_equivalent"]
                    or not np.array_equal(restored, policy)
                    or not np.array_equal(restored_active, active)
                    or not np.array_equal(restored_visits, visited)
                ):
                    raise ArithmeticError(
                        "checkpoint does not reproduce frozen strategy/visits/work"
                    )
                receipts += 1
        for cell in crossplay(exact, final_snapshots(game_snapshots, config)):
            cell["spot_file"] = filename
            crossplays.append(cell)
    return (
        report,
        snapshots,
        {
            "maximum_own_replay_error_chips": maximum,
            "checkpoint_receipts_checked": receipts,
            "crossplay": crossplays,
        },
    )
