"""Score retained own policies and complete fixed own opponents, never train."""

from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_artifacts import array_sha, decode_mass
from poker_ai.evaluation.averaging_history_math import (
    coverage,
    fixed_match,
    window_mass,
)
from poker_ai.evaluation.opponent_learning_contexts import Contexts
from poker_ai.evaluation.opponent_learning_design import Design, is_raw
from poker_ai.evaluation.opponent_learning_replay import ContextFor, member, metadata
from poker_ai.evaluation.opponent_learning_sources import Opponent
from poker_ai.finite import FloatArray
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_checkpoints import write_snapshot
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline


def scoring(contexts: Contexts, row: dict[str, Any]) -> ScoringContext:
    kind = row["tree_kind"] if is_raw(row) else "coarse"
    return contexts.scoring[kind]


class Books:
    """Decode each immutable own mass only once; expose read-only arrays."""

    def __init__(
        self,
        folder: Path,
        design: Design,
        masses: list[dict[str, Any]],
        warms: list[dict[str, Any]],
        context_for: ContextFor,
    ) -> None:
        design.require_rows("masses", masses)
        if len(warms) != 30 or {r["path_index"] for r in warms} != set(range(30)):
            raise ArithmeticError("complete warm origins required for support")
        self.mass: dict[Any, FloatArray] = {}
        self.warm: dict[Any, FloatArray] = {}
        for rows, destination in ((masses, self.mass), (warms, self.warm)):
            for row in rows:
                path = design.path(row["path_index"])
                tree = context_for(path["coordinate"]).tree(path["tree_kind"])
                metadata(row)
                values = decode_mass(
                    member(folder, row["file"]).read_bytes(), tree, row
                )
                key = (
                    (row["path_index"], row["work_label"], row["readout"])
                    if rows is masses
                    else row["path_index"]
                )
                destination[key] = values

    def support(
        self,
        contexts: Contexts,
        row: dict[str, Any],
        captures: dict[str, dict[str, Any]],
    ) -> dict[str, Any] | None:
        if row["readout"] == "current":
            return None
        weight = row["readout"].removesuffix("_average")
        sources = [row] if is_raw(row) else [captures[k] for k in row["components"]]
        masses = [self.mass[r["path_index"], r["work_label"], weight] for r in sources]
        warms = [self.warm[r["path_index"]] for r in sources]
        mass = (
            masses[0]
            if len(masses) == 1
            else contexts.combine_mass(row["arm"], masses[0], masses[1])
        )
        warm = (
            warms[0]
            if len(warms) == 1
            else contexts.combine_mass(row["arm"], warms[0], warms[1])
        )
        context = scoring(contexts, row)
        first = np.unique(context.exact_to_partition, return_index=True)[1]
        river = (context.river_masks[0] | context.river_masks[1])[first]
        return dict(
            whole=coverage(context.partition, mass, river),
            post_warm=coverage(
                context.partition, window_mass(context.partition, warm, mass), river
            ),
        )


def score_profiles(
    folder: Path,
    design: Design,
    profiles: list[dict[str, Any]],
    captures: list[dict[str, Any]],
    policies: dict[str, FloatArray],
    books: Books,
    context_for: ContextFor,
    binding: str,
    send: Send,
    deadline: Deadline,
) -> list[dict[str, Any]]:
    design.require_rows("profiles", profiles)
    if set(policies) != {r["id"] for r in profiles}:
        raise ArithmeticError("all432 retained own policies required before scoring")
    captured = {r["id"]: r for r in captures}
    result = []
    for row in profiles:
        deadline.check()
        contexts = context_for(row["coordinate"])
        context = scoring(contexts, row)
        policy = policies[row["id"]]
        if (
            array_sha(policy) != row["receipt"]["policy_sha256"]
            or row["source_sha256"] != binding
            or row["tree_sha256"] != tree_digest(context.partition)
        ):
            raise ArithmeticError("scoring differs from its own captured game/policy")
        meta = dict(
            **metadata(row),
            source_policy_receipt=row["receipt"],
            coverage=books.support(contexts, row, captured),
            **score_data(context, context.score(policy)),
        )
        filename = f"scored/{sha(row['id'])}.json.gz"
        receipt = write_snapshot(folder / filename, context.partition, policy, meta)
        if receipt["policy_sha256"] != row["receipt"]["policy_sha256"]:
            raise ArithmeticError("scoring changed own policy bits")
        scored = dict(meta, file=filename, receipt=receipt, metadata_sha256=sha(meta))
        result.append(scored)
        send(dict(kind="cell", phase="score", index=row["coordinate"], row=scored))
    design.require_rows("profiles", result)
    return result


def fixed_conditions(
    design: Design,
    policies: dict[str, FloatArray],
    context_for: ContextFor,
    opponents: tuple[Opponent, ...],
    binding: str,
    send: Send,
    deadline: Deadline,
) -> list[dict[str, Any]]:
    if len(opponents) != 16 or any(
        len({p.identifier for p in opponents if p.game == game}) != 8 for game in (0, 1)
    ):
        raise ArithmeticError(
            "all eight distinct frozen own opponents per game required"
        )
    result = []
    for arm in design.manifest()["arms"]:
        if arm["work_label"] != design.labels[-1]:
            continue
        contexts = context_for(arm["coordinate"])
        context = contexts.scoring[arm["information"]]
        fine = context.expand(policies[arm["id"]])
        for opponent in opponents:
            if opponent.game != arm["coordinate"] // 3:
                continue
            if array_sha(opponent.policy) != opponent.fine_policy_sha256:
                raise ArithmeticError("frozen own opponent policy mutated")
            for target in (0, 1):
                deadline.check()
                reply = opponent.replies[target]
                measured = fixed_match(contexts.fine, fine, opponent.policy, reply)
                row = dict(
                    **arm,
                    condition_id=sha([arm["id"], opponent.identifier, target]),
                    target=target,
                    opponent_id=opponent.identifier,
                    source_sha256=binding,
                    candidate_policy_sha256=array_sha(fine),
                    opponent_policy_sha256=array_sha(opponent.policy),
                    opponent_source_policy_sha256=opponent.source_policy_sha256,
                    own_reply_sha256=array_sha(
                        reply.apply(contexts.fine, opponent.policy)
                    ),
                    target_ev_chips=measured["baseline_value_chips"],
                    fine_reply_value_chips=measured["restricted_reply_value_chips"],
                    achieved_own_reply_value_chips=measured[
                        "achieved_reply_value_chips"
                    ],
                    fine_reply_gain_chips=measured["gain_chips"],
                    reply_information="legal fine own-card/public-board information",
                )
                result.append(row)
                send(dict(kind="cell", phase="fixed", index=arm["coordinate"], row=row))
    fixed_inventory(design, result, opponents)
    return result


def fixed_inventory(
    design: Design, rows: list[dict[str, Any]], opponents: tuple[Opponent, ...]
) -> None:
    expected = {}
    for arm in design.manifest()["arms"]:
        if arm["work_label"] == design.labels[-1]:
            for opponent in opponents:
                if opponent.game == arm["coordinate"] // 3:
                    for target in (0, 1):
                        identifier = sha([arm["id"], opponent.identifier, target])
                        expected[identifier] = dict(
                            arm, opponent_id=opponent.identifier, target=target
                        )
    observed = {r["condition_id"]: r for r in rows}
    if (
        len(expected) != 1152
        or len(rows) != len(observed)
        or set(observed) != set(expected)
    ):
        raise ArithmeticError(
            "complete1152 own fixed conditions missing/extra/duplicate"
        )
    for key, wanted in expected.items():
        if any(not same(observed[key].get(k), v) for k, v in wanted.items()):
            raise ArithmeticError(
                "fixed condition changed its typed own/opponent/seat identity"
            )
