"""Complete saved-profile self traces and ordered fixed-opponent crosses."""

import itertools
import math
from collections.abc import Callable
from typing import Any

from poker_ai.evaluation.controlled_reply_inputs import GROUP, Inputs, modes
from poker_ai.evaluation.controlled_reply_math import Reply, cross
from poker_ai.evaluation.controlled_reply_traces import make_record, public_streets
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline

TraceSink = Callable[[dict[str, Any]], None]
Progress = Callable[[], None]


def compute(
    data: Inputs,
    deadline: Deadline,
    emit: TraceSink,
    saved: dict[str, Any],
    progress: Progress,
) -> None:
    """Only frozen OWN policies enter; all forty-eight sampled and sixteen full kept."""
    tolerance = data.config["tolerance_chips"]
    replies: dict[tuple[str, int], Reply] = {}
    for source in data.policies:
        deadline.check()
        context = data.context(source.case)
        streets = public_streets(context)
        responses = []
        for target in (0, 1):
            summary, record, reply = make_record(
                source, context, target, streets, tolerance
            )
            emit(record)
            responses.append(summary)
            replies[source.identifier, target] = reply
        within = math.fsum(r["gain_chips"] for r in responses) / 2
        street = {
            name: math.fsum(r["street_losses_chips"][name] for r in responses) / 2
            for name in ("TURN", "RIVER")
        }
        if (
            abs(within - source.row["metrics"]["within_partition_gain_chips"])
            > tolerance
        ):
            raise ArithmeticError(
                "self response gain differs from source within metric"
            )
        saved["self_profiles"].append(
            dict(
                id=source.identifier,
                case=source.case,
                source_snapshot_id=source.row["id"],
                source_policy_sha256=source.row["receipt"]["policy_sha256"],
                value_player_zero_chips=source.row["metrics"][
                    "value_player_zero_chips"
                ],
                within_partition_gain_chips=within,
                street_losses_chips=street,
                responses=responses,
            )
        )
        progress()
    groups = sorted({source.group for source in data.policies})
    for group in groups:
        members = {p.mode: p for p in data.policies if p.group == group}
        order = modes(data.config)
        if set(members) != set(order) or len(members) != 4:
            raise ArithmeticError("crossed source-mode group incomplete")
        for a_mode, b_mode in itertools.product(order, repeat=2):
            deadline.check()
            a, b = members[a_mode], members[b_mode]
            context = data.context(a.case)
            result = cross(
                context.partition,
                a.policy,
                b.policy,
                replies[b.identifier, 0],
                replies[a.identifier, 1],
                tolerance=tolerance,
            )
            for target, response in enumerate(result["responses"]):
                own, opponent = (a, b) if target == 0 else (b, a)
                response.update(
                    own_profile_id=own.identifier,
                    opponent_profile_id=opponent.identifier,
                    reply_sha256=opponent.row["reply_sha256"][target]["restricted"],
                )
            saved["crosses"].append(
                dict(
                    group={key: a.case[key] for key in GROUP},
                    first_id=a.identifier,
                    second_id=b.identifier,
                    first_mode=list(a_mode),
                    second_mode=list(b_mode),
                    **result,
                )
            )
        progress()
    validate(saved, data)


def validate(saved: dict[str, Any], data: Inputs) -> dict[str, Any]:
    """No favorable subset can satisfy complete-grid/root/EV/source identities."""
    tolerance = data.config["tolerance_chips"]
    profiles = {p.identifier: p for p in data.policies}
    selfs = saved["self_profiles"]
    if len(selfs) != 64 or {r["id"] for r in selfs} != set(profiles):
        raise ArithmeticError("self source grid incomplete/duplicate")
    for row in selfs:
        source = profiles[row["id"]]
        if (
            not same(row["case"], source.case)
            or row["source_snapshot_id"] != source.row["id"]
            or (row["source_policy_sha256"] != source.row["receipt"]["policy_sha256"])
        ):
            raise ArithmeticError("self source identity changed")
        responses = row["responses"]
        if len(responses) != 2 or not same([r["target"] for r in responses], [0, 1]):
            raise ArithmeticError("self targets incomplete")
        for target, response in enumerate(responses):
            peer = source.row["responses"][target]
            for key, old in {
                "baseline_value_chips": "baseline_value_chips",
                "restricted_reply_value_chips": "restricted_reply_value_chips",
                "gain_chips": "within_partition_gain_chips",
            }.items():
                if (
                    not number(response[key])
                    or abs(response[key] - peer[old]) > tolerance
                ):
                    raise ArithmeticError("self response root/gain differs from source")
            if (
                response["profile_id"] != source.identifier
                or response["reply_sha256"]
                != source.row["reply_sha256"][target]["restricted"]
            ):
                raise ArithmeticError("self own reply/source fingerprint changed")
        within = math.fsum(r["gain_chips"] for r in responses) / 2
        if (
            not number(row["within_partition_gain_chips"])
            or abs(within - row["within_partition_gain_chips"]) > tolerance
            or abs(within - source.row["metrics"]["within_partition_gain_chips"])
            > tolerance
        ):
            raise ArithmeticError("self balanced within gain changed")
        for street in ("TURN", "RIVER"):
            street_total = (
                math.fsum(r["street_losses_chips"][street] for r in responses) / 2
            )
            if (
                not number(row["street_losses_chips"][street])
                or abs(street_total - row["street_losses_chips"][street]) > tolerance
            ):
                raise ArithmeticError("self street summary changed")
    crosses = saved["crosses"]
    expected_pairs = {
        (a.identifier, b.identifier)
        for a in data.policies
        for b in data.policies
        if a.group == b.group
    }
    pairs = [(r["first_id"], r["second_id"]) for r in crosses]
    if len(crosses) != 256 or len(set(pairs)) != 256 or set(pairs) != expected_pairs:
        raise ArithmeticError("crossed profile grid incomplete/duplicate")
    maximum = 0.0
    for record in crosses:
        a, b = profiles[record["first_id"]], profiles[record["second_id"]]
        if (
            not same(record["group"], {k: a.case[k] for k in GROUP})
            or not same(record["first_mode"], list(a.mode))
            or not same(record["second_mode"], list(b.mode))
        ):
            raise ArithmeticError("crossed grouping/source modes changed")
        baseline = record["value_player_zero_chips"]
        responses = record["responses"]
        if (
            not number(baseline)
            or len(responses) != 2
            or not same([r["target"] for r in responses], [0, 1])
        ):
            raise ArithmeticError("crossed baseline/target inventory changed")
        for target, response in enumerate(responses):
            own, opponent = (a, b) if target == 0 else (b, a)
            sign = 1 if target == 0 else -1
            root = opponent.row["responses"][target]["restricted_reply_value_chips"]
            if (
                response["own_profile_id"] != own.identifier
                or response["opponent_profile_id"] != opponent.identifier
                or (
                    response["reply_sha256"]
                    != opponent.row["reply_sha256"][target]["restricted"]
                )
            ):
                raise ArithmeticError(
                    "crossed target/opponent/own-reply binding changed"
                )
            expected_response = dict(
                baseline_value_chips=sign * baseline,
                restricted_reply_value_chips=root,
                achieved_reply_value_chips=root,
                gain_chips=root - sign * baseline,
            )
            for key, value in expected_response.items():
                if not number(response[key]):
                    raise ArithmeticError("nonfinite crossed response")
                maximum = max(maximum, abs(response[key] - value))
            if response["gain_chips"] < -tolerance:
                raise ArithmeticError("crossed response cannot be worse than baseline")
        within = math.fsum(r["gain_chips"] for r in responses) / 2
        if (
            not number(record["within_partition_gain_chips"])
            or abs(within - record["within_partition_gain_chips"]) > tolerance
        ):
            raise ArithmeticError("crossed balanced gain changed")
        if a.identifier == b.identifier:
            maximum = max(
                maximum,
                abs(baseline - a.row["metrics"]["value_player_zero_chips"]),
                abs(within - a.row["metrics"]["within_partition_gain_chips"]),
            )
    if maximum > tolerance:
        raise ArithmeticError("crossed fixed-opponent/root/diagonal identities failed")
    for group in {p.group for p in data.policies}:
        members = {p.identifier for p in data.policies if p.group == group}
        subset = [r for r in crosses if r["first_id"] in members]
        for target, opponent_id in itertools.product((0, 1), members):
            rows = [
                r
                for c in subset
                for r in c["responses"]
                if r["target"] == target and r["opponent_profile_id"] == opponent_id
            ]
            if len(rows) != 4 or len({r["own_profile_id"] for r in rows}) != 4:
                raise ArithmeticError("fixed-opponent own-mode grid incomplete")
            first = rows[0]
            for row in rows[1:]:
                maximum = max(
                    maximum,
                    abs(
                        row["restricted_reply_value_chips"]
                        - first["restricted_reply_value_chips"]
                    ),
                    abs(
                        row["gain_chips"]
                        - first["gain_chips"]
                        + row["baseline_value_chips"]
                        - first["baseline_value_chips"]
                    ),
                )
    if maximum > tolerance:
        raise ArithmeticError("fixed-opponent gain/EV difference identity failed")
    return dict(
        source_profiles=64,
        self_target_traces=128,
        crossed_profiles=256,
        crossed_target_conditions=512,
        maximum_identity_error_chips=maximum,
    )
