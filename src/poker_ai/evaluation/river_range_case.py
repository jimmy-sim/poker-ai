"""Own/public river inventories and fixed-suffix local group diagnostics."""

from dataclasses import dataclass
from typing import Any, cast

import numpy as np

from poker_ai.cards import format_card
from poker_ai.evaluation.opponent_decision_inputs import Profile
from poker_ai.evaluation.opponent_learning_score import scoring
from poker_ai.evaluation.river_range_math import (
    RangeMixture,
    decompose,
    local_group,
    total_variation,
)
from poker_ai.finite import FloatArray, IntArray
from poker_ai.postflop.controlled_checkpoints import pack_policy, unpack_policy
from poker_ai.postflop.controlled_scoring import BoolArray
from poker_ai.postflop.learning import decision_mass
from poker_ai.postflop.learning_artifacts import canonical, sha
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.river_distinctions import river_features, river_mask
from poker_ai.training.no_limit import NoLimitState


@dataclass(frozen=True)
class Inventory:
    tree_sha256: str
    river: BoolArray
    node_combo: IntArray
    compatible: BoolArray
    declared_weights: FloatArray
    declared_combos: list[list[str]]
    rows: list[dict[str, Any]]


def inventory(tree: MatrixTree, target: int) -> Inventory:
    if type(target) is not int or target not in (0, 1):
        raise ValueError("river inventory needs seat zero or one")
    river = river_mask(tree, target)
    known = tuple(h.cards for h in tree.source.spot.ranges[1 - target])
    declared = np.array([h.weight for h in tree.source.spot.ranges[1 - target]])
    compatible = np.zeros((len(tree.keys), len(known)), dtype=np.bool_)
    combo = np.full(len(tree.player), -1, dtype=np.int64)
    nodes = np.flatnonzero(
        (tree.player == target) & river[np.maximum(tree.information, 0)]
    )
    for raw in nodes:
        node = int(raw)
        state = tree.source.states[node]
        value = state.second if target == 0 else state.first
        if value is None:
            raise ArithmeticError("river history lacks declared hypothetical combo")
        combo[node] = value
    rows = []
    for raw in np.flatnonzero(river):
        info = int(raw)
        state = tree.source.states[tree.source.representatives[info]]
        assert state.dealer is not None
        observation = state.dealer.observe(target)
        features = river_features(observation.hole_cards, observation.board, known)
        compatible[info] = features["range_compatibility"]
        actions = []
        for action in tree.actions[info]:
            move = NoLimitState(state.dealer, tree.source.spot.rules).decode(action)
            actions.append(
                move.kind.value + ("" if move.amount is None else f" {move.amount}")
            )
        rows.append(
            dict(
                exact_info=info,
                hole=[format_card(c) for c in observation.hole_cards],
                board=[format_card(c) for c in observation.board],
                pot=observation.pot,
                actions=actions,
                static_features=features,
                history=[
                    dict(
                        seat=h.seat,
                        street=h.street.name,
                        kind=h.action.kind.value,
                        amount=h.action.amount,
                        chips_paid=h.chips_paid,
                    )
                    for h in observation.history
                ],
            )
        )
    for array in (river, combo, compatible, declared):
        array.flags.writeable = False
    return Inventory(
        tree_digest(tree),
        river,
        combo,
        compatible,
        declared,
        [[format_card(c) for c in hand] for hand in known],
        rows,
    )


def grouped(
    data: RangeMixture,
    rows: list[dict[str, Any]],
    mapping: IntArray,
    values: FloatArray,
) -> tuple[dict[str, Any], dict[str, list[dict[str, Any]]]]:
    """Same actual support/uniform weights under each range and grouping control."""
    result: dict[str, Any] = {}
    details: dict[str, list[dict[str, Any]]] = {}
    for control in ("declared_partition", "full_static_probe_refinement"):
        groups: dict[tuple[int, bytes], list[dict[str, Any]]] = {}
        for row in rows:
            parent = int(mapping[row["exact_info"]])
            signature = (
                b""
                if control == "declared_partition"
                else canonical(row["static_features"])
            )
            groups.setdefault((parent, signature), []).append(row)
        records: list[dict[str, Any]] = []
        for (parent, signature), members in sorted(groups.items()):
            menus = {tuple(row["actions"]) for row in members}
            if len(menus) != 1:
                raise ArithmeticError("shared river group changes concrete action menu")
            width = len(next(iter(menus)))
            active = [
                row["exact_info"]
                for row in members
                if data.support[row["exact_info"]] > 0
            ]
            measured = local_group(values[active, :width], data.uniform_weights[active])
            if (
                control == "full_static_probe_refinement"
                and total_variation(data.prior[active]) > 1e-12
            ):
                raise ArithmeticError(
                    "full static control changes compatible prior within group"
                )
            records.append(
                dict(
                    group_id=str(parent)
                    if not signature
                    else f"{parent}:{sha(signature.decode())}",
                    abstract_info=parent,
                    infos=[r["exact_info"] for r in members],
                    supported_infos=active,
                    static_signature=None
                    if not signature
                    else members[0]["static_features"],
                    maximum_posterior_total_variation=total_variation(
                        data.posterior[active]
                    ),
                    intervention_range_total_variation=total_variation(
                        data.prior[active]
                    )
                    if values is data.prior_values
                    else total_variation(data.posterior[active]),
                    **measured,
                )
            )
        result[control] = dict(
            supported_uniform_decision_weight=float(
                data.uniform_weights[data.support > 0].sum()
            ),
            local_sharing_cost_chips_per_weighted_decision=sum(
                r["local_cost"] for r in records
            ),
            strict_conflicting_groups=sum(r["strict_conflict"] for r in records),
            total_groups=len(records),
            supported_groups=sum(r["supported_rows"] > 0 for r in records),
            maximum_posterior_total_variation_within_group=max(
                (r["maximum_posterior_total_variation"] for r in records), default=0.0
            ),
        )
        details[control] = records
    if (
        result["full_static_probe_refinement"][
            "local_sharing_cost_chips_per_weighted_decision"
        ]
        > result["declared_partition"]["local_sharing_cost_chips_per_weighted_decision"]
        + 1e-9
    ):
        raise ArithmeticError("refinement increased convex local sharing cost")
    return result, details


def analyse_profile(
    profile: Profile,
    previous: dict[str, Any],
    previous_detail: dict[str, Any],
    config: dict[str, Any],
    cache: dict[tuple[str, int], Inventory],
) -> tuple[dict[str, Any], dict[str, Any]]:
    context = scoring(profile.contexts, profile.row)
    fine = cast(MatrixTree, context.exact)
    tolerance = config["absolute_tolerance_chips"]
    saved_mass = decision_mass(fine, profile.fine_policy)
    summaries, details = [], []
    for target in (0, 1):
        key = profile.game, target
        if key not in cache:
            cache[key] = inventory(fine, target)
        source = cache[key]
        if source.tree_sha256 != tree_digest(fine):
            raise ArithmeticError("cached river inventory belongs to another game")
        old = previous_detail["responses"][target]
        prior_response = previous["responses"][target]
        if old["target"] != target or prior_response["target"] != target:
            raise ArithmeticError("river range source target changed")
        if [r["exact_info"] for r in old["infos"]] != list(
            np.flatnonzero(fine.owners == target)
        ):
            raise ArithmeticError("complete prior river/source row inventory required")
        old_rows = {r["exact_info"]: r for r in old["infos"]}
        suffix_summaries, suffix_details = [], []
        invariant: tuple[bytes, ...] | None = None
        for label, field, reply_key in (
            ("fine_reply", "exact_reply_profile", "exact"),
            ("restricted_reply", "restricted_reply_profile", "restricted"),
        ):
            reply = unpack_policy(fine, old[field])
            if (
                sha(pack_policy(fine, reply))
                != profile.row["reply_sha256"][target][reply_key]
                or reply[fine.owners != target].tobytes()
                != profile.fine_policy[fine.owners != target].tobytes()
            ):
                raise ArithmeticError("river suffix fingerprint/fixed opponent changed")
            data = decompose(
                fine,
                reply,
                target,
                source.river,
                source.node_combo,
                source.compatible,
                source.declared_weights,
                chip_tolerance=tolerance,
                unitless_tolerance=config["unitless_tolerance"],
            )
            root = (1 if target == 0 else -1) * float(fine.values(fine.edges(reply))[0])
            expected = prior_response[
                "exact_reply_value_chips"
                if reply_key == "exact"
                else "restricted_reply_value_chips"
            ]
            errors = [data.maximum_chip_error, abs(root - expected)]
            unitless_errors = [data.maximum_unitless_error]
            current = tuple(
                a.tobytes()
                for a in (
                    data.posterior,
                    data.prior,
                    data.support,
                    data.uniform_weights,
                )
            )
            if invariant is not None and current != invariant:
                raise ArithmeticError(
                    "changing own suffix changed opponent range/support/weighting"
                )
            invariant = current
            full_rows = []
            for row in source.rows:
                info = row["exact_info"]
                width = len(row["actions"])
                unitless_errors.append(
                    abs(
                        float(data.support[info])
                        - old_rows[info]["counterfactual_mass"]
                    )
                )
                unitless_errors.append(
                    abs(float(saved_mass[info]) - old_rows[info]["saved_reach_mass"])
                )
                if reply_key == "exact":
                    errors.append(
                        float(
                            np.max(
                                np.abs(
                                    data.actual_values[info, :width]
                                    - old_rows[info]["conditional_values_chips"]
                                ),
                                initial=0,
                            )
                        )
                    )
                full_rows.append(
                    dict(
                        **row,
                        abstract_info=int(context.exact_to_partition[info]),
                        compatible=source.compatible[info].tolist(),
                        actual_posterior=data.posterior[info].tolist(),
                        compatible_prior=data.prior[info].tolist(),
                        combo_action_values_chips=data.combo_values[
                            info, :, :width
                        ].tolist(),
                        actual_action_values_chips=data.actual_values[
                            info, :width
                        ].tolist(),
                        prior_action_values_chips=data.prior_values[
                            info, :width
                        ].tolist(),
                        counterfactual_support=float(data.support[info]),
                        uniform_decision_weight=float(data.uniform_weights[info]),
                        saved_reach_mass=float(saved_mass[info]),
                        saved_probabilities=profile.fine_policy[info, :width].tolist(),
                        prior_fine_trace_loss_chips=old_rows[info]["loss_chips"],
                    )
                )
            panels, group_details = [], {}
            for weights, values in (
                ("actual_posterior", data.actual_values),
                ("compatible_prior", data.prior_values),
            ):
                metrics, groups = grouped(
                    data, source.rows, context.exact_to_partition, values
                )
                if profile.arm == "fine_self" and any(
                    m["local_sharing_cost_chips_per_weighted_decision"] != 0
                    or m["strict_conflicting_groups"] != 0
                    for m in metrics.values()
                ):
                    raise ArithmeticError("fine-self singleton local control failed")
                panels.append(dict(range_weights=weights, group_controls=metrics))
                group_details[weights] = groups
            if any(not np.isfinite(e) or e > tolerance for e in errors):
                raise ArithmeticError(
                    "river mixture differs from bound source roots/Q/support"
                )
            if any(
                not np.isfinite(e) or e > config["unitless_tolerance"]
                for e in unitless_errors
            ):
                raise ArithmeticError("river range source reach/support changed")
            ranked = [
                g
                for g in group_details["actual_posterior"]["declared_partition"]
                if g["supported_rows"] > 0
            ]
            ranked.sort(key=lambda g: (-g["local_cost"], g["abstract_info"]))
            suffix_summaries.append(
                dict(
                    suffix=label,
                    panels=panels,
                    river_info_ids=[r["exact_info"] for r in full_rows],
                    maximum_source_chip_error=max(errors),
                    maximum_unitless_error=max(unitless_errors),
                    top_groups=ranked[: config["top_groups"]],
                )
            )
            suffix_details.append(
                dict(suffix=label, rows=full_rows, groups=group_details)
            )
        summaries.append(dict(target=target, suffixes=suffix_summaries))
        details.append(
            dict(
                target=target,
                declared_opponent_range=source.declared_combos,
                suffixes=suffix_details,
            )
        )
    return dict(responses=summaries), dict(responses=details)
