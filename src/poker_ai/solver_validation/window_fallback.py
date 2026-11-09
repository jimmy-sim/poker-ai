"""Comparison-only native scalars for every saved-window fill and fixed target."""

import json
import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import window_fallback_run as own
from poker_ai.evaluation.averaging_history_replay import archive_path
from poker_ai.evaluation.window_fallback_inputs import FallbackInputs, inputs
from poker_ai.evaluation.window_fallback_math import LABELS, panel_identity
from poker_ai.evaluation.window_fallback_validation import validate_replay
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.learning_artifacts import read_archive, sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_training import replay_detail
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.averaging_history import (
    compare_fixed,
    fixed_error,
    self_error,
)
from poker_ai.solver_validation.controlled_pipeline import (
    compare_one,
    license_record,
    references,
)

FORMAT = "poker-ai-window-fallback-native-v1"
CONTEXT = ("index", "source_window_id", "window_variant", "fill_label")


def panel(rows: list[dict[str, Any]]) -> dict[str, float]:
    if len(rows) != 4:
        raise ArithmeticError("native fill panel incomplete")
    scores = {
        label: dict(
            metrics=row["native_metrics"],
            responses=[
                dict(
                    exact_reply_value_chips=r["exact_root_chips"],
                    restricted_reply_value_chips=r["restricted_root_chips"],
                )
                for r in row["responses"]
            ],
        )
        for label, row in zip(LABELS, rows, strict=True)
    }
    return panel_identity(scores)


def differences(rows: list[dict[str, Any]], peers: list[dict[str, Any]]) -> float:
    if len(rows) != 2048 or len(peers) != 2048:
        raise ArithmeticError("native fallback fixed grid incomplete")
    baseline = {}
    maximum = 0.0
    identities = set()
    for row, peer in zip(rows, peers, strict=True):
        if any(not same(row[k], peer[k]) for k in CONTEXT):
            raise ArithmeticError("native fallback fixed context/order changed")
        error = fixed_error(row, peer)
        identity = row["own_snapshot_id"], row["opponent_profile_id"], row["target"]
        if identity in identities:
            raise ArithmeticError("duplicate native fallback target")
        identities.add(identity)
        key = row["index"], row["opponent_profile_id"], row["target"]
        if row["fill_label"] == "raw":
            baseline[key] = row
        raw = baseline[key]
        expected = dict(
            gain_difference_chips=row["gain_chips"] - raw["gain_chips"],
            ev_difference_chips=row["baseline_value_chips"]
            - raw["baseline_value_chips"],
        )
        if any(not number(row[k]) or not same(row[k], v) for k, v in expected.items()):
            raise ArithmeticError(
                "native fallback difference differs from its raw values"
            )
        delta_error = max(abs(row[k] - peer[k]) for k in expected)
        if not same(delta_error, row["maximum_difference_error_chips"]):
            raise ArithmeticError("native fallback difference summary changed")
        maximum = max(maximum, error, delta_error, abs(sum(expected.values())))
    return maximum


def validate(
    saved: dict[str, Any], original: dict[str, Any], path: Path, data: FallbackInputs
) -> dict[str, Any]:
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or not same(saved["config"], data.config)
        or saved["own_sha256"] != digest(path)
        or saved["details_sha256"] != original["details_sha256"]
        or saved["source_sha256"] != original["source_sha256"]
        or saved["source"]["dirty"] is not False
        or sha(saved["source"]["sha256"]) != saved["source_sha256"]
        or saved["reference_output_used_in_training"] is not False
        or not number(saved["seconds"], nonnegative=True)
        or saved["seconds"] >= data.config["maximum_native_seconds"]
        or saved["license"]["sha256"]
        != data.config["native_reference"]["license_sha256"]
        or len(saved["self_comparisons"]) != 512
        or len(saved["panels"]) != 128
        or not same(saved["fixed_opponent_target_identities_evaluated"], 128)
    ):
        raise ArithmeticError("incomplete/changed window fallback native receipt")
    validate_replay(saved["own_replay"], data.config)
    if (
        not same(saved["own_replay"]["upstream_profiles_replayed"], 512)
        or saved["own_replay"]["seconds"] > saved["seconds"]
    ):
        raise ArithmeticError("native fallback input replay incomplete/outside stage")
    errors = [
        self_error(row, peer)
        for row, peer in zip(saved["self_comparisons"], original["rows"], strict=True)
    ]
    for index, record in enumerate(saved["panels"]):
        actual = panel(saved["self_comparisons"][4 * index : 4 * index + 4])
        if not same(record, dict(index=index, **actual)):
            raise ArithmeticError("native fallback panel identity/summary changed")
        peer = original["panels"][index]
        errors.extend(
            [
                actual["maximum_error_chips"],
                abs(
                    actual["baseline_ev_interaction_chips"]
                    - peer["baseline_ev_interaction_chips"]
                ),
            ]
        )
    errors.append(differences(saved["fixed_comparisons"], original["fixed_matches"]))
    maximum = max(errors)
    if maximum > data.config["tolerance_chips"]:
        raise ArithmeticError("native fallback value/root/achieved reply mismatch")
    return dict(
        status="all_window_fallback_native_comparisons_passed",
        self_profiles=512,
        fixed_target_conditions=2048,
        additivity_panels=128,
        fixed_opponent_target_identities_evaluated=128,
        maximum_error_chips=maximum,
        seconds=saved["seconds"],
        reference_strategies_used_in_training=False,
    )


def run(root: Path, path: Path, output: Path) -> dict[str, Any]:
    if output.exists() or output.with_suffix(".tmp").exists():
        raise FileExistsError("retain complete/partial native window fallback attempt")
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    config = inputs(root)
    deadline = Deadline(config["maximum_native_seconds"])
    deadline.started = started
    source = own.source(root)
    if source["dirty"] is not False:
        raise ValueError("publish complete own fallback evidence before native audit")
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
        own_replay=None,
        self_comparisons=[],
        fixed_comparisons=[],
        panels=[],
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
                "native fallback source differs from checked own code"
            )
        saved["license"] = license_record(config)
        refs = references(data.history.base.contexts)
        opponents = {p.identifier: p for p in data.history.base.policies}
        by_profile: dict[str, list[dict[str, Any]]] = {}
        for match in original["fixed_matches"]:
            by_profile.setdefault(match["own_snapshot_id"], []).append(match)
        cache: dict[tuple[str, int], tuple[str, float, float]] = {}
        baseline = {}
        for row, blob in read_archive(
            archive_path(path, original["details_file"]),
            original["details_sha256"],
            original["rows"],
        ):
            deadline.check()
            context = data.history.base.context(row["case"])
            key = row["case"]["spot_file"], row["case"]["representation"]
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
            if self_error(result, row) > config["tolerance_chips"]:
                raise ArithmeticError("native fallback self comparison failed")
            saved["self_comparisons"].append(result)
            candidate = unpack_policy(context.partition, detail["policy"])
            for peer in by_profile.get(row["id"], []):
                deadline.check()
                result = compare_fixed(
                    data.history, peer, candidate, opponents, refs[key][1], cache
                )
                result.update({k: peer[k] for k in CONTEXT})
                identity = peer["index"], peer["opponent_profile_id"], peer["target"]
                if peer["fill_label"] == "raw":
                    baseline[identity] = result
                raw = baseline[identity]
                result["gain_difference_chips"] = (
                    result["gain_chips"] - raw["gain_chips"]
                )
                result["ev_difference_chips"] = (
                    result["baseline_value_chips"] - raw["baseline_value_chips"]
                )
                result["maximum_difference_error_chips"] = max(
                    abs(result[k] - peer[k])
                    for k in ("gain_difference_chips", "ev_difference_chips")
                )
                if (
                    max(
                        fixed_error(result, peer),
                        result["maximum_difference_error_chips"],
                    )
                    > config["tolerance_chips"]
                ):
                    raise ArithmeticError("native fallback fixed comparison failed")
                saved["fixed_comparisons"].append(result)
            if row["order"] == 3:
                actual = panel(saved["self_comparisons"][-4:])
                saved["panels"].append(dict(index=row["index"], **actual))
                saved["fixed_opponent_target_identities_evaluated"] = len(cache)
                saved["seconds"] = time.perf_counter() - started
                persist(output, saved)
        saved["status"] = "completed"
        saved["seconds"] = time.perf_counter() - started
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
