"""Independent scalar audit of own fixed-work policies, never training targets.

The adapter owns the432-profile/1152-fixed inventory rather than using the old
144-profile validator. The explicit toy proof additionally checks its separately
retained baseline fixture policies. Partial outcomes remain in raw events.
No native action policy is returned, exported or supplied to an own learner.
"""

import json
import math
from collections.abc import Callable
from pathlib import Path
from typing import Any

from poker_ai.evaluation.controlled_reply_math import Reply
from poker_ai.evaluation.private_prefix_archive import ContextFor
from poker_ai.evaluation.private_prefix_design import OLD, REAL, TOY, index_rows
from poker_ai.finite import FloatArray
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.learning_artifacts import read_archive, sha
from poker_ai.postflop.learning_training import replay_detail
from poker_ai.postflop.parallel_profile import finite, same
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.solver_validation.averaging_history import fixed_error
from poker_ai.solver_validation.frozen_batches import error as self_error
from poker_ai.solver_validation.matched_array_reference import ScalarReference, compare
from poker_ai.solver_validation.matched_update_values import Cache, fixed

FORMAT = "poker-ai-private-prefix-native-comparison-v1"
OpponentFor = Callable[[dict[str, Any]], tuple[FloatArray, Reply]]


def inventory(
    own: dict[str, Any],
) -> tuple[list[tuple[str, list[dict[str, Any]]]], list[dict[str, Any]]]:
    """Core counts stay fixed; additional toy/baseline checks are separate."""
    if len(own["rows"]) != 432 or len(own["fixed_matches"]) != 1152:
        raise ArithmeticError("private-prefix core audit inventory incomplete")
    streams = [("details", own["rows"])]
    fixed_rows = list(own["fixed_matches"])
    if own["scope"] == TOY:
        if len(own["baseline_rows"]) != 648 or len(own["baseline_fixed"]) != 1728:
            raise ArithmeticError("complete explicit toy baseline audit required")
        streams.append(("baseline", own["baseline_rows"]))
        fixed_rows.extend(own["baseline_fixed"])
    elif own["scope"] == OLD:
        pass  # All source currents were already scored; v2 corrects v1.
    elif own["scope"] != REAL:
        raise ArithmeticError("unknown private-prefix audit scope")
    return streams, fixed_rows


def audit_rows(
    path: Path,
    own: dict[str, Any],
    indices: list[int],
    context_for: ContextFor,
    refs: dict[int, tuple[ScalarReference, ScalarReference]],
    opponent_for: OpponentFor,
    send: Send,
    deadline: Deadline,
) -> dict[str, Any]:
    peers: dict[str, list[dict[str, Any]]] = {}
    streams, fixed_rows = inventory(own)
    for row in fixed_rows:
        peers.setdefault(row["own_snapshot_id"], []).append(row)
    cache: Cache = {}
    profiles = targets = 0
    maximum = 0.0
    for prefix, rows in streams:
        for row, blob in read_archive(
            path.with_name(own[prefix + "_file"]), own[prefix + "_sha256"], rows
        ):
            deadline.check()
            index = row["path_index"]
            if index not in indices:
                continue
            context = context_for(index)
            _, detail = replay_detail(context, row, blob, 1e-9)
            result = dict(
                id=row["id"],
                path_index=index,
                work_label=row["work_label"],
                policy_sha256=row["receipt"]["policy_sha256"],
                own_reply_sha256=row["reply_sha256"],
                **compare(context, refs[index], detail),
            )
            error = self_error(result, row)
            if not math.isfinite(error) or error > 1e-9:
                raise ArithmeticError(
                    "private-prefix independent self/root/reply disagreement"
                )
            send(dict(kind="cell", phase="self", index=index, result=result))
            profiles += 1
            maximum = max(maximum, error)
            policy = unpack_policy(context.partition, detail["policy"])
            for peer in peers.get(row["id"], []):
                opponent, reply = opponent_for(peer)
                record = fixed(peer, policy, opponent, reply, refs[index][1], cache)
                error = fixed_error(record, peer)
                if not math.isfinite(error) or error > 1e-9:
                    raise ArithmeticError(
                        "private-prefix independent fixed disagreement"
                    )
                send(dict(kind="cell", phase="fixed", index=index, result=record))
                targets += 1
                maximum = max(maximum, error)
    deadline.check()
    return dict(
        paths=len(indices),
        profiles=profiles,
        fixed_targets=targets,
        cached_opponent_targets=len(cache),
        maximum_error_chips=maximum,
    )


def gather(saved: dict[str, Any]) -> None:
    saved["rows"] = []
    saved["fixed"] = []
    for event in saved["events"]:
        if event["kind"] != "cell" or event["phase"] not in ("self", "fixed"):
            raise ArithmeticError("unknown private-prefix native event")
        key = "rows" if event["phase"] == "self" else "fixed"
        saved[key].append(event["result"])
    saved["rows"].sort(key=lambda r: r["id"])
    saved["fixed"].sort(
        key=lambda r: (r["own_snapshot_id"], r["opponent_profile_id"], r["target"])
    )
    saved["completed_profiles"] = len(saved["rows"])
    saved["completed_fixed_targets"] = len(saved["fixed"])


def validate(
    saved: dict[str, Any], own: dict[str, Any], own_path: Path
) -> dict[str, Any]:
    json.dumps(saved, allow_nan=False)
    streams, fixed_rows = inventory(own)
    peers = [row for _, rows in streams for row in rows]
    expected_profiles = len(peers)
    expected_fixed = len(fixed_rows)
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed_native_comparison_only"
        or saved["failure"] is not None
        or saved["scope"] != own["scope"]
        or not same(saved["reference"], own["config"]["reference"])
        or saved["own_sha256"] != digest(own_path)
        or saved["details_sha256"] != own["details_sha256"]
        or saved["source_sha256"] != own["source_sha256"]
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["publication"]["own_sha256"] != digest(own_path)
        or saved["license"]["sha256"]
        != "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
        or not saved["license"]["installed_license_files"]
        or saved["reference_setup_started"] is not True
        or saved["reference_setup_completed"] is not True
        or any(
            saved[k] is not False
            for k in (
                "training_performed",
                "reference_actions_exported",
                "reference_output_used_in_training",
                "long_run_admitted",
            )
        )
        or not finite(saved["seconds"])
        or saved["seconds"] >= (180 if own["scope"] == TOY else 900)
    ):
        raise ArithmeticError("incomplete/changed private-prefix native header")
    rebuilt = dict(saved)
    gather(rebuilt)
    if any(
        not same(rebuilt[k], saved[k])
        for k in ("rows", "fixed", "completed_profiles", "completed_fixed_targets")
    ):
        raise ArithmeticError(
            "private-prefix native records differ from retained events"
        )
    by_id = {row["id"]: row for row in peers}
    for event in saved["events"]:
        identifier = (
            event["result"]["id"]
            if event["phase"] == "self"
            else event["result"]["own_snapshot_id"]
        )
        if identifier not in by_id or not same(
            event["index"], by_id[identifier]["path_index"]
        ):
            raise ArithmeticError("native event routed to wrong own context")
    maximum = 0.0
    for expected, actual, fields, error in (
        (peers, saved["rows"], ("id",), self_error),
        (
            fixed_rows,
            saved["fixed"],
            ("own_snapshot_id", "opponent_profile_id", "target"),
            fixed_error,
        ),
    ):
        a, b = index_rows(expected, fields), index_rows(actual, fields)
        if set(a) != set(b):
            raise ArithmeticError("private-prefix native inventory missing/extra")
        for key, row in b.items():
            discrepancy = error(row, a[key])
            if not math.isfinite(discrepancy) or discrepancy > 1e-9:
                raise ArithmeticError(
                    "private-prefix native scalar/root/own reply changed"
                )
            maximum = max(maximum, discrepancy)
    if (
        not same(saved["completed_profiles"], expected_profiles)
        or not same(saved["completed_fixed_targets"], expected_fixed)
        or not same(saved["maximum_error_chips"], maximum)
    ):
        raise ArithmeticError("private-prefix native counts/error changed")
    return dict(
        profiles=expected_profiles,
        core_profiles=432,
        core_fixed_targets=1152,
        fixed_targets=expected_fixed,
        maximum_error_chips=maximum,
        reference_actions_exported=False,
        long_run_admitted=False,
    )
