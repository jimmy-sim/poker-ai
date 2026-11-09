"""Complete three-process NONUNIFORM KUHN software IO, never poker outcomes.

Different toy game names/work labels cannot pass the formal config byte gate.
This exercises actual serialization, observations, barriers and all 480 scores.
Reference solvers are neither constructed nor represented as independently run.
"""

import copy
import json
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import frozen_batch_inputs as inputs
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.averaging_history_software import toy_context
from poker_ai.evaluation.controlled_reply_inputs import (
    Inputs,
    SourcePolicy,
    expected,
    identity,
)
from poker_ai.evaluation.frozen_batch_replay import replay_archives
from poker_ai.evaluation.frozen_batch_validation import gather
from poker_ai.evaluation.reduced_study_run import copy_full, prefix_grid, sort_rows
from poker_ai.evaluation.reduced_study_training import train_one
from poker_ai.finite import FloatArray
from poker_ai.postflop.cell_process import Send, run_batch
from poker_ai.postflop.controlled_checkpoints import (
    Observation,
    observe,
    write_snapshot,
)
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.learning_artifacts import sha, write_archive
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.node_profile import trainer
from poker_ai.postflop.river_study import Deadline

SCOPE = "EXPLICIT_NONUNIFORM_KUHN_SOFTWARE_NOT_POKER_RESULTS"


def prepare(
    root: Path, config: dict[str, Any], deadline: Deadline
) -> tuple[HistoryInputs, dict[str, Any]]:
    config = copy.deepcopy(config)
    config.update(
        status=SCOPE,
        spot_files=["EXPLICIT_TOY_LOW", "EXPLICIT_TOY_MEDIUM"],
        work_labels=[1000, 3000, 5000],
    )
    source_config = dict(
        config,
        traversals=["full", "external"],
        original_average_replay_labels=config["work_labels"],
    )
    context = toy_context()
    rows = []
    prefixes = {}
    policies = []
    cases = [
        dict(json.loads(k), bridge="common", regret_weight="linear")
        for k in sorted(expected(source_config))
    ]
    scratch = root / "original-scratch"
    for index, case in enumerate(cases):
        solver = trainer(context.partition, case, "parent")
        solver.initialize_exact()
        snapshots: list[FloatArray] = []

        def capture(
            point: Observation,
            case: dict[str, Any] = case,
            index: int = index,
            solver: ControlledTrainer = solver,
            snapshots: list[FloatArray] = snapshots,
        ) -> None:
            for _, label in point.labels:
                metadata = dict(
                    id=f"EXPLICIT_TOY_OLD_{index}_{label}",
                    index=index,
                    case=case,
                    iteration=point.iteration,
                    previous_work=point.previous_work,
                    total_work=point.total_work,
                    last_iteration_visits=point.last_iteration_visits,
                    initialization_visits=solver.initialization_visits,
                    state_sha256=point.state_sha256,
                    labels=[["work", label]],
                    **score_data(context, context.score(point.policy)),
                )
                filename = f"{metadata['id']}.json.gz"
                row = dict(
                    **metadata,
                    file=filename,
                    receipt=write_snapshot(
                        scratch / filename, context.partition, point.policy, metadata
                    ),
                    metadata_sha256=sha(metadata),
                )
                rows.append(row)
                prefixes[identity(case), label] = row
                snapshots.append(point.policy)

        observe(
            solver, config["work_labels"], [], context.river_masks[0], capture, deadline
        )
        policies.append(
            SourcePolicy(case, prefixes[identity(case), 5000], snapshots[-1])
        )
    original = dict(rows=rows, scope=SCOPE)
    path = root / "results/controlled-learning/own-profiles.jsonl.gz"
    path.parent.mkdir(parents=True, exist_ok=True)
    original["details_sha256"] = write_archive(path, scratch, rows)
    contexts = {
        (game, rep): context
        for game in config["spot_files"]
        for rep in config["representations"]
    }
    data = HistoryInputs(
        source_config,
        Inputs(source_config, original, contexts, tuple(policies)),
        prefixes,
        {},
    )
    for name in config["spot_files"]:
        (root / name).write_text(json.dumps(dict(scope=SCOPE, pot=2)))
    return data, config


def job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    context = toy_context()
    deadline = Deadline(payload["remaining_seconds"])
    for local in indices:
        index = payload["selected"][local]
        train_one(
            context,
            payload["paths"][index],
            index,
            payload["prefixes"][index],
            payload["labels"],
            Path(payload["scratch"]),
            payload["binding"],
            send,
            deadline,
        )
    return dict(
        paths=len(indices),
        profiles=6 * len(indices),
        masses=6 * len(indices),
        currents=3 * len(indices),
        prefix_checks=6 * len(indices) if payload["selected"] == list(range(24)) else 0,
    )


def roundtrip(
    root: Path, config: dict[str, Any], binding: str, deadline: Deadline
) -> tuple[dict[str, Any], HistoryInputs, Path]:
    if root.exists():
        raise FileExistsError("retain complete/partial explicit toy batch exercise")
    root.mkdir(parents=True)
    data, config = prepare(root, config, deadline)
    selected_paths = inputs.paths(config)
    scratch = root / "scratch"
    saved: dict[str, Any] = dict(
        scope=SCOPE,
        status="running",
        failure=None,
        config=config,
        source_sha256=binding,
        rows=[],
        masses=[],
        currents=[],
        prefix_checks=[],
        batches=[],
    )
    path = root / "own.json"
    try:
        for selected in (list(range(24)), list(range(24, 72))):
            if selected[0] == 24:
                prefix_grid(saved["prefix_checks"], data, config)
            batch: dict[str, Any] = {}
            saved["batches"].append(batch)
            run_batch(
                len(selected),
                3,
                job,
                dict(
                    selected=selected,
                    paths=selected_paths,
                    prefixes=[inputs.prefix_map(data, p) for p in selected_paths],
                    labels=config["work_labels"],
                    scratch=str(scratch),
                    binding=binding,
                    remaining_seconds=deadline.seconds
                    - (time.perf_counter() - deadline.started),
                ),
                deadline,
                batch,
            )
            rows, checks, masses, currents = gather(batch, selected)
            saved["rows"].extend(rows)
            saved["prefix_checks"].extend(checks)
            saved["masses"].extend(masses)
            saved["currents"].extend(currents)
        prefix_grid(saved["prefix_checks"], data, config)
        saved["rows"].extend(copy_full(root, data, scratch, binding, deadline))
        for name, key, stem in (
            ("rows", "details", "profiles"),
            ("masses", "mass_details", "masses"),
            ("currents", "current_details", "currents"),
        ):
            saved[name] = sort_rows(saved[name])
            archive = root / f"own-{stem}.jsonl.gz"
            saved[key + "_file"] = archive.name
            saved[key + "_sha256"] = write_archive(archive, scratch, saved[name])
        saved["own_replay"] = replay_archives(path, saved, data, deadline)
        saved["status"] = "passed_complete_toy_IO_no_postflop_learning"
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        persist(path, saved)
    return saved, data, path
