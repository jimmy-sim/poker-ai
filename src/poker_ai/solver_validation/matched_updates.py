"""Source-bound independent matched-update audit, with retained partial failures."""

import json
import math
import os
import socket
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import matched_update_inputs as inputs
from poker_ai.evaluation import matched_update_software as software
from poker_ai.evaluation.averaging_history_software import toy_context
from poker_ai.evaluation.frozen_batch_validation import full_sources
from poker_ai.evaluation.matched_update_run import read_saved, source
from poker_ai.evaluation.matched_update_software_inputs import SCOPE
from poker_ai.postflop.cell_process import Send, run_batch
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.averaging_history import fixed_error
from poker_ai.solver_validation.controlled_pipeline import license_record
from poker_ai.solver_validation.frozen_batches import error as self_error
from poker_ai.solver_validation.matched_array_reference import ScalarReference
from poker_ai.solver_validation.matched_update_audit import audit_rows, published

FORMAT = "poker-ai-complete-matched-update-native-v1"


def job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    deadline = Deadline(payload["remaining_seconds"])
    sources = inputs.load(Path(payload["root"]))
    opponents = {p.identifier: p for p in full_sources(sources.archived.data)}
    send(dict(kind="prepared", phase="reference_setup_started"))
    cache: dict[tuple[str, str], ScalarReference] = {}
    refs = {}
    for index in indices:
        context = sources.context(index)
        path = sources.paths[index]
        exact_key = path["spot_file"], "exact"
        limited_key = path["spot_file"], path["representation"]
        if exact_key not in cache:
            cache[exact_key] = ScalarReference(context.exact)
        if limited_key not in cache:
            cache[limited_key] = ScalarReference(context.partition)
        refs[index] = cache[exact_key], cache[limited_key]
    send(dict(kind="prepared", phase="reference_setup_completed"))

    def opponent(peer: dict[str, Any]) -> Any:
        identifier = peer["opponent_profile_id"]
        return opponents[identifier].policy, sources.archived.data.replies[
            identifier, peer["target"]
        ]

    return audit_rows(
        Path(payload["own_path"]),
        payload["own"],
        indices,
        sources.context,
        refs,
        opponent,
        send,
        deadline,
    )


def results(saved: dict[str, Any]) -> None:
    if saved["batch"]:
        events = [e for w in saved["batch"].get("workers", []) for e in w["messages"]]
        saved["rows"] = [
            e["result"] for e in events if e["kind"] == "cell" and e["phase"] == "self"
        ]
        saved["fixed"] = [
            e["result"] for e in events if e["kind"] == "cell" and e["phase"] == "fixed"
        ]
        saved["reference_setup_started"] = any(
            e["kind"] == "prepared" and e.get("phase") == "reference_setup_started"
            for e in events
        )
        saved["reference_setup_completed"] = any(
            e["kind"] == "prepared" and e.get("phase") == "reference_setup_completed"
            for e in events
        )
    saved["completed_profiles"] = len(saved["rows"])
    saved["completed_fixed_targets"] = len(saved["fixed"])


def validate(
    saved: dict[str, Any], own: dict[str, Any], own_path: Path
) -> dict[str, Any]:
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
        or saved["own_sha256"] != digest(own_path)
        or saved["details_sha256"] != own["details_sha256"]
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["publication"]["own_sha256"] != digest(own_path)
        or saved["reference_setup_started"] is not True
        or saved["reference_setup_completed"] is not True
        or any(
            saved[k] is not False
            for k in (
                "training_performed",
                "reference_actions_exported",
                "reference_output_used_in_training",
                "long_run_admitted",
            )
        )
        or saved["scope"] != own["scope"]
    ):
        raise ArithmeticError("incomplete/mislabeled native matched receipt")
    if saved["scope"] == SCOPE:
        if saved["batch"] != {} or any(
            not same(saved["summary"][k], v)
            for k, v in dict(
                paths=24, profiles=144, fixed_targets=1152, cached_opponent_targets=32
            ).items()
        ):
            raise ArithmeticError("tiny native complete inventory summary changed")
    else:
        from poker_ai.evaluation.matched_update_workers import complete

        complete(
            saved["batch"],
            dict(paths=8, profiles=48, fixed_targets=384, cached_opponent_targets=32),
        )
        rebuilt = dict(saved)
        results(rebuilt)
        if not same(rebuilt["rows"], saved["rows"]) or not same(
            rebuilt["fixed"], saved["fixed"]
        ):
            raise ArithmeticError("native records differ from raw worker events")
    maximum = 0.0
    for kind, peers, actual, fields in (
        ("self", own["rows"], saved["rows"], ("id",)),
        (
            "fixed",
            own["fixed_matches"],
            saved["fixed"],
            ("own_snapshot_id", "opponent_profile_id", "target"),
        ),
    ):

        def key(
            row: dict[str, Any], columns: tuple[str, ...] = fields
        ) -> tuple[Any, ...]:
            return tuple(row[k] for k in columns)

        expected = {key(r): r for r in peers}
        observed = {key(r): r for r in actual}
        if (
            len(expected) != len(peers)
            or len(actual) != len(observed)
            or set(expected) != set(observed)
            or len(actual) != (144 if kind == "self" else 1152)
        ):
            raise ArithmeticError("native matched inventory missing/duplicate/extra")
        for k, row in observed.items():
            error = (
                self_error(row, expected[k])
                if kind == "self"
                else fixed_error(row, expected[k])
            )
            if not math.isfinite(error) or error > 1e-9:
                raise ArithmeticError(
                    "native matched scalar/root/own-reply disagreement"
                )
            maximum = max(maximum, error)
    if (
        type(saved["seconds"]) not in (int, float)
        or not 0 <= saved["seconds"] < (180 if saved["scope"] == SCOPE else 900)
        or type(saved["completed_profiles"]) is not int
        or saved["completed_profiles"] != 144
        or type(saved["completed_fixed_targets"]) is not int
        or saved["completed_fixed_targets"] != 1152
        or not same(maximum, saved["maximum_error_chips"])
    ):
        raise ArithmeticError("native matched cap/count/error changed")
    return dict(
        profiles=144,
        fixed_targets=1152,
        maximum_error_chips=maximum,
        reference_actions_exported=False,
        long_run_admitted=False,
    )


def audit(
    root: Path,
    own_path: Path,
    output: Path,
    *,
    tiny: bool = False,
    timing: bool = False,
) -> dict[str, Any]:
    if output.exists() or output.with_suffix(".tmp").exists():
        raise FileExistsError("retain native matched attempt")
    started, cpu, children = time.perf_counter(), time.process_time(), os.times()
    saved: dict[str, Any] = dict(
        format=FORMAT,
        status="running",
        failure=None,
        source=None,
        source_sha256=None,
        own_sha256=None,
        details_sha256=None,
        publication=None,
        license=None,
        scope=SCOPE if tiny else None,
        reference=None,
        environment=runtime_environment(),
        reference_setup_started=False,
        reference_setup_completed=False,
        rows=[],
        fixed=[],
        batch={},
        completed_profiles=0,
        completed_fixed_targets=0,
        maximum_error_chips=None,
        training_performed=False,
        reference_actions_exported=False,
        reference_output_used_in_training=False,
        long_run_admitted=False,
        seconds=0.0,
    )
    try:
        saved["source"] = source(root)
        saved["source_sha256"] = sha(saved["source"]["sha256"])
        persist(output, saved)
        if saved["source"]["dirty"] is not False:
            raise ArithmeticError("publish clean own matched evidence first")
        config = inputs.config_inputs(root)
        saved["publication"] = published(root, own_path)
        if tiny:
            raw = json.loads(own_path.read_text())
            beginning = raw["proof_started_perf_counter"]
            if (
                raw["proof_host"] != socket.gethostname()
                or type(beginning) not in (int, float)
                or not 0 <= time.perf_counter() - beginning < 180
            ):
                raise ArithmeticError(
                    "shared180s tiny proof clock/publication interval expired"
                )
            deadline = Deadline(180)
            deadline.started = beginning
            own, fixture, _ = software.read(root, own_path, deadline)
        else:
            deadline = Deadline(900)
            deadline.started = started
            if timing:
                from poker_ai.evaluation.matched_update_overhead import (
                    read as read_timing,
                )

                own, sources = read_timing(root, own_path, deadline)
            else:
                own, sources = read_saved(root, own_path)
                from poker_ai.evaluation.matched_update_replay import replay_real

                replay_real(own_path, own, sources, deadline)
        saved.update(
            own_sha256=digest(own_path),
            details_sha256=own["details_sha256"],
            scope=own["scope"],
        )
        saved["reference"] = config["reference"]
        saved["license"] = license_record(dict(native_reference=config["reference"]))
        if tiny:
            saved["reference_setup_started"] = True
            reference = ScalarReference(toy_context().exact)
            saved["reference_setup_completed"] = True

            def send(event: dict[str, Any]) -> None:
                saved["rows" if event["phase"] == "self" else "fixed"].append(
                    event["result"]
                )

            def opponent(peer: dict[str, Any]) -> Any:
                policy, replies = fixture.controls[peer["opponent_profile_id"]]
                return policy, replies[peer["target"]]

            summary = audit_rows(
                own_path,
                own,
                list(range(24)),
                lambda _: toy_context(),
                {i: (reference, reference) for i in range(24)},
                opponent,
                send,
                deadline,
            )
            saved["summary"] = summary
            # Complete final OWN replay is inside the SAME deadline, including
            # time spent committing/pushing own evidence between these commands.
            software.read(root, own_path, deadline)
            saved["seconds"] = time.perf_counter() - deadline.started
        else:
            run_batch(
                24,
                3,
                job,
                dict(
                    root=str(root),
                    own_path=str(own_path),
                    own=own,
                    remaining_seconds=900 - (time.perf_counter() - started),
                ),
                deadline,
                saved["batch"],
            )
            results(saved)
            saved["seconds"] = time.perf_counter() - started
        results(saved)
        errors = [r["maximum_error_chips"] for r in saved["rows"] + saved["fixed"]]
        saved["maximum_error_chips"] = max(errors)
        deadline.check()
        saved["status"] = "completed"
        validate(saved, own, own_path)
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        results(saved)
        saved["native_stage_seconds"] = time.perf_counter() - started
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


def read(root: Path, path: Path, own_path: Path, own: dict[str, Any]) -> dict[str, Any]:
    from poker_ai.postflop.pipeline_report import check_source

    saved: dict[str, Any] = json.loads(path.read_text())
    check_source(root, saved["source"])
    reference = inputs.config_inputs(root)["reference"]
    if (
        saved["reference"] != reference
        or saved["license"]["sha256"] != reference["license_sha256"]
        or saved["license"]["previously_read_record"] != "docs/solver_validation.md"
        or not saved["license"]["installed_license_files"]
    ):
        raise ArithmeticError("native matched license receipt changed")
    return validate(saved, own, own_path)
