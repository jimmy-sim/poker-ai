"""Fixed B4 captures; real callers must authenticate admission before entry."""

import copy
import json
import os
import time
from pathlib import Path
from typing import Any

from numpy.random import PCG64, Generator

from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
from poker_ai.postflop.compact_full_artifacts import write_snapshot
from poker_ai.postflop.compact_full_context import Context
from poker_ai.postflop.compact_sampled_state import FORMAT, READOUTS, WARM, table
from poker_ai.postflop.controlled_training import Rules
from poker_ai.postflop.frozen_batches import BatchPoint, guard, observe
from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.postflop.river_study import Deadline


class Journal:
    """One append-only file per worker; incomplete final bytes remain evidence."""

    def __init__(
        self, path: Path, source_fingerprint: str, scope: str, slot: int
    ) -> None:
        self.path, self.source, self.scope, self.slot = (
            path,
            source_fingerprint,
            scope,
            slot,
        )
        self.sequence = 0
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb"):
            pass

    def add(self, kind: str, **fields: Any) -> dict[str, Any]:
        event = dict(
            sequence=self.sequence,
            source_fingerprint=self.source,
            scope=self.scope,
            slot=self.slot,
            kind=kind,
            **fields,
        )
        with self.path.open("ab") as stream:
            stream.write(canonical(event) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        self.sequence += 1
        return event


def payload(
    context: Context,
    case: dict[str, Any],
    index: int,
    scope: str,
    fingerprint: str,
    solver: ReducedDispatchBatchTrainer,
    point: BatchPoint | None,
    warm_receipt: dict[str, Any] | None,
) -> dict[str, Any]:
    tree = context.scoring.partition
    if scope not in ("software", "real") or len(fingerprint) != 64:
        raise ValueError("cost scope cannot capture a training state")
    result = dict(
        format=WARM if point is None else FORMAT,
        scope=scope,
        source_fingerprint=fingerprint,
        seed=case["seed"],
        path_index=index,
        binding=context.binding,
        iteration=solver.iteration,
        total_node_work=solver.nodes_visited,
        initialization_work=solver.initialization_visits,
        row_evaluations=solver.row_evaluations,
        sampled_traversals=solver.sampled_traversals,
        last_pass_rows=list(solver.last_pass_rows),
        sampled_rows=[int(k in solver.sampled_keys) for k in tree.keys],
        rng_state=copy.deepcopy(solver.rng.bit_generator.state),
        guard_sha256=guard(solver),
        actions=[list(menu) for menu in tree.actions],
        regrets=table(tree, solver.regrets, signed=True),
        uniform_sum=table(tree, solver.uniform_sum, signed=False),
        linear_sum=table(tree, solver.strategy_sum, signed=False),
        policies={
            name: table(tree, values, signed=False)
            for name, values in (
                ("current", solver.current_policy),
                ("uniform", tree.normalize(solver.uniform_sum)),
                ("linear", solver.average_policy),
            )
        },
    )
    if point is None:
        result["warm_sum"] = table(tree, solver.warm_sum, signed=False)
    else:
        if warm_receipt is None or result["guard_sha256"] != point.guard_sha256:
            raise ArithmeticError("observer guard/warm binding changed before capture")
        if len(point.labels) != 1:
            raise ArithmeticError(
                "fixed study labels require distinct whole-iteration crossings"
            )
        result.update(
            previous_node_work=point.previous_work,
            last_iteration_work=point.last_iteration_visits,
            work_checkpoint=point.labels[0],
            warm_receipt=warm_receipt,
        )
    if set(result["policies"]) != set(READOUTS):
        raise ArithmeticError("three readouts required")
    return result


def collect(
    context: Context,
    case: dict[str, Any],
    index: int,
    scope: str,
    labels: list[int],
    folder: Path,
    fingerprint: str,
    journal: Journal,
    deadline: Deadline,
) -> dict[str, Any]:
    """Fresh PCG64(seed), simultaneous warm, unchanged frozen-policy B4 updates."""
    if scope not in ("software", "real"):
        raise ValueError("no learner may be constructed in COST scope")
    if (case["spot_file"], case["representation"]) != (
        context.spot_file,
        context.representation,
    ):
        raise ArithmeticError("case/context mismatch")
    warm_file = folder / "warms" / f"{index:02d}.json.gz"
    state_files = [folder / "states" / f"{index:02d}-{w}.json.gz" for w in labels]
    for path in (warm_file, *state_files):
        if path.exists() or path.with_suffix(path.suffix + ".tmp").exists():
            raise FileExistsError("retain complete/partial sampled path")
    started, cpu = time.perf_counter(), time.process_time()
    deadline.check()
    journal.add("path_started", index=index, case=case)
    solver = ReducedDispatchBatchTrainer(
        context.scoring.partition,
        Generator(PCG64(case["seed"])),
        batch_size=4,
        rules=Rules("signed", "linear", "linear"),
    )
    solver.initialize_exact()
    if solver.nodes_visited >= labels[0]:
        raise ArithmeticError("warm work must fit below first fixed checkpoint")
    warm = payload(context, case, index, scope, fingerprint, solver, None, None)
    receipt = write_snapshot(warm_file, warm)
    journal.add(
        "warm",
        index=index,
        case=case,
        binding=context.binding,
        receipt=receipt,
        confirmed_work=solver.nodes_visited,
    )
    warm_fingerprint = json.dumps(receipt, sort_keys=True)
    count = 0

    def capture(point: BatchPoint) -> None:
        nonlocal count
        deadline.check()
        raw = payload(context, case, index, scope, fingerprint, solver, point, receipt)
        path = folder / "states" / f"{index:02d}-{point.labels[0]}.json.gz"
        state_receipt = write_snapshot(path, raw)
        journal.add(
            "checkpoint",
            index=index,
            case=case,
            binding=context.binding,
            work_checkpoint=point.labels[0],
            iteration=point.iteration,
            receipt=state_receipt,
            confirmed_work=point.total_work,
            guard_sha256=point.guard_sha256,
        )
        if json.dumps(receipt, sort_keys=True) != warm_fingerprint:
            raise ArithmeticError("observer mutated its warm receipt")
        count += 1
        deadline.check()

    observe(solver, labels, capture, deadline)
    if count != len(labels):
        raise ArithmeticError("fixed checkpoint inventory incomplete")
    result = dict(
        index=index,
        case=case,
        checkpoints=count,
        readouts=3 * count,
        iteration=solver.iteration,
        confirmed_work=solver.nodes_visited,
        sampled_traversals=solver.sampled_traversals,
        seconds=time.perf_counter() - started,
        cpu_seconds=time.process_time() - cpu,
    )
    journal.add("path_done", **result)
    deadline.check()
    return result
