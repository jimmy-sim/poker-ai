"""River-only own response switches and observable rank/range diagnostics."""

import gzip
import json
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, cast

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.cards import cards_to_mask, format_card
from poker_ai.evaluator import evaluate_best
from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.collision_diagnosis import conditional_actions
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.made_admission import REPRESENTATIONS, build_representation
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.reply_diagnosis import numerical_difference
from poker_ai.postflop.reply_diagnosis import replay as replay_replies
from poker_ai.postflop.reply_trace import require_recall
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.training.no_limit import NoLimitState
from poker_ai.validation.five_card import source_provenance

PANELS = ["restricted_prefix", "exact_prefix"]
PROBES = ["own_rank", "range_compatibility", "range_relations"]
FORMAT = "poker-ai-river-distinction-diagnosis-v1"
DETAIL_FORMAT = "poker-ai-river-distinction-details-v1"


def river_features(
    hole: tuple[int, ...],
    board: tuple[int, ...],
    declared_range: tuple[tuple[int, ...], ...],
) -> dict[str, tuple[Any, ...]]:
    """Static diagnostic signatures, not agent features or hidden-deal inputs.

    Relations are None when blocked, else -1/0/+1 for own showdown loss/tie/win.
    Ordered range entries are game inputs; no posterior/strategy enters probes.
    """
    if len(hole) != 2 or len(board) != 5 or not declared_range:
        raise ValueError("need own cards, river board and declared opponent range")
    known = cards_to_mask(hole + board)
    own = evaluate_best(hole + board)
    compatible: list[bool] = []
    relations: list[int | None] = []
    for combo in declared_range:
        if len(combo) != 2:
            raise ValueError("range combo needs two cards")
        mask = cards_to_mask(combo)
        allowed = not bool(mask & known)
        compatible.append(allowed)
        if allowed:
            other = evaluate_best(combo + board)
            relations.append(int(own > other) - int(own < other))
        else:
            relations.append(None)
    return {
        "own_rank": (int(own.category), *own.tiebreakers),
        "range_compatibility": tuple(compatible),
        "range_relations": tuple(relations),
    }


@dataclass(frozen=True)
class RiverPanel:
    before: FloatArray
    after: FloatArray
    before_value: float
    after_value: float
    losses: FloatArray
    mass: FloatArray
    error: float


def river_switches(
    tree: ArrayTree,
    exact_reply: FloatArray,
    restricted_reply: FloatArray,
    target: int,
    river: np.ndarray[Any, np.dtype[np.bool_]],
    *,
    tolerance: float,
) -> dict[str, RiverPanel]:
    """Switch only responder river rows, retaining BOTH fixed earlier prefixes.

    Sum saved-F full reach times [W_G - F W_G(children)] across hidden histories.
    Only river rows differ, so its sum telescopes to target value(G)-value(F).
    These are frozen-policy interventions, not expected gains after retraining.
    """
    if target not in (0, 1) or not 0 < tolerance <= 1e-8:
        raise ValueError("invalid river target/tolerance")
    if (
        river.dtype != np.bool_
        or river.shape != (len(tree.keys),)
        or np.any(river & (tree.owners != target))
    ):
        raise ValueError("river mask must select only responder rows")
    require_recall(tree)
    tree.validate_policy(exact_reply)
    tree.validate_policy(restricted_reply)
    if not np.array_equal(
        exact_reply[tree.owners != target], restricted_reply[tree.owners != target]
    ):
        raise ArithmeticError("river comparison changed the fixed opponent")
    result = {}
    sign = 1 if target == 0 else -1
    nodes = np.flatnonzero(
        (tree.player == target) & river[np.maximum(tree.information, 0)]
    )
    for prefix in PANELS:
        before = (
            restricted_reply if prefix == "restricted_prefix" else exact_reply
        ).copy()
        before[river] = restricted_reply[river]
        after = before.copy()
        after[river] = exact_reply[river]
        edges = tree.edges(before)
        values = sign * tree.values(tree.edges(after))
        baseline = sign * float(tree.values(edges)[0])
        reach = tree.chance_reach * tree.reaches(edges).prod(axis=1)
        losses, mass = np.zeros(len(tree.keys)), np.zeros(len(tree.keys))
        advantage = values[nodes] - (values[tree.children[nodes]] * edges[nodes]).sum(
            axis=1
        )
        np.add.at(losses, tree.information[nodes], reach[nodes] * advantage)
        np.add.at(mass, tree.information[nodes], reach[nodes])
        error = abs(float(losses.sum()) - (float(values[0]) - baseline))
        if error > tolerance or losses.min(initial=0) < -tolerance:
            raise ArithmeticError("river switch accounting mismatch")
        result[prefix] = RiverPanel(
            before, after, baseline, float(values[0]), losses, mass, error
        )
    return result


def conflicting(rows: list[dict[str, Any]], probe: str | None = None) -> bool:
    """True if some (optionally refined) subgroup lacks a common near-best action."""
    groups: dict[tuple[Any, ...], list[set[int]]] = {}
    for row in rows:
        key = () if probe is None else tuple(row["features"][probe])
        groups.setdefault(key, []).append(set(row["near_optimal_columns"]))
    return any(
        len(sets) >= 2 and not set.intersection(*sets) for sets in groups.values()
    )


def river_mask(exact: MatrixTree, target: int) -> np.ndarray[Any, np.dtype[np.bool_]]:
    selected = np.zeros(len(exact.keys), dtype=np.bool_)
    for i, node in enumerate(exact.source.representatives):
        state = exact.source.states[node]
        assert state.dealer is not None
        if state.dealer.street.name not in ("TURN", "RIVER"):
            raise ValueError("this diagnosis supports turn-start cases only")
        selected[i] = state.actor == target and state.dealer.street.name == "RIVER"
    return selected


def conditional_ranges(
    exact: MatrixTree,
    profile: FloatArray,
    target: int,
    river: np.ndarray[Any, np.dtype[np.bool_]],
) -> FloatArray:
    """Average all hidden deals using chance*fixed-opponent reach, not own reach."""
    edges = exact.edges(profile)
    cf = exact.chance_reach * exact.reaches(edges)[:, 1 - target]
    posterior = np.zeros((len(exact.keys), len(exact.source.spot.ranges[1 - target])))
    for raw in np.flatnonzero(
        (exact.player == target) & river[np.maximum(exact.information, 0)]
    ):
        node = int(raw)
        state = exact.source.states[node]
        combo = state.second if target == 0 else state.first
        assert combo is not None
        posterior[exact.information[node], combo] += cf[node]
    total = posterior.sum(axis=1, keepdims=True)
    return cast(
        FloatArray,
        np.divide(posterior, total, out=np.zeros_like(posterior), where=total > 0),
    )


def analyse_case(
    exact: MatrixTree,
    abstract: MatrixTree,
    detail: dict[str, Any],
    config: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    tolerance = config["tolerance_chips"]
    responses, full = [], []
    for target in (0, 1):
        saved = detail["responses"][target]
        if saved["target"] != target:
            raise ArithmeticError("changed saved responder ordering")
        b, c = [
            exact.dense_exact(tuple(tuple(v for v in row) for row in saved[k]))
            for k in ("exact_reply_profile", "restricted_reply_profile")
        ]
        river = river_mask(exact, target)
        panels = river_switches(exact, b, c, target, river, tolerance=tolerance)
        q, support = conditional_actions(exact, b)
        posterior = conditional_ranges(exact, b, target, river)
        records = []
        known_range = tuple(h.cards for h in exact.source.spot.ranges[1 - target])
        for raw in np.flatnonzero(river):
            i = int(raw)
            state = exact.source.states[exact.source.representatives[i]]
            assert state.dealer is not None
            obs = state.dealer.observe(target)
            features = river_features(obs.hole_cards, obs.board, known_range)
            if np.any(
                posterior[i][np.logical_not(features["range_compatibility"])] > 0
            ):
                raise ArithmeticError("posterior gives mass to blocked combo")
            actions = []
            for action in exact.actions[i]:
                move = NoLimitState(state.dealer, exact.source.spot.rules).decode(
                    action
                )
                actions.append(
                    move.kind.value + ("" if move.amount is None else f" {move.amount}")
                )
            n = len(actions)
            values = q[i, :n]
            best = float(values.max())
            gap = best - float(c[i, :n] @ values)
            row = {
                "exact_info": i,
                "abstract_info": int(abstract.exact_to_abstract[i]),
                "seat": target,
                "hole": [format_card(v) for v in obs.hole_cards],
                "board": [format_card(v) for v in obs.board],
                "pot": obs.pot,
                "declared_opponent_range": [
                    [format_card(v) for v in h] for h in known_range
                ],
                "features": features,
                "actions": actions,
                "exact_action": actions[int(b[i].argmax())],
                "restricted_probabilities": c[i, :n].tolist(),
                "near_optimal_columns": np.flatnonzero(
                    best - values <= tolerance
                ).tolist(),
                "conditional_values_chips": values.tolist(),
                "counterfactual_mass": float(support[i]),
                "conditional_opponent_range": posterior[i].tolist(),
                "conditional_action_gap_chips": gap,
                "different_reply": not np.array_equal(b[i], c[i]),
                "panels": {
                    p: {"reach": float(v.mass[i]), "loss_chips": float(v.losses[i])}
                    for p, v in panels.items()
                },
            }
            for v in panels.values():
                if abs(v.losses[i] - v.mass[i] * gap) > tolerance:
                    raise ArithmeticError("river conditional loss identity mismatch")
            records.append(row)
        summaries = []
        for prefix, panel in panels.items():
            active = [
                r
                for r in records
                if r["counterfactual_mass"] > 0 and r["panels"][prefix]["reach"] > 0
            ]
            groups: dict[int, list[dict[str, Any]]] = {}
            for row in active:
                groups.setdefault(row["abstract_info"], []).append(row)
            conflicts = [(i, rows) for i, rows in groups.items() if conflicting(rows)]
            ranked = sorted(
                conflicts,
                key=lambda g: (
                    -sum(r["panels"]["exact_prefix"]["loss_chips"] for r in g[1]),
                    g[0],
                ),
            )
            top_groups = []
            for group, rows in ranked[: config["top_groups"]]:
                rows = sorted(
                    rows,
                    key=lambda r: (-r["panels"][prefix]["loss_chips"], r["exact_info"]),
                )
                selected, seen = [], set()
                for row in rows:
                    signature = tuple(row["near_optimal_columns"])
                    if signature not in seen:
                        selected.append(row)
                        seen.add(signature)
                selected += [r for r in rows if r not in selected]
                top_groups.append(
                    {
                        "abstract_info": group,
                        "reachable_exact_infos": len(rows),
                        "loss_chips": sum(
                            r["panels"][prefix]["loss_chips"] for r in rows
                        ),
                        "probe_unresolved": {
                            probe: conflicting(rows, probe) for probe in PROBES
                        },
                        "examples": selected[: config["examples_per_group"]],
                    }
                )
            different = [r for r in active if r["different_reply"]]
            summaries.append(
                {
                    "prefix": prefix,
                    "before_value_chips": panel.before_value,
                    "after_value_chips": panel.after_value,
                    "river_gain_chips": panel.after_value - panel.before_value,
                    "loss_sum_chips": float(panel.losses.sum()),
                    "accounting_error_chips": panel.error,
                    "river_infos": len(records),
                    "positive_reach_infos": len(active),
                    "unsupported_infos": sum(
                        r["counterfactual_mass"] == 0 for r in records
                    ),
                    "unreachable_supported_infos": sum(
                        r["counterfactual_mass"] > 0
                        and r["panels"][prefix]["reach"] == 0
                        for r in records
                    ),
                    "different_reply_infos": len(different),
                    "tie_only_difference_infos": sum(
                        r["conditional_action_gap_chips"] <= tolerance
                        for r in different
                    ),
                    "strict_missed_infos": sum(
                        r["conditional_action_gap_chips"] > tolerance for r in active
                    ),
                    "conflicting_rows": len(conflicts),
                    "unresolved_after_probe": {
                        probe: sum(conflicting(rows, probe) for _, rows in conflicts)
                        for probe in PROBES
                    },
                    "top_groups": top_groups,
                }
            )
        # B-C = (H-C) + (B-H), no summing the two prefix-panel gains.
        restricted, precise = panels["restricted_prefix"], panels["exact_prefix"]
        B, C, H = precise.after_value, restricted.before_value, restricted.after_value
        if B < H - tolerance or abs((B - C) - ((H - C) + (B - H))) > tolerance:
            raise ArithmeticError("river/prefix value decomposition mismatch")
        responses.append(
            {
                "target": target,
                "exact_information_value_chips": B - C,
                "river_gain_restricted_prefix_chips": H - C,
                "prefix_readjustment_chips": B - H,
                "panels": summaries,
            }
        )
        full.append(
            {
                "target": target,
                "range_combos": [[format_card(v) for v in h] for h in known_range],
                "river_infos": records,
            }
        )
    return (
        {
            "spot": exact.source.spot.name,
            "pot": exact.source.spot.pot,
            "responses": responses,
        },
        {"responses": full},
    )


def validate_config(config: dict[str, Any]) -> None:
    if (
        config["schema_version"] != 1
        or config["representations"] != REPRESENTATIONS
        or config["prefix_panels"] != PANELS
        or config["probes"] != PROBES
        or type(config["top_groups"]) is not int
        or not 1 <= config["top_groups"] <= 20
        or type(config["examples_per_group"]) is not int
        or not 2 <= config["examples_per_group"] <= 8
        or not 0 < config["tolerance_chips"] <= 1e-8
    ):
        raise ValueError("invalid fixed river diagnosis")


def inputs(
    root: Path, config: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    validate_config(config)
    path = root / config["input_report"]
    if digest(path) != config["input_report_sha256"]:
        raise ArithmeticError("river input report changed")
    report, details, _ = replay_replies(root, path)
    if report["details_sha256"] != config["input_details_sha256"]:
        raise ArithmeticError("river input details changed")
    admission = json.loads((root / report["config"]["input_report"]).read_text())
    return report, details, admission


def compute(
    root: Path, config: dict[str, Any]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    original, details, admission = inputs(root, config)
    model = CardAbstraction.load(root / admission["config"]["model"])
    cases, all_details = [], []
    for filename in admission["config"]["spot_files"]:
        source = SpotTree.build(load_spot(root / filename))
        if len(source.spot.board) != 4:
            raise ValueError("river diagnosis requires turn-start inputs")
        exact = MatrixTree.build(source)
        for name in config["representations"]:
            identity = {"spot_file": filename, "representation": name}
            detail = next(
                c for c in details if all(c[k] == v for k, v in identity.items())
            )
            case, full = analyse_case(
                exact, build_representation(source, name, model), detail, config
            )
            prior = next(
                c
                for c in original["cases"]
                if all(c[k] == v for k, v in identity.items())
            )
            for target in (0, 1):
                if (
                    abs(
                        case["responses"][target]["exact_information_value_chips"]
                        - prior["responses"][target]["extra_information_value_chips"]
                    )
                    > config["tolerance_chips"]
                ):
                    raise ArithmeticError(
                        "river diagnosis changed prior response value"
                    )
            cases.append({**identity, **case})
            all_details.append({**identity, **full})
    return cases, all_details


def diagnose(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    started = time.perf_counter()
    timestamp = datetime.now(UTC).isoformat()
    config = json.loads(config_path.read_text())
    validate_config(config)
    sidecar = output.with_name(output.stem + "-details.json.gz")
    if output.exists() or sidecar.exists():
        raise FileExistsError("retain previous river diagnosis")
    provenance = source_provenance(
        root, config_path, entrypoints=("scripts/diagnose_river_distinctions.py",)
    )
    if provenance["dirty"] is not False:
        raise ValueError("publish tested river code/config before measurement")
    cases, details = compute(root, config)
    output.parent.mkdir(parents=True, exist_ok=True)
    sidecar.write_bytes(
        gzip.compress(
            json.dumps(
                {"format": DETAIL_FORMAT, "cases": details}, allow_nan=False
            ).encode(),
            mtime=0,
        )
    )
    result = {
        "format": FORMAT,
        "status": "completed",
        "config": config,
        "source": provenance,
        "environment": runtime_environment(),
        "started_at_utc": timestamp,
        "seconds": time.perf_counter() - started,
        "details_file": sidecar.name,
        "details_sha256": digest(sidecar),
        "cases": cases,
        "scope": config["scope"],
    }
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return result


def replay(
    root: Path, path: Path
) -> tuple[dict[str, Any], list[dict[str, Any]], float]:
    report = json.loads(path.read_text())
    json.dumps(report, allow_nan=False)
    if report["format"] != FORMAT or report["status"] != "completed":
        raise ArithmeticError("river report format/status changed")
    for name, sha in report["source"]["sha256"].items():
        if digest(root / name) != sha:
            raise ArithmeticError("river source/config changed")
    sidecar = path.parent / report["details_file"]
    if digest(sidecar) != report["details_sha256"]:
        raise ArithmeticError("river details hash changed")
    payload = json.loads(gzip.decompress(sidecar.read_bytes()))
    if payload["format"] != DETAIL_FORMAT:
        raise ArithmeticError("river details format changed")
    cases, details = compute(root, report["config"])
    error = max(
        numerical_difference(cases, report["cases"]),
        numerical_difference(details, payload["cases"]),
    )
    if error > report["config"]["tolerance_chips"]:
        raise ArithmeticError("river numerical replay mismatch")
    return report, payload["cases"], error
