"""Own IID-B4 captures without scoring or supplying an external strategy.

The eventual real runner must verify its published source-bound admission before
calling this low-level function. Software tests call it on explicit tiny games.
Both opponent updates and exact warm initialization count as visited-node work.
"""

import time
from pathlib import Path
from typing import Any

from numpy.random import PCG64, Generator, SeedSequence

from poker_ai.evaluation.averaging_history_artifacts import array_sha, write_mass
from poker_ai.evaluation.opponent_learning_design import READOUTS, WEIGHTS, Design
from poker_ai.finite import ArrayTree
from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_checkpoints import write_snapshot
from poker_ai.postflop.controlled_training import Rules, Weight
from poker_ai.postflop.frozen_batches import BatchPoint, observe
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.river_study import Deadline


def trainer(tree: ArrayTree, design: Design, index: int) -> ReducedDispatchBatchTrainer:
    path = design.path(index)
    entropy = path["rng_entropy"]
    # Preserve the historical scalar-seed stream for role zero. Do not replace
    # it by SeedSequence([seed,0]), which is a different scientific declaration.
    rng = Generator(PCG64(entropy if type(entropy) is int else SeedSequence(entropy)))
    return ReducedDispatchBatchTrainer(
        tree, rng, batch_size=4, rules=Rules("signed", "linear", "linear")
    )


def collect(
    tree: ArrayTree,
    design: Design,
    index: int,
    folder: Path,
    binding: str,
    send: Send,
    deadline: Deadline,
) -> dict[str, Any]:
    """Retain all readouts/books at first whole-iteration work crossings.

    Intermediate half-budget observations do not consume RNG or change any
    training array. The frozen observer guards both ledgers, RNG, keys and work
    counters around every capture. Complete and partial files are never replaced.
    """
    started, cpu = time.perf_counter(), time.process_time()
    path = design.path(index)
    labels = design.boundaries(index)
    if (
        type(binding) is not str
        or len(binding) != 64
        or any(c not in "0123456789abcdef" for c in binding)
    ):
        raise ValueError("own capture needs the exact source fingerprint")
    names = [f"warm/{index:02d}.json.gz"]
    names.extend(
        f"{directory}/{index:02d}-{label}-{readout}.json.gz"
        for directory, readouts in (("captures", READOUTS), ("masses", WEIGHTS))
        for label in labels
        for readout in readouts
    )
    for name in names:
        output = folder / name
        temporary = output.with_suffix(output.suffix + ".tmp")
        if (
            output.exists()
            or output.is_symlink()
            or temporary.exists()
            or temporary.is_symlink()
            or not output.resolve().is_relative_to(folder.resolve())
        ):
            raise FileExistsError(
                "retain existing/partial own path before initialization"
            )
    deadline.check()
    solver = trainer(tree, design, index)
    solver.initialize_exact()
    setup = time.perf_counter() - started
    context = tree_digest(tree)
    warm_metadata = dict(
        **path,
        id=f"opponent-warm-{design.scope}-{index:02d}",
        source_sha256=binding,
        tree_sha256=context,
        initialization_visits=solver.initialization_visits,
        origin="own_simultaneous_uniform_warm_mass_both_books",
    )
    filename = f"warm/{index:02d}.json.gz"
    warm_receipt = write_mass(folder / filename, tree, solver.warm_sum, warm_metadata)
    warm = dict(
        **warm_metadata,
        file=filename,
        receipt=warm_receipt,
        metadata_sha256=sha(warm_metadata),
    )
    send(dict(kind="cell", phase="warm", index=index, row=warm))
    captures, masses = [], []

    def capture(point: BatchPoint) -> None:
        current = solver.current_policy
        common = dict(
            source_sha256=binding,
            tree_sha256=context,
            iteration=point.iteration,
            previous_work=point.previous_work,
            total_work=point.total_work,
            last_iteration_visits=point.last_iteration_visits,
            initialization_visits=solver.initialization_visits,
            sampled_traversals=solver.sampled_traversals,
            guard_sha256=point.guard_sha256,
            current_sha256=array_sha(current),
            warm_mass_sha256=warm_receipt["mass_sha256"],
        )
        policies = {"current": current}
        for label in point.labels:
            per_label = dict(common, overshoot=point.total_work - label)
            for weight in WEIGHTS:
                deadline.check()
                mass = solver.ledger(weight)  # type: ignore[arg-type]
                metadata = dict(
                    **design.mass(index, label, weight),
                    **per_label,
                    state_sha256=solver.readout_fingerprint(weight),  # type: ignore[arg-type]
                )
                filename = f"masses/{index:02d}-{label}-{weight}.json.gz"
                receipt = write_mass(folder / filename, tree, mass, metadata)
                row = dict(
                    **metadata,
                    file=filename,
                    receipt=receipt,
                    metadata_sha256=sha(metadata),
                )
                masses.append(row)
                send(dict(kind="cell", phase="mass", index=index, row=row))
                policies[weight + "_average"] = tree.normalize(mass)
            for readout in READOUTS:
                deadline.check()
                readout_weight: Weight = (
                    "uniform" if readout == "uniform_average" else "linear"
                )
                metadata = dict(
                    **design.raw(index, label, readout),
                    **per_label,
                    state_sha256=solver.readout_fingerprint(readout_weight),
                )
                filename = f"captures/{index:02d}-{label}-{readout}.json.gz"
                receipt = write_snapshot(
                    folder / filename, tree, policies[readout], metadata
                )
                row = dict(
                    **metadata,
                    file=filename,
                    receipt=receipt,
                    metadata_sha256=sha(metadata),
                )
                captures.append(row)
                send(dict(kind="cell", phase="capture", index=index, row=row))

    observe(solver, labels, capture, deadline)
    if len(captures) != 3 * len(labels) or len(masses) != 2 * len(labels):
        raise ArithmeticError("all fixed path readouts and both books required")
    if tree_digest(tree) != context:
        raise ArithmeticError("own training game mutated during capture")
    deadline.check()
    return dict(
        path=path,
        captures=captures,
        masses=masses,
        warm=warm,
        final_total_work=solver.nodes_visited,
        final_iteration=solver.iteration,
        initialization_seconds=setup,
        seconds=time.perf_counter() - started,
        cpu_seconds=time.process_time() - cpu,
    )
