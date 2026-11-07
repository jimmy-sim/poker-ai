"""Explain lossy rows using frozen own continuations, never reference strategies."""

import json
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.cards import format_card
from poker_ai.evaluator import evaluate_best
from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning import decision_mass
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.public_study import checked_artifacts, verify_inputs
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.toy.analysis import evaluate
from poker_ai.training.no_limit import NoLimitState
from poker_ai.validation.five_card import source_provenance


def conditional_actions(
    tree: ArrayTree, policy: FloatArray
) -> tuple[FloatArray, FloatArray]:
    """Conditional own-chip Q values at EXACT information sets, plus support mass.

    Sum chance * opponent reach across hidden histories BEFORE any maximization.
    Exclude acting-player reach. Continue all future actions under the fixed own
    profile; these are local deviations, not a full best response. Unsupported
    infos get zero Q with zero mass and must be excluded from any ranking.
    """
    edges = tree.edges(policy)
    values, reach = tree.values(edges), tree.reaches(edges)
    nodes = np.flatnonzero(tree.player >= 0)
    actors = tree.player[nodes]
    infos = tree.information[nodes]
    cf = tree.chance_reach[nodes] * reach[nodes, 1 - actors]
    scores, mass = np.zeros_like(tree.legal), np.zeros(len(tree.keys))
    np.add.at(mass, infos, cf)
    np.add.at(
        scores,
        infos,
        cf[:, None]
        * values[tree.children[nodes]]
        * np.where(actors == 0, 1.0, -1.0)[:, None]
        * tree.valid[nodes],
    )
    return np.divide(
        scores, mass[:, None], out=np.zeros_like(scores), where=mass[:, None] > 0
    ), mass


def sharing_cost(q: FloatArray, weights: FloatArray) -> float:
    """Sum w_i max_a Q_i(a) - max_a sum w_i Q_i(a), nonnegative by convexity.

    All columns must be legal in every row. Weights need not sum to one. With
    globally normalized uniform decision reach the units are chips per decision
    under that weighting, NOT game EV loss or exploitability. Costs at different
    nodes overlap and must not be interpreted as additive game losses.
    """
    if (
        q.ndim != 2
        or not q.shape[0]
        or not q.shape[1]
        or weights.shape != (len(q),)
        or not np.all(np.isfinite(q))
        or not np.all(np.isfinite(weights))
        or np.any(weights < 0)
    ):
        raise ValueError("invalid legal action values/weights")
    cost = float(weights @ q.max(axis=1) - (weights[:, None] * q).sum(axis=0).max())
    if cost < -1e-9:
        raise ArithmeticError("negative local sharing cost")
    return max(0.0, cost)


def ranked_groups(
    exact: MatrixTree,
    abstract: MatrixTree,
    policy: FloatArray,
    *,
    top: int,
    examples: int,
    tolerance: float,
) -> dict[str, Any]:
    q, support = conditional_actions(exact, policy)
    weights = decision_mass(exact, exact.normalize(exact.legal))
    weights /= weights.sum()
    active = support > 0
    weighted_support = weights * active
    ranked: list[dict[str, Any]] = []
    for info, menu in enumerate(abstract.actions):
        members = np.flatnonzero((abstract.exact_to_abstract == info) & active)
        if len(members) < 2:
            continue
        values = q[members, : len(menu)]
        cost = sharing_cost(values, weighted_support[members])
        preferred = values.max(axis=1, keepdims=True) - values <= tolerance
        if cost <= tolerance or np.any(preferred.all(axis=0)):
            continue
        rows: list[dict[str, Any]] = []
        for member, best in zip(members, preferred, strict=True):
            state = exact.source.states[exact.source.representatives[int(member)]]
            assert state.dealer is not None
            observation = state.dealer.observe(state.actor)
            rank = evaluate_best(observation.hole_cards + observation.board)
            labels = []
            for action in menu:
                move = NoLimitState(state.dealer, exact.source.spot.rules).decode(
                    action
                )
                labels.append(
                    move.kind.value + ("" if move.amount is None else f" {move.amount}")
                )
            if rows and labels != rows[0]["actions"]:
                raise ArithmeticError("merged row has incompatible concrete actions")
            rows.append(
                {
                    "exact_info": int(member),
                    "seat": observation.seat,
                    "street": observation.street.name,
                    "hole": [format_card(c) for c in observation.hole_cards],
                    "board": [format_card(c) for c in observation.board],
                    "pot": observation.pot,
                    "stacks": observation.stacks,
                    "hand_category": rank.category.name,
                    "hand_tiebreakers": rank.tiebreakers,
                    "actions": labels,
                    "conditional_action_values_chips": q[member, : len(menu)].tolist(),
                    "preferred_actions": [
                        a for a, allowed in zip(labels, best, strict=True) if allowed
                    ],
                    "own_control_probabilities": policy[member, : len(menu)].tolist(),
                    "uniform_decision_weight": float(weights[member]),
                }
            )
        # Deterministic coverage of distinct preferred-action sets before repeats.
        rows.sort(
            key=lambda r: (
                r["preferred_actions"],
                -r["uniform_decision_weight"],
                r["exact_info"],
            )
        )
        selected = []
        seen: set[tuple[str, ...]] = set()
        for row in rows:
            signature = tuple(row["preferred_actions"])
            if signature not in seen:
                selected.append(row)
                seen.add(signature)
        selected += [r for r in rows if r not in selected]
        ranked.append(
            {
                "abstract_info": info,
                "supported_exact_infos": len(members),
                "local_sharing_cost_chips_per_decision": cost,
                "uniform_decision_weight": float(weights[members].sum()),
                "examples": selected[:examples],
            }
        )
    ranked.sort(
        key=lambda r: (-r["local_sharing_cost_chips_per_decision"], r["abstract_info"])
    )
    return {
        "supported_uniform_decision_weight": float(weighted_support.sum()),
        "conflicting_rows": len(ranked),
        "top_groups": ranked[:top],
        "score_convention": (
            "weighted local continuation disagreement; not game EV/exploitability; "
            "groups are not additive game losses"
        ),
    }


def diagnose(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text())
    if (
        config["schema_version"] != 1
        or config["encoding"] != "texture_b8"
        or config["panels"] != ["own_exact_full", "uniform"]
        or config["top_groups"] < 1
        or config["examples_per_group"] < 2
        or not 0 < config["tie_tolerance_chips"] <= 1e-8
    ):
        raise ValueError("invalid fixed collision diagnosis")
    if output.exists():
        raise FileExistsError("retain existing diagnosis; choose a new output")
    path = root / config["input_report"]
    if digest(path) != config["input_report_sha256"]:
        raise ArithmeticError("diagnosis input report changed")
    report, policies = checked_artifacts(path)
    verify_inputs(root, report)
    if report["own_policies_sha256"] != config["input_policy_sha256"]:
        raise ArithmeticError("diagnosis input policies changed")
    source = source_provenance(
        root, config_path, entrypoints=("scripts/diagnose_board_collisions.py",)
    )
    if source["dirty"] is not False:
        raise ValueError("publish diagnosis code/config first; use a clean worktree")
    model = CardAbstraction.load(root / report["config"]["model"])
    cases = []
    for filename in report["config"]["development_spots"]:
        tree = SpotTree.build(load_spot(root / filename))
        exact = MatrixTree.build(tree)
        abstract = MatrixTree.build(tree, "texture_b8", model)
        selected = [
            p
            for p in policies
            if p["spot_file"] == filename
            and p["encoding"] == "exact"
            and p["method"] == "full_cfr_plus"
            and p["iteration"] == report["config"]["full_tree_checkpoints"][-1]
        ]
        if len(selected) != 1:
            raise ArithmeticError("missing unique own exact continuation control")
        control = exact.dense_exact(
            tuple(tuple(v for v in p) for p in selected[0]["policy"])
        )
        metrics = evaluate(exact, control)
        recorded = next(
            r
            for r in report["rows"]
            if all(
                r[k] == selected[0][k]
                for k in ("spot_file", "encoding", "method", "seed", "iteration")
            )
        )
        if (
            max(
                abs(metrics.value_player_zero - recorded["value_player_zero_chips"]),
                abs(metrics.exploitability - recorded["exploitability_chips"]),
            )
            > 1e-9
        ):
            raise ArithmeticError("own exact control replay mismatch")
        for label in config["panels"]:
            policy = (
                control if label == "own_exact_full" else exact.normalize(exact.legal)
            )
            cases.append(
                {
                    "spot_file": filename,
                    "spot": tree.spot.name,
                    "panel": label,
                    **ranked_groups(
                        exact,
                        abstract,
                        policy,
                        top=config["top_groups"],
                        examples=config["examples_per_group"],
                        tolerance=config["tie_tolerance_chips"],
                    ),
                }
            )
    result = {
        "format": "poker-ai-board-collision-diagnosis-v1",
        "config": config,
        "source": source,
        "cases": cases,
        "scope": (
            "post-hoc known-case diagnosis; own controls only; "
            "no new training or reference strategy input"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return result
