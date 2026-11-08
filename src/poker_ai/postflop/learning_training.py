"""Fixed-cell learning worker around frozen trainers, observer and own scorer."""

import time
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.postflop import controlled_profile, node_profile, pipeline_cost
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_checkpoints import (
    Observation,
    observe,
    pack_policy,
    write_snapshot,
)
from poker_ai.postflop.controlled_scoring import OwnScore, ScoringContext
from poker_ai.postflop.learning_artifacts import decode, sha
from poker_ai.postflop.learning_validation import validate_row
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline


def score_data(context: ScoringContext, score: OwnScore) -> dict[str, Any]:
    return dict(
        metrics=score.metrics,
        responses=score.responses,
        reply_sha256=[
            {k: sha(pack_policy(context.exact, v)) for k, v in row.items()}
            for row in score.replies
        ],
        maximum_accounting_error=score.maximum_accounting_error,
    )


def replay_detail(
    context: ScoringContext, row: dict[str, Any], blob: bytes, tolerance: float
) -> tuple[float, dict[str, Any]]:
    from poker_ai.postflop.controlled_checkpoints import unpack_policy

    detail = decode(blob, context, row)
    policy = unpack_policy(context.partition, detail["policy"])
    score = context.score(policy, tolerance=tolerance)
    actual = score_data(context, score)
    error = compare(actual, {k: detail[k] for k in actual})
    if error > tolerance:
        raise ArithmeticError("own checkpoint replay changed metrics/replies")
    detail["replies"] = [
        {k: pack_policy(context.exact, v) for k, v in row.items()}
        for row in score.replies
    ]
    return error, detail


def replay_snapshot(
    context: ScoringContext, row: dict[str, Any], blob: bytes, tolerance: float
) -> float:
    return replay_detail(context, row, blob, tolerance)[0]


def train_one(
    context: ScoringContext,
    cell: dict[str, Any],
    index: int,
    labels: dict[str, list[int]],
    scratch: Path,
    binding: str,
    deadline: Deadline,
    send: Send,
    prefix: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """No native inputs. All observations are guarded by frozen state fingerprints."""
    started, cpu = time.perf_counter(), time.process_time()
    solver = node_profile.trainer(
        context.partition,
        cell,
        "nodes" if cell["traversal"] == "external" else "parent",
    )
    if cell["bridge"] != "cold_target_history_mass":
        solver.initialize_exact()
    initialization_seconds = time.perf_counter() - started
    first = np.unique(context.exact_to_partition, return_index=True)[1]
    river = (context.river_masks[0] | context.river_masks[1])[first]
    iterations = sorted(
        set(labels["iteration"] + ([prefix["iterations"]] if prefix else []))
    )
    records = []
    observed_seconds = 0.0

    def capture(packet: Observation) -> None:
        nonlocal observed_seconds
        before, consumed = time.perf_counter(), time.process_time()
        if prefix is not None and packet.iteration == prefix["iterations"]:
            if (
                packet.state_sha256 != prefix["state_sha256"]
                or packet.total_work != prefix["total_visits"]
                or solver.initialization_visits != prefix["initialization_visits"]
            ):
                raise ArithmeticError(
                    "controlled prefix differs from pinned serial endpoint"
                )
            send(
                dict(
                    kind="cell",
                    phase="prefix",
                    index=index,
                    iteration=packet.iteration,
                    state_sha256=packet.state_sha256,
                    work=packet.total_work,
                )
            )
        requested: list[list[Any]] = [
            list(label) for label in packet.labels if label[1] in labels[label[0]]
        ]
        if not requested:
            return
        identifier = f"cell-{index:03d}-iteration-{packet.iteration}"
        metadata = dict(
            id=identifier,
            tree_nodes=len(context.partition.player),
            information_sets=len(context.partition.keys),
            padded_width=context.partition.legal.shape[1],
            index=index,
            case=cell,
            source_sha256=binding,
            labels=requested,
            iteration=packet.iteration,
            previous_work=packet.previous_work,
            total_work=packet.total_work,
            last_iteration_visits=packet.last_iteration_visits,
            overshoots={
                str(t): packet.total_work - t for axis, t in requested if axis == "work"
            },
            state_sha256=packet.state_sha256,
            initialization_visits=solver.initialization_visits,
            diagnostics=packet.diagnostics,
            initialization_seconds=initialization_seconds,
            elapsed_cell_seconds=before - started,
            **score_data(context, context.score(packet.policy)),
        )
        relative = f"snapshots/{identifier}.json.gz"
        receipt = write_snapshot(
            scratch / relative, context.partition, packet.policy, metadata
        )
        # Own reply fingerprints bind reconstruction without redundant arrays.
        scalar = metadata
        # These timing fields are metadata too; the row's outer timers are separate.
        row = dict(
            **scalar,
            file=relative,
            receipt=receipt,
            metadata_sha256=sha(metadata),
            seconds=time.perf_counter() - before,
            cpu_seconds=time.process_time() - consumed,
        )
        records.append(row)
        send(dict(kind="cell", phase="snapshot", index=index, row=row))
        observed_seconds += time.perf_counter() - before
        deadline.check()

    observe(solver, labels["work"], iterations, river, capture, deadline)
    send(
        dict(
            kind="cell",
            phase="trained",
            index=index,
            snapshots=len(records),
            iteration=solver.iteration,
            work=solver.nodes_visited,
            seconds=time.perf_counter() - started,
            cpu_seconds=time.process_time() - cpu,
            observation_seconds=observed_seconds,
        )
    )
    return records


def own_job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    root, scratch = Path(payload["root"]), Path(payload["scratch"])
    deadline = Deadline(payload["remaining_seconds"])
    started = time.perf_counter()
    contexts = pipeline_cost.contexts(root, payload["comparison"])
    send(dict(kind="prepared", seconds=time.perf_counter() - started))
    records = []
    for index in indices:
        deadline.check()
        cell = payload["cells"][index]
        records.extend(
            train_one(
                contexts[cell["spot_file"], cell["representation"]],
                cell,
                index,
                payload["labels"],
                scratch,
                payload["source_sha256"],
                deadline,
                send,
                payload["prefixes"][controlled_profile.identity(cell)],
            )
        )
        print(
            f"controlled cell {index + 1}/140 saved; worker partition {indices[0] % 3}",
            flush=True,
        )
    maximum, replay_started = 0.0, time.perf_counter()
    for row in records:
        deadline.check()
        cell = row["case"]
        context = contexts[cell["spot_file"], cell["representation"]]
        maximum = max(
            maximum,
            replay_snapshot(
                context,
                row,
                (scratch / row["file"]).read_bytes(),
                payload["tolerance"],
            ),
        )
    return dict(
        cells=len(indices),
        snapshots=len(records),
        own_replayed=len(records),
        maximum_error_chips=maximum,
        replay_seconds=time.perf_counter() - replay_started,
    )


def rows_from_batch(batch: dict[str, Any]) -> list[dict[str, Any]]:
    return sorted(
        [
            e["row"]
            for w in batch["workers"]
            for e in w["messages"]
            if e["kind"] == "cell" and e["phase"] == "snapshot"
        ],
        key=lambda row: (row["index"], row["iteration"]),
    )


def validate_grid(
    batch: dict[str, Any],
    cells: list[dict[str, Any]],
    labels: dict[str, list[int]],
    *,
    require_prefix: bool = True,
) -> list[dict[str, Any]]:
    """Reject missing/duplicate cells, labels, worker ownership or false crossings."""
    rows = rows_from_batch(batch)
    if batch["status"] != "completed" or batch["failure"] is not None:
        raise ArithmeticError("incomplete controlled grid")
    for row in rows:
        validate_row(row)
    ids = [r["id"] for r in rows]
    if len(ids) != len(set(ids)):
        raise ArithmeticError("duplicate controlled snapshot")
    for worker, assigned in zip(batch["workers"], batch["assignments"], strict=True):
        if worker["exitcode"] != 0:
            raise ArithmeticError("controlled worker did not exit cleanly")
        events = [e for e in worker["messages"] if e["kind"] == "cell"]
        if any(e["phase"] not in {"snapshot", "prefix", "trained"} for e in events):
            raise ArithmeticError("unknown controlled cell event")
        if any(
            e["phase"] == "snapshot" and e["row"]["index"] != e["index"] for e in events
        ):
            raise ArithmeticError("controlled snapshot event identity changed")
        if any(e["index"] not in assigned for e in events):
            raise ArithmeticError("controlled cell in wrong worker")
        for phase in ("trained", "prefix") if require_prefix else ("trained",):
            if sorted(e["index"] for e in events if e["phase"] == phase) != assigned:
                raise ArithmeticError("controlled cell endpoint/prefix grid incomplete")
        done = [e for e in worker["messages"] if e["kind"] == "done"]
        if len(done) != 1 or done[0]["summary"]["cells"] != len(assigned):
            raise ArithmeticError("controlled worker completion missing")
        n = sum(e["phase"] == "snapshot" for e in events)
        summary = done[0]["summary"]
        if (
            summary["snapshots"] != n
            or summary["own_replayed"] != n
            or summary["maximum_error_chips"] > 1e-9
        ):
            raise ArithmeticError("own checkpoint replay incomplete")
    expected = sorted((axis, t) for axis, targets in labels.items() for t in targets)
    for index, cell in enumerate(cells):
        peers = [r for r in rows if r["index"] == index]
        found = [tuple(label) for r in peers for label in r["labels"]]
        if sorted(found) != expected or any(not same(r["case"], cell) for r in peers):
            raise ArithmeticError("controlled logical label/cell inventory changed")
        trained = [
            e
            for w in batch["workers"]
            for e in w["messages"]
            if e["kind"] == "cell" and e["phase"] == "trained" and e["index"] == index
        ][0]
        if (
            trained["snapshots"] != len(peers)
            or trained["iteration"] != peers[-1]["iteration"]
            or trained["work"] != peers[-1]["total_work"]
        ):
            raise ArithmeticError("controlled final endpoint changed")
        previous_iteration, previous_work = -1, -1
        for row in peers:
            if (
                row["iteration"] <= previous_iteration
                or row["total_work"] <= previous_work
            ):
                raise ArithmeticError("nonmonotone controlled snapshots")
            previous_iteration, previous_work = row["iteration"], row["total_work"]
            if row["total_work"] - row["previous_work"] != row["last_iteration_visits"]:
                raise ArithmeticError("controlled last iteration work changed")
            for axis, target in row["labels"]:
                if axis == "iteration":
                    valid = row["iteration"] == target
                else:
                    valid = (
                        row["previous_work"] < target <= row["total_work"]
                        and row["overshoots"].get(str(target))
                        == row["total_work"] - target
                    )
                if not valid:
                    raise ArithmeticError("false controlled checkpoint crossing")
    return rows
