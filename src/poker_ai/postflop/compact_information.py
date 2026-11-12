"""Attribute already-audited B-R under the restricted-own-reply prefix.

All best-response and conditional-action math comes from unchanged own helpers.
This attribution does not localize a causal street bug or measure retraining EV.
"""

import math
from typing import Any

import numpy as np

from poker_ai.evaluation.compact_information_inputs import Input
from poker_ai.postflop.controlled_checkpoints import pack_policy, unpack_policy
from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.reply_diagnosis import example
from poker_ai.postflop.reply_trace import trace_losses


def panel(source: Input, alias: Input, target: int) -> dict[str, Any]:
    if type(target) is not int or target not in (0, 1):
        raise ValueError("integer target 0/1 required")
    c = source.context
    if source.context.binding != alias.context.binding:
        raise ArithmeticError("trace aliases change context")
    for item in (source, alias):
        if (
            item.row["binding"] != item.context.binding
            or item.packet["binding"] != item.context.binding
            or any(
                item.row[k] != item.packet[k]
                for k in ("spot_file", "representation", "seed", "mixture")
            )
        ):
            raise ArithmeticError("trace source/context/menu binding changed")
    mode, other = source.row["mixture"], alias.row["mixture"]
    if (
        mode[target] != "S"
        or other[target] != "F"
        or mode[1 - target] != other[1 - target]
    ):
        raise ArithmeticError("canonical own-S/own-F aliases required")
    if source.row["seed"] != alias.row["seed"]:
        raise ArithmeticError("trace alias seed changed")
    replies = source.packet["replies"][target]
    if canonical(replies) != canonical(alias.packet["replies"][target]):
        raise ArithmeticError("fixed-opponent own reply alias changed")
    exact = c.scoring.exact
    policy = unpack_policy(exact, replies["restricted"])
    before = policy.tobytes()
    trace = trace_losses(exact, policy, target, tolerance=1e-9)
    old = source.row["responses"][target]
    native = source.native["responses"][target]
    if (
        type(old["target"]) is not int
        or type(native["target"]) is not int
        or old["target"] != target
        or native["target"] != target
    ):
        raise ArithmeticError("parent responding-seat alignment changed")
    errors = [
        abs(trace.value - old["exact_reply_value_chips"]),
        abs(trace.value - native["exact_root_chips"]),
        abs(trace.value - trace.gain - old["restricted_reply_value_chips"]),
        abs(trace.value - trace.gain - native["restricted_root_chips"]),
        abs(trace.gain - old["extra_information_gap_chips"]),
        trace.accounting_error,
    ]
    if (
        any(not math.isfinite(e) or e > 1e-9 for e in errors)
        or canonical(pack_policy(exact, trace.profile)) != canonical(replies["exact"])
        or policy.tobytes() != before
    ):
        raise ArithmeticError("trace no longer reproduces audited B/R/own reply")
    rows = []
    mapping = c.scoring.exact_to_partition
    for raw in np.flatnonzero(exact.owners == target):
        i = int(raw)
        n = len(exact.actions[i])
        q = trace.conditional_values[i, :n]
        row = dict(
            exact_info=i,
            abstract_info=int(mapping[i]),
            seat=target,
            actions=[str(a) for a in exact.actions[i]],
            restricted_probabilities=policy[i, :n].tolist(),
            reply_action=str(exact.actions[i][int(trace.profile[i].argmax())]),
            reply_continuation_values_chips=q.tolist(),
            near_optimal_columns=np.flatnonzero(q.max() - q <= 1e-9).tolist(),
            counterfactual_mass=float(trace.counterfactual_mass[i]),
            restricted_prefix_reach_mass=float(trace.saved_reach_mass[i]),
            loss_contribution_chips=float(trace.losses[i]),
            street="RIVER" if c.scoring.river_masks[target][i] else "EARLIER",
        )
        if isinstance(exact, MatrixTree):
            labels = example(exact, i, policy, trace)
            row.update(
                {
                    k: v
                    for k, v in labels.items()
                    if k not in {"saved_probabilities", "saved_reach_mass"}
                }
            )
        rows.append(row)
    groups = []
    grouped: dict[int, list[dict[str, Any]]] = {}
    for row in rows:
        grouped.setdefault(row["abstract_info"], []).append(row)
    for g, members in sorted(grouped.items()):
        supported = [
            r
            for r in members
            if r["counterfactual_mass"] > 0 and r["restricted_prefix_reach_mass"] > 0
        ]
        sets = [set(r["near_optimal_columns"]) for r in supported]
        groups.append(
            dict(
                abstract_info=g,
                exact_members=len(members),
                supported_members=len(supported),
                strict_conflict=bool(sets) and not bool(set.intersection(*sets)),
                loss_contribution_chips=math.fsum(
                    r["loss_contribution_chips"] for r in members
                ),
            )
        )
    groups.sort(key=lambda r: (-r["loss_contribution_chips"], r["abstract_info"]))
    streets = {
        s: math.fsum(r["loss_contribution_chips"] for r in rows if r["street"] == s)
        for s in sorted({r["street"] for r in rows})
    }
    error = max(
        *errors,
        abs(math.fsum(r["loss_contribution_chips"] for r in rows) - trace.gain),
        abs(math.fsum(g["loss_contribution_chips"] for g in groups) - trace.gain),
        abs(math.fsum(streets.values()) - trace.gain),
    )
    if error > 1e-9 or any(r["loss_contribution_chips"] < -1e-9 for r in rows):
        raise ArithmeticError("complete row/group/street accounting failed")
    return dict(
        spot_file=c.spot_file,
        representation=c.representation,
        seed=source.row["seed"],
        target=target,
        opponent_source=mode[1 - target],
        binding=c.binding,
        initial_pot_chips=c.pot,
        source_aliases=[
            {k: r[k] for k in ("mixture", "receipt")} for r in (source.row, alias.row)
        ],
        restricted_root_chips=trace.value - trace.gain,
        exact_root_chips=trace.value,
        information_gain_chips=trace.gain,
        maximum_error_chips=error,
        prefix="restricted own best reply; fixed opponent",
        street_losses_chips=streets,
        rows=rows,
        groups=groups,
        new_training=False,
        native_constructed=False,
        independent_new_row_value_audit=False,
        actual_admission=False,
    )
