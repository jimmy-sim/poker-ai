"""Independent OpenSpiel EFG scalar adapter; exports no strategies or actions.

The explicit array exporter permits the SAME audit path for marked tiny software
fixtures and real matrix games. Only game topology/payoffs/chance and OWN policy
probabilities enter OpenSpiel. Native best-response roots and achieved OWN reply
values come back; native response policies are never requested.
"""

import importlib
import math
from typing import Any

import numpy as np

from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.reply_trace import require_recall


def efg(tree: ArrayTree) -> str:
    require_recall(tree)
    lines = ['EFG 2 R "own-array-comparison" { "P0" "P1" }']
    numbers: list[int] = []
    counts = [0, 0]
    for owner in tree.owners:
        counts[int(owner)] += 1
        numbers.append(counts[int(owner)])
    pending = [0]
    seen: set[int] = set()
    chance = terminal = 0
    while pending:
        node = pending.pop()
        if node in seen:
            raise ArithmeticError("array export requires a rooted tree")
        seen.add(node)
        actor = int(tree.player[node])
        width = int(tree.valid[node].sum())
        if actor == -2:
            terminal += 1
            value = float(tree.terminal_values[node])
            if not math.isfinite(value) or width:
                raise ArithmeticError("invalid exported terminal")
            lines.append(f't "" {terminal} "" {{ {value:.17g} {-value:.17g} }}')
            continue
        if not np.array_equal(tree.valid[node], np.arange(tree.valid.shape[1]) < width):
            raise ArithmeticError("noncontiguous exported edges")
        if actor == -1:
            chance += 1
            probabilities = tree.chance_edges[node, :width]
            if (
                np.any(probabilities < 0)
                or not np.all(np.isfinite(probabilities))
                or abs(float(probabilities.sum()) - 1) > 1e-12
            ):
                raise ArithmeticError("invalid exported chance probabilities")
            menu = " ".join(f'"a{i}" {p:.17g}' for i, p in enumerate(probabilities))
            lines.append(f'c "" {chance} "" {{ {menu} }} 0')
        elif actor in (0, 1):
            info = int(tree.information[node])
            if width != len(tree.actions[info]) or tree.owners[info] != actor:
                raise ArithmeticError("exported owner/menu changed")
            menu = " ".join(f'"a{i}"' for i in range(width))
            lines.append(f'p "" {actor + 1} {numbers[info]} "i{info}" {{ {menu} }} 0')
        else:
            raise ArithmeticError("invalid exported actor")
        pending.extend(int(c) for c in reversed(tree.children[node, :width]))
    if len(seen) != len(tree.player):
        raise ArithmeticError("exported tree omits nodes")
    return "\n".join(lines) + "\n"


class ScalarReference:
    """Read-only independent EFG evaluation/BR; no learner or strategy exporter."""

    def __init__(self, tree: ArrayTree) -> None:
        self.tree = tree
        self.pyspiel: Any = importlib.import_module("pyspiel")
        self.game: Any = self.pyspiel.load_efg_game(efg(tree))
        self.keys = [""] * len(tree.keys)
        self.actions: list[tuple[int, ...]] = [()] * len(tree.keys)
        pending = [(0, self.game.new_initial_state())]
        reverse: dict[str, int] = {}
        while pending:
            node, state = pending.pop()
            actor = int(tree.player[node])
            if actor == -2:
                if (
                    not state.is_terminal()
                    or abs(state.returns()[0] - tree.terminal_values[node]) > 1e-12
                    or abs(sum(state.returns())) > 1e-12
                ):
                    raise ArithmeticError("native terminal alignment changed")
                continue
            width = int(tree.valid[node].sum())
            labels = {state.action_to_string(a): a for a in state.legal_actions()}
            if set(labels) != {f"a{i}" for i in range(width)}:
                raise ArithmeticError("native action labels changed")
            actions = tuple(labels[f"a{i}"] for i in range(width))
            if actor == -1:
                probabilities = dict(state.chance_outcomes())
                if not state.is_chance_node() or any(
                    abs(probabilities[a] - tree.chance_edges[node, i]) > 1e-12
                    for i, a in enumerate(actions)
                ):
                    raise ArithmeticError("native chance alignment changed")
            else:
                info = int(tree.information[node])
                key = str(state.information_state_string())
                if (
                    state.current_player() != actor
                    or (self.keys[info] and self.keys[info] != key)
                    or reverse.setdefault(key, info) != info
                ):
                    raise ArithmeticError("native information/owner alignment changed")
                self.keys[info], self.actions[info] = key, actions
            pending.extend(
                (int(tree.children[node, i]), state.child(a))
                for i, a in reversed(list(enumerate(actions)))
            )
        if not all(self.keys) or len(reverse) != len(tree.keys):
            raise ArithmeticError("native information inventory incomplete")

    def native_policy(self, policy: FloatArray) -> Any:
        self.tree.validate_policy(policy)
        return self.pyspiel.TabularPolicy(
            {
                key: [
                    (a, float(p))
                    for a, p in zip(actions, row[: len(actions)], strict=True)
                ]
                for key, actions, row in zip(
                    self.keys, self.actions, policy, strict=True
                )
            }
        )

    def value(self, policy: FloatArray) -> float:
        return float(
            self.pyspiel.expected_returns(
                self.game.new_initial_state(), self.native_policy(policy), -1, True
            )[0]
        )

    def response_value(self, policy: FloatArray, target: int) -> float:
        if type(target) is not int or target not in (0, 1):
            raise ValueError("invalid native response target")
        native = self.native_policy(policy)
        # OpenSpiel borrows the policy pointer: retain it through .value().
        response = self.pyspiel.TabularBestResponse(self.game, target, native)
        return float(response.value(""))


def compare(
    context: ScoringContext,
    refs: tuple[ScalarReference, ScalarReference],
    detail: dict[str, Any],
) -> dict[str, Any]:
    exact, limited = refs
    policy = unpack_policy(context.partition, detail["policy"])
    saved = context.expand(policy)
    value = exact.value(saved)
    responses = []
    for target in (0, 1):
        sign = 1 if target == 0 else -1
        achieved = {
            name: sign
            * exact.value(unpack_policy(context.exact, detail["replies"][target][name]))
            for name in ("exact", "restricted", "river_before")
        }
        responses.append(
            dict(
                target=target,
                exact_root_chips=exact.response_value(saved, target),
                restricted_root_chips=limited.response_value(policy, target),
                achieved_exact_chips=achieved["exact"],
                achieved_restricted_chips=achieved["restricted"],
                achieved_river_before_chips=achieved["river_before"],
            )
        )
    metrics = dict(
        value_player_zero_chips=value,
        exact_exploitability_chips=math.fsum(r["exact_root_chips"] for r in responses)
        / 2,
        within_partition_gain_chips=math.fsum(
            r["restricted_root_chips"] for r in responses
        )
        / 2,
        extra_information_gap_chips=math.fsum(
            r["exact_root_chips"] - r["restricted_root_chips"] for r in responses
        )
        / 2,
        river_only_gain_exact_prefix_chips=math.fsum(
            r["exact_root_chips"] - r["achieved_river_before_chips"] for r in responses
        )
        / 2,
    )
    errors = [abs(metrics[k] - detail["metrics"][k]) for k in metrics]
    names = dict(
        exact_root_chips="exact_reply_value_chips",
        restricted_root_chips="restricted_reply_value_chips",
        achieved_exact_chips="exact_reply_value_chips",
        achieved_restricted_chips="restricted_reply_value_chips",
        achieved_river_before_chips="river_before_value_chips",
    )
    errors.extend(
        abs(r[k] - detail["responses"][i][v])
        for i, r in enumerate(responses)
        for k, v in names.items()
    )
    if any(not math.isfinite(e) for e in errors):
        raise ArithmeticError("nonfinite independent matched audit")
    return dict(
        native_metrics=metrics, responses=responses, maximum_error_chips=max(errors)
    )
