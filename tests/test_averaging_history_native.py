"""Native adapter checks; fictional receipt grids are explicitly not evidence."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import averaging_history_protocol as protocol
from poker_ai.evaluation import averaging_history_run as own
from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.averaging_history_inputs import inputs, load
from poker_ai.evaluation.averaging_history_math import fixed_match
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation import averaging_history as native

ROOT = Path(__file__).resolve().parents[1]


def forbidden(*args: Any, **kwargs: Any) -> None:
    raise AssertionError("new learning/reference strategy export forbidden")


@pytest.mark.slow
def test_old_medium_policies_check_both_target_signs_and_cached_replies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("pyspiel")
    from poker_ai.postflop.controlled_checkpoints import pack_policy
    from poker_ai.solver_validation.controlled_pipeline import compare_one, references
    from poker_ai.solver_validation.reference import Reference

    monkeypatch.setattr(ControlledTrainer, "step", forbidden)
    monkeypatch.setattr(ControlledTrainer, "initialize_exact", forbidden)
    monkeypatch.setattr(Reference, "policy", forbidden)
    monkeypatch.setattr(Reference, "train_to", forbidden)
    data = load(ROOT)
    candidates = [
        p
        for p in data.base.policies
        if p.case["spot_file"].endswith("dev_medium_oop.json")
        and p.case["representation"] == "texture_range_q8_b8"
        and p.case["traversal"] == "external"
        and p.case["seed"] == 20261301
    ]
    assert len(candidates) == 4
    opponent = candidates[0]
    context = data.base.context(opponent.case)
    key = opponent.case["spot_file"], opponent.case["representation"]
    refs = references({key: context})[key]
    reference = refs[1]
    score = context.score(opponent.policy)
    detail = dict(
        opponent.row,
        policy=pack_policy(context.partition, opponent.policy),
        replies=[
            {k: pack_policy(context.exact, v) for k, v in r.items()}
            for r in score.replies
        ],
    )
    peer_self = dict(opponent.row, order=5)
    result_self = dict(
        id=peer_self["id"],
        index=peer_self["index"],
        order=5,
        policy_sha256=array_sha(opponent.policy),
        **compare_one(context, refs, detail),
    )
    assert native.self_error(result_self, peer_self) <= 1e-9
    opponents = {opponent.identifier: opponent}
    cache: dict[tuple[str, int], tuple[str, float, float]] = {}
    for candidate in candidates:
        for target in (0, 1):
            reply = data.replies[opponent.identifier, target]
            peer = dict(
                **fixed_match(
                    context.partition, candidate.policy, opponent.policy, reply
                ),
                own_snapshot_id="OLD_OWN_POLICY_ADAPTER_TEST",
                own_source_profile_id=candidate.identifier,
                own_variant="whole_average",
                opponent_profile_id=opponent.identifier,
                own_policy_sha256=array_sha(candidate.policy),
                opponent_policy_sha256=array_sha(opponent.policy),
                reply_sha256=opponent.row["reply_sha256"][target]["restricted"],
            )
            result = native.compare_fixed(
                data, peer, candidate.policy, opponents, reference, cache
            )
            assert native.fixed_error(result, peer) <= 1e-9
            with pytest.raises(ArithmeticError, match="bound OWN policy"):
                native.compare_fixed(
                    data,
                    dict(peer, own_policy_sha256="0" * 64),
                    candidate.policy,
                    opponents,
                    reference,
                    cache,
                )
    assert len(cache) == 2
    changed = dict(cache)
    fingerprint, root, achieved = changed[opponent.identifier, 1]
    changed[opponent.identifier, 1] = "0" * 64, root, achieved
    assert fingerprint != "0" * 64
    with pytest.raises(ArithmeticError, match="reply bits changed"):
        native.compare_fixed(
            data, peer, candidate.policy, opponents, reference, changed
        )


def fictional_replay() -> dict[str, Any]:
    return dict(
        status="all_averaging_history_profiles_and_windows_replayed",
        new_postflop_training_performed=False,
        seconds=0.1,
        source_cases=64,
        profiles=512,
        cumulative_boundaries=192,
        suffix_reconstructions=128,
        whole_reconstructions=64,
        identical_current_pairs=160,
        fixed_opponent_target_conditions=2048,
        maximum_error_chips=0.0,
        maximum_error_unitless=0.0,
        maximum_fixed_identity_error_chips=0.0,
    )


@pytest.fixture
def fictional_native(tmp_path: Path) -> tuple[Any, ...]:
    """Invented schema-only scalars; no reference constructor or scientific claim."""
    from types import SimpleNamespace

    config = inputs(ROOT)
    path = tmp_path / "EXPLICIT_FICTIONAL_SCHEMA_NOT_RESEARCH.json"
    path.write_text("{}\n")
    source: dict[str, Any] = dict(dirty=False, sha256={"EXPLICIT_FIXTURE": "f" * 64})
    rows, comparisons = [], []
    for i in range(512):
        responses = [
            dict(
                exact_reply_value_chips=1.0 + target,
                restricted_reply_value_chips=0.5 + target,
                river_before_value_chips=0.25 + target,
            )
            for target in (0, 1)
        ]
        metrics = {"FICTIONAL_SCHEMA_METRIC": 0.5}
        rows.append(
            dict(
                id=str(i),
                index=i // 8,
                order=i % 8,
                receipt=dict(policy_sha256="a" * 64),
                metrics=metrics,
                responses=responses,
            )
        )
        comparisons.append(
            dict(
                id=str(i),
                index=i // 8,
                order=i % 8,
                policy_sha256="a" * 64,
                native_metrics=metrics,
                maximum_error_chips=0.0,
                responses=[
                    dict(
                        target=t,
                        exact_root_chips=1.0 + t,
                        restricted_root_chips=0.5 + t,
                        achieved_exact_chips=1.0 + t,
                        achieved_restricted_chips=0.5 + t,
                        achieved_river_before_chips=0.25 + t,
                    )
                    for t in (0, 1)
                ],
            )
        )
    fixed = [
        dict(
            target=t,
            own_snapshot_id=str(i),
            own_source_profile_id=str(i // 8),
            own_variant="FICTIONAL_VARIANT",
            opponent_profile_id=str(o),
            own_policy_sha256="a" * 64,
            opponent_policy_sha256="b" * 64,
            reply_sha256="c" * 64,
            baseline_value_chips=-0.5,
            restricted_reply_value_chips=0.25,
            achieved_reply_value_chips=0.25,
            gain_chips=0.75,
        )
        for i in range(256)
        for o in range(4)
        for t in (0, 1)
    ]
    original = dict(
        rows=rows,
        fixed_matches=fixed,
        details_sha256="d" * 64,
        mass_details_sha256="e" * 64,
        source_sha256=sha(source["sha256"]),
    )
    saved = dict(
        format=native.FORMAT,
        status="completed",
        failure=None,
        config=config,
        own_sha256=digest(path),
        details_sha256="d" * 64,
        mass_details_sha256="e" * 64,
        source=source,
        source_sha256=sha(source["sha256"]),
        seconds=1.0,
        reference_output_used_in_training=False,
        license=dict(sha256=config["native_reference"]["license_sha256"]),
        self_comparisons=comparisons,
        fixed_comparisons=[dict(r, maximum_error_chips=0.0) for r in fixed],
        fixed_opponent_target_identities_evaluated=128,
        own_replay=fictional_replay(),
    )
    return saved, original, path, SimpleNamespace(config=config)


def test_complete_fictional_native_grid_validates_schema_only(
    fictional_native: tuple[Any, ...],
) -> None:
    proof = native.validate(*fictional_native)
    assert proof["self_profiles"] == 512
    assert proof["fixed_target_conditions"] == 2048
    assert proof["maximum_error_chips"] == 0


@pytest.mark.parametrize(
    "mode",
    [
        "partial",
        "failure",
        "source",
        "own_hash",
        "mass_hash",
        "license",
        "cap",
        "nan_seconds",
        "training",
        "self_missing",
        "self_target_bool",
        "self_id",
        "self_metric",
        "self_achieved",
        "self_error",
        "fixed_missing",
        "duplicate",
        "fixed_target_bool",
        "fixed_reply",
        "fixed_nan",
        "fixed_ev",
        "fixed_error",
        "cache_count",
        "replay_count",
        "replay_unitless",
        "replay_seconds",
    ],
)
def test_changed_fictional_receipts_cannot_complete(
    fictional_native: tuple[Any, ...],
    mode: str,
) -> None:
    original_saved, original, path, data = fictional_native
    saved = copy.deepcopy(original_saved)
    first = saved["self_comparisons"][0]
    fixed = saved["fixed_comparisons"][0]
    if mode == "partial":
        saved["status"] = "incomplete"
    elif mode == "failure":
        saved["failure"] = {"reason": "EXPLICIT_FIXTURE"}
    elif mode == "source":
        saved["source"]["sha256"]["EXPLICIT_FIXTURE"] = "0" * 64
    elif mode == "own_hash":
        saved["own_sha256"] = "0" * 64
    elif mode == "mass_hash":
        saved["mass_details_sha256"] = "0" * 64
    elif mode == "license":
        saved["license"]["sha256"] = "0" * 64
    elif mode == "cap":
        saved["seconds"] = 900.0
    elif mode == "nan_seconds":
        saved["seconds"] = float("nan")
    elif mode == "training":
        saved["reference_output_used_in_training"] = True
    elif mode == "self_missing":
        saved["self_comparisons"].pop()
    elif mode == "self_target_bool":
        first["responses"][0]["target"] = False
    elif mode == "self_id":
        first["id"] = "changed"
    elif mode == "self_metric":
        first["native_metrics"]["FICTIONAL_SCHEMA_METRIC"] = float("nan")
    elif mode == "self_achieved":
        first["responses"][0]["achieved_restricted_chips"] += 0.25
        first["maximum_error_chips"] = 0.25
    elif mode == "self_error":
        first["maximum_error_chips"] = 1.0
    elif mode == "fixed_missing":
        saved["fixed_comparisons"].pop()
    elif mode == "duplicate":
        saved["fixed_comparisons"][1] = copy.deepcopy(fixed)
    elif mode == "fixed_target_bool":
        fixed["target"] = False
    elif mode == "fixed_reply":
        fixed["reply_sha256"] = "0" * 64
    elif mode == "fixed_nan":
        fixed["gain_chips"] = float("nan")
    elif mode == "fixed_ev":
        fixed["baseline_value_chips"] += 0.5
        fixed["maximum_error_chips"] = 0.5
    elif mode == "fixed_error":
        fixed["maximum_error_chips"] = 1.0
    elif mode == "cache_count":
        saved["fixed_opponent_target_identities_evaluated"] = 127
    elif mode == "replay_count":
        saved["own_replay"]["profiles"] = 511
    elif mode == "replay_unitless":
        saved["own_replay"]["maximum_error_unitless"] = 2e-11
    else:
        saved["own_replay"]["seconds"] = 2.0
    with pytest.raises(ArithmeticError):
        native.validate(saved, original, path, data)


def test_failed_native_input_replay_is_retained_and_cannot_be_overwritten(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = dict(dirty=False, sha256={"EXPLICIT_SCHEMA_SOURCE": "f" * 64})
    own_path, output = tmp_path / "own.json", tmp_path / "native.json"
    own_path.write_text(
        json.dumps(
            dict(
                source_sha256=sha(source["sha256"]),
                details_sha256="d" * 64,
                mass_details_sha256="e" * 64,
            )
        )
    )
    monkeypatch.setattr(protocol, "source", lambda root: source)
    monkeypatch.setattr(native, "references", forbidden)

    def fail(*args: Any, **kwargs: Any) -> None:
        raise TimeoutError("explicit input replay timeout fixture")

    monkeypatch.setattr(own, "replay", fail)
    with pytest.raises(TimeoutError):
        native.run(ROOT, own_path, output)
    before = output.read_bytes()
    saved = json.loads(before)
    assert saved["status"] == "incomplete"
    assert saved["failure"]["type"] == "TimeoutError"
    assert saved["self_comparisons"] == saved["fixed_comparisons"] == []
    assert saved["own_replay"] is None
    assert saved["seconds"] >= 0
    with pytest.raises(FileExistsError):
        native.run(ROOT, own_path, output)
    assert output.read_bytes() == before


def test_dirty_own_evidence_cannot_start_native_comparison(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(protocol, "source", lambda root: dict(dirty=True))
    monkeypatch.setattr(own, "replay", forbidden)
    with pytest.raises(ValueError, match="publish complete OWN"):
        native.run(ROOT, tmp_path / "unpublished.json", tmp_path / "native.json")
    assert not (tmp_path / "native.json").exists()
