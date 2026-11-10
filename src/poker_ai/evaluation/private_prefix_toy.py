"""Complete explicit toy baselines; no real source loader or reference output.

One nonuniform Kuhn game stands in for four logical game/encoding labels.
Every old IID B1/B4/B16 path/readout/work label is retained:648 baseline
profiles and1728 final fixed conditions. These are software fixture outputs,
not independent poker games or additional new-candidate trajectories.
"""

from pathlib import Path
from typing import Any

from numpy.random import PCG64, Generator

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.averaging_history_software import toy_context
from poker_ai.evaluation.frozen_batch_inputs import case
from poker_ai.evaluation.private_prefix_design import READOUTS, TOY, Design
from poker_ai.evaluation.private_prefix_opponents import ToyOpponents
from poker_ai.evaluation.reduced_study_training import save
from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.controlled_training import Rules, Weight
from poker_ai.postflop.frozen_batches import BatchPoint, observe
from poker_ai.postflop.learning_artifacts import read_archive
from poker_ai.postflop.learning_training import replay_snapshot
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline


def fixture(config: dict[str, Any]) -> tuple[Design, ScoringContext, ToyOpponents]:
    context = toy_context()
    initial = 2 * len(context.partition.player)
    design = Design.build(
        config, mode="toy", toy_labels=(initial + 17, initial + 113, initial + 701)
    )
    return design, context, ToyOpponents(context)


def baselines(
    design: Design,
    context: ScoringContext,
    opponents: ToyOpponents,
    scratch: Path,
    binding: str,
    deadline: Deadline,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if design.scope != TOY:
        raise ValueError("toy baselines cannot substitute for real published sources")
    rows, fixed = [], []
    contexts = design.paths[:24]
    for batch in (1, 4, 16):
        for index, path in enumerate(contexts):
            original_index = {1: 0, 4: 24, 16: 48}[batch] + index
            solver = ReducedDispatchBatchTrainer(
                context.partition,
                Generator(PCG64(path["seed"])),
                batch_size=batch,
                rules=Rules(path["regret_rule"], "linear", "linear"),
            )
            solver.initialize_exact()

            def capture(
                point: BatchPoint,
                index: int = index,
                batch: int = batch,
                path: dict[str, Any] = path,
                original_index: int = original_index,
                solver: ReducedDispatchBatchTrainer = solver,
            ) -> None:
                for label in point.labels:
                    for readout in READOUTS:
                        weight: Weight = (
                            "uniform" if readout == "uniform_average" else "linear"
                        )
                        policy = (
                            solver.current_policy
                            if readout == "current"
                            else context.partition.normalize(solver.ledger(weight))
                        )
                        metadata = dict(
                            id=f"EXPLICIT-TOY-IID-{original_index:03d}-{label}-{readout}",
                            path_index=index,
                            original_path_index=original_index,
                            scope=TOY,
                            case=case(dict(path, batch_size=batch), weight),
                            batch_size=batch,
                            readout=readout,
                            variant=readout,
                            work_label=label,
                            iteration=point.iteration,
                            previous_work=point.previous_work,
                            total_work=point.total_work,
                            last_iteration_visits=point.last_iteration_visits,
                            initialization_visits=solver.initialization_visits,
                            sampled_traversals=solver.sampled_traversals,
                            guard_sha256=point.guard_sha256,
                            current_sha256=array_sha(solver.current_policy),
                            source_sha256=binding,
                            origin="EXPLICIT_TOY_UNCHANGED_IID_BASELINE",
                        )
                        row = save(
                            context, policy, metadata, scratch, lambda _: None, deadline
                        )
                        rows.append(row)
                        if label == design.labels[-1]:
                            fixed.extend(opponents.matches(row, policy, binding))

            observe(solver, design.labels, capture, deadline)
    if len(rows) != 648 or len(fixed) != 1728:
        raise ArithmeticError("complete toy baseline output required")
    rows.sort(key=lambda r: r["id"])
    fixed.sort(
        key=lambda r: (r["own_snapshot_id"], r["opponent_profile_id"], r["target"])
    )
    return rows, fixed


def maps(
    design: Design, rows: list[dict[str, Any]], fixed: list[dict[str, Any]]
) -> tuple[dict[Any, Any], dict[Any, Any]]:
    """Independent case/coordinate joins: no best-value policy selection."""
    by_coordinate = {}
    fixed_by_id = {}
    for row in rows:
        key = (row["original_path_index"], row["work_label"], row["readout"])
        if key in by_coordinate:
            raise ArithmeticError("duplicate toy baseline coordinate")
        by_coordinate[key] = row
    for row in fixed:
        key = (row["own_snapshot_id"], row["opponent_profile_id"], row["target"])
        if key in fixed_by_id:
            raise ArithmeticError("duplicate toy fixed baseline coordinate")
        fixed_by_id[key] = row
    if len(by_coordinate) != 648 or len(fixed_by_id) != 1728:
        raise ArithmeticError("complete toy baseline archive required")
    selves, targets = {}, {}
    for i in range(48):
        for label in design.labels:
            for readout in READOUTS:
                for kind, source_index in (("B1", i % 24), ("IID", i + 24)):
                    baseline = by_coordinate[source_index, label, readout]
                    selves[kind, i, label, readout] = baseline
                    if label != design.labels[-1]:
                        continue
                    candidate_id = design.profile(i, label, readout)["id"]
                    for (identifier, opponent, target), row in fixed_by_id.items():
                        if identifier == baseline["id"]:
                            targets[kind, candidate_id, opponent, target] = row
    return selves, targets


def replay_baselines(
    path: Path,
    saved: dict[str, Any],
    design: Design,
    context: ScoringContext,
    opponents: ToyOpponents,
    deadline: Deadline,
) -> dict[str, Any]:
    """Read all648 toy baseline exports; no baseline learner is reconstructed."""
    if design.scope != TOY:
        raise ValueError("explicit toy baseline replay only")
    expected = {(i, t, r) for i in range(72) for t in design.labels for r in READOUTS}
    observed = set()
    expected_fixed = {
        (r["own_snapshot_id"], r["opponent_profile_id"], r["target"]): r
        for r in saved["baseline_fixed"]
    }
    if len(expected_fixed) != 1728 or len(saved["baseline_fixed"]) != 1728:
        raise ArithmeticError("complete toy fixed baseline inventory required")
    observed_fixed = set()
    maximum = 0.0
    for row, blob in read_archive(
        path.with_name(saved["baseline_file"]),
        saved["baseline_sha256"],
        saved["baseline_rows"],
    ):
        deadline.check()
        i, t, readout = row["original_path_index"], row["work_label"], row["readout"]
        key = (i, t, readout)
        if (
            key not in expected
            or key in observed
            or row["source_sha256"] != saved["source_sha256"]
        ):
            raise ArithmeticError("toy baseline identity/source duplicate/extra")
        observed.add(key)
        batch = (1, 4, 16)[i // 24]
        weight = "uniform" if readout == "uniform_average" else "linear"
        expected_case = case(design.paths[i % 24], weight)  # type: ignore[arg-type]
        if (
            row["id"] != f"EXPLICIT-TOY-IID-{i:03d}-{t}-{readout}"
            or not same(row["case"], expected_case)
            or not same(row["batch_size"], batch)
            or not same(row["path_index"], i % 24)
            or row["scope"] != TOY
            or row["origin"] != "EXPLICIT_TOY_UNCHANGED_IID_BASELINE"
        ):
            raise ArithmeticError("toy baseline case/readout/origin changed")
        maximum = max(maximum, replay_snapshot(context, row, blob, 1e-9))
        if t != design.labels[-1]:
            continue
        from poker_ai.postflop.controlled_checkpoints import unpack_policy
        from poker_ai.postflop.learning_artifacts import decode

        policy = unpack_policy(context.partition, decode(blob, context, row)["policy"])
        for fixed in opponents.matches(row, policy, saved["source_sha256"]):
            fkey = (
                fixed["own_snapshot_id"],
                fixed["opponent_profile_id"],
                fixed["target"],
            )
            if fkey not in expected_fixed or fkey in observed_fixed:
                raise ArithmeticError("toy baseline fixed target changed")
            observed_fixed.add(fkey)
            maximum = max(maximum, compare(fixed, expected_fixed[fkey]))
    if observed != expected or observed_fixed != set(expected_fixed) or maximum > 1e-9:
        raise ArithmeticError("toy baseline archive replay incomplete")
    return dict(
        profiles=648,
        fixed_targets=1728,
        maximum_error_chips=maximum,
        learner_constructed=False,
        reference_constructed=False,
    )
