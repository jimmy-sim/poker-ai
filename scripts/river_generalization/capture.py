"""Durable own B4 snapshots and data-only replay for the river-generalization panel."""

import json
import os
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_artifacts import decode_mass, write_mass
from poker_ai.evaluation.averaging_history_math import coverage, window_mass
from poker_ai.finite import FloatArray
from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
from poker_ai.postflop.controlled_checkpoints import read_snapshot, write_snapshot
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.controlled_training import Weight
from poker_ai.postflop.frozen_batches import BatchPoint
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.matrix import MatrixTree, recall_violations
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline
from river_generalization.learning import (
    READOUTS,
    PathSpec,
    train,
)


def _write(path: Path, row: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    if path.exists() or temporary.exists():
        raise FileExistsError("retain existing own record")
    temporary.write_text(json.dumps(row, sort_keys=True, indent=2) + "\n")
    temporary.replace(path)


def _event(path: Path, row: dict[str, Any]) -> None:
    with path.open("a") as stream:
        stream.write(json.dumps(row, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def capture_path(
    scoring: ScoringContext,
    path: PathSpec,
    folder: Path,
    binding: str,
    labels: tuple[int, ...],
    deadline: Deadline,
) -> dict[str, Any]:
    """Refuse existing output, retain each complete artifact and failure event."""
    if (
        len(binding) != 64
        or any(c not in "0123456789abcdef" for c in binding)
        or not labels
        or labels != tuple(sorted(set(labels)))
    ):
        raise ValueError("source binding or labels invalid")
    folder.mkdir(parents=True, exist_ok=False)
    events = folder / "events.jsonl"
    identity = dict(index=path.index, game=path.game, seed=path.seed, arm=path.arm)
    _event(events, dict(kind="started", path=identity, binding=binding, labels=labels))
    result: list[dict[str, Any]] = []
    warm: dict[str, Any] | None = None
    tree = scoring.partition
    first = np.unique(scoring.exact_to_partition, return_index=True)[1]
    river = (scoring.river_masks[0] | scoring.river_masks[1])[first]
    try:
        violations = recall_violations(tree) if isinstance(tree, MatrixTree) else 0
        if violations:
            raise ArithmeticError("river path violates abstract recall")

        def at(
            point: BatchPoint,
            solver: ReducedDispatchBatchTrainer,
            policies: dict[str, FloatArray],
        ) -> None:
            nonlocal warm
            if warm is None:
                warm_meta = dict(path_index=path.index, binding=binding, origin="warm")
                receipt = write_mass(
                    folder / "warm-mass.json.gz", tree, solver.warm_sum, warm_meta
                )
                warm = dict(metadata=warm_meta, receipt=receipt)
                _event(events, dict(kind="warm", **warm))
            for label in point.labels:
                common = dict(
                    path_index=path.index,
                    game=path.game,
                    seed=path.seed,
                    arm=path.arm,
                    binding=binding,
                    work_label=label,
                    iteration=point.iteration,
                    total_work=point.total_work,
                    previous_work=point.previous_work,
                    overshoot=point.total_work - label,
                    guard_sha256=point.guard_sha256,
                )
                for weight in ("uniform", "linear"):
                    mass = solver.ledger(weight)
                    metadata = dict(**common, readout=weight)
                    name = f"{label}-{weight}-mass.json.gz"
                    receipt = write_mass(folder / name, tree, mass, metadata)
                    _event(
                        events,
                        dict(
                            kind="mass", file=name, metadata=metadata, receipt=receipt
                        ),
                    )
                for name in READOUTS:
                    deadline.check()
                    policy = policies[name]
                    metadata = dict(**common, readout=name)
                    filename = f"{label}-{name}.json.gz"
                    receipt = write_snapshot(folder / filename, tree, policy, metadata)
                    score = score_data(scoring, scoring.score(policy))
                    support = None
                    if name != "current":
                        average_weight: Weight = (
                            "uniform" if name == "uniform_average" else "linear"
                        )
                        mass = solver.ledger(average_weight)
                        support = dict(
                            whole=coverage(tree, mass, river),
                            post_warm=coverage(
                                tree, window_mass(tree, solver.warm_sum, mass), river
                            ),
                        )
                    row = dict(
                        file=filename,
                        metadata=metadata,
                        receipt=receipt,
                        score=score,
                        support=support,
                        information_rows=len(tree.keys),
                        tree_nodes=len(tree.player),
                        padded_width=tree.legal.shape[1],
                    )
                    _event(events, dict(kind="capture", row=row))
                    result.append(row)

        solver = train(tree, path.seed, labels, deadline, at)
        if len(result) != len(labels) * len(READOUTS):
            raise ArithmeticError("incomplete fixed path readouts")
        if warm is None:
            raise ArithmeticError("missing exact initialization mass")
        summary = dict(
            status="completed",
            path=dict(index=path.index, game=path.game, seed=path.seed, arm=path.arm),
            binding=binding,
            labels=list(labels),
            final_work=solver.nodes_visited,
            final_iteration=solver.iteration,
            recall_violations=0,
            warm=warm,
            captures=result,
        )
        _write(folder / "summary.json", summary)
        _event(events, dict(kind="completed", summary_sha256=sha(summary)))
        return summary
    except BaseException as error:
        _event(
            events,
            dict(kind="failed_retained", type=type(error).__name__, reason=str(error)),
        )
        raise


def replay_path(scoring: ScoringContext, folder: Path) -> dict[str, Any]:
    """Recompute every own scalar and coverage from immutable snapshot bytes."""
    summary: dict[str, Any] = json.loads((folder / "summary.json").read_bytes())
    if summary["status"] != "completed":
        raise ArithmeticError("incomplete path cannot enter complete report")
    tree = scoring.partition
    violations = recall_violations(tree) if isinstance(tree, MatrixTree) else 0
    if summary.get("recall_violations") != 0 or violations:
        raise ArithmeticError("river path abstract recall changed")
    rows = summary["captures"]
    if len(rows) != len(summary["labels"]) * len(READOUTS):
        raise ArithmeticError("missing fixed readout")
    events = [
        json.loads(line) for line in (folder / "events.jsonl").read_text().splitlines()
    ]
    if (
        not events
        or events[0]["kind"] != "started"
        or events[-1] != dict(kind="completed", summary_sha256=sha(summary))
        or sum(event["kind"] == "capture" for event in events) != len(rows)
        or sum(event["kind"] == "mass" for event in events)
        != len(summary["labels"]) * 2
        or sum(event["kind"] == "warm" for event in events) != 1
    ):
        raise ArithmeticError("own path event inventory changed")
    warm_row = summary["warm"]
    warm_meta = warm_row["metadata"]
    warm = decode_mass(
        (folder / "warm-mass.json.gz").read_bytes(),
        tree,
        dict(
            **warm_meta,
            receipt=warm_row["receipt"],
            metadata_sha256=sha(warm_meta),
        ),
    )
    first = np.unique(scoring.exact_to_partition, return_index=True)[1]
    river = (scoring.river_masks[0] | scoring.river_masks[1])[first]
    for row in rows:
        meta = row["metadata"]
        policy = read_snapshot(folder / row["file"], tree, row["receipt"], meta)
        actual = score_data(scoring, scoring.score(policy))
        if compare(actual, row["score"]) > 1e-9:
            raise ArithmeticError("own river-generalization score changed on replay")
        name = meta["readout"]
        if name == "current":
            if row["support"] is not None:
                raise ArithmeticError("current policy has no average mass")
            continue
        weight = name.removesuffix("_average")
        mass_file = folder / f"{meta['work_label']}-{weight}-mass.json.gz"
        matches = [
            event["receipt"]
            for event in events
            if event["kind"] == "mass" and event["file"] == mass_file.name
        ]
        if len(matches) != 1:
            raise ArithmeticError("missing or duplicate cumulative mass")
        mass_meta = dict(meta, readout=weight)
        mass = decode_mass(
            mass_file.read_bytes(),
            tree,
            dict(**mass_meta, receipt=matches[0], metadata_sha256=sha(mass_meta)),
        )
        whole = coverage(tree, mass, river)
        post = coverage(tree, window_mass(tree, warm, mass), river)
        if not same(whole, row["support"]["whole"]) or not same(
            post, row["support"]["post_warm"]
        ):
            raise ArithmeticError("average coverage changed on replay")
    return summary
