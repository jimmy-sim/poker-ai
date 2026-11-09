"""Comparison-only native scalars for OWN current/whole/suffix strategies."""

import json
import math
import os
import time
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation import averaging_history_protocol as protocol
from poker_ai.evaluation import averaging_history_run as own
from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs, inputs
from poker_ai.evaluation.averaging_history_replay import archive_path
from poker_ai.evaluation.controlled_reply_inputs import SourcePolicy
from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.learning_artifacts import read_archive, sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_training import replay_detail
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.controlled_pipeline import (
    compare_one,
    license_record,
    references,
)
from poker_ai.solver_validation.reference import Reference

FORMAT = "poker-ai-averaging-history-native-v1"
FIXED_FIELDS = (
    "target",
    "own_snapshot_id",
    "own_source_profile_id",
    "own_variant",
    "opponent_profile_id",
    "own_policy_sha256",
    "opponent_policy_sha256",
    "reply_sha256",
)


def packed(tree: ArrayTree, policy: FloatArray) -> tuple[tuple[float, ...], ...]:
    tree.validate_policy(policy)
    return tuple(
        tuple(float(v) for v in policy[i, : len(menu)])
        for i, menu in enumerate(tree.actions)
    )


def compare_fixed(
    data: HistoryInputs,
    peer: dict[str, Any],
    candidate: FloatArray,
    opponents: dict[str, SourcePolicy],
    reference: Reference,
    cache: dict[tuple[str, int], tuple[str, float, float]],
) -> dict[str, Any]:
    """A fixed-opponent reply is identical after every target-row replacement.

    Native BR/root and achieved OWN reply are evaluated once per opponent/target
    identity. Check the full reply array's bits before reuse. Every new candidate
    EV is independently evaluated, and every target scalar is compared. No native
    action probabilities are exported or supplied to an own learning algorithm.
    """
    target = peer["target"]
    if type(target) is not int or target not in (0, 1):
        raise ValueError("native fixed target must be seat zero or one")
    opponent = opponents[peer["opponent_profile_id"]]
    tree = data.base.context(opponent.case).partition
    tree.validate_policy(candidate)
    if array_sha(candidate) != peer["own_policy_sha256"]:
        raise ArithmeticError("native candidate differs from bound OWN policy")
    mixed = np.where((tree.owners == target)[:, None], candidate, opponent.policy)
    baseline = (1 if target == 0 else -1) * reference.value(packed(tree, mixed))
    reply = data.replies[opponent.identifier, target].apply(tree, mixed)
    fingerprint = array_sha(reply)
    key = opponent.identifier, target
    if key not in cache:
        native_policy = reference.native_policy(packed(tree, mixed))
        root = float(
            reference.pyspiel.TabularBestResponse(
                reference.game, target, native_policy
            ).value("")
        )
        achieved = (1 if target == 0 else -1) * reference.value(packed(tree, reply))
        cache[key] = fingerprint, root, achieved
    elif cache[key][0] != fingerprint:
        raise ArithmeticError("fixed-opponent own reply bits changed across candidates")
    _, root, achieved = cache[key]
    result = dict(
        **{k: peer[k] for k in FIXED_FIELDS},
        baseline_value_chips=baseline,
        restricted_reply_value_chips=root,
        achieved_reply_value_chips=achieved,
        gain_chips=root - baseline,
    )
    errors = [
        abs(result[k] - peer[k])
        for k in (
            "baseline_value_chips",
            "restricted_reply_value_chips",
            "achieved_reply_value_chips",
            "gain_chips",
        )
    ]
    if any(not math.isfinite(e) for e in errors):
        raise ArithmeticError("nonfinite native fixed-opponent comparison")
    result["maximum_error_chips"] = max(errors)
    return result


def self_error(result: dict[str, Any], peer: dict[str, Any]) -> float:
    if (
        not same(result["id"], peer["id"])
        or not same([result["index"], result["order"]], [peer["index"], peer["order"]])
        or result["policy_sha256"] != peer["receipt"]["policy_sha256"]
        or set(result["native_metrics"]) != set(peer["metrics"])
        or len(result["responses"]) != 2
        or not same([r["target"] for r in result["responses"]], [0, 1])
    ):
        raise ArithmeticError("native history self profile/target binding changed")
    errors = []
    for key, value in result["native_metrics"].items():
        if not number(value):
            raise ArithmeticError("nonfinite native history metric")
        errors.append(abs(value - peer["metrics"][key]))
    names = dict(
        exact_root_chips="exact_reply_value_chips",
        restricted_root_chips="restricted_reply_value_chips",
        achieved_exact_chips="exact_reply_value_chips",
        achieved_restricted_chips="restricted_reply_value_chips",
        achieved_river_before_chips="river_before_value_chips",
    )
    for target, response in enumerate(result["responses"]):
        for actual, expected in names.items():
            if not number(response[actual]):
                raise ArithmeticError("nonfinite native history root/achieved value")
            errors.append(abs(response[actual] - peer["responses"][target][expected]))
    error = max(errors)
    if not same(error, result["maximum_error_chips"]):
        raise ArithmeticError("native self error summary changed")
    return float(error)


def fixed_error(result: dict[str, Any], peer: dict[str, Any]) -> float:
    if any(not same(result[k], peer[k]) for k in FIXED_FIELDS):
        raise ArithmeticError("native fixed target/source/reply binding changed")
    errors = []
    for key in (
        "baseline_value_chips",
        "restricted_reply_value_chips",
        "achieved_reply_value_chips",
        "gain_chips",
    ):
        if not number(result[key]):
            raise ArithmeticError("nonfinite native fixed target value")
        errors.append(abs(result[key] - peer[key]))
    error = max(errors)
    if not same(error, result["maximum_error_chips"]):
        raise ArithmeticError("native fixed error summary changed")
    return float(error)


def validate(
    saved: dict[str, Any], original: dict[str, Any], path: Path, data: HistoryInputs
) -> dict[str, Any]:
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or not same(saved["config"], data.config)
        or saved["own_sha256"] != digest(path)
        or saved["details_sha256"] != original["details_sha256"]
        or saved["mass_details_sha256"] != original["mass_details_sha256"]
        or saved["source_sha256"] != original["source_sha256"]
        or saved["source"]["dirty"] is not False
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["reference_output_used_in_training"] is not False
        or not number(saved["seconds"], nonnegative=True)
        or saved["seconds"] >= data.config["maximum_native_seconds"]
        or saved["license"]["sha256"]
        != data.config["native_reference"]["license_sha256"]
        or len(saved["self_comparisons"]) != 512
        or len(saved["fixed_comparisons"]) != 2048
        or not same(saved["fixed_opponent_target_identities_evaluated"], 128)
    ):
        raise ArithmeticError("incomplete/changed averaging native receipt")
    protocol.validate_replay(saved["own_replay"], data.config)
    if saved["own_replay"]["seconds"] > saved["seconds"]:
        raise ArithmeticError("native input replay exceeds recorded native stage")
    errors = [
        self_error(result, peer)
        for result, peer in zip(
            saved["self_comparisons"], original["rows"], strict=True
        )
    ]
    peers = {
        (r["own_snapshot_id"], r["opponent_profile_id"], r["target"]): r
        for r in original["fixed_matches"]
    }
    identities = [
        (r["own_snapshot_id"], r["opponent_profile_id"], r["target"])
        for r in saved["fixed_comparisons"]
    ]
    if (
        len(peers) != 2048
        or len(set(identities)) != 2048
        or set(identities) != set(peers)
    ):
        raise ArithmeticError("native averaging fixed target grid incomplete/duplicate")
    errors.extend(
        fixed_error(row, peers[key])
        for row, key in zip(saved["fixed_comparisons"], identities, strict=True)
    )
    maximum = max(errors)
    if maximum > data.config["tolerance_chips"]:
        raise ArithmeticError("native averaging value/root/achieved reply mismatch")
    return dict(
        status="all_averaging_history_native_comparisons_passed",
        self_profiles=512,
        fixed_target_conditions=2048,
        fixed_opponent_target_identities_evaluated=128,
        maximum_error_chips=maximum,
        seconds=saved["seconds"],
        reference_strategies_used_in_training=False,
    )


def run(root: Path, path: Path, output: Path) -> dict[str, Any]:
    if output.exists() or output.with_suffix(".tmp").exists():
        raise FileExistsError("retain averaging native attempt")
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    config = inputs(root)
    deadline = Deadline(config["maximum_native_seconds"])
    deadline.started = started
    source = protocol.source(root)
    if source["dirty"] is not False:
        raise ValueError(
            "publish complete OWN averaging evidence before native comparison"
        )
    initial = json.loads(path.read_text())
    saved: dict[str, Any] = dict(
        format=FORMAT,
        status="running",
        failure=None,
        config=config,
        source=source,
        source_sha256=initial["source_sha256"],
        environment=runtime_environment(),
        license=None,
        own_sha256=digest(path),
        details_sha256=initial["details_sha256"],
        mass_details_sha256=initial["mass_details_sha256"],
        own_replay=None,
        self_comparisons=[],
        fixed_comparisons=[],
        fixed_opponent_target_identities_evaluated=0,
        seconds=0.0,
        reference_output_used_in_training=False,
    )
    persist(output, saved)
    try:
        original, data, proof = own.replay(root, path, deadline)
        saved["own_replay"] = proof
        if sha(source["sha256"]) != original["source_sha256"]:
            raise ArithmeticError(
                "native source differs from checked OWN implementation"
            )
        saved["license"] = license_record(config)
        refs = references(data.base.contexts)
        opponents = {p.identifier: p for p in data.base.policies}
        fixed: dict[str, list[dict[str, Any]]] = {}
        for match in original["fixed_matches"]:
            fixed.setdefault(match["own_snapshot_id"], []).append(match)
        cache: dict[tuple[str, int], tuple[str, float, float]] = {}
        for row, blob in read_archive(
            archive_path(path, original["details_file"]),
            original["details_sha256"],
            original["rows"],
        ):
            deadline.check()
            key = row["case"]["spot_file"], row["case"]["representation"]
            context = data.base.context(row["case"])
            _, detail = replay_detail(
                context, row, blob, data.config["tolerance_chips"]
            )
            result = dict(
                id=row["id"],
                index=row["index"],
                order=row["order"],
                policy_sha256=row["receipt"]["policy_sha256"],
                **compare_one(context, refs[key], detail),
            )
            if self_error(result, row) > data.config["tolerance_chips"]:
                raise ArithmeticError("native history self comparison failed")
            saved["self_comparisons"].append(result)
            from poker_ai.postflop.controlled_checkpoints import unpack_policy

            candidate = unpack_policy(context.partition, detail["policy"])
            for peer in fixed.get(row["id"], []):
                deadline.check()
                result = compare_fixed(
                    data, peer, candidate, opponents, refs[key][1], cache
                )
                if fixed_error(result, peer) > data.config["tolerance_chips"]:
                    raise ArithmeticError(
                        "native history fixed target comparison failed"
                    )
                saved["fixed_comparisons"].append(result)
            if row["order"] == 7:
                saved["fixed_opponent_target_identities_evaluated"] = len(cache)
                saved["seconds"] = time.perf_counter() - started
                persist(output, saved)
        saved["status"] = "completed"
        saved["seconds"] = time.perf_counter() - started
        saved["fixed_opponent_target_identities_evaluated"] = len(cache)
        validate(saved, original, path, data)
        deadline.check()
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        saved["seconds"] = time.perf_counter() - started
        saved["parent_cpu_seconds"] = time.process_time() - cpu
        now = os.times()
        saved["reaped_children_cpu_seconds"] = (
            now.children_user
            + now.children_system
            - children.children_user
            - children.children_system
        )
        persist(output, saved)
    return saved
