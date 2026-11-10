"""Explicit toy-only fixed OWN controls; production uses original saved controls."""

from typing import Any

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.averaging_history_math import fixed_match
from poker_ai.evaluation.controlled_reply_math import Reply, trace
from poker_ai.evaluation.private_prefix_design import TOY
from poker_ai.finite import FloatArray
from poker_ai.postflop.controlled_scoring import ScoringContext


class ToyOpponents:
    """Four deterministic probability tables, not trained/reference strategies.

    They are fictional stand-ins for the four old full controls, used solely to
    exercise the complete archive/evaluation shape. Logical repeated contexts
    share these same tables; their results are not poker-strength observations.
    """

    def __init__(self, context: ScoringContext) -> None:
        self.context = context
        self.policies = {}
        self.replies = {}
        tree = context.partition
        for k in range(4):
            weights = tree.legal.copy()
            for i, menu in enumerate(tree.actions):
                weights[i, : len(menu)] = [
                    1 + ((i + j + k) % 5) for j in range(len(menu))
                ]
            policy = tree.normalize(weights)
            policy.flags.writeable = False
            identifier = f"EXPLICIT_TOY_SCRIPTED_CONTROL_{k}"
            self.policies[identifier] = policy
            for target in (0, 1):
                self.replies[identifier, target] = trace(
                    tree, policy, target, ("TURN",) * len(tree.keys), 1e-9
                )[1]

    def opponent(self, row: dict[str, Any]) -> tuple[FloatArray, Reply]:
        return self.policies[row["opponent_profile_id"]], self.replies[
            row["opponent_profile_id"], row["target"]
        ]

    def matches(
        self, row: dict[str, Any], policy: FloatArray, binding: str
    ) -> list[dict[str, Any]]:
        if row["scope"] != TOY:
            raise ValueError("fictional opponents cannot enter a real poker study")
        tree = self.context.partition
        result = []
        for identifier, opponent in self.policies.items():
            for target in (0, 1):
                reply = self.replies[identifier, target]
                result.append(
                    dict(
                        **fixed_match(tree, policy, opponent, reply),
                        path_index=row["path_index"],
                        case=row["case"],
                        batch_size=row["batch_size"],
                        work_label=row["work_label"],
                        own_snapshot_id=row["id"],
                        own_source_profile_id=row["id"],
                        own_variant=row["readout"],
                        opponent_profile_id=identifier,
                        own_policy_sha256=array_sha(policy),
                        opponent_policy_sha256=array_sha(opponent),
                        reply_sha256=array_sha(reply.apply(tree, opponent)),
                        source_sha256=binding,
                    )
                )
        return result
