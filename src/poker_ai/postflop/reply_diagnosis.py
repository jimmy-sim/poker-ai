"""Deterministic response diagnosis of retained own policies; no learning."""

import gzip
import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.cards import format_card
from poker_ai.evaluator import evaluate_best
from poker_ai.finite import FloatArray
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.made_admission import (
    REPRESENTATIONS,
    build_representation,
    checked_artifacts,
    verify_inputs,
)
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.reply_trace import LossTrace, response_profile, trace_losses
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.toy.analysis import best_response, evaluate
from poker_ai.training.no_limit import NoLimitState
from poker_ai.validation.five_card import source_provenance

FORMAT = "poker-ai-saved-reply-diagnosis-v1"
DETAIL_FORMAT = "poker-ai-saved-reply-details-v1"
IDENTITY = ("spot_file", "representation")


def validate_config(config: dict[str, Any]) -> None:
    if (
        config["schema_version"] != 1
        or config["representations"] != REPRESENTATIONS
        or type(config["iteration"]) is not int
        or config["iteration"] < 1
        or type(config["top_groups"]) is not int
        or not 1 <= config["top_groups"] <= 20
        or type(config["examples_per_group"]) is not int
        or not 2 <= config["examples_per_group"] <= 8
        or not 0 < config["tolerance_chips"] <= 1e-8
        or config["tie_rule"]
        != "first legal maximizer, no approximate tie substitution"
    ):
        raise ValueError("invalid fixed saved-reply diagnosis")


def example(
    exact: MatrixTree, info: int, policy: FloatArray, trace: LossTrace
) -> dict[str, Any]:
    state = exact.source.states[exact.source.representatives[info]]
    assert state.dealer is not None
    observation = state.dealer.observe(state.actor)
    rank = evaluate_best(observation.hole_cards + observation.board)
    actions = []
    for action in exact.actions[info]:
        move = NoLimitState(state.dealer, exact.source.spot.rules).decode(action)
        actions.append(
            move.kind.value + ("" if move.amount is None else f" {move.amount}")
        )
    count = len(actions)
    return {
        "exact_info": info,
        "seat": observation.seat,
        "street": observation.street.name,
        "hole": [format_card(c) for c in observation.hole_cards],
        "board": [format_card(c) for c in observation.board],
        "hand_category": rank.category.name,
        "hand_tiebreakers": rank.tiebreakers,
        "pot": observation.pot,
        "actions": actions,
        "saved_probabilities": policy[info, :count].tolist(),
        "reply_action": actions[int(trace.profile[info].argmax())],
        "reply_continuation_values_chips": trace.conditional_values[
            info, :count
        ].tolist(),
        "counterfactual_mass": float(trace.counterfactual_mass[info]),
        "saved_reach_mass": float(trace.saved_reach_mass[info]),
        "loss_contribution_chips": float(trace.losses[info]),
    }


def analyse(
    exact: MatrixTree,
    abstract: MatrixTree,
    policy: FloatArray,
    *,
    top: int,
    examples: int,
    tolerance: float,
) -> tuple[dict[str, Any], dict[str, Any]]:
    first = np.unique(abstract.exact_to_abstract, return_index=True)[1]
    limited_policy = policy[first]
    if not np.array_equal(
        exact.dense_exact(abstract.exact_policy(limited_policy)), policy
    ):
        raise ArithmeticError("saved profile violates its declared partition")
    metrics = evaluate(exact, policy)
    summaries: list[dict[str, Any]] = []
    details: list[dict[str, Any]] = []
    for target in (0, 1):
        trace = trace_losses(exact, policy, target, tolerance=tolerance)
        constrained = response_profile(abstract, limited_policy, target)
        expanded = exact.dense_exact(abstract.exact_policy(constrained))
        sign = 1 if target == 0 else -1
        limited_value = sign * float(exact.values(exact.edges(expanded))[0])
        own_limited_value = sign * float(
            abstract.values(abstract.edges(constrained))[0]
        )
        baseline = sign * metrics.value_player_zero
        if (
            abs(trace.value - best_response(exact, policy, target)) > tolerance
            or abs(limited_value - own_limited_value) > tolerance
            or abs(limited_value - best_response(abstract, limited_policy, target))
            > tolerance
            or limited_value < baseline - tolerance
            or trace.value < limited_value - tolerance
        ):
            raise ArithmeticError("response root/restriction mismatch")
        groups = np.zeros(len(abstract.keys))
        np.add.at(groups, abstract.exact_to_abstract, trace.losses)
        ranked = sorted(
            (int(i) for i in np.flatnonzero(groups > tolerance)),
            key=lambda i: (-groups[i], i),
        )
        top_groups = []
        for group in ranked[:top]:
            members = [
                int(i) for i in np.flatnonzero(abstract.exact_to_abstract == group)
            ]
            # Full details retain every info; displayed action comparisons need
            # positive saved reach, which also gives opponent/chance support.
            rows = [
                example(exact, i, policy, trace)
                for i in members
                if trace.saved_reach_mass[i] > 0 and trace.counterfactual_mass[i] > 0
            ]
            rows.sort(key=lambda r: (-r["loss_contribution_chips"], r["exact_info"]))
            chosen, seen = [], set()
            for row in rows:
                if row["reply_action"] not in seen:
                    chosen.append(row)
                    seen.add(row["reply_action"])
            chosen += [r for r in rows if r not in chosen]
            top_groups.append(
                {
                    "abstract_info": group,
                    "exact_members": len(members),
                    "loss_contribution_chips": float(groups[group]),
                    "examples": chosen[:examples],
                }
            )
        infos = [int(i) for i in np.flatnonzero(exact.owners == target)]
        street_losses: dict[str, float] = {}
        for info in infos:
            state = exact.source.states[exact.source.representatives[info]]
            assert state.dealer is not None
            street = state.dealer.street.name
            street_losses[street] = street_losses.get(street, 0.0) + float(
                trace.losses[info]
            )
        summaries.append(
            {
                "target": target,
                "baseline_value_chips": baseline,
                "exact_reply_value_chips": trace.value,
                "restricted_reply_value_chips": limited_value,
                "exact_gain_chips": trace.gain,
                "within_partition_gain_chips": limited_value - baseline,
                "extra_information_value_chips": trace.value - limited_value,
                "loss_sum_chips": float(trace.losses.sum()),
                "accounting_error_chips": trace.accounting_error,
                "street_losses_chips": street_losses,
                "top_groups": top_groups,
            }
        )
        details.append(
            {
                "target": target,
                "exact_reply_profile": exact.exact_policy(trace.profile),
                "restricted_reply_profile": exact.exact_policy(expanded),
                "infos": [
                    {
                        "exact_info": i,
                        "abstract_info": int(abstract.exact_to_abstract[i]),
                        "loss_chips": float(trace.losses[i]),
                        "counterfactual_mass": float(trace.counterfactual_mass[i]),
                        "saved_reach_mass": float(trace.saved_reach_mass[i]),
                        "conditional_values_chips": trace.conditional_values[
                            i, : len(exact.actions[i])
                        ].tolist(),
                    }
                    for i in infos
                ],
            }
        )
    restricted = sum(r["within_partition_gain_chips"] for r in summaries) / 2
    extra = sum(r["extra_information_value_chips"] for r in summaries) / 2
    if abs(metrics.exploitability - restricted - extra) > tolerance:
        raise ArithmeticError("response exploitability accounting mismatch")
    return (
        {
            "spot": exact.source.spot.name,
            "pot": exact.source.spot.pot,
            "saved_value_player_zero_chips": metrics.value_player_zero,
            "exact_exploitability_chips": metrics.exploitability,
            "restricted_exploitability_chips": restricted,
            "extra_information_chips": extra,
            "responses": summaries,
        },
        {"responses": details},
    )


def diagnose(root: Path, config_path: Path, output: Path) -> dict[str, Any]:
    started = time.perf_counter()
    started_at = datetime.now(UTC).isoformat()
    config = json.loads(config_path.read_text())
    validate_config(config)
    sidecar = output.with_name(output.stem + "-details.json.gz")
    if output.exists() or sidecar.exists():
        raise FileExistsError("retain existing reply diagnosis; choose a new output")
    path = root / config["input_report"]
    if digest(path) != config["input_report_sha256"]:
        raise ArithmeticError("reply input report changed")
    report, policies = checked_artifacts(path)
    verify_inputs(root, report)
    if (
        report["own_policies_sha256"] != config["input_policy_sha256"]
        or config["iteration"] != report["config"]["full_tree_checkpoints"][-1]
    ):
        raise ArithmeticError("reply input policy/checkpoint changed")
    provenance = source_provenance(
        root, config_path, entrypoints=("scripts/diagnose_saved_replies.py",)
    )
    if provenance["dirty"] is not False:
        raise ValueError("publish tested reply code/config first; use clean source")
    model = CardAbstraction.load(root / report["config"]["model"])
    cases, details = [], []
    for filename in report["config"]["spot_files"]:
        source = SpotTree.build(load_spot(root / filename))
        exact = MatrixTree.build(source)
        for name in config["representations"]:
            abstract = build_representation(source, name, model)
            selected = [
                p
                for p in policies
                if p["spot_file"] == filename
                and p["representation"] == name
                and p["iteration"] == config["iteration"]
            ]
            if len(selected) != 1:
                raise ArithmeticError("missing unique saved reply input")
            dense = exact.dense_exact(
                tuple(tuple(v for v in r) for r in selected[0]["policy"])
            )
            case, detail = analyse(
                exact,
                abstract,
                dense,
                top=config["top_groups"],
                examples=config["examples_per_group"],
                tolerance=config["tolerance_chips"],
            )
            recorded = next(
                r
                for r in report["rows"]
                if all(r[k] == selected[0][k] for k in (*IDENTITY, "iteration"))
            )
            if (
                abs(
                    case["exact_exploitability_chips"]
                    - recorded["exploitability_chips"]
                )
                > config["tolerance_chips"]
            ):
                raise ArithmeticError("saved reply epsilon replay mismatch")
            identity = {"spot_file": filename, "representation": name}
            cases.append({**identity, **case})
            details.append({**identity, **detail})
            print(f"reply diagnosis: {source.spot.name}/{name}", flush=True)
    verify_inputs(root, report)
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
        "started_at_utc": started_at,
        "seconds": time.perf_counter() - started,
        "details_file": sidecar.name,
        "details_sha256": digest(sidecar),
        "cases": cases,
        "scope": (
            "fixed saved known-game profiles; no training, feature selection "
            "or fresh/global admission"
        ),
    }
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return result


def checked_details(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report: dict[str, Any] = json.loads(path.read_text())
    validate_config(report["config"])
    sidecar = path.parent / report["details_file"]
    if (
        report["format"] != FORMAT
        or report["status"] != "completed"
        or digest(sidecar) != report["details_sha256"]
    ):
        raise ArithmeticError("reply diagnosis format/status/details changed")
    details = json.loads(gzip.decompress(sidecar.read_bytes()))
    ids = [tuple(c[k] for k in IDENTITY) for c in report["cases"]]
    other_ids = [tuple(c[k] for k in IDENTITY) for c in details["cases"]]
    if (
        details["format"] != DETAIL_FORMAT
        or len(ids) != len(set(ids))
        or ids != other_ids
    ):
        raise ArithmeticError("reply details grid changed")
    return report, details["cases"]


def numerical_difference(actual: Any, recorded: Any) -> float:
    """Compare a complete nested receipt, allowing only finite float roundoff."""
    if isinstance(actual, float):
        if not isinstance(recorded, (float, int)) or not np.isfinite(recorded):
            raise ArithmeticError("nonfinite/changed reply number")
        return abs(actual - float(recorded))
    if isinstance(actual, dict):
        if not isinstance(recorded, dict) or actual.keys() != recorded.keys():
            raise ArithmeticError("changed reply fields")
        return max(
            (numerical_difference(v, recorded[k]) for k, v in actual.items()), default=0
        )
    if isinstance(actual, (tuple, list)):
        if not isinstance(recorded, (tuple, list)) or len(actual) != len(recorded):
            raise ArithmeticError("changed reply sequence")
        return max(
            (numerical_difference(a, b) for a, b in zip(actual, recorded, strict=True)),
            default=0,
        )
    if actual != recorded:
        raise ArithmeticError("changed reply identity/claim")
    return 0


def replay(
    root: Path, path: Path
) -> tuple[dict[str, Any], list[dict[str, Any]], float]:
    report, details = checked_details(path)
    config = report["config"]
    for name, sha in report["source"]["sha256"].items():
        if digest(root / name) != sha:
            raise ArithmeticError("saved-reply source/config changed")
    input_path = root / config["input_report"]
    if digest(input_path) != config["input_report_sha256"]:
        raise ArithmeticError("saved-reply input changed")
    original, policies = checked_artifacts(input_path)
    verify_inputs(root, original)
    if original["own_policies_sha256"] != config["input_policy_sha256"]:
        raise ArithmeticError("saved-reply policy input changed")
    expected = {
        (p, e)
        for p in original["config"]["spot_files"]
        for e in config["representations"]
    }
    if {tuple(c[k] for k in IDENTITY) for c in report["cases"]} != expected:
        raise ArithmeticError("incomplete reply case grid")
    model = CardAbstraction.load(root / original["config"]["model"])
    error = 0.0
    for filename in original["config"]["spot_files"]:
        source = SpotTree.build(load_spot(root / filename))
        exact = MatrixTree.build(source)
        for name in config["representations"]:
            selected = [
                p
                for p in policies
                if p["spot_file"] == filename
                and p["representation"] == name
                and p["iteration"] == config["iteration"]
            ]
            if len(selected) != 1:
                raise ArithmeticError("missing replay checkpoint")
            abstract = build_representation(source, name, model)
            policy = exact.dense_exact(
                tuple(tuple(v for v in row) for row in selected[0]["policy"])
            )
            actual, detail = analyse(
                exact,
                abstract,
                policy,
                top=config["top_groups"],
                examples=config["examples_per_group"],
                tolerance=config["tolerance_chips"],
            )
            identity = {"spot_file": filename, "representation": name}
            case = next(
                c
                for c in report["cases"]
                if all(c[k] == v for k, v in identity.items())
            )
            recorded = next(
                c for c in details if all(c[k] == v for k, v in identity.items())
            )
            error = max(
                error,
                numerical_difference({**identity, **actual}, case),
                numerical_difference({**identity, **detail}, recorded),
            )
    if error > config["tolerance_chips"]:
        raise ArithmeticError("saved-reply numerical replay mismatch")
    return report, details, error
