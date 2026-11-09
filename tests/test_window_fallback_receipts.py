"""Fictional byte/native ledgers test schema only, never independent evidence."""

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.averaging_history_math import fixed_match
from poker_ai.evaluation.averaging_history_software import toy_context
from poker_ai.evaluation.controlled_reply_inputs import Inputs, SourcePolicy, expected
from poker_ai.evaluation.controlled_reply_math import trace
from poker_ai.evaluation.window_fallback_compute import evaluate_window, fixed_targets
from poker_ai.evaluation.window_fallback_inputs import FallbackInputs, Window, inputs
from poker_ai.evaluation.window_fallback_validation import grid, validate_replay
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.solver_validation import window_fallback as native

ROOT = Path(__file__).resolve().parents[1]


def fictional_proof() -> dict[str, Any]:
    return dict(
        status="all_window_fallback_profiles_and_targets_replayed",
        new_postflop_training_performed=False,
        source_windows=128,
        profiles=512,
        raw_window_controls=128,
        full_windows=32,
        additivity_panels=128,
        fixed_target_conditions=2048,
        maximum_error_chips=0.0,
        maximum_error_unitless=0.0,
        maximum_full_control_error_chips=0.0,
        maximum_full_realization_change=0.0,
        seconds=0.1,
        upstream_profiles_replayed=512,
    )


@pytest.fixture(scope="module")
def fictional_grid(tmp_path_factory: pytest.TempPathFactory) -> tuple[Any, ...]:
    """Invented snapshot receipts; real tiny math, but NO native solver output."""
    config = copy.deepcopy(inputs(ROOT))
    config["status"] = "EXPLICIT_FICTIONAL_RECEIPTS_NOT_RESEARCH"
    config["spot_files"] = ["EXPLICIT_SCHEMA_LOW", "EXPLICIT_SCHEMA_MEDIUM"]
    context = toy_context()
    tree = context.partition
    uniform = tree.normalize(tree.legal)
    scored = score_data(context, context.score(uniform))
    policies = []
    for i, case_text in enumerate(sorted(expected(config))):
        case = dict(json.loads(case_text), bridge="common", regret_weight="linear")
        policies.append(
            SourcePolicy(
                case,
                dict(
                    id=f"EXPLICIT_SCHEMA_{i}",
                    index=i,
                    receipt=dict(policy_sha256=array_sha(uniform)),
                    **scored,
                ),
                uniform,
            )
        )
    base = Inputs(
        config,
        {},
        dict.fromkeys(
            [(g, n) for g in config["spot_files"] for n in config["representations"]],
            context,
        ),
        tuple(policies),
    )
    replies = {}
    for p in policies:
        for target in (0, 1):
            _, reply, _ = trace(
                tree, p.policy, target, ("TURN",) * len(tree.keys), 1e-9
            )
            replies[p.identifier, target] = reply
    history = HistoryInputs(config, base, {}, replies)
    parent_rows = []
    parent_fixed = []
    windows = []
    for i, p in enumerate(policies):
        for j, variant in enumerate(config["suffix_variants"]):
            row = dict(
                id=f"EXPLICIT_SCHEMA_WINDOW_{2 * i + j}",
                index=i,
                variant=variant,
                receipt=dict(policy_sha256=array_sha(uniform)),
                iteration=10,
                total_work=100,
                window=dict(increment_mass_sha256=array_sha(tree.legal)),
                **scored,
            )
            parent_rows.append(row)
            windows.append(
                Window(
                    2 * i + j,
                    p,
                    row,
                    context,
                    uniform,
                    tree.legal,
                    np.zeros(len(tree.keys), dtype=np.bool_),
                )
            )
            for opponent in policies:
                if opponent.group != p.group:
                    continue
                for target in (0, 1):
                    parent_fixed.append(
                        dict(
                            own_snapshot_id=row["id"],
                            opponent_profile_id=opponent.identifier,
                            **fixed_match(
                                tree,
                                uniform,
                                uniform,
                                replies[opponent.identifier, target],
                            ),
                        )
                    )
    data = FallbackInputs(
        config,
        history,
        dict(rows=parent_rows, fixed_matches=parent_fixed),
        Path("EXPLICIT_NO_UPSTREAM_FILE"),
        {},
        dict(status="EXPLICIT_NO_NATIVE_AUDIT"),
    )
    source = dict(dirty=False, sha256={"EXPLICIT_FICTIONAL_SOURCE": "f" * 64})
    binding = sha(source["sha256"])
    saved: dict[str, Any] = dict(
        scope="EXPLICIT_FICTIONAL_BYTE_RECEIPTS_NOT_RESEARCH",
        source=source,
        source_sha256=binding,
        rows=[],
        panels=[],
        fixed_matches=[],
        own_replay=fictional_proof(),
        details_sha256="a" * 64,
    )
    for window in windows:
        profiles, panel = evaluate_window(window, config, binding, Deadline(120))
        for profile in profiles:
            # Invented byte envelope: only the schema validator uses this fixture.
            saved["rows"].append(
                dict(
                    **profile.metadata,
                    file=f"snapshots/{profile.metadata['id']}.json.gz",
                    metadata_sha256=sha(profile.metadata),
                    receipt=dict(
                        bytes=123,
                        sha256="b" * 64,
                        policy_sha256=array_sha(profile.policy),
                    ),
                )
            )
        saved["panels"].append(panel)
        matches, _ = fixed_targets(window, profiles, data, Deadline(120))
        saved["fixed_matches"].extend(matches)
    path = tmp_path_factory.mktemp("fictional-native") / "EXPLICIT_NOT_RESEARCH.json"
    path.write_text(json.dumps(saved, sort_keys=True))
    return data, saved, path


def test_fictional_grid_checks_schema_without_claiming_byte_or_native_evidence(
    fictional_grid: tuple[Any, ...],
) -> None:
    data, saved, _ = fictional_grid
    grid(saved, data)
    assert len(saved["rows"]) == 512 and len(saved["fixed_matches"]) == 2048


@pytest.mark.parametrize(
    "mode",
    [
        "row_count",
        "row_bool",
        "source",
        "targets",
        "policy",
        "count_bool",
        "count_changed",
        "nan_reach",
        "full_reach",
        "panel_count",
        "panel_source",
        "panel_error",
        "panel_full",
        "fixed_count",
        "fixed_duplicate",
        "fixed_reply",
        "fixed_nan",
        "fixed_ev",
    ],
)
def test_changed_fictional_grid_cannot_complete(
    fictional_grid: tuple[Any, ...], mode: str
) -> None:
    data, original, _ = fictional_grid
    saved = copy.deepcopy(original)
    row = saved["rows"][0]
    if mode == "row_count":
        saved["rows"].pop()
    elif mode == "row_bool":
        row["index"] = False
    elif mode == "source":
        row["source_window_id"] = "changed"
    elif mode == "targets":
        row["fill_targets"] = [False]
    elif mode == "policy":
        row["receipt"]["policy_sha256"] = "0" * 64
    elif mode == "count_bool":
        row["support"][0]["eligible_rows"] = False
    elif mode == "count_changed":
        row["support"][0]["changed_rows"] = 1
    elif mode == "nan_reach":
        row["support"][0]["maximum_own_reach_at_eligible_histories"] = float("nan")
    elif mode == "full_reach":
        next(r for r in saved["rows"] if r["case"]["traversal"] == "full")[
            "maximum_realization_change"
        ] = 2e-11
    elif mode == "panel_count":
        saved["panels"].pop()
    elif mode == "panel_source":
        saved["panels"][0]["index"] = False
    elif mode == "panel_error":
        saved["panels"][0]["maximum_error_chips"] = 1e-8
    elif mode == "panel_full":
        next(r for r in saved["panels"] if r["case"]["traversal"] == "full")[
            "full_control_error_chips"
        ] = None
    elif mode == "fixed_count":
        saved["fixed_matches"].pop()
    elif mode == "fixed_duplicate":
        saved["fixed_matches"][1] = copy.deepcopy(saved["fixed_matches"][0])
    elif mode == "fixed_reply":
        saved["fixed_matches"][0]["reply_sha256"] = "0" * 64
    elif mode == "fixed_nan":
        saved["fixed_matches"][0]["gain_chips"] = float("nan")
    else:
        saved["fixed_matches"][0]["baseline_value_chips"] += 1
    with pytest.raises(ArithmeticError):
        grid(saved, data)


def fictional_native(
    data: FallbackInputs, original: dict[str, Any], path: Path
) -> dict[str, Any]:
    """Copy OWN toy scalars to test fields, explicitly NOT a native comparison."""
    rows = []
    for peer in original["rows"]:
        rows.append(
            dict(
                id=peer["id"],
                index=peer["index"],
                order=peer["order"],
                policy_sha256=peer["receipt"]["policy_sha256"],
                native_metrics=peer["metrics"],
                maximum_error_chips=0.0,
                responses=[
                    dict(
                        target=r["target"],
                        exact_root_chips=r["exact_reply_value_chips"],
                        restricted_root_chips=r["restricted_reply_value_chips"],
                        achieved_exact_chips=r["exact_reply_value_chips"],
                        achieved_restricted_chips=r["restricted_reply_value_chips"],
                        achieved_river_before_chips=r["river_before_value_chips"],
                    )
                    for r in peer["responses"]
                ],
            )
        )
    return dict(
        format=native.FORMAT,
        status="completed",
        failure=None,
        config=data.config,
        scope="EXPLICIT_FICTIONAL_SCHEMA_NO_NATIVE_EVIDENCE",
        own_sha256=digest(path),
        details_sha256=original["details_sha256"],
        source=original["source"],
        source_sha256=original["source_sha256"],
        reference_output_used_in_training=False,
        seconds=100.0,
        license=dict(sha256=data.config["native_reference"]["license_sha256"]),
        own_replay=fictional_proof(),
        self_comparisons=rows,
        panels=[
            dict(index=i, **native.panel(rows[4 * i : 4 * i + 4])) for i in range(128)
        ],
        fixed_comparisons=[
            dict(r, maximum_error_chips=0.0, maximum_difference_error_chips=0.0)
            for r in original["fixed_matches"]
        ],
        fixed_opponent_target_identities_evaluated=128,
    )


def test_fictional_native_receipt_only_demonstrates_complete_schema(
    fictional_grid: tuple[Any, ...],
) -> None:
    data, original, path = fictional_grid
    saved = fictional_native(data, original, path)
    proof = native.validate(saved, original, path, data)
    assert proof["self_profiles"] == 512
    assert proof["fixed_target_conditions"] == 2048
    assert proof["maximum_error_chips"] == 0


@pytest.mark.parametrize(
    "mode",
    [
        "incomplete",
        "failure",
        "own_hash",
        "source",
        "license",
        "cap",
        "seconds_nan",
        "training",
        "self_count",
        "self_bool_target",
        "self_hash",
        "self_nan",
        "self_root",
        "self_error",
        "panels_missing",
        "panel_summary",
        "fixed_count",
        "fixed_duplicate",
        "fixed_context",
        "fixed_target",
        "fixed_root",
        "fixed_delta",
        "fixed_delta_error",
        "cached_count",
        "proof_count",
        "proof_unitless",
        "proof_parent",
        "proof_time",
    ],
)
def test_corrupted_fictional_native_receipts_are_rejected(
    fictional_grid: tuple[Any, ...], mode: str
) -> None:
    data, original, path = fictional_grid
    saved = copy.deepcopy(fictional_native(data, original, path))
    first = saved["self_comparisons"][0]
    fixed = saved["fixed_comparisons"][0]
    if mode == "incomplete":
        saved["status"] = "incomplete"
    elif mode == "failure":
        saved["failure"] = {"reason": "EXPLICIT_FIXTURE"}
    elif mode == "own_hash":
        saved["own_sha256"] = "0" * 64
    elif mode == "source":
        saved["source"]["sha256"]["EXPLICIT_FICTIONAL_SOURCE"] = "0" * 64
    elif mode == "license":
        saved["license"]["sha256"] = "0" * 64
    elif mode == "cap":
        saved["seconds"] = 900.0
    elif mode == "seconds_nan":
        saved["seconds"] = float("nan")
    elif mode == "training":
        saved["reference_output_used_in_training"] = True
    elif mode == "self_count":
        saved["self_comparisons"].pop()
    elif mode == "self_bool_target":
        first["responses"][0]["target"] = False
    elif mode == "self_hash":
        first["policy_sha256"] = "0" * 64
    elif mode == "self_nan":
        first["native_metrics"]["value_player_zero_chips"] = float("nan")
    elif mode == "self_root":
        first["responses"][0]["achieved_restricted_chips"] += 0.25
        first["maximum_error_chips"] = 0.25
    elif mode == "self_error":
        first["maximum_error_chips"] = 1.0
    elif mode == "panels_missing":
        saved["panels"].pop()
    elif mode == "panel_summary":
        saved["panels"][0]["baseline_ev_interaction_chips"] += 0.25
    elif mode == "fixed_count":
        saved["fixed_comparisons"].pop()
    elif mode == "fixed_duplicate":
        saved["fixed_comparisons"][1] = copy.deepcopy(fixed)
    elif mode == "fixed_context":
        fixed["index"] = False
    elif mode == "fixed_target":
        fixed["target"] = False
    elif mode == "fixed_root":
        fixed["achieved_reply_value_chips"] += 0.25
        fixed["maximum_error_chips"] = 0.25
    elif mode == "fixed_delta":
        fixed["ev_difference_chips"] += 0.25
    elif mode == "fixed_delta_error":
        fixed["maximum_difference_error_chips"] = 1.0
    elif mode == "cached_count":
        saved["fixed_opponent_target_identities_evaluated"] = 127
    elif mode == "proof_count":
        saved["own_replay"]["profiles"] = 511
    elif mode == "proof_unitless":
        saved["own_replay"]["maximum_error_unitless"] = 2e-11
    elif mode == "proof_parent":
        saved["own_replay"]["upstream_profiles_replayed"] = 511
    else:
        saved["own_replay"]["seconds"] = 101.0
    with pytest.raises(ArithmeticError):
        native.validate(saved, original, path, data)


@pytest.mark.parametrize(
    "key,value",
    [
        ("profiles", 511),
        ("full_windows", True),
        ("new_postflop_training_performed", True),
        ("maximum_error_unitless", 2e-11),
        ("maximum_full_realization_change", 2e-11),
        ("seconds", float("nan")),
    ],
)
def test_replay_proof_uses_strict_counts_and_separate_unitless_limit(
    key: str, value: Any
) -> None:
    proof = fictional_proof()
    proof[key] = value
    with pytest.raises(ArithmeticError):
        validate_replay(proof, inputs(ROOT))
