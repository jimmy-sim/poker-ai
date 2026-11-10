"""Capture without scoring; verify old trajectories before the global barrier.

The generic worker accepts explicit contexts so small tests can exercise exactly
the production capture path. Only matched_update_inputs.load creates real poker
inputs; fixture records must never be used to obtain real study admission.
"""

from pathlib import Path
from typing import Any

from poker_ai.evaluation import reduced_study_inputs as study
from poker_ai.evaluation.averaging_history_artifacts import array_sha, write_mass
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_checkpoints import write_snapshot
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.coordinate_observer import CoordinatePoint, observe
from poker_ai.postflop.frozen_batches import FrozenBatchTrainer
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline


def checkpoint(
    solver: FrozenBatchTrainer,
    point: CoordinatePoint,
    expected: dict[str, Any],
) -> dict[str, Any]:
    """Compare actual counters, full state, both books/current and raw mass bits."""
    label = expected["work_label"]
    if type(label) is not int or label not in point.work_labels:
        raise ArithmeticError("checkpoint is not an observed source work crossing")
    actual = dict(
        path_index=expected["path_index"],
        work_label=label,
        iteration=point.iteration,
        previous_work=point.previous_work,
        total_work=point.total_work,
        last_iteration_visits=point.last_iteration_visits,
        initialization_visits=solver.initialization_visits,
        sampled_traversals=solver.sampled_traversals,
        guard_sha256=point.guard_sha256,
        current_sha256=array_sha(solver.current_policy),
        readouts={
            w: dict(
                source_id=expected["readouts"][w]["source_id"],
                original_id=expected["readouts"][w]["original_id"],
                policy_sha256=array_sha(solver.tree.normalize(solver.ledger(w))),
                mass_sha256=array_sha(solver.ledger(w)),
                state_sha256=solver.readout_fingerprint(w),
            )
            for w in study.WEIGHTS
        },
    )
    if not same(actual, expected):
        raise ArithmeticError("B1 source current/mass/readout/state/work mismatch")
    return actual


def barrier(checks: list[dict[str, Any]], expected: list[dict[str, Any]]) -> None:
    """Every case/work crossing must pass, not only the last worker to finish."""

    def key(r: dict[str, Any]) -> tuple[int, int]:
        return r["path_index"], r["work_label"]

    if (
        len(checks) != len(expected)
        or len({key(r) for r in checks}) != len(checks)
        or not same(sorted(checks, key=key), sorted(expected, key=key))
    ):
        raise ArithmeticError("complete original B1 barrier has not passed")


def collect(
    context: ScoringContext,
    path: dict[str, Any],
    index: int,
    targets: list[dict[str, Any]],
    expected: list[dict[str, Any]],
    scratch: Path,
    binding: str,
    scope: str,
    send: Send,
    deadline: Deadline,
) -> dict[str, int]:
    """Whole two-seat updates only; duplicate targets keep logical identities."""
    if (
        path["batch_size"] != 1
        or any(
            t["baseline_path_index"] != index
            or type(t["target_iteration"]) is not int
            or t["target_iteration"] < 1
            for t in targets
        )
        or len({t["id"] for t in targets}) != len(targets)
    ):
        raise ValueError("invalid B1 capture target identity")
    if (
        not targets
        or not expected
        or any(t["target_iteration"] > expected[-1]["iteration"] for t in targets)
    ):
        raise ValueError("capture target would extend the original B1 endpoint")
    labels = sorted(r["work_label"] for r in expected)
    if any(r["path_index"] != index for r in expected):
        raise ValueError("cross-context B1 checkpoint")
    solver = study.trainer(context.partition, path)
    solver.initialize_exact()
    counts = dict(captures=0, masses=0, checkpoints=0, capture_events=0)

    def capture(point: CoordinatePoint) -> None:
        for label in point.work_labels:
            peer = next(r for r in expected if r["work_label"] == label)
            checked = checkpoint(solver, point, peer)
            send(dict(kind="cell", phase="checkpoint", index=index, row=checked))
            counts["checkpoints"] += 1
        selected = [t for t in targets if t["target_iteration"] == point.iteration]
        if not selected:
            return
        counts["capture_events"] += 1
        for target in selected:
            common = dict(
                path_index=index,
                case=study.case(path, "linear"),
                batch_size=1,
                scope=scope,
                target_id=target["id"],
                comparison_batch_size=target["comparison_batch_size"],
                iteration=point.iteration,
                total_work=point.total_work,
                previous_work=point.previous_work,
                last_iteration_visits=point.last_iteration_visits,
                initialization_visits=solver.initialization_visits,
                sampled_traversals=solver.sampled_traversals,
                guard_sha256=point.guard_sha256,
                source_sha256=binding,
            )
            policies = {"current": solver.current_policy}
            for weight in study.WEIGHTS:
                mass = solver.ledger(weight)
                metadata = dict(
                    **common, id=target["id"] + "-" + weight, readout=weight
                )
                filename = "masses/" + metadata["id"] + ".json.gz"
                receipt = write_mass(
                    scratch / filename, context.partition, mass, metadata
                )
                send(
                    dict(
                        kind="cell",
                        phase="mass",
                        index=index,
                        row=dict(
                            **metadata,
                            file=filename,
                            receipt=receipt,
                            metadata_sha256=sha(metadata),
                        ),
                    )
                )
                counts["masses"] += 1
                policies[weight + "_average"] = context.partition.normalize(mass)
            for readout, policy in policies.items():
                deadline.check()
                metadata = dict(
                    **common,
                    id=target["id"] + "-" + readout,
                    readout=readout,
                    variant=readout,
                )
                filename = "captures/" + metadata["id"] + ".json.gz"
                receipt = write_snapshot(
                    scratch / filename, context.partition, policy, metadata
                )
                send(
                    dict(
                        kind="cell",
                        phase="capture",
                        index=index,
                        row=dict(
                            **metadata,
                            file=filename,
                            receipt=receipt,
                            metadata_sha256=sha(metadata),
                        ),
                    )
                )
                counts["captures"] += 1

    observe(
        solver,
        iterations=sorted({t["target_iteration"] for t in targets}),
        work=labels,
        capture=capture,
        deadline=deadline,
    )
    if counts["captures"] != 3 * len(targets) or counts["masses"] != 2 * len(targets):
        raise ArithmeticError("capture inventory incomplete")
    return dict(**counts, iteration=solver.iteration, total_work=solver.nodes_visited)
