"""Capture one isolated regret-recency path in the parent snapshot format."""

import json
import os
from pathlib import Path
from typing import Any

import numpy as np
from medium_dry_full.learning import FullPoint
from turn_exact_transfer.learning import PathSpec

from known_turn_regret_recency.learning import train
from poker_ai.evaluation.averaging_history_artifacts import decode_mass, write_mass
from poker_ai.evaluation.averaging_history_math import coverage, window_mass
from poker_ai.finite import FloatArray
from poker_ai.postflop.controlled_checkpoints import write_snapshot
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.matrix import MatrixTree, recall_violations
from poker_ai.postflop.river_study import Deadline

READOUTS = ("current", "linear_average")


def _write(path: Path, row: dict[str, Any]) -> None:
    temporary = path.with_suffix(path.suffix + ".tmp")
    if path.exists() or temporary.exists():
        raise FileExistsError("retain existing full-pass record")
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
    """Retain each deterministic first-crossing policy and any failure event."""
    if (
        len(binding) != 64
        or any(c not in "0123456789abcdef" for c in binding)
        or not labels
        or labels != tuple(sorted(set(labels)))
    ):
        raise ValueError("source binding or labels invalid")
    index, game, arm = path.index, path.game, path.arm
    folder.mkdir(parents=True, exist_ok=False)
    events = folder / "events.jsonl"
    identity = dict(index=index, game=game, arm=arm, seed=path.seed)
    _event(events, dict(kind="started", path=identity, binding=binding, labels=labels))
    result: list[dict[str, Any]] = []
    warm: dict[str, Any] | None = None
    tree = scoring.partition
    first = np.unique(scoring.exact_to_partition, return_index=True)[1]
    river = (scoring.river_masks[0] | scoring.river_masks[1])[first]
    try:
        violations = recall_violations(tree) if isinstance(tree, MatrixTree) else 0
        if violations:
            raise ArithmeticError("full-pass representation violates recall")

        def at_warm(solver: ControlledTrainer) -> None:
            nonlocal warm
            mass = solver.strategy_sum.copy()
            meta = dict(path_index=index, binding=binding, origin="warm")
            receipt = write_mass(folder / "warm-mass.json.gz", tree, mass, meta)
            warm = dict(metadata=meta, receipt=receipt)
            _event(events, dict(kind="warm", **warm))

        def at(
            point: FullPoint,
            solver: ControlledTrainer,
            policies: dict[str, FloatArray],
        ) -> None:
            for label in point.labels:
                common = dict(
                    path_index=index,
                    game=game,
                    arm=arm,
                    seed=path.seed,
                    binding=binding,
                    work_label=label,
                    iteration=point.iteration,
                    total_work=point.total_work,
                    previous_work=point.previous_work,
                    overshoot=point.total_work - label,
                    guard_sha256=point.guard_sha256,
                    rng_state=solver.rng.bit_generator.state,
                )
                mass = solver.strategy_sum.copy()
                mass_meta = dict(**common, readout="linear")
                mass_name = f"{label}-linear-mass.json.gz"
                mass_receipt = write_mass(folder / mass_name, tree, mass, mass_meta)
                _event(
                    events,
                    dict(
                        kind="mass",
                        file=mass_name,
                        metadata=mass_meta,
                        receipt=mass_receipt,
                    ),
                )
                for name in READOUTS:
                    deadline.check()
                    policy = policies[name]
                    meta = dict(**common, readout=name)
                    filename = f"{label}-{name}.json.gz"
                    receipt = write_snapshot(folder / filename, tree, policy, meta)
                    score = score_data(scoring, scoring.score(policy))
                    support = None
                    if name == "linear_average":
                        if warm is None:
                            raise ArithmeticError("warm mass missing before capture")
                        warm_mass = decode_mass(
                            (folder / "warm-mass.json.gz").read_bytes(),
                            tree,
                            dict(
                                **warm["metadata"],
                                receipt=warm["receipt"],
                                metadata_sha256=sha(warm["metadata"]),
                            ),
                        )
                        support = dict(
                            whole=coverage(tree, mass, river),
                            post_warm=coverage(
                                tree, window_mass(tree, warm_mass, mass), river
                            ),
                        )
                    row = dict(
                        file=filename,
                        metadata=meta,
                        receipt=receipt,
                        score=score,
                        support=support,
                        information_rows=len(tree.keys),
                        tree_nodes=len(tree.player),
                        padded_width=tree.legal.shape[1],
                    )
                    _event(events, dict(kind="capture", row=row))
                    result.append(row)

        solver = train(tree, labels, deadline, at, at_warm)
        if len(result) != len(labels) * len(READOUTS) or warm is None:
            raise ArithmeticError("incomplete full-pass readouts or warm mass")
        summary = dict(
            status="completed",
            path=identity,
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
