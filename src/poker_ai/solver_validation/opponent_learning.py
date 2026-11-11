"""Scalar-only independent audit for every own-opponent profile and fixed target.

An outer driver must check published own evidence/source before calling audit.
This module never learns, requests a reference strategy or exports native actions.
The same explicit array/EFG reader supports marked fictional and real own games.
"""

import math
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.opponent_learning_design import Design, is_raw
from poker_ai.evaluation.opponent_learning_replay import ContextFor, member
from poker_ai.evaluation.opponent_learning_score import fixed_inventory, scoring
from poker_ai.evaluation.opponent_learning_sources import Opponent
from poker_ai.finite import FloatArray
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.learning_artifacts import read_archive
from poker_ai.postflop.learning_training import replay_detail
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline
from poker_ai.solver_validation.matched_array_reference import ScalarReference, compare

FORMAT = "poker-ai-own-opponent-learning-native-v1"
FIXED_VALUES = (
    "target_ev_chips",
    "fine_reply_value_chips",
    "achieved_own_reply_value_chips",
    "fine_reply_gain_chips",
)
FIXED_IDENTITY = (
    "condition_id",
    "id",
    "coordinate",
    "target",
    "opponent_id",
    "source_sha256",
    "candidate_policy_sha256",
    "opponent_policy_sha256",
    "opponent_source_policy_sha256",
    "own_reply_sha256",
    "scope",
    "readout",
    "arm",
    "work_label",
)


def _finite(value: Any) -> bool:
    return type(value) in (int, float) and math.isfinite(value)


def self_error(result: dict[str, Any], peer: dict[str, Any]) -> float:
    if (
        not same(result["id"], peer["id"])
        or not same(result["coordinate"], peer["coordinate"])
        or not same(result["scope"], peer["scope"])
        or result["policy_sha256"] != peer["receipt"]["policy_sha256"]
        or not same(result["own_reply_sha256"], peer["reply_sha256"])
        or set(result["native_metrics"]) != set(peer["metrics"])
        or len(result["responses"]) != 2
        or not same([r["target"] for r in result["responses"]], [0, 1])
    ):
        raise ArithmeticError("native own profile/source/reply identity changed")
    errors = []
    for k, v in result["native_metrics"].items():
        if not _finite(v) or not _finite(peer["metrics"][k]):
            raise ArithmeticError("nonfinite native own profile metric")
        errors.append(abs(v - peer["metrics"][k]))
    names = dict(
        exact_root_chips="exact_reply_value_chips",
        restricted_root_chips="restricted_reply_value_chips",
        achieved_exact_chips="exact_reply_value_chips",
        achieved_restricted_chips="restricted_reply_value_chips",
        achieved_river_before_chips="river_before_value_chips",
    )
    for target, response in enumerate(result["responses"]):
        for native, own in names.items():
            value = response[native]
            if not _finite(value) or not _finite(peer["responses"][target][own]):
                raise ArithmeticError("nonfinite native own reply root")
            errors.append(abs(value - peer["responses"][target][own]))
    if any(not math.isfinite(e) for e in errors):
        raise ArithmeticError("nonfinite own/native scalar comparison")
    maximum = max(errors)
    if not same(maximum, result["maximum_error_chips"]) or maximum > 1e-9:
        raise ArithmeticError("independent own profile/root/reply disagreement")
    return float(maximum)


def fixed_error(result: dict[str, Any], peer: dict[str, Any]) -> float:
    if any(not same(result.get(k), peer[k]) for k in FIXED_IDENTITY):
        raise ArithmeticError("native fixed condition source/opponent/target changed")
    errors = []
    for key in FIXED_VALUES:
        value = result[key]
        if not _finite(value) or not _finite(peer[key]):
            raise ArithmeticError("nonfinite native fixed condition")
        errors.append(abs(value - peer[key]))
    if any(not math.isfinite(e) for e in errors):
        raise ArithmeticError("nonfinite own/native fixed comparison")
    maximum = max(errors)
    if not same(result["maximum_error_chips"], maximum) or maximum > 1e-9:
        raise ArithmeticError("independent fixed own condition disagreement")
    return float(maximum)


def fixed(
    peer: dict[str, Any],
    candidate: FloatArray,
    opponent: Opponent,
    reference: ScalarReference,
    cache: dict[Any, Any],
) -> dict[str, Any]:
    tree, target = reference.tree, peer["target"]
    if type(target) is not int or target not in (0, 1):
        raise ArithmeticError("native fixed target must be seat zero or one")
    tree.validate_policy(candidate)
    tree.validate_policy(opponent.policy)
    if (
        array_sha(candidate) != peer["candidate_policy_sha256"]
        or array_sha(opponent.policy) != opponent.fine_policy_sha256
        or opponent.fine_policy_sha256 != peer["opponent_policy_sha256"]
        or opponent.source_policy_sha256 != peer["opponent_source_policy_sha256"]
        or opponent.identifier != peer["opponent_id"]
        or opponent.game != peer["coordinate"] // 3
    ):
        raise ArithmeticError("native fixed policies differ from bound own sources")
    mixed = np.where((tree.owners == target)[:, None], candidate, opponent.policy)
    sign = 1 if target == 0 else -1
    baseline = sign * reference.value(mixed)
    own_reply = opponent.replies[target].apply(tree, mixed)
    fingerprint = array_sha(own_reply)
    if fingerprint != peer["own_reply_sha256"]:
        raise ArithmeticError("native fixed achieved OWN reply differs from source")
    key = opponent.game, opponent.identifier, target
    if key not in cache:
        cache[key] = (
            fingerprint,
            reference.response_value(mixed, target),
            sign * reference.value(own_reply),
        )
    elif cache[key][0] != fingerprint:
        raise ArithmeticError("native fixed cache changed own opponent/reply")
    _, root, achieved = cache[key]
    result = dict(
        **{k: peer[k] for k in FIXED_IDENTITY},
        target_ev_chips=baseline,
        fine_reply_value_chips=root,
        achieved_own_reply_value_chips=achieved,
        fine_reply_gain_chips=root - baseline,
    )
    result["maximum_error_chips"] = max(abs(result[k] - peer[k]) for k in FIXED_VALUES)
    fixed_error(result, peer)
    return result


def audit(
    folder: Path,
    own: dict[str, Any],
    design: Design,
    context_for: ContextFor,
    opponents: tuple[Opponent, ...],
    send: Send,
    deadline: Deadline,
    coordinates: tuple[int, ...] = (0, 1, 2, 3, 4, 5),
) -> dict[str, Any]:
    """Full scalar comparisons; driver publishes own evidence before this call."""
    design.require_rows("profiles", own["rows"])
    fixed_inventory(design, own["fixed_conditions"], opponents)
    if (
        not coordinates
        or len(set(coordinates)) != len(coordinates)
        or any(type(i) is not int or not 0 <= i < 6 for i in coordinates)
    ):
        raise ValueError("native worker needs distinct prescribed coordinates")
    refs = {}
    for game in sorted({i // 3 for i in coordinates}):
        contexts = context_for(game * 3)
        deadline.check()
        fine = ScalarReference(contexts.fine)
        for kind in ("coarse", "mixed0", "mixed1", "fine"):
            deadline.check()
            refs[game, kind] = (
                fine,
                fine if kind == "fine" else ScalarReference(contexts.tree(kind)),
            )
    opponent_by_id = {p.identifier: p for p in opponents}
    fixed_by_profile: dict[str, list[dict[str, Any]]] = {}
    for row in own["fixed_conditions"]:
        fixed_by_profile.setdefault(row["id"], []).append(row)
    selves, targets, maximum = [], [], 0.0
    cache: dict[Any, Any] = {}
    for row, blob in read_archive(
        member(folder, own["details_file"]),
        own["details_sha256"],
        own["rows"],
    ):
        deadline.check()
        if row["coordinate"] not in coordinates:
            continue
        contexts = context_for(row["coordinate"])
        context = scoring(contexts, row)
        kind = row["tree_kind"] if is_raw(row) else "coarse"
        pair = refs[row["coordinate"] // 3, kind]
        _, detail = replay_detail(context, row, blob, 1e-9)
        result = dict(
            id=row["id"],
            coordinate=row["coordinate"],
            scope=row["scope"],
            policy_sha256=row["receipt"]["policy_sha256"],
            own_reply_sha256=row["reply_sha256"],
            **compare(context, pair, detail),
        )
        maximum = max(maximum, self_error(result, row))
        selves.append(result)
        send(dict(kind="cell", phase="self", index=row["coordinate"], result=result))
        policy = context.expand(unpack_policy(context.partition, detail["policy"]))
        for peer in fixed_by_profile.get(row["id"], []):
            deadline.check()
            fixed_result = fixed(
                peer, policy, opponent_by_id[peer["opponent_id"]], pair[0], cache
            )
            maximum = max(maximum, fixed_result["maximum_error_chips"])
            targets.append(fixed_result)
            send(
                dict(
                    kind="cell",
                    phase="fixed",
                    index=row["coordinate"],
                    result=fixed_result,
                )
            )
    if len(selves) != 72 * len(coordinates) or len(targets) != 192 * len(coordinates):
        raise ArithmeticError("native worker incomplete own profile/fixed inventory")
    deadline.check()
    return dict(
        profiles=selves,
        fixed_conditions=targets,
        maximum_error_chips=maximum,
        coordinates=list(coordinates),
        reference_actions_exported=False,
        reference_output_used_in_training=False,
        training_performed=False,
    )


def validate_rows(result: dict[str, Any], own: dict[str, Any]) -> dict[str, Any]:
    """Require all432/1152 identities and recompute every stored error bound."""
    peers = {r["id"]: r for r in own["rows"]}
    fixed_peers = {r["condition_id"]: r for r in own["fixed_conditions"]}
    actual = {r["id"]: r for r in result["profiles"]}
    fixed_actual = {r["condition_id"]: r for r in result["fixed_conditions"]}
    if (
        len(peers) != 432
        or len(own["rows"]) != 432
        or len(fixed_peers) != 1152
        or len(own["fixed_conditions"]) != 1152
        or len(actual) != len(result["profiles"])
        or set(actual) != set(peers)
        or len(fixed_actual) != len(result["fixed_conditions"])
        or set(fixed_actual) != set(fixed_peers)
        or any(
            result[k] is not False
            for k in (
                "reference_actions_exported",
                "reference_output_used_in_training",
                "training_performed",
            )
        )
        or not same(result["coordinates"], list(range(6)))
    ):
        raise ArithmeticError("complete scalar-only432/1152 native inventory required")
    maximum = max(
        [self_error(actual[k], row) for k, row in peers.items()]
        + [fixed_error(fixed_actual[k], row) for k, row in fixed_peers.items()]
    )
    if not same(maximum, result["maximum_error_chips"]):
        raise ArithmeticError("native whole-grid maximum error changed")
    return dict(
        profiles=432,
        fixed_conditions=1152,
        maximum_error_chips=maximum,
        reference_actions_exported=False,
        training_performed=False,
    )
