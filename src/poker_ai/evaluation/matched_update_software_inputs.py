"""Marked tiny inputs for the complete pipeline; never substitutes for real sources.

Twenty-four logical cases share one nonuniform Kuhn tree and six seed/rule paths.
The right-hand policies deliberately equal independent B1 prefixes: a zero-gap
control for arithmetic/lineage, not evidence about batched poker training.
"""

import itertools
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from poker_ai.evaluation import reduced_study_inputs as study
from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.averaging_history_math import fixed_match
from poker_ai.evaluation.averaging_history_software import toy_context
from poker_ai.evaluation.controlled_reply_math import Reply, trace
from poker_ai.finite import FloatArray
from poker_ai.postflop.frozen_batches import guard
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.river_study import Deadline

SCOPE = "EXPLICIT_TINY_FIXTURES_NOT_POKER_RESULTS"


@dataclass(frozen=True)
class Fixture:
    paths: list[dict[str, Any]]
    expected: list[dict[str, Any]]
    manifest: dict[str, Any]
    right: list[dict[str, Any]]
    right_fixed: list[dict[str, Any]]
    controls: dict[str, tuple[FloatArray, dict[int, Reply]]]

    def fixed(self, row: dict[str, Any], policy: FloatArray) -> list[dict[str, Any]]:
        tree = toy_context().partition
        group = row["path_index"] // 6
        result = []
        for name, (opponent, replies) in self.controls.items():
            if not name.startswith(f"EXPLICIT-control-{group}-"):
                continue
            for target in (0, 1):
                result.append(
                    dict(
                        **fixed_match(tree, policy, opponent, replies[target]),
                        path_index=row["path_index"],
                        case=row["case"],
                        batch_size=1,
                        work_label=None,
                        own_snapshot_id=row["id"],
                        own_source_profile_id=row["id"],
                        own_variant=row["readout"],
                        opponent_profile_id=name,
                        own_policy_sha256=array_sha(policy),
                        opponent_policy_sha256=array_sha(opponent),
                        reply_sha256=array_sha(replies[target].apply(tree, opponent)),
                        source_sha256=row["source_sha256"],
                    )
                )
        return result


def build(
    binding: str, deadline: Deadline, mark_started: Callable[[], None] | None = None
) -> Fixture:
    context = toy_context()
    paths = [
        dict(
            batch_size=1,
            spot_file=game,
            representation=rep,
            regret_rule=rule,
            seed=seed,
        )
        for game, rep, rule, seed in itertools.product(
            ("EXPLICIT_LOW", "EXPLICIT_MEDIUM"),
            ("EXPLICIT_EXACT", "EXPLICIT_PARTITION"),
            ("signed", "clipped"),
            (20261301, 20261302, 20261303),
        )
    ]
    controls = {}
    path = paths[0]
    control = study.trainer(context.partition, path)
    control.initialize_exact()
    if mark_started is not None:
        mark_started()
    for slot, iteration in enumerate((1, 3, 5, 9)):
        while control.iteration < iteration:
            control.step()
        opponent = control.current_policy.copy()
        opponent.flags.writeable = False
        replies = {
            target: trace(
                context.partition,
                opponent,
                target,
                ("TURN",) * len(context.partition.keys),
                1e-9,
            )[1]
            for target in (0, 1)
        }
        for group in range(4):
            controls[f"EXPLICIT-control-{group}-{slot}"] = opponent, replies
    expected: list[dict[str, Any]] = []
    targets: list[dict[str, Any]] = []
    pairs: list[dict[str, Any]] = []
    right: list[dict[str, Any]] = []
    right_fixed: list[dict[str, Any]] = []
    fixture = Fixture(
        paths,
        expected,
        dict(iteration_targets=targets, self_pairs=pairs),
        right,
        right_fixed,
        controls,
    )
    for index, path in enumerate(paths):
        solver = study.trainer(context.partition, path)
        solver.initialize_exact()
        previous = 0
        for iteration in range(1, 17):
            deadline.check()
            if iteration in (2, 7, 16):
                expected.append(
                    dict(
                        path_index=index,
                        work_label=solver.nodes_visited - 1,
                        iteration=iteration,
                        previous_work=previous,
                        total_work=solver.nodes_visited,
                        last_iteration_visits=solver.nodes_visited - previous,
                        initialization_visits=solver.initialization_visits,
                        sampled_traversals=solver.sampled_traversals,
                        guard_sha256=guard(solver),
                        current_sha256=array_sha(solver.current_policy),
                        readouts={
                            w: dict(
                                source_id=f"EXPLICIT-source-{index}-{iteration}-{w}",
                                original_id=f"EXPLICIT-original-{index}-{iteration}-{w}",
                                policy_sha256=array_sha(
                                    context.partition.normalize(solver.ledger(w))
                                ),
                                mass_sha256=array_sha(solver.ledger(w)),
                                state_sha256=solver.readout_fingerprint(w),
                            )
                            for w in study.WEIGHTS
                        },
                    )
                )
            if iteration in (4, 8):
                batch = 4 if iteration == 4 else 16
                target_id = f"prefix-{index:03d}-B{batch}"
                targets.append(
                    dict(
                        id=target_id,
                        baseline_path_index=index,
                        comparison_batch_size=batch,
                        target_iteration=iteration,
                        baseline_original_final_iteration=16,
                    )
                )
                policies = dict(current=solver.current_policy)
                policies.update(
                    {
                        w + "_average": context.partition.normalize(solver.ledger(w))
                        for w in study.WEIGHTS
                    }
                )
                for readout, policy in policies.items():
                    identifier = "EXPLICIT-reused-" + target_id + "-" + readout
                    row = dict(
                        id=identifier,
                        path_index=index,
                        case=study.case(path, "linear"),
                        iteration=iteration,
                        total_work=solver.nodes_visited,
                        receipt=dict(policy_sha256=array_sha(policy)),
                        readout=readout,
                        source_sha256=binding,
                        **score_data(context, context.score(policy)),
                    )
                    right.append(row)
                    right_fixed.extend(fixture.fixed(row, policy))
                    pairs.append(
                        dict(
                            target_id=target_id,
                            readout=readout,
                            target_iteration=iteration,
                            planned_prefix_id=target_id + "-" + readout,
                            reused_profile_id=identifier,
                            reused_policy_sha256=array_sha(policy),
                        )
                    )
            if iteration < 16:
                previous = solver.nodes_visited
                solver.step()
    return fixture
