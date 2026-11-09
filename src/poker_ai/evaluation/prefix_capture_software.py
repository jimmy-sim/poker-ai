"""Source-bound OWN tiny prefix archives; never a poker experiment/admission."""

import json
import math
import time
from pathlib import Path
from typing import Any

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.evaluation.averaging_history_artifacts import (
    array_sha,
    decode_mass,
    write_mass,
)
from poker_ai.evaluation.averaging_history_software import toy_context
from poker_ai.evaluation.tiny_policy_math import metrics as independent_metrics
from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
from poker_ai.postflop.controlled_checkpoints import unpack_policy, write_snapshot
from poker_ai.postflop.controlled_training import Rules, Weight
from poker_ai.postflop.coordinate_observer import CoordinatePoint, observe
from poker_ai.postflop.frozen_batches import guard
from poker_ai.postflop.learning_artifacts import (
    decode,
    read_archive,
    sha,
    write_archive,
)
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/matched-prefix-capture.json"
CONFIG_SHA = "a8773012cb9470bf7b5411a965503f7a88d95124c3be0ece4c066bf52c7d3035"
SCOPE = "EXPLICIT_SOFTWARE_FIXTURE_ONLY_NOT_POKER_RESULTS"
ENTRIES = ("scripts/check_prefix_capture.py",)


def config_inputs(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prefix capture software config changed")
    saved: dict[str, Any] = json.loads((root / CONFIG).read_text())
    if digest(root / saved["parent_config"]) != saved["parent_config_sha256"]:
        raise ArithmeticError("parent prospective protocol changed")
    return saved


def learner(index: int) -> ReducedDispatchBatchTrainer:
    solver = ReducedDispatchBatchTrainer(
        toy_context().partition,
        Generator(PCG64(20261301 + index % 3)),
        batch_size=1,
        rules=Rules(
            "signed" if (index // 3) % 2 == 0 else "clipped", "linear", "linear"
        ),
    )
    solver.initialize_exact()
    return solver


def collect(
    index: int,
    scratch: Path,
    binding: str,
    profiles: list[dict[str, Any]],
    masses: list[dict[str, Any]],
    checks: list[dict[str, Any]],
    deadline: Deadline,
) -> None:
    context = toy_context()
    direct = learner(index)
    trace: dict[int, dict[str, Any]] = {
        1: dict(work=direct.nodes_visited, guard=guard(direct))
    }
    for _ in range(15):
        deadline.check()
        direct.step()
        trace[direct.iteration] = dict(work=direct.nodes_visited, guard=guard(direct))
    work = [trace[i]["work"] - 1 for i in (2, 7, 16)]
    solver = learner(index)

    def capture(point: CoordinatePoint) -> None:
        if point.guard_sha256 != trace[point.iteration]["guard"]:
            raise ArithmeticError(
                "observed tiny trajectory differs from uninterrupted path"
            )
        checks.append(
            dict(
                fixture_case=index,
                iteration=point.iteration,
                total_work=point.total_work,
                state_sha256=point.guard_sha256,
                work_labels=list(point.work_labels),
            )
        )
        if point.iteration not in (4, 8):
            return
        base: dict[str, Any] = dict(
            scope=SCOPE,
            fixture_case=index,
            iteration=point.iteration,
            total_work=point.total_work,
            source_sha256=binding,
            guard_sha256=point.guard_sha256,
        )
        policies = {"current": solver.current_policy}
        for weight in ("uniform", "linear"):
            typed_weight: Weight = weight
            mass = solver.ledger(typed_weight)
            meta: dict[str, Any] = dict(
                **base,
                id=f"EXPLICIT-mass-{index:02d}-{point.iteration}-{weight}",
                readout=weight,
            )
            name = "masses/" + meta["id"] + ".json.gz"
            receipt = write_mass(scratch / name, context.partition, mass, meta)
            masses.append(
                dict(**meta, file=name, receipt=receipt, metadata_sha256=sha(meta))
            )
            policies[weight + "_average"] = context.partition.normalize(mass)
        for readout, policy in policies.items():
            deadline.check()
            meta = dict(
                **base,
                id=f"EXPLICIT-policy-{index:02d}-{point.iteration}-{readout}",
                readout=readout,
                **score_data(context, context.score(policy)),
            )
            name = "policies/" + meta["id"] + ".json.gz"
            receipt = write_snapshot(scratch / name, context.partition, policy, meta)
            profiles.append(
                dict(**meta, file=name, receipt=receipt, metadata_sha256=sha(meta))
            )

    observe(
        solver,
        iterations=list(range(1, 17)),
        work=work,
        capture=capture,
        deadline=deadline,
    )
    if guard(solver) != guard(direct):
        raise ArithmeticError("tiny final state changed")


def inventory(saved: dict[str, Any]) -> None:
    expected_profiles = {
        (i, t, r)
        for i in range(24)
        for t in (4, 8)
        for r in ("current", "uniform_average", "linear_average")
    }
    expected_masses = {
        (i, t, r) for i in range(24) for t in (4, 8) for r in ("uniform", "linear")
    }
    for name, expected in (
        ("profiles", expected_profiles),
        ("masses", expected_masses),
    ):
        rows = saved[name]
        actual = [(r["fixture_case"], r["iteration"], r["readout"]) for r in rows]
        if (
            len(actual) != len(expected)
            or set(actual) != expected
            or len({r["id"] for r in rows}) != len(rows)
        ):
            raise ArithmeticError("incomplete/duplicate tiny capture inventory")
        if any(
            type(r["fixture_case"]) is not int
            or type(r["iteration"]) is not int
            or r["scope"] != SCOPE
            or r["source_sha256"] != saved["source_sha256"]
            for r in rows
        ):
            raise ArithmeticError("tiny row source/scope changed")
    checks = saved["checks"]
    identities = [(r["fixture_case"], r["iteration"]) for r in checks]
    if len(identities) != 384 or set(identities) != {
        (i, t) for i in range(24) for t in range(1, 17)
    }:
        raise ArithmeticError("tiny full-step trajectory checks incomplete")
    if sum(len(r["work_labels"]) for r in checks) != 72:
        raise ArithmeticError("tiny source-work checks incomplete")

    by_key = {(r["fixture_case"], r["iteration"]): r for r in checks}
    for case in range(24):
        previous = 0
        for iteration in range(1, 17):
            item = by_key[case, iteration]
            if (
                type(item["fixture_case"]) is not int
                or type(item["iteration"]) is not int
                or type(item["total_work"]) is not int
                or item["total_work"] <= previous
                or not isinstance(item["state_sha256"], str)
                or len(item["state_sha256"]) != 64
                or bool(item["work_labels"]) != (iteration in (2, 7, 16))
                or any(
                    type(label) is not int or not previous < label <= item["total_work"]
                    for label in item["work_labels"]
                )
            ):
                raise ArithmeticError("invalid tiny source-work/state check")
            previous = item["total_work"]
    for row in [*saved["profiles"], *saved["masses"]]:
        item = by_key[row["fixture_case"], row["iteration"]]
        if (row["total_work"], row["guard_sha256"]) != (
            item["total_work"],
            item["state_sha256"],
        ):
            raise ArithmeticError("tiny capture is not bound to its source step")


def metric_error(reported: dict[str, Any], expected: dict[str, float]) -> float:
    errors: list[float] = []
    for key, value in expected.items():
        actual = reported[key]
        if type(actual) not in (int, float) or not math.isfinite(actual):
            raise ArithmeticError("nonfinite/invalid tiny score")
        errors.append(abs(float(actual) - value))
    return max(errors)


def replay(
    root: Path, path: Path, saved: dict[str, Any], deadline: Deadline
) -> dict[str, Any]:
    inventory(saved)
    context = toy_context()
    tree = context.partition
    policies = {}
    maximum = 0.0
    cache: dict[str, dict[str, float]] = {}
    for row, blob in read_archive(
        path.with_name(saved["policies_file"]),
        saved["policies_sha256"],
        saved["profiles"],
    ):
        deadline.check()
        policy = unpack_policy(tree, decode(blob, context, row)["policy"])
        policies[row["fixture_case"], row["iteration"], row["readout"]] = policy
        fingerprint = array_sha(policy)
        if fingerprint not in cache:
            cache[fingerprint] = independent_metrics(tree, policy)
        maximum = max(maximum, metric_error(row["metrics"], cache[fingerprint]))
    for row, blob in read_archive(
        path.with_name(saved["masses_file"]), saved["masses_sha256"], saved["masses"]
    ):
        deadline.check()
        mass = decode_mass(blob, tree, row)
        policy = policies[
            row["fixture_case"], row["iteration"], row["readout"] + "_average"
        ]
        if not np.array_equal(tree.normalize(mass), policy):
            raise ArithmeticError("stored raw mass does not reproduce prefix policy")
    if maximum > 1e-12:
        raise ArithmeticError("independent tiny EV/pure best reply differs")
    return dict(
        status="all144policies96masses_replayed_independent_math",
        profiles=144,
        raw_ledgers=96,
        full_step_checks=384,
        source_work_checks=72,
        maximum_error_fixture_chips=maximum,
        reference_constructed=False,
        poker_training_performed=False,
        long_run_admitted=False,
    )


def run(root: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain complete/partial tiny proof")
    started = time.perf_counter()
    deadline = Deadline(180)
    saved: dict[str, Any] = dict(
        scope=SCOPE,
        status="running",
        failure=None,
        environment=runtime_environment(),
        config=None,
        source=None,
        source_sha256=None,
        profiles=[],
        masses=[],
        checks=[],
        software_training_attempted=False,
        software_training_performed=False,
        poker_training_performed=False,
        reference_constructed=False,
        long_run_admitted=False,
        seconds=0.0,
    )
    scratch = root / "results/runs/matched-prefix-capture" / str(time.time_ns())
    saved["scratch"] = str(scratch)
    try:
        saved["source"] = source_provenance(root, root / CONFIG, entrypoints=ENTRIES)
        saved["source_sha256"] = sha(saved["source"]["sha256"])
        if saved["source"]["dirty"] is not False:
            raise ArithmeticError("tiny proof requires clean committed source")
        persist(output, saved)
        saved["config"] = config_inputs(root)
        saved["software_training_attempted"] = True
        for i in range(24):
            collect(
                i,
                scratch,
                saved["source_sha256"],
                saved["profiles"],
                saved["masses"],
                saved["checks"],
                deadline,
            )
        inventory(saved)
        for kind in ("policies", "masses"):
            archive = output.with_name(kind + ".jsonl.gz")
            rows = saved["profiles" if kind == "policies" else "masses"]
            saved[kind + "_file"] = archive.name
            saved[kind + "_sha256"] = write_archive(archive, scratch, rows)
        saved["replay"] = replay(root, output, saved, deadline)
        deadline.check()
        saved["status"] = "completed_software_only_not_poker"
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        saved["software_training_performed"] = bool(saved["checks"])
        saved["completed_profiles"] = len(saved["profiles"])
        saved["completed_raw_ledgers"] = len(saved["masses"])
        saved["completed_step_checks"] = len(saved["checks"])
        saved["seconds"] = time.perf_counter() - started
        persist(output, saved)
    return saved


def compare_proofs(actual: dict[str, Any], recorded: dict[str, Any]) -> None:
    diagnostic = "maximum_error_fixture_chips"
    if set(actual) != set(recorded) or any(
        (
            type(actual[key]) is not type(recorded[key])
            or not same(actual[key], recorded[key])
        )
        for key in actual
        if key != diagnostic
    ):
        raise ArithmeticError("tiny replay proof structure changed")
    errors = (actual[diagnostic], recorded[diagnostic])
    if (
        any(
            type(x) not in (int, float) or not math.isfinite(x) or not 0 <= x <= 1e-12
            for x in errors
        )
        or abs(errors[0] - errors[1]) > 1e-12
    ):
        raise ArithmeticError("tiny replay error exceeds preset chip tolerance")


def read(root: Path, path: Path) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads(path.read_text())
    if saved["status"] != "completed_software_only_not_poker":
        raise ArithmeticError("incomplete tiny proof")
    check_source(root, saved["source"])
    if (
        saved["scope"] != SCOPE
        or saved["status"] != "completed_software_only_not_poker"
        or saved["failure"] is not None
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["config"] != config_inputs(root)
        or type(saved["seconds"]) not in (int, float)
        or not 0 <= saved["seconds"] < 180
        or saved["software_training_attempted"] is not True
        or saved["software_training_performed"] is not True
        or type(saved["completed_profiles"]) is not int
        or saved["completed_profiles"] != 144
        or type(saved["completed_raw_ledgers"]) is not int
        or saved["completed_raw_ledgers"] != 96
        or type(saved["completed_step_checks"]) is not int
        or saved["completed_step_checks"] != 384
        or saved["poker_training_performed"] is not False
        or saved["reference_constructed"] is not False
        or saved["long_run_admitted"] is not False
    ):
        raise ArithmeticError("incomplete or mislabeled tiny proof")
    proof = replay(root, path, saved, Deadline(180))
    compare_proofs(proof, saved["replay"])
    return proof
