"""Audit frozen own policies and derive local diagnostics; no training or references.

Cross-play EV averages the tested strategy's two seats against the frozen OWN
full-tree CFR+ control. It is neither a best response nor full-game strength.
"""

import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.finite import FloatArray
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning import POLICY_FORMAT, acceptance, decision_mass
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.tree import SpotTree
from poker_ai.toy.analysis import evaluate


def crossplay_ev(tree: MatrixTree, tested: FloatArray, control: FloatArray) -> float:
    """Net chips for tested, mean over both seats, versus a fixed own control."""
    tree.validate_policy(tested)
    tree.validate_policy(control)
    first = np.where((tree.owners == 0)[:, None], tested, control)
    second = np.where((tree.owners == 1)[:, None], tested, control)
    return float(
        (tree.values(tree.edges(first))[0] - tree.values(tree.edges(second))[0]) / 2
    )


def weighted_gap(tree: MatrixTree, first: FloatArray, second: FloatArray) -> float:
    """Uniform-decision-reach weighted row L1; range [0,2], not percentage points."""
    tree.validate_policy(first)
    tree.validate_policy(second)
    mass = decision_mass(tree, tree.normalize(tree.legal))
    return float(mass @ np.abs(first - second).sum(axis=1) / mass.sum())


def checked_artifacts(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report = json.loads(path.read_text())
    if report["status"] != "completed":
        raise ValueError("partial training report cannot be summarized")
    policy_path = path.parent / report["own_policies_file"]
    if (
        hashlib.sha256(policy_path.read_bytes()).hexdigest()
        != report["own_policies_sha256"]
    ):
        raise ArithmeticError("frozen own policy hash mismatch")
    policies = json.loads(gzip.decompress(policy_path.read_bytes()))
    if policies["format"] != POLICY_FORMAT:
        raise ValueError("expected frozen own policies")
    fields = ("spot", "encoding", "method", "seed", "iteration")
    rows = {tuple(r[f] for f in fields): r for r in report["rows"]}
    snapshots = {tuple(r[f] for f in fields): r for r in policies["policies"]}
    if (
        rows.keys() != snapshots.keys()
        or len(rows) != len(report["rows"])
        or len(snapshots) != len(policies["policies"])
    ):
        raise ArithmeticError("missing or duplicate frozen own policy")
    return report, policies["policies"]


def summarize(root: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    """Re-evaluate every frozen policy, verify linked comparisons, retain gate fails."""
    inputs, summaries, crossplay, collisions = [], [], [], []
    independent_count = 0
    maximum_error = 0.0
    for entry in manifest["experiments"]:
        path = root / entry["report"]
        report, snapshots = checked_artifacts(path)
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        independent_path = root / entry["independent"]
        independent = json.loads(independent_path.read_text())
        if independent["input_sha256"] != digest or independent["status"] != "passed":
            raise ArithmeticError(
                "missing successful independent check for this exact report"
            )
        independent_count += len(independent["comparisons"])
        inputs.append(
            {
                "experiment": entry["name"],
                "report": entry["report"],
                "sha256": digest,
                "independent_sha256": hashlib.sha256(
                    independent_path.read_bytes()
                ).hexdigest(),
            }
        )
        config = report["config"]
        if json.loads((root / entry["config"]).read_text()) != config:
            raise ArithmeticError("frozen training config changed")
        model_path = root / config["model"]
        if (
            hashlib.sha256(model_path.read_bytes()).hexdigest()
            != report["model_sha256"]
        ):
            raise ArithmeticError("card model changed")
        model = CardAbstraction.load(model_path)
        recomputed_rows: list[dict[str, Any]] = []
        for filename, expected in report["spot_sha256"].items():
            spot_path = root / filename
            if hashlib.sha256(spot_path.read_bytes()).hexdigest() != expected:
                raise ArithmeticError("spot definition changed")
            source = SpotTree.build(load_spot(spot_path))
            tree = MatrixTree.build(source)
            own = [p for p in snapshots if p["spot"] == source.spot.name]
            controls = [
                p
                for p in own
                if p["encoding"] == "exact"
                and p["method"] == "full_cfr_plus"
                and p["iteration"] == config["full_tree_checkpoints"][-1]
            ]
            # Representation-only reports reuse the exact control through the manifest.
            if not controls:
                control_report, control_snapshots = checked_artifacts(
                    root / entry["exact_control"]
                )
                if (
                    control_report["spot_sha256"].get(filename) != expected
                    or control_report["model_sha256"] != report["model_sha256"]
                ):
                    raise ArithmeticError(
                        "own exact control uses a different game/model"
                    )
                controls = [
                    p
                    for p in control_snapshots
                    if p["spot"] == source.spot.name
                    and p["encoding"] == "exact"
                    and p["method"] == "full_cfr_plus"
                    and p["iteration"] == config["full_tree_checkpoints"][-1]
                ]
            if len(controls) != 1:
                raise ArithmeticError("missing unique own exact full-tree control")
            control = tree.dense_exact(
                tuple(tuple(v for v in r) for r in controls[0]["policy"])
            )
            for encoding in report["encodings"]:
                representation = MatrixTree.build(source, encoding, model)
                counts = np.bincount(
                    representation.exact_to_abstract, minlength=len(representation.keys)
                )
                boards: list[set[tuple[int, ...]]] = [
                    set() for _ in representation.keys
                ]
                for info, node in enumerate(source.representatives):
                    dealer = source.states[node].dealer
                    assert dealer is not None
                    boards[int(representation.exact_to_abstract[info])].add(
                        dealer.board
                    )
                collisions.append(
                    {
                        "experiment": entry["name"],
                        "spot": source.spot.name,
                        "encoding": encoding,
                        "exact_rows": len(tree.keys),
                        "abstract_rows": len(representation.keys),
                        "rows_merging_exact_infos": int((counts > 1).sum()),
                        "rows_merging_distinct_public_boards": sum(
                            len(b) > 1 for b in boards
                        ),
                        "maximum_exact_infos_per_row": int(counts.max()),
                    }
                )
            for snapshot in own:
                key = tuple(
                    snapshot[f]
                    for f in ("spot", "encoding", "method", "seed", "iteration")
                )
                row = next(
                    r
                    for r in report["rows"]
                    if tuple(
                        r[f]
                        for f in ("spot", "encoding", "method", "seed", "iteration")
                    )
                    == key
                )
                policy = tree.dense_exact(
                    tuple(tuple(v for v in r) for r in snapshot["policy"])
                )
                metrics = evaluate(tree, policy)
                error = max(
                    abs(metrics.exploitability - row["exploitability_chips"]),
                    abs(metrics.value_player_zero - row["value_player_zero_chips"]),
                )
                maximum_error = max(maximum_error, error)
                if error > config["independent_tolerance"]:
                    raise ArithmeticError(
                        "frozen own policy metrics cannot be replayed"
                    )
                recomputed_rows.append(
                    {
                        **row,
                        "exploitability_pot_fraction": metrics.exploitability
                        / source.spot.pot,
                    }
                )
                if (
                    snapshot["method"] == "external"
                    and snapshot["iteration"] == config["sampled_checkpoints"][-1]
                ):
                    crossplay.append(
                        {
                            **{f: snapshot[f] for f in ("spot", "encoding", "seed")},
                            "experiment": entry["name"],
                            "ev_vs_own_full_control_pot": crossplay_ev(
                                tree, policy, control
                            )
                            / source.spot.pot,
                            "uniform_reach_weighted_row_l1_vs_own_full": weighted_gap(
                                tree, policy, control
                            ),
                        }
                    )
            for encoding in report["encodings"]:
                final = [
                    r
                    for r in report["rows"]
                    if r["spot"] == source.spot.name
                    and r["encoding"] == encoding
                    and r["method"] == "external"
                    and r["iteration"] == config["sampled_checkpoints"][-1]
                ]
                if sorted(r["seed"] for r in final) != sorted(config["seeds"]):
                    raise ArithmeticError("missing fixed final seeds")
                eps = [r["exploitability_pot_fraction"] for r in final]
                summaries.append(
                    {
                        "experiment": entry["name"],
                        "spot": source.spot.name,
                        "encoding": encoding,
                        "iteration": config["sampled_checkpoints"][-1],
                        "median_epsilon_pot": float(np.median(eps)),
                        "min_epsilon_pot": min(eps),
                        "max_epsilon_pot": max(eps),
                        "minimum_uniform_average_coverage": min(
                            r["uniform_reach_average_row_coverage"] for r in final
                        ),
                        "minimum_subsequently_sampled_rows": min(
                            r["subsequently_sampled_information_sets"] for r in final
                        ),
                        "maximum_initial_only_rows": max(
                            r["initial_only_information_sets"] for r in final
                        ),
                        "maximum_sampled_nodes": max(
                            r["nodes_visited_or_full_node_equivalent"] for r in final
                        ),
                        "warm_node_equivalent": max(
                            r["warm_node_equivalent"] for r in final
                        ),
                    }
                )
        if report["exact_acceptance"] is not None:
            gate = acceptance(
                recomputed_rows,
                config,
                [load_spot(root / f).name for f in report["spot_sha256"]],
            )
            if gate != report["exact_acceptance"]:
                raise ArithmeticError("stored acceptance differs from replay")
    heldout = next(e for e in manifest["experiments"] if e["name"] == "heldout")
    gate = json.loads((root / heldout["report"]).read_text())["exact_acceptance"]
    return {
        "audit_status": "passed",
        "learning_gate_passed": gate["passed"],
        "heldout_acceptance": gate,
        "inputs": inputs,
        "summaries": summaries,
        "crossplay": crossplay,
        "collisions": collisions,
        "independently_checked_policies": independent_count,
        "maximum_own_replay_error_chips": maximum_error,
        "scope": (
            "restricted own-game diagnostic; cross-play uses own full-tree "
            "control; failed gate retained; no global strength claim"
        ),
    }
