"""Reproduce complete saved-profile traces and common-opponent diagnostics."""

import argparse
import csv
import gzip
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any, cast
from unittest.mock import patch

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.opponent_decision_inputs import (
    CONFIG,
    CONFIG_SHA,
    ENTRIES,
    FOLDER,
    checked,
    contract,
    profiles,
)
from poker_ai.evaluation.opponent_decision_math import cross_policies, verify_trace
from poker_ai.evaluation.opponent_learning_clock import atomic
from poker_ai.evaluation.opponent_learning_score import scoring
from poker_ai.postflop.learning_artifacts import canonical, sha
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.reply_diagnosis import analyse
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

BLOCKED = (
    "poker_ai.postflop.batch_reduction.ReducedDispatchBatchTrainer.__init__",
    "poker_ai.postflop.frozen_batches.FrozenBatchTrainer.__init__",
    "poker_ai.postflop.controlled_training.ControlledTrainer.__init__",
    "poker_ai.postflop.stratified_batches.StratifiedBatchTrainer.__init__",
    "poker_ai.solver_validation.reference.Reference.__init__",
    "poker_ai.solver_validation.matched_array_reference.ScalarReference.__init__",
)


def forbidden(*args: Any, **kwargs: Any) -> None:
    raise AssertionError("read-only diagnosis constructed a learner/reference")


def run(root: Path, output: Path, started: float) -> dict[str, Any]:
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain existing complete/partial diagnostic output")
    config = contract(root)
    deadline = Deadline(config["maximum_seconds"])
    deadline.started = started
    provenance = source_provenance(root, root / CONFIG, entrypoints=ENTRIES)
    if provenance["dirty"] is not False:
        raise ValueError("publish clean diagnostic source before full reproduction")
    output.mkdir(parents=True)
    summaries: list[dict[str, Any]] = []
    crosses: list[dict[str, Any]] = []
    maximum = 0.0
    try:
        with ExitStack() as stack:
            for name in BLOCKED:
                stack.enter_context(patch(name, forbidden))
            print(
                "Replaying bound source evidence; "
                "learner/reference constructors blocked...",
                flush=True,
            )
            own = checked(root, config, deadline)
            selected = profiles(root, config, own, deadline)
            before = {
                p.coordinate: (
                    tree_digest(p.contexts.fine),
                    tree_digest(p.contexts.coarse),
                )
                for p in selected
            }
            details = output / "details"
            details.mkdir()
            for profile in selected:
                deadline.check()
                context = scoring(profile.contexts, profile.row)
                exact = cast(MatrixTree, context.exact)
                limited = cast(MatrixTree, context.partition)
                policy_hash = array_sha(profile.fine_policy)
                summary, detail = analyse(
                    exact,
                    limited,
                    profile.fine_policy,
                    top=config["top_groups"],
                    examples=config["examples_per_group"],
                    tolerance=config["absolute_tolerance_chips"],
                )
                streets = []
                for info in range(len(exact.keys)):
                    state = exact.source.states[exact.source.representatives[info]]
                    assert state.dealer is not None
                    streets.append(state.dealer.street.name)
                error = verify_trace(
                    summary,
                    detail,
                    profile.row,
                    [int(x) for x in exact.owners],
                    [len(x) for x in exact.actions],
                    [int(x) for x in context.exact_to_partition],
                    streets,
                    config["absolute_tolerance_chips"],
                )
                maximum = max(maximum, error)
                if (
                    array_sha(profile.fine_policy) != policy_hash
                    or array_sha(profile.policy)
                    != profile.row["receipt"]["policy_sha256"]
                ):
                    raise ArithmeticError("trace mutated a saved policy")
                identity = profile.identity()
                filename = f"details/{profile.coordinate:02d}-{profile.arm}.json.gz"
                with (output / filename).open("xb") as raw:
                    with gzip.GzipFile(
                        fileobj=raw, mode="wb", filename="", mtime=0
                    ) as compressed:
                        compressed.write(canonical(dict(**identity, **detail)))
                summaries.append(
                    dict(
                        **identity,
                        **summary,
                        details_file=filename,
                        maximum_accounting_error_chips=error,
                    )
                )
                atomic(
                    output / "partial.json",
                    dict(
                        status="partial",
                        profiles=summaries,
                        training_performed=False,
                        reference_constructed=False,
                    ),
                )
                print(
                    f"traced {profile.game}/{profile.seed}/{profile.arm} "
                    f"({len(summaries)}/24)",
                    flush=True,
                )
            for coordinate in range(6):
                deadline.check()
                group = [p for p in selected if p.coordinate == coordinate]
                crosses.extend(
                    cross_policies(
                        group[0].contexts.fine,
                        {p.arm: p.fine_policy for p in group},
                        {p.arm: p.row for p in group},
                        dict(
                            coordinate=coordinate,
                            game=group[0].game,
                            seed=group[0].seed,
                        ),
                        config["absolute_tolerance_chips"],
                    )
                )
                atomic(
                    output / "partial-cross.json",
                    dict(
                        status="partial",
                        conditions=crosses,
                        independent_new_cross_audit=False,
                    ),
                )
                print(
                    f"crossed coordinate {coordinate} ({len(crosses)}/192)", flush=True
                )
            if before != {
                p.coordinate: (
                    tree_digest(p.contexts.fine),
                    tree_digest(p.contexts.coarse),
                )
                for p in selected
            }:
                raise ArithmeticError("diagnosis mutated a source game")
        if (
            len(summaries) != 24
            or sum(len(p["responses"]) for p in summaries) != 48
            or len(crosses) != 192
        ):
            raise ArithmeticError("complete24/48/192 diagnostic inventory required")
        atomic(output / "summary.json", dict(profiles=summaries))
        atomic(
            output / "cross.json",
            dict(conditions=crosses, independent_new_cross_audit=False),
        )
        with (output / "cross.csv").open("x", newline="") as stream:
            writer = csv.DictWriter(stream, sorted(crosses[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(crosses)
        deadline.check()
        if any(
            digest(root / config[n]) != config[n + "_sha256"]
            for n in ("own", "native", "learning_config")
        ):
            raise ArithmeticError("bound source input changed during diagnosis")
        if (
            source_provenance(root, root / CONFIG, entrypoints=ENTRIES)["sha256"]
            != provenance["sha256"]
        ):
            raise ArithmeticError("diagnostic source changed during reproduction")
        manifest = dict(
            status="complete_own_opponent_decisions",
            config_sha256=CONFIG_SHA,
            source=provenance,
            source_sha256=sha(provenance["sha256"]),
            own_sha256=config["own_sha256"],
            native_sha256=config["native_sha256"],
            model_source_sha256=config["historical_source_sha256"],
            profiles=24,
            responses=48,
            cross_conditions=192,
            maximum_trace_accounting_error_chips=maximum,
            cross_accounting_verified=True,
            maximum_seconds=config["maximum_seconds"],
            clock_scope=(
                "Thin-script entry before numerical imports, through all source "
                "checks/math/writes; interpreter startup is not measured."
            ),
            constructors_blocked=True,
            training_performed=False,
            reference_constructed=False,
            independent_new_cross_audit=False,
            new_agent_default=False,
            fresh_global_admission=False,
            environment=runtime_environment(),
            seconds=time.perf_counter() - started,
            limits=(
                "Known saved profiles; fixed-profile row loss is not retraining EV. "
                "Off-diagonal cross values are own calculations; only original "
                "diagonal roots inherit the prior independent scalar comparison."
            ),
            outputs={
                str(p.relative_to(output)): digest(p)
                for p in sorted(output.rglob("*"))
                if p.is_file()
            },
        )
        atomic(output / "manifest.json", manifest)
        deadline.check()
        return manifest
    except BaseException as exc:
        atomic(
            output / "failure.json",
            dict(
                status="failed_retained",
                failure=dict(type=type(exc).__name__, message=str(exc)),
                completed_profiles=len(summaries),
                cross_conditions=len(crosses),
                seconds=time.perf_counter() - started,
                training_performed=False,
                reference_constructed=False,
                new_agent_default=False,
                fresh_global_admission=False,
            ),
        )
        raise


def main(root: Path, started: float) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(FOLDER))
    args = parser.parse_args()
    result = run(root, root / args.output, started)
    print(
        f"{result['status']}: 24 profiles / 48 seat traces / "
        "192 common-opponent conditions"
    )
    return 0
