"""Own matched-update orchestration; real trajectories need published admission."""

import json
import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import matched_update_inputs as inputs
from poker_ai.evaluation.matched_update_records import (
    inventory,
    paired_fixed,
    paired_self,
)
from poker_ai.evaluation.matched_update_replay import replay_real, reused
from poker_ai.evaluation.matched_update_scoring import (
    REAL_SCOPE,
    scoring_job,
    training_job,
)
from poker_ai.postflop.cell_process import run_batch
from poker_ai.postflop.learning_artifacts import sha, write_archive
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

FORMAT = "poker-ai-complete-matched-update-own-v1"
ENTRIES = tuple(
    "scripts/" + n + "_matched_updates.py"
    for n in ("check", "profile", "study", "audit", "report")
)
PHASES = dict(
    capture="captures",
    mass="masses",
    checkpoint="checkpoints",
    profile="rows",
    fixed="fixed_matches",
)


def source(root: Path) -> dict[str, Any]:
    return source_provenance(root, root / inputs.CONFIG, entrypoints=ENTRIES)


def fresh(output: Path) -> None:
    for p in [
        output,
        output.with_suffix(".tmp"),
        *[
            output.with_name(output.stem + "-" + n + ".jsonl.gz")
            for n in ("captures", "masses", "profiles")
        ],
    ]:
        if p.exists() or p.with_suffix(".tmp").exists():
            raise FileExistsError("retain complete/partial matched-update attempt")


def gather(saved: dict[str, Any]) -> None:
    """Also called after failure: retain each actually emitted partial record."""
    for name in PHASES.values():
        saved[name] = []
    started = initialized = 0
    for batch in saved["batches"]:
        for worker in batch.get("workers", []):
            for event in worker["messages"]:
                if event["kind"] != "cell":
                    continue
                if event["index"] not in batch["assignments"][worker["slot"]]:
                    raise ArithmeticError(
                        "worker event outside fixed context partition"
                    )
                phase = event["phase"]
                if phase in PHASES:
                    saved[PHASES[phase]].append(event["row"])
                if phase == "training_started":
                    started += 1
                elif phase == "training_initialized":
                    initialized += 1
    saved["training_attempted_paths"] = started
    saved["initialized_training_paths"] = initialized
    saved["training_performed"] = initialized > 0
    for name in PHASES.values():
        if name == "fixed_matches":
            saved[name].sort(
                key=lambda r: (
                    r["own_snapshot_id"],
                    r["opponent_profile_id"],
                    r["target"],
                )
            )
        else:
            saved[name].sort(
                key=lambda r: (
                    r["path_index"],
                    str(r.get("id", "")),
                    r.get("work_label") or 0,
                )
            )
        saved["completed_" + name] = len(saved[name])


def archive(
    output: Path, saved: dict[str, Any], scratch: Path, key: str, name: str
) -> None:
    path = output.with_name(output.stem + "-" + name + ".jsonl.gz")
    saved[key + "_file"] = path.name
    saved[key + "_sha256"] = write_archive(
        path,
        scratch,
        saved[
            "captures"
            if name == "captures"
            else "masses"
            if name == "masses"
            else "rows"
        ],
    )


def run(root: Path, output: Path) -> dict[str, Any]:
    from poker_ai.evaluation.matched_update_admission import require_admission
    from poker_ai.evaluation.matched_update_report import write_report

    fresh(output)
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    deadline = Deadline(7200)
    saved: dict[str, Any] = dict(
        format=FORMAT,
        scope=REAL_SCOPE,
        status="running",
        failure=None,
        source=None,
        source_sha256=None,
        config=None,
        admission=None,
        environment=runtime_environment(),
        source_inputs=None,
        manifest=None,
        batches=[],
        captures=[],
        masses=[],
        checkpoints=[],
        rows=[],
        fixed_matches=[],
        self_pairs=[],
        fixed_pairs=[],
        own_replay=None,
        report=None,
        training_attempted_paths=0,
        training_performed=False,
        reference_constructed=False,
        reference_output_used_in_training=False,
        new_agent_default=False,
        fresh_global_admission=False,
        seconds=0.0,
    )
    scratch = root / "results/runs/matched-update-pipeline" / str(time.time_ns())
    saved["scratch"] = str(scratch)
    try:
        # Persist even dirty-source/config/runtime/admission failures. Capture the
        # clean source BEFORE this new output appears in git status.
        saved["source"] = source(root)
        saved["source_sha256"] = sha(saved["source"]["sha256"])
        persist(output, saved)
        if saved["source"]["dirty"] is not False:
            raise ArithmeticError("publish clean matched-update source first")
        saved["config"] = inputs.config_inputs(root)
        required = saved["config"]["required_runtime"]
        if any(saved["environment"][k] != required[k] for k in ("python", "numpy")):
            raise ArithmeticError("real matched prefixes require original Python/NumPy")
        saved["admission"] = require_admission(root, saved["source_sha256"])
        sources = inputs.load(root)
        saved["source_inputs"] = sources.manifest["input_sha256"]
        saved["manifest"] = sources.manifest
        expected = [
            sources.original(i, w)
            for i in range(24)
            for w in (100000, 1000000, 10000000)
        ]
        for phase, job in (("capture", training_job), ("score", scoring_job)):
            batch: dict[str, Any] = {}
            saved["batches"].append(batch)
            run_batch(
                24,
                3,
                job,
                dict(
                    root=str(root),
                    scratch=str(scratch),
                    binding=saved["source_sha256"],
                    own_path=str(output),
                    own=saved,
                    checkpoints=saved["checkpoints"],
                    remaining_seconds=7200 - (time.perf_counter() - started),
                ),
                deadline,
                batch,
            )
            gather(saved)
            persist(output, saved)
            if phase == "capture":
                archive(output, saved, scratch, "captures", "captures")
                archive(output, saved, scratch, "masses", "masses")
                inventory(saved, sources.manifest, expected)
        right, right_fixed = reused(sources)
        saved["self_pairs"] = paired_self(sources.manifest, saved["rows"], right)
        saved["fixed_pairs"] = paired_fixed(
            sources.manifest, saved["fixed_matches"], right_fixed
        )
        archive(output, saved, scratch, "details", "profiles")
        saved["own_replay"] = replay_real(output, saved, sources, deadline)
        saved["report"] = write_report(saved, output.parent / "report")
        if any(digest(root / p) != h for p, h in saved["source_inputs"].items()):
            raise ArithmeticError("historical input changed during matched study")
        deadline.check()
        saved["status"] = "completed_own_native_pending"
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        try:
            gather(saved)
        except BaseException as retention_error:
            saved["retention_failure"] = dict(
                type=type(retention_error).__name__, reason=str(retention_error)
            )
            saved["status"] = "incomplete"
            # Preserve the primary worker/IO failure and all raw messages even
            # when a malformed event cannot be assembled into a trusted row.
            if saved["failure"] is None:
                saved["failure"] = saved["retention_failure"]

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


def read_saved(root: Path, path: Path) -> tuple[dict[str, Any], inputs.Sources]:
    from poker_ai.evaluation.matched_update_admission import require_admission
    from poker_ai.postflop.parallel_profile import same
    from poker_ai.postflop.pipeline_report import check_source

    saved: dict[str, Any] = json.loads(path.read_text())
    check_source(root, saved["source"])
    if (
        saved["format"] != FORMAT
        or saved["scope"] != REAL_SCOPE
        or saved["status"] != "completed_own_native_pending"
        or saved["failure"] is not None
        or saved["config"] != inputs.config_inputs(root)
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["training_performed"] is not True
        or type(saved["initialized_training_paths"]) is not int
        or saved["initialized_training_paths"] != 24
        or any(
            saved[k] is not False
            for k in (
                "reference_constructed",
                "reference_output_used_in_training",
                "new_agent_default",
                "fresh_global_admission",
            )
        )
        or type(saved["seconds"]) not in (int, float)
        or not 0 <= saved["seconds"] < 7200
        or len(saved["batches"]) != 2
        or any(b["status"] != "completed" for b in saved["batches"])
    ):
        raise ArithmeticError("incomplete/changed real matched-update receipt")
    expected_admission = require_admission(root, saved["source_sha256"])
    if not same(expected_admission, saved["admission"]):
        raise ArithmeticError("real matched-update admission changed")
    if any(
        saved["environment"][k] != saved["config"]["required_runtime"][k]
        for k in ("python", "numpy")
    ):
        raise ArithmeticError("matched trajectory recorded a different runtime")
    from poker_ai.evaluation.matched_update_workers import complete

    complete(saved["batches"][0], dict(paths=8, captures=48, masses=32, checkpoints=24))
    complete(saved["batches"][1], dict(paths=8, profiles=48, fixed_targets=384))
    sources = inputs.load(root)
    if not same(saved["source_inputs"], sources.manifest["input_sha256"]):
        raise ArithmeticError("matched study input binding changed")
    rebuilt = dict(saved)
    gather(rebuilt)
    if any(
        not same(rebuilt[k], saved[k])
        for k in (
            *PHASES.values(),
            "training_attempted_paths",
            "initialized_training_paths",
        )
    ):
        raise ArithmeticError("matched rows differ from raw worker messages")
    inventory(
        saved,
        sources.manifest,
        [
            sources.original(i, w)
            for i in range(24)
            for w in (100000, 1000000, 10000000)
        ],
    )
    return saved, sources
