"""Own fixed-work dual-book training worker; no reference inputs or algorithms."""

import hashlib
import time
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation import frozen_batch_inputs as inputs
from poker_ai.evaluation.averaging_history_artifacts import write_mass
from poker_ai.evaluation.averaging_history_math import coverage, movement, window_mass
from poker_ai.finite import FloatArray
from poker_ai.postflop import pipeline_cost
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_checkpoints import write_snapshot
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.controlled_training import Weight
from poker_ai.postflop.frozen_batches import BatchPoint, observe
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.river_study import Deadline


def array_sha(array: FloatArray) -> str:
    return hashlib.sha256(array.astype("<f8").tobytes()).hexdigest()


def save(
    context: ScoringContext,
    policy: FloatArray,
    metadata: dict[str, Any],
    scratch: Path,
    send: Send,
    deadline: Deadline,
) -> dict[str, Any]:
    deadline.check()
    before, cpu = time.perf_counter(), time.process_time()
    metadata = dict(**metadata, **score_data(context, context.score(policy)))
    relative = f"snapshots/{metadata['id']}.json.gz"
    receipt = write_snapshot(scratch / relative, context.partition, policy, metadata)
    row = dict(
        **metadata,
        file=relative,
        receipt=receipt,
        metadata_sha256=sha(metadata),
        seconds=time.perf_counter() - before,
        cpu_seconds=time.process_time() - cpu,
    )
    send(dict(kind="cell", phase="profile", index=metadata["path_index"], row=row))
    deadline.check()
    return row


def train_one(
    context: ScoringContext,
    path: dict[str, Any],
    index: int,
    originals: dict[str, dict[int, Any]],
    labels: list[int],
    scratch: Path,
    binding: str,
    send: Send,
    deadline: Deadline,
) -> None:
    started, cpu = time.perf_counter(), time.process_time()
    solver = inputs.trainer(context.partition, path)
    solver.initialize_exact()
    setup = time.perf_counter() - started
    first = np.unique(context.exact_to_partition, return_index=True)[1]
    river = (context.river_masks[0] | context.river_masks[1])[first]
    previous: FloatArray | None = None
    profiles = checks = 0

    def capture(point: BatchPoint) -> None:
        nonlocal previous, profiles, checks
        current = solver.current_policy
        changes = (
            movement(context.partition, previous, current)
            if previous is not None
            else None
        )
        for label in point.labels:
            observed = dict(
                id=f"current-{index:03d}-{label}",
                path_index=index,
                case=inputs.case(path, "linear"),
                batch_size=path["batch_size"],
                work_label=label,
                guard_sha256=point.guard_sha256,
                source_sha256=binding,
                current_sha256=array_sha(current),
                current_movement=changes,
            )
            filename = f"currents/{observed['id']}.json.gz"
            receipt = write_snapshot(
                scratch / filename, context.partition, current, observed
            )
            send(
                dict(
                    kind="cell",
                    phase="current",
                    index=index,
                    row=dict(
                        **observed,
                        file=filename,
                        receipt=receipt,
                        metadata_sha256=sha(observed),
                    ),
                )
            )
            verified = (
                inputs.check_prefix(solver, point, label, originals)
                if path["batch_size"] == 1
                else []
            )
            for row in verified:
                send(dict(kind="cell", phase="prefix", index=index, check=row))
                checks += 1
            weights: tuple[Weight, ...] = ("uniform", "linear")
            for weight in weights:
                mass = solver.ledger(weight)
                mass_meta = dict(
                    id=f"mass-{index:03d}-{weight}-{label}",
                    path_index=index,
                    case=inputs.case(path, weight),
                    batch_size=path["batch_size"],
                    work_label=label,
                    guard_sha256=point.guard_sha256,
                    source_sha256=binding,
                )
                mass_file = f"masses/{mass_meta['id']}.json.gz"
                mass_receipt = write_mass(
                    scratch / mass_file, context.partition, mass, mass_meta
                )
                send(
                    dict(
                        kind="cell",
                        phase="mass",
                        index=index,
                        row=dict(
                            **mass_meta,
                            file=mass_file,
                            receipt=mass_receipt,
                            metadata_sha256=sha(mass_meta),
                        ),
                    )
                )
                post = window_mass(context.partition, solver.warm_sum, mass)
                support = dict(
                    whole=coverage(context.partition, mass, river),
                    post_warm=coverage(context.partition, post, river),
                )
                metadata = dict(
                    id=f"path-{index:03d}-{weight}-{label}",
                    path_index=index,
                    case=inputs.case(path, weight),
                    batch_size=path["batch_size"],
                    origin="fresh_B1_replay"
                    if path["batch_size"] == 1
                    else "fresh_batch",
                    work_label=label,
                    iteration=point.iteration,
                    previous_work=point.previous_work,
                    total_work=point.total_work,
                    last_iteration_visits=point.last_iteration_visits,
                    overshoot=point.total_work - label,
                    initialization_visits=solver.initialization_visits,
                    sampled_traversals=solver.sampled_traversals,
                    state_sha256=solver.readout_fingerprint(weight),
                    guard_sha256=point.guard_sha256,
                    current_sha256=array_sha(current),
                    current_movement=changes,
                    coverage=support,
                    source_original_id=originals[weight][label]["id"]
                    if verified
                    else None,
                    source_sha256=binding,
                    initialization_seconds=setup,
                    elapsed_cell_seconds=time.perf_counter() - started,
                )
                save(
                    context,
                    context.partition.normalize(mass),
                    metadata,
                    scratch,
                    send,
                    deadline,
                )
                profiles += 1
        previous = current.copy()

    observe(solver, labels, capture, deadline)
    if profiles != 6 or checks != (6 if path["batch_size"] == 1 else 0):
        raise ArithmeticError("batch path checkpoint/prefix inventory incomplete")
    send(
        dict(
            kind="cell",
            phase="trained",
            index=index,
            profiles=profiles,
            prefix_checks=checks,
            work=solver.nodes_visited,
            iteration=solver.iteration,
            initialization_seconds=setup,
            seconds=time.perf_counter() - started,
            cpu_seconds=time.process_time() - cpu,
        )
    )


def own_job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    started = time.perf_counter()
    contexts = pipeline_cost.contexts(Path(payload["root"]), payload["comparison"])
    deadline = Deadline(payload["remaining_seconds"])
    send(dict(kind="prepared", seconds=time.perf_counter() - started))
    for local in indices:
        deadline.check()
        index = payload["selected"][local]
        path = payload["paths"][index]
        train_one(
            contexts[path["spot_file"], path["representation"]],
            path,
            index,
            payload["prefixes"][index],
            payload["labels"],
            Path(payload["scratch"]),
            payload["binding"],
            send,
            deadline,
        )
    return dict(
        paths=len(indices),
        profiles=6 * len(indices),
        masses=6 * len(indices),
        currents=3 * len(indices),
        prefix_checks=(
            6 * len(indices) if payload["selected"] == list(range(24)) else 0
        ),
    )
