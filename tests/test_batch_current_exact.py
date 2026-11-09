"""Independent terminal-path enumeration and exhaustive deterministic own replies."""

import itertools
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.averaging_history_software import toy_context
from poker_ai.evaluation.batch_current_fixture import analytic
from poker_ai.evaluation.batch_current_inputs import Sources
from poker_ai.evaluation.batch_current_math import matches
from poker_ai.evaluation.controlled_reply_inputs import Inputs, SourcePolicy
from poker_ai.evaluation.controlled_reply_math import trace
from poker_ai.finite import ArrayTree, FloatArray


def terminal_sum(
    tree: ArrayTree, first: FloatArray, second: FloatArray, target: int
) -> float:
    # Explicit terminal path products, not tree.edges/tree.values or a BR helper.
    total = 0.0
    stack = [(0, 1.0)]
    while stack:
        node, reach = stack.pop()
        actor = int(tree.player[node])
        if actor == -2:
            total += (
                reach * float(tree.terminal_values[node]) * (1 if target == 0 else -1)
            )
            continue
        for col in np.flatnonzero(tree.valid[node]):
            probability = (
                float(tree.chance_edges[node, col])
                if actor == -1
                else float(
                    (first if actor == 0 else second)[tree.information[node], col]
                )
            )
            stack.append((int(tree.children[node, col]), reach * probability))
    return total


def exhaustive_root(tree: ArrayTree, opponent: FloatArray, target: int) -> float:
    owned = np.flatnonzero(tree.owners == target)
    values = []
    for choices in itertools.product(*(range(len(tree.actions[i])) for i in owned)):
        candidate = opponent.copy()
        candidate[owned] = 0
        candidate[owned, np.asarray(choices)] = 1
        values.append(
            terminal_sum(
                tree,
                candidate if target == 0 else opponent,
                opponent if target == 0 else candidate,
                target,
            )
        )
    return max(values)


def test_all8_fixed_targets_equal_independent_path_sums_and_exhaustive_roots() -> None:
    context = toy_context()
    tree = context.partition
    candidate = analytic(17)
    base: dict[str, Any] = dict(
        spot_file="EXPLICIT_TINY",
        representation="exact",
        seed=None,
        traversal="full",
        regret_weight="linear",
        bridge="common",
    )
    controls: list[SourcePolicy] = []
    replies = {}
    for i, (clip, weight) in enumerate(
        itertools.product(("signed", "clipped"), ("uniform", "linear"))
    ):
        case = dict(base, regret_rule=clip, average_weight=weight)
        policy = analytic(i + 2)
        control = SourcePolicy(
            case, dict(receipt=dict(policy_sha256=array_sha(policy))), policy
        )
        controls.append(control)
        for target in (0, 1):
            _, reply, _ = trace(
                tree, policy, target, tuple("TURN" for _ in tree.keys), 1e-9
            )
            replies[control.identifier, target] = reply
    data = HistoryInputs(
        {},
        Inputs(
            {},
            dict(scope="EXPLICIT_TOY"),
            {("EXPLICIT_TINY", "exact"): context},
            tuple(controls),
        ),
        {},
        replies,
    )
    sources = Sources(Path("EXPLICIT_UNUSED_SOURCE"), {}, data, {})
    case = dict(
        base,
        traversal="external",
        seed=7,
        regret_rule="signed",
        average_weight="linear",
    )
    row: dict[str, Any] = dict(
        id="EXPLICIT_CURRENT",
        path_index=0,
        case=case,
        batch_size=4,
        work_label=10000000,
        variant="current",
        receipt=dict(policy_sha256=array_sha(candidate)),
    )
    before = candidate.tobytes()
    result = matches(sources, row, candidate, "e" * 64)
    assert len(result) == 8 and before == candidate.tobytes()
    by_id = {p.identifier: p for p in controls}
    for r in result:
        opponent = by_id[r["opponent_profile_id"]].policy
        target = r["target"]
        expected = terminal_sum(
            tree,
            candidate if target == 0 else opponent,
            opponent if target == 0 else candidate,
            target,
        )
        root = exhaustive_root(tree, opponent, target)
        assert abs(r["baseline_value_chips"] - expected) < 1e-12
        assert abs(r["restricted_reply_value_chips"] - root) < 1e-12
        assert abs(r["gain_chips"] - (root - expected)) < 1e-12
