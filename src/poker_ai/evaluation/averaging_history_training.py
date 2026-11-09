"""Replay frozen OWN trajectories and observe current/window/whole policies."""

import time
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_artifacts import array_sha, write_mass
from poker_ai.evaluation.averaging_history_math import coverage, movement, window_mass
from poker_ai.evaluation.averaging_history_observe import HistoryPoint, observe_history
from poker_ai.finite import FloatArray
from poker_ai.postflop import node_profile, pipeline_cost
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_checkpoints import write_snapshot
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline


def check_prefix(point: HistoryPoint, original: dict[str, Any]) -> None:
    p = point.observation
    if (
        not same(p.iteration, original["iteration"])
        or not same(p.previous_work, original["previous_work"])
        or not same(p.total_work, original["total_work"])
        or not same(p.last_iteration_visits, original["last_iteration_visits"])
        or p.state_sha256 != original["state_sha256"]
        or array_sha(p.policy) != original["receipt"]["policy_sha256"]
    ):
        raise ArithmeticError("original trajectory/average prefix changed")


def train_one(
    context: ScoringContext,
    case: dict[str, Any],
    source_id: str,
    index: int,
    original: dict[int, dict[str, Any]],
    config: dict[str, Any],
    scratch: Path,
    binding: str,
    deadline: Deadline,
    send: Send,
) -> None:
    """No native input influences updates. Parent prerequisite receipts are separate.

    Profiles and masses have independent immutable OWN envelopes. Every observer
    callback, including score/IO work, is inside the frozen state-mutation guard.
    A failed prefix prevents a completed case and leaves its partial files/events.
    """
    started, cpu = time.perf_counter(), time.process_time()
    tree = context.partition
    solver = node_profile.trainer(
        tree, case, "nodes" if case["traversal"] == "external" else "parent"
    )
    solver.initialize_exact()
    initialization_seconds = time.perf_counter() - started
    first = np.unique(context.exact_to_partition, return_index=True)[1]
    river = (context.river_masks[0] | context.river_masks[1])[first]
    boundaries: dict[int, HistoryPoint] = {}
    mass_rows: dict[int, dict[str, Any]] = {}
    previous: FloatArray | None = None
    prefixes, profiles, masses = 0, 0, 0
    final_label = config["source_target"]
    source_final = original[final_label]

    def common(point: HistoryPoint, threshold: int) -> dict[str, Any]:
        p = point.observation
        return dict(
            index=index,
            case=case,
            source_profile_id=source_id,
            source_snapshot_id=source_final["id"],
            original_index=source_final["index"],
            original_policy_sha256=source_final["receipt"]["policy_sha256"],
            source_sha256=binding,
            work_label=threshold,
            iteration=p.iteration,
            previous_work=p.previous_work,
            total_work=p.total_work,
            last_iteration_visits=p.last_iteration_visits,
            state_sha256=p.state_sha256,
            learning_path_sha256=point.learning_path_sha256,
            initialization_visits=solver.initialization_visits,
        )

    def save_profile(
        point: HistoryPoint,
        threshold: int,
        kind: str,
        variant: str,
        order: int,
        policy: FloatArray,
        support: dict[str, Any] | None,
        changes: dict[str, float] | None = None,
        window: dict[str, Any] | None = None,
    ) -> None:
        nonlocal profiles
        deadline.check()
        before, consumed = time.perf_counter(), time.process_time()
        scored = score_data(
            context, context.score(policy, tolerance=config["tolerance_chips"])
        )
        if (
            kind == "whole_average"
            and compare(scored, {k: source_final[k] for k in scored})
            > config["tolerance_chips"]
        ):
            raise ArithmeticError("recaptured whole average score differs from source")
        identifier = f"case-{index:03d}-{variant}"
        metadata = dict(
            **common(point, threshold),
            id=identifier,
            kind=kind,
            variant=variant,
            order=order,
            coverage=support,
            current_movement=changes,
            window=window,
            **scored,
        )
        relative = f"snapshots/{identifier}.json.gz"
        receipt = write_snapshot(scratch / relative, tree, policy, metadata)
        row = dict(
            **metadata,
            file=relative,
            receipt=receipt,
            metadata_sha256=sha(metadata),
            seconds=time.perf_counter() - before,
            cpu_seconds=time.process_time() - consumed,
        )
        send(dict(kind="cell", phase="profile", index=index, row=row))
        profiles += 1
        deadline.check()

    def capture(point: HistoryPoint) -> None:
        nonlocal previous, prefixes, masses
        for _, threshold in point.observation.labels:
            if threshold in original:
                check_prefix(point, original[threshold])
                if (
                    solver.initialization_visits
                    != original[threshold]["initialization_visits"]
                ):
                    raise ArithmeticError("original warm initialization work changed")
                send(
                    dict(
                        kind="cell",
                        phase="prefix",
                        index=index,
                        work_label=threshold,
                        source_snapshot_id=original[threshold]["id"],
                        **{
                            k: common(point, threshold)[k]
                            for k in ("state_sha256", "iteration", "total_work")
                        },
                    )
                )
                prefixes += 1
            if threshold in config["cumulative_mass_work_labels"]:
                boundaries[threshold] = point
                identifier = f"case-{index:03d}-mass-{threshold}"
                metadata = dict(
                    **common(point, threshold),
                    id=identifier,
                    kind="cumulative_mass",
                    order=config["cumulative_mass_work_labels"].index(threshold),
                )
                relative = f"masses/{identifier}.json.gz"
                receipt = write_mass(
                    scratch / relative, tree, point.cumulative_average, metadata
                )
                row = dict(
                    **metadata,
                    file=relative,
                    receipt=receipt,
                    metadata_sha256=sha(metadata),
                )
                mass_rows[threshold] = row
                send(dict(kind="cell", phase="mass", index=index, row=row))
                masses += 1
            changes = (
                movement(tree, previous, point.current)
                if previous is not None
                else None
            )
            save_profile(
                point,
                threshold,
                "current",
                f"current-{threshold}",
                config["current_work_labels"].index(threshold),
                point.current,
                None,
                changes,
            )
            previous = point.current
            if threshold != final_label:
                continue
            save_profile(
                point,
                threshold,
                "whole_average",
                "whole_average",
                5,
                point.observation.policy,
                coverage(tree, point.cumulative_average, river),
            )
            for number, (left, right) in enumerate(config["suffix_windows"]):
                begin, end = boundaries[left], boundaries[right]
                mass = window_mass(
                    tree, begin.cumulative_average, end.cumulative_average
                )
                window = dict(
                    left_label=left,
                    right_label=right,
                    left_iteration=begin.observation.iteration,
                    left_work=begin.observation.total_work,
                    left_state_sha256=begin.observation.state_sha256,
                    left_mass_sha256=mass_rows[left]["receipt"]["mass_sha256"],
                    right_mass_sha256=mass_rows[right]["receipt"]["mass_sha256"],
                    increment_mass_sha256=array_sha(mass),
                )
                variant = ("suffix_5m_10m", "suffix_9m_10m")[number]
                save_profile(
                    point,
                    right,
                    "suffix",
                    variant,
                    6 + number,
                    tree.normalize(mass),
                    coverage(tree, mass, river),
                    window=window,
                )

    observe_history(solver, config["current_work_labels"], river, capture, deadline)
    if (prefixes, profiles, masses) != (3, 8, 3):
        raise ArithmeticError("history case prefix/profile/mass inventory incomplete")
    send(
        dict(
            kind="cell",
            phase="trained",
            index=index,
            prefixes=prefixes,
            profiles=profiles,
            masses=masses,
            iteration=solver.iteration,
            work=solver.nodes_visited,
            initialization_seconds=initialization_seconds,
            seconds=time.perf_counter() - started,
            cpu_seconds=time.process_time() - cpu,
        )
    )


def own_job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    root, scratch = Path(payload["root"]), Path(payload["scratch"])
    deadline = Deadline(payload["remaining_seconds"])
    started = time.perf_counter()
    contexts = pipeline_cost.contexts(root, payload["comparison"])
    send(dict(kind="prepared", seconds=time.perf_counter() - started))
    for index in indices:
        deadline.check()
        cell = payload["cells"][index]
        train_one(
            contexts[cell["case"]["spot_file"], cell["case"]["representation"]],
            cell["case"],
            cell["source_id"],
            index,
            cell["prefixes"],
            payload["config"],
            scratch,
            payload["binding"],
            deadline,
            send,
        )
    return dict(
        cells=len(indices),
        profiles=8 * len(indices),
        masses=3 * len(indices),
        prefixes=3 * len(indices),
    )
