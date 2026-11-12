"""Refine frozen cached river groups by public features; never change values."""

import math
from dataclasses import dataclass, field
from typing import Any

from poker_ai.cards import format_card, parse_card
from poker_ai.evaluation.range_blocker_features import (
    PublicRanges,
    Ranges,
    compatible_with_own,
    public_ranges,
)

CONTROLS = (
    "source_static",
    "own_public",
    "both_public",
    "both_public_joint",
    "exact_information",
)
SUFFIXES = ("fine_reply", "restricted_reply")
WEIGHTS = ("actual_posterior", "compatible_prior")
FIELDS = ("actual_action_values_chips", "prior_action_values_chips")


def declared_ranges(detail: dict[str, Any]) -> Ranges:
    if [r["target"] for r in detail["responses"]] != [0, 1]:
        raise ArithmeticError("two ordered source responding seats required")
    return tuple(
        tuple(
            tuple(parse_card(c) for c in h)
            for h in detail["responses"][1 - seat]["declared_opponent_range"]
        )
        for seat in (0, 1)
    )


@dataclass
class FeatureBook:
    ranges: dict[str, Ranges] = field(default_factory=dict)
    features: dict[str, PublicRanges] = field(default_factory=dict)
    entries: dict[str, dict[str, Any]] = field(default_factory=dict)
    frozen: bool = False

    def bind(
        self, game: str, ranges: Ranges, board: list[str]
    ) -> tuple[str, PublicRanges]:
        if game in self.ranges and self.ranges[game] != ranges:
            raise ArithmeticError("ordered declared ranges changed within the game")
        self.ranges[game] = ranges
        key = (
            game + ":" + ",".join(board)
        )  # Storage lookup ONLY, never a group feature.
        if key not in self.features:
            if self.frozen:
                raise ArithmeticError("cached feature catalog lacks a source board")
            f = public_ranges(tuple(parse_card(c) for c in board), ranges)
            self.features[key] = f
            self.entries[key] = dict(game=game, board=board.copy(), **f.record())
        return key, self.features[key]

    def record(self) -> dict[str, Any]:
        return dict(
            ranges={
                g: [[[format_card(c) for c in h] for h in side] for side in rs]
                for g, rs in self.ranges.items()
            },
            features=self.entries,
        )


def local(rows: list[dict[str, Any]], qfield: str) -> dict[str, Any]:
    """Independent scalar fsum accounting on source-supported legal decisions."""
    for r in rows:
        values = [r["counterfactual_support"], r["uniform_decision_weight"], *r[qfield]]
        if (
            any(type(v) not in (int, float) or not math.isfinite(v) for v in values)
            or r["counterfactual_support"] < 0
            or r["uniform_decision_weight"] < 0
        ):
            raise ArithmeticError(
                "finite source values and nonnegative support/weights required"
            )
    active = [r for r in rows if r["counterfactual_support"] > 0]
    if not active:
        return dict(cost=0.0, conflict=False, weight=0.0)
    width = len(active[0]["actions"])
    if not width or any(
        len(r["actions"]) != width or len(r[qfield]) != width for r in active
    ):
        raise ArithmeticError("fixed concrete legal menu required")
    for r in active:
        numbers = [r["uniform_decision_weight"], *r[qfield]]
        if (
            any(type(v) not in (int, float) or not math.isfinite(v) for v in numbers)
            or r["uniform_decision_weight"] < 0
        ):
            raise ArithmeticError(
                "finite values and nonnegative fixed weights required"
            )
    separate = math.fsum(r["uniform_decision_weight"] * max(r[qfield]) for r in active)
    shared = max(
        math.fsum(r["uniform_decision_weight"] * r[qfield][a] for r in active)
        for a in range(width)
    )
    cost = separate - shared
    if cost < -1e-9:
        raise ArithmeticError("negative convex local sharing cost")
    common = set(range(width))
    for r in active:
        best = max(r[qfield])
        common.intersection_update(
            a for a, q in enumerate(r[qfield]) if best - q <= 1e-9
        )
    return dict(
        cost=max(0.0, cost),
        conflict=not bool(common),
        weight=math.fsum(r["uniform_decision_weight"] for r in active),
    )


def geometry(
    game: str, target: int, ranges: Ranges, source: dict[str, Any], book: FeatureBook
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rows = source["rows"]
    lookup = {r["exact_info"]: r for r in rows}
    if len(lookup) != len(rows) or any(type(i) is not int for i in lookup):
        raise ArithmeticError("unique integer own information rows required")
    baseline = source["groups"][WEIGHTS[0]]["full_static_probe_refinement"]
    parents = {i: g["group_id"] for g in baseline for i in g["infos"]}
    if sorted(parents) != sorted(lookup) or sum(
        len(g["infos"]) for g in baseline
    ) != len(rows):
        raise ArithmeticError("complete disjoint original static inventory required")
    bindings, fs = [], {}
    for row in rows:
        key, f = book.bind(game, ranges, row["board"])
        own = tuple(parse_card(c) for c in row["hole"])
        if compatible_with_own(f, ranges, target, own) != tuple(row["compatible"]):
            raise ArithmeticError(
                "joint projection differs from source card compatibility"
            )
        fs[row["exact_info"]] = f
        bindings.append(dict(exact_info=row["exact_info"], feature=key))
    partitions = []
    for control in CONTROLS:
        grouped: dict[tuple[str, Any], list[int]] = {}
        for row in rows:
            info = row["exact_info"]
            f = fs[info]
            signature: Any = ()
            if control == "own_public":
                signature = f.available[target]
            elif control == "both_public":
                signature = f.available
            elif control == "both_public_joint":
                signature = f.available, f.joint
            elif control == "exact_information":
                signature = (info,)
            grouped.setdefault((parents[info], signature), []).append(info)
        groups = []
        for (parent, _), infos in sorted(
            grouped.items(), key=lambda pair: repr(pair[0])
        ):
            members = [lookup[i] for i in infos]
            if len({tuple(r["actions"]) for r in members}) != 1:
                raise ArithmeticError("a shared group changed concrete action menu")
            supported = [r for r in members if r["counterfactual_support"] > 0]
            groups.append(
                dict(
                    source_group_id=parent,
                    infos=infos,
                    supported_infos=[r["exact_info"] for r in supported],
                    weight=math.fsum(r["uniform_decision_weight"] for r in supported),
                )
            )
        partitions.append(dict(control=control, groups=groups))

    def member_sets(p: dict[str, Any]) -> set[tuple[int, ...]]:
        return {tuple(g["infos"]) for g in p["groups"]}

    if member_sets(partitions[2]) != member_sets(partitions[3]):
        raise ArithmeticError(
            "joint table falsely adds information beyond public masks"
        )
    return bindings, partitions


def score(
    rows: list[dict[str, Any]],
    partitions: list[dict[str, Any]],
    qfield: str,
    old_groups: list[dict[str, Any]],
    old_metrics: dict[str, Any],
) -> tuple[dict[str, Any], list[dict[str, Any]], float, float]:
    lookup = {r["exact_info"]: r for r in rows}
    old = {g["group_id"]: g for g in old_groups}
    if sorted(i for g in old_groups for i in g["infos"]) != sorted(lookup):
        raise ArithmeticError("source static Q panel changed membership")
    source_conflicts = {k for k, g in old.items() if g["strict_conflict"]}
    results, panels = {}, []
    chip_error = unitless_error = 0.0
    previous_cost = math.inf
    for partition in partitions:
        control = partition["control"]
        costs, conflicts, unresolved = [], [], set()
        for group in partition["groups"]:
            members = [lookup[i] for i in group["infos"]]
            measured = local(members, qfield)
            costs.append(measured["cost"])
            conflicts.append(measured["conflict"])
            unitless_error = max(
                unitless_error, abs(measured["weight"] - group["weight"])
            )
            if measured["conflict"]:
                unresolved.add(group["source_group_id"])
            if control == CONTROLS[0]:
                source = old[group["source_group_id"]]
                if (
                    group["infos"] != source["infos"]
                    or group["supported_infos"] != source["supported_infos"]
                    or measured["conflict"] != source["strict_conflict"]
                ):
                    raise ArithmeticError(
                        "source static decision/support reconstruction failed"
                    )
                chip_error = max(
                    chip_error, abs(measured["cost"] - source["local_cost"])
                )
                unitless_error = max(
                    unitless_error, abs(measured["weight"] - source["weight"])
                )
        if not unresolved <= source_conflicts:
            raise ArithmeticError(
                "refinement created a conflict in a nonconflicting parent"
            )
        groups = partition["groups"]
        metrics = dict(
            local_sharing_cost_chips_per_weighted_decision=math.fsum(costs),
            strict_conflicting_groups=sum(conflicts),
            total_groups=len(groups),
            supported_groups=sum(bool(g["supported_infos"]) for g in groups),
            supported_uniform_decision_weight=math.fsum(g["weight"] for g in groups),
            source_conflicting_groups=len(source_conflicts),
            source_conflicting_groups_resolved=len(source_conflicts - unresolved),
        )
        value = metrics["local_sharing_cost_chips_per_weighted_decision"]
        if value > previous_cost + 1e-9:
            raise ArithmeticError("public refinement increased convex sharing cost")
        previous_cost = value
        if control == CONTROLS[0]:
            for key in (
                "total_groups",
                "supported_groups",
                "strict_conflicting_groups",
            ):
                if metrics[key] != old_metrics[key]:
                    raise ArithmeticError("source static group denominator changed")
            chip_error = max(
                chip_error,
                abs(
                    value
                    - old_metrics["local_sharing_cost_chips_per_weighted_decision"]
                ),
            )
            unitless_error = max(
                unitless_error,
                abs(
                    metrics["supported_uniform_decision_weight"]
                    - old_metrics["supported_uniform_decision_weight"]
                ),
            )
        if control == CONTROLS[-1] and (value != 0 or any(conflicts)):
            raise ArithmeticError("exact-information singleton control failed")
        results[control] = metrics
        panels.append(dict(control=control, costs=costs, conflicts=conflicts))
    if chip_error > 1e-9 or unitless_error > 1e-12:
        raise ArithmeticError("source-static scalar reconstruction exceeded tolerance")
    if (
        any(
            results[CONTROLS[2]][k] != results[CONTROLS[3]][k]
            for k in (
                "total_groups",
                "supported_groups",
                "strict_conflicting_groups",
                "source_conflicting_groups_resolved",
            )
        )
        or abs(
            results[CONTROLS[2]]["local_sharing_cost_chips_per_weighted_decision"]
            - results[CONTROLS[3]]["local_sharing_cost_chips_per_weighted_decision"]
        )
        > 1e-9
    ):
        raise ArithmeticError("redundant joint control changes measured result")
    return results, panels, chip_error, unitless_error


def analyse(
    profile: dict[str, Any], detail: dict[str, Any], book: FeatureBook
) -> tuple[dict[str, Any], dict[str, Any]]:
    ranges = declared_ranges(detail)
    summaries, complete = [], []
    for target in (0, 1):
        old_summary = profile["responses"][target]
        old_detail = detail["responses"][target]
        first = old_detail["suffixes"][0]
        bindings, partitions = geometry(profile["game"], target, ranges, first, book)
        invariant = [
            (
                r["exact_info"],
                r["hole"],
                r["board"],
                r["actions"],
                r["uniform_decision_weight"],
                r["counterfactual_support"],
            )
            for r in first["rows"]
        ]
        suffixes, evaluated = [], []
        for summary, source in zip(
            old_summary["suffixes"], old_detail["suffixes"], strict=True
        ):
            if [
                (
                    r["exact_info"],
                    r["hole"],
                    r["board"],
                    r["actions"],
                    r["uniform_decision_weight"],
                    r["counterfactual_support"],
                )
                for r in source["rows"]
            ] != invariant:
                raise ArithmeticError(
                    "own suffix changed source information/support/weighting"
                )
            weight_summaries, weight_details = [], []
            for index, weight in enumerate(WEIGHTS):
                reference = source["groups"][weight]["full_static_probe_refinement"]
                old_metrics = summary["panels"][index]["group_controls"][
                    "full_static_probe_refinement"
                ]
                metrics, scores, error, unitless = score(
                    source["rows"], partitions, FIELDS[index], reference, old_metrics
                )
                if profile["arm"] == "fine_self" and any(
                    m["local_sharing_cost_chips_per_weighted_decision"] != 0
                    or m["strict_conflicting_groups"] != 0
                    for m in metrics.values()
                ):
                    raise ArithmeticError("fine-self singleton source control failed")
                weight_summaries.append(
                    dict(
                        range_weights=weight,
                        group_controls=metrics,
                        maximum_source_chip_error=error,
                        maximum_unitless_error=unitless,
                    )
                )
                weight_details.append(dict(range_weights=weight, controls=scores))
            top = sorted(
                [
                    g
                    for g in source["groups"][WEIGHTS[0]][
                        "full_static_probe_refinement"
                    ]
                    if g["supported_rows"] > 0
                ],
                key=lambda g: (-g["local_cost"], g["group_id"]),
            )[:10]
            suffixes.append(
                dict(
                    suffix=summary["suffix"],
                    panels=weight_summaries,
                    top_source_groups=[g["group_id"] for g in top],
                )
            )
            evaluated.append(dict(suffix=summary["suffix"], panels=weight_details))
        summaries.append(
            dict(
                target=target,
                river_info_ids=[r["exact_info"] for r in first["rows"]],
                suffixes=suffixes,
            )
        )
        complete.append(
            dict(
                target=target,
                row_features=bindings,
                partitions=partitions,
                suffixes=evaluated,
            )
        )
    return dict(responses=summaries), dict(responses=complete)
