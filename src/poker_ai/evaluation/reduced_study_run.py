"""Admitted fixed-work study, baseline barrier and immutable own artifacts."""

import json
import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import reduced_study_inputs as inputs
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.frozen_batch_replay import replay_archives
from poker_ai.evaluation.frozen_batch_validation import full_sources, gather, grid
from poker_ai.evaluation.reduced_study_protocol import fresh_output, require_admission
from poker_ai.evaluation.reduced_study_training import save
from poker_ai.postflop.cell_process import run_batch
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.learning_artifacts import (
    decode,
    read_archive,
    sha,
    write_archive,
)
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_validation import number
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment


def prefix_grid(
    checks: list[dict[str, Any]], data: HistoryInputs, config: dict[str, Any]
) -> None:
    expected = []
    for index, path in enumerate(inputs.paths(config)[:24]):
        for weight in inputs.WEIGHTS:
            for label in config["work_labels"]:
                peer = inputs.prefix_map(data, path)[weight][label]
                expected.append(
                    dict(
                        index=index,
                        average_weight=weight,
                        work_label=label,
                        original_id=peer["id"],
                        policy_sha256=peer["receipt"]["policy_sha256"],
                        **{
                            k: peer[k]
                            for k in (
                                "iteration",
                                "previous_work",
                                "total_work",
                                "last_iteration_visits",
                                "initialization_visits",
                                "state_sha256",
                            )
                        },
                    )
                )

    def key(r: dict[str, Any]) -> tuple[Any, ...]:
        return r["index"], r["average_weight"], r["work_label"]

    if not same(sorted(checks, key=key), sorted(expected, key=key)):
        raise ArithmeticError("original B1 prefix barrier incomplete/changed")


def copy_full(
    root: Path,
    data: HistoryInputs,
    scratch: Path,
    binding: str,
    deadline: Deadline,
) -> list[dict[str, Any]]:
    selected = {
        data.prefixes[p.identifier, t]["id"]: (i, p, t)
        for i, p in enumerate(full_sources(data))
        for t in data.config["original_average_replay_labels"]
    }
    rows = []
    for original, blob in read_archive(
        root / "results/controlled-learning/own-profiles.jsonl.gz",
        data.base.original["details_sha256"],
        data.base.original["rows"],
    ):
        deadline.check()
        if original["id"] not in selected:
            continue
        i, p, label = selected[original["id"]]
        context = data.base.context(p.case)
        policy = unpack_policy(
            context.partition, decode(blob, context, original)["policy"]
        )
        metadata = dict(
            id=f"full-{i:02d}-{label}",
            path_index=72 + i,
            case=p.case,
            batch_size=None,
            origin="reused_full",
            work_label=label,
            **{
                k: original[k]
                for k in (
                    "iteration",
                    "previous_work",
                    "total_work",
                    "last_iteration_visits",
                    "initialization_visits",
                    "state_sha256",
                )
            },
            overshoot=original["total_work"] - label,
            sampled_traversals=0,
            guard_sha256=None,
            current_sha256=None,
            current_movement=None,
            coverage=None,
            source_original_id=original["id"],
            source_sha256=binding,
            initialization_seconds=None,
            elapsed_cell_seconds=None,
        )
        row = save(context, policy, metadata, scratch, lambda e: None, deadline)
        if compare(row["metrics"], original["metrics"]) > 1e-9:
            raise ArithmeticError("reused full profile score changed")
        rows.append(row)
    if len(rows) != 48:
        raise ArithmeticError("reused full work controls incomplete")
    return rows


def sort_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(
        rows,
        key=lambda r: (r["path_index"], r["case"]["average_weight"], r["work_label"]),
    )


def run(root: Path, output: Path) -> dict[str, Any]:
    from poker_ai.evaluation.reduced_study_training import own_job

    fresh_output(output)
    if (output.parent / "report").exists():
        raise FileExistsError("retain previous batch study report directory")
    for name in ("profiles", "masses", "currents"):
        fresh_output(output.with_name(output.stem + "-" + name + ".jsonl.gz"))
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    config = inputs.config_inputs(root)
    current, binding = inputs.binding(root)
    env = runtime_environment()
    if any(env[k] != config["prefix_runtime"][k] for k in ("python", "numpy")):
        raise ArithmeticError("batch learning requires original prefix runtime")
    deadline = Deadline(7200)
    deadline.started = started
    scratch = root / "results/runs/reduced-batch-study" / str(time.time_ns())
    scratch.mkdir(parents=True, exist_ok=False)
    saved: dict[str, Any] = dict(
        format=inputs.FORMAT,
        status="running",
        failure=None,
        config=config,
        protocol=inputs.protocol(root),
        source=current,
        source_sha256=binding,
        environment=env,
        admission=None,
        scratch=str(scratch),
        batches=[],
        rows=[],
        masses=[],
        currents=[],
        prefix_checks=[],
        own_replay=None,
        details_file=None,
        details_sha256=None,
        mass_details_file=None,
        mass_details_sha256=None,
        current_details_file=None,
        current_details_sha256=None,
        report=None,
        seconds=0.0,
        training_performed=True,
        reference_output_used_in_training=False,
        new_agent_default=False,
        fresh_global_admission=False,
    )
    persist(output, saved)
    try:
        # The captured source was clean before writing this new attempt. Its
        # uncommitted evidence must not masquerade as a code change, nor may it
        # admit a different source inventory.
        saved["admission"] = require_admission(root, clean=False)
        if saved["admission"]["source_sha256"] != binding:
            raise ArithmeticError("new batch attempt differs from admitted code")
        data = inputs.prerequisites(root)
        paths = inputs.paths(config)
        comparison = json.loads((root / "configs/training-isolation.json").read_text())[
            "future_comparison"
        ]
        for phase, selected in enumerate((list(range(24)), list(range(24, 72)))):
            if phase == 1:
                prefix_grid(saved["prefix_checks"], data, config)
            batch: dict[str, Any] = {}
            saved["batches"].append(batch)
            run_batch(
                len(selected),
                3,
                own_job,
                dict(
                    root=str(root),
                    comparison=comparison,
                    selected=selected,
                    paths=paths,
                    prefixes=[inputs.prefix_map(data, p) for p in paths],
                    labels=config["work_labels"],
                    scratch=str(scratch),
                    binding=binding,
                    remaining_seconds=7200 - (time.perf_counter() - started),
                ),
                deadline,
                batch,
            )
            rows, checks, masses, currents = gather(batch, selected)
            saved["rows"].extend(rows)
            saved["prefix_checks"].extend(checks)
            saved["masses"].extend(masses)
            saved["currents"].extend(currents)
            persist(output, saved)
        prefix_grid(saved["prefix_checks"], data, config)
        saved["rows"].extend(copy_full(root, data, scratch, binding, deadline))
        for name in ("rows", "masses", "currents"):
            saved[name] = sort_rows(saved[name])
        grid(saved["rows"], data, config, binding)
        for name, key, stem in (
            ("rows", "details", "profiles"),
            ("masses", "mass_details", "masses"),
            ("currents", "current_details", "currents"),
        ):
            archive = output.with_name(output.stem + "-" + stem + ".jsonl.gz")
            saved[key + "_file"] = archive.name
            saved[key + "_sha256"] = write_archive(archive, scratch, saved[name])
            deadline.check()
        saved["own_replay"] = replay_archives(output, saved, data, deadline)
        from poker_ai.evaluation.frozen_batch_report import write_report

        saved["report"] = write_report(root, saved, output.parent / "report")
        deadline.check()
        saved["status"] = "completed_own_native_pending"
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        saved["seconds"] = time.perf_counter() - started
        saved["parent_cpu_seconds"] = time.process_time() - cpu
        now = os.times()
        saved["reaped_children_cpu_seconds"] = (
            now.children_user
            + now.children_system
            - children.children_user
            - children.children_system
        )
        persist(output, saved)
    return saved


def read_saved(root: Path, path: Path) -> tuple[dict[str, Any], HistoryInputs]:
    saved: dict[str, Any] = json.loads(path.read_text())
    config = inputs.config_inputs(root)
    if (
        saved["format"] != inputs.FORMAT
        or saved["status"] != "completed_own_native_pending"
        or saved["failure"] is not None
        or not same(saved["config"], config)
        or not same(saved["protocol"], inputs.protocol(root))
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["training_performed"] is not True
        or saved["reference_output_used_in_training"] is not False
        or saved["new_agent_default"] is not False
        or saved["fresh_global_admission"] is not False
        or not number(saved["seconds"], nonnegative=True)
        or saved["seconds"] >= 7200
        or len(saved["batches"]) != 2
    ):
        raise ArithmeticError("incomplete/changed batch study receipt")
    check_source(root, saved["source"])
    admission = require_admission(root, clean=False)
    if (
        not same(saved["admission"], admission)
        or saved["source_sha256"] != admission["source_sha256"]
    ):
        raise ArithmeticError("own batch source admission mismatch")
    data = inputs.prerequisites(root)
    rows = []
    checks = []
    masses = []
    currents = []
    for batch, selected in zip(
        saved["batches"], (list(range(24)), list(range(24, 72))), strict=True
    ):
        r, c, m, o = gather(batch, selected)
        rows.extend(r)
        checks.extend(c)
        masses.extend(m)
        currents.extend(o)
    prefix_grid(checks, data, config)
    if (
        not same(sort_rows(rows), [r for r in saved["rows"] if r["path_index"] < 72])
        or not same(sort_rows(masses), saved["masses"])
        or not same(sort_rows(currents), saved["currents"])
        or not same(checks, saved["prefix_checks"])
    ):
        raise ArithmeticError("own batch worker grid differs from archived rows")
    grid(saved["rows"], data, config, saved["source_sha256"])
    validate_replay(saved["own_replay"])
    return saved, data


def validate_replay(proof: dict[str, Any]) -> None:
    fixed = dict(
        status="all_batch_profiles_and_raw_observations_replayed",
        profiles=480,
        fresh_profiles=432,
        reused_full_profiles=48,
        mass_reconstructions=432,
        current_observations=216,
        new_postflop_training_performed=False,
    )
    if (
        any(not same(proof[k], v) for k, v in fixed.items())
        or any(
            not number(proof[k], nonnegative=True) or proof[k] > limit
            for k, limit in (
                ("maximum_error_chips", 1e-9),
                ("maximum_error_unitless", 1e-12),
            )
        )
        or not number(proof["seconds"], nonnegative=True)
    ):
        raise ArithmeticError("incomplete/changed own batch replay proof")


def replay(
    root: Path, path: Path, deadline: Deadline | None = None
) -> tuple[dict[str, Any], HistoryInputs, dict[str, Any]]:
    started = time.perf_counter()
    deadline = deadline or Deadline(900)
    saved, data = read_saved(root, path)
    proof = replay_archives(path, saved, data, deadline)
    proof["seconds"] = time.perf_counter() - started
    validate_replay(proof)
    deadline.check()
    return saved, data, proof
