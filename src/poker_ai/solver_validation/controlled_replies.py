"""Native scalar comparisons for crossed OWN controlled profiles, never training."""

import json
import math
import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import controlled_reply_io as own
from poker_ai.evaluation.controlled_reply_inputs import (
    Inputs,
    SourcePolicy,
    config_inputs,
)
from poker_ai.evaluation.controlled_reply_math import Reply, crossed_policy
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.controlled_pipeline import license_record
from poker_ai.solver_validation.reference import Reference
from poker_ai.solver_validation.reply_diagnosis import partition_source

FORMAT = "poker-ai-controlled-reply-native-v1"


def references(data: Inputs) -> dict[tuple[str, str], Reference]:
    result = {}
    for key, context in data.contexts.items():
        if not isinstance(context.partition, MatrixTree):
            raise ValueError("native controlled replies require poker matrix sources")
        result[key] = Reference(
            context.partition.source
            if context.partition is context.exact
            else partition_source(context.partition)
        )
    return result


def compare_cross(
    data: Inputs,
    record: dict[str, Any],
    profiles: dict[str, SourcePolicy],
    replies: dict[tuple[str, int], Reply],
    reference: Reference,
) -> dict[str, Any]:
    a, b = profiles[record["first_id"]], profiles[record["second_id"]]
    context = data.context(a.case)
    tree = context.partition
    policy = crossed_policy(tree, a.policy, b.policy)

    def packed(p: Any) -> tuple[tuple[float, ...], ...]:
        return tuple(
            tuple(float(v) for v in p[i, : len(menu)])
            for i, menu in enumerate(tree.actions)
        )

    value = reference.value(packed(policy))
    responses = []
    errors = [abs(value - record["value_player_zero_chips"])]
    native_policy = reference.native_policy(packed(policy))
    for target, opponent in ((0, b), (1, a)):
        root = float(
            reference.pyspiel.TabularBestResponse(
                reference.game, target, native_policy
            ).value("")
        )
        reply = replies[opponent.identifier, target]
        achieved = (1 if target == 0 else -1) * reference.value(
            packed(reply.apply(tree, policy))
        )
        gain = root - (1 if target == 0 else -1) * value
        row = dict(
            target=target,
            restricted_reply_value_chips=root,
            achieved_reply_value_chips=achieved,
            gain_chips=gain,
        )
        peer = record["responses"][target]
        errors.extend(
            abs(row[k] - peer[k])
            for k in (
                "restricted_reply_value_chips",
                "achieved_reply_value_chips",
                "gain_chips",
            )
        )
        responses.append(row)
    if any(not math.isfinite(e) for e in errors):
        raise ArithmeticError("nonfinite native crossed comparison")
    return dict(
        value_player_zero_chips=value,
        responses=responses,
        maximum_error_chips=max(errors),
    )


def validate(
    saved: dict[str, Any], original: dict[str, Any], path: Path, data: Inputs
) -> dict[str, Any]:
    replayed = saved["own_replay"]
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or not same(saved["config"], data.config)
        or saved["own_sha256"] != digest(path)
        or saved["details_sha256"] != original["details_sha256"]
        or saved["reference_output_used_in_training"] is not False
        or not number(saved["seconds"], nonnegative=True)
        or saved["seconds"] >= data.config["maximum_native_seconds"]
        or saved["license"]["sha256"]
        != data.config["native_reference"]["license_sha256"]
        or len(saved["comparisons"]) != 256
        or replayed["status"] != "all_controlled_reply_rows_replayed"
        or not same(replayed["target_traces"], 128)
        or not number(replayed["maximum_error_chips"], nonnegative=True)
        or replayed["maximum_error_chips"] > data.config["tolerance_chips"]
        or not number(replayed["seconds"], nonnegative=True)
        or replayed["seconds"] > saved["seconds"]
    ):
        raise ArithmeticError("incomplete/changed native controlled reply receipt")
    maximum = 0.0
    for index, (result, peer) in enumerate(
        zip(saved["comparisons"], original["crosses"], strict=True)
    ):
        if (
            not same(result["index"], index)
            or result["first_id"] != peer["first_id"]
            or result["second_id"] != peer["second_id"]
            or len(result["responses"]) != 2
            or not same([r["target"] for r in result["responses"]], [0, 1])
            or not number(result["value_player_zero_chips"])
        ):
            raise ArithmeticError("native crossed source/target order changed")
        errors = [
            abs(result["value_player_zero_chips"] - peer["value_player_zero_chips"])
        ]
        for target, response in enumerate(result["responses"]):
            for key in (
                "restricted_reply_value_chips",
                "achieved_reply_value_chips",
                "gain_chips",
            ):
                if not number(response[key]):
                    raise ArithmeticError("invalid native crossed scalar")
                errors.append(abs(response[key] - peer["responses"][target][key]))
        error = max(errors)
        if (
            not same(error, result["maximum_error_chips"])
            or error > data.config["tolerance_chips"]
        ):
            raise ArithmeticError("native crossed root/own reply comparison changed")
        maximum = max(maximum, error)
    return dict(
        status="all_crossed_controlled_replies_audited",
        crossed_profiles=256,
        target_conditions=512,
        maximum_error_chips=maximum,
        seconds=saved["seconds"],
        reference_strategies_used_in_training=False,
    )


def run(root: Path, path: Path, output: Path) -> dict[str, Any]:
    if output.exists() or output.with_suffix(".tmp").exists():
        raise FileExistsError("retain native controlled reply attempt")
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    deadline = Deadline(900)
    provenance = own.source(root)
    if provenance["dirty"] is not False:
        raise ValueError("publish own controlled reply results before native audit")
    config = config_inputs(root)
    initial = json.loads(path.read_text())
    saved: dict[str, Any] = dict(
        format=FORMAT,
        status="running",
        failure=None,
        config=config,
        source=provenance,
        environment=runtime_environment(),
        license=None,
        own_sha256=digest(path),
        details_sha256=initial["details_sha256"],
        own_replay=None,
        comparisons=[],
        seconds=0.0,
        reference_output_used_in_training=False,
    )
    persist(output, saved)
    try:
        original, data, replayed = own.replay(root, path, deadline)
        saved["own_replay"] = replayed
        saved["license"] = license_record(data.config)
        profiles = {p.identifier: p for p in data.policies}
        replies = {}
        for record in own.trace_records(path, original, data):
            deadline.check()
            s = record["summary"]
            replies[s["profile_id"], s["target"]] = Reply(
                s["target"],
                s["restricted_reply_value_chips"],
                tuple(r[5] for r in record["rows"]),
            )
        refs = references(data)
        for index, record in enumerate(original["crosses"]):
            deadline.check()
            key = record["group"]["spot_file"], record["group"]["representation"]
            result = compare_cross(data, record, profiles, replies, refs[key])
            if result["maximum_error_chips"] > data.config["tolerance_chips"]:
                raise ArithmeticError("independent controlled reply comparison failed")
            saved["comparisons"].append(
                dict(
                    index=index,
                    first_id=record["first_id"],
                    second_id=record["second_id"],
                    **result,
                )
            )
            saved["seconds"] = time.perf_counter() - started
            persist(output, saved)
        saved["status"] = "completed"
        saved["seconds"] = time.perf_counter() - started
        validate(saved, original, path, data)
        deadline.check()
    except BaseException as error:
        saved["status"] = "incomplete"
        saved["failure"] = dict(type=type(error).__name__, reason=str(error))
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
