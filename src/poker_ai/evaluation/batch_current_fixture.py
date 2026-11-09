"""Analytic nonuniform tiny-game sources, never trained poker or native results.

The real input gate rejects this scope. Source policies are deterministic legal
arrays, not learned trajectories. Every new evaluator/archive/process equation
runs on these arrays; fictional guards/work labels test source binding only.
"""

import json
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation import batch_current_inputs as inputs
from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.averaging_history_software import toy_context
from poker_ai.evaluation.batch_current_cells import evaluate_paths
from poker_ai.evaluation.controlled_reply_inputs import Inputs, SourcePolicy
from poker_ai.evaluation.controlled_reply_math import trace
from poker_ai.evaluation.frozen_batch_inputs import case, paths
from poker_ai.finite import FloatArray
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_checkpoints import (
    pack_policy,
    unpack_policy,
    write_snapshot,
)
from poker_ai.postflop.learning_artifacts import sha, write_archive
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.river_study import Deadline

SCOPE = "EXPLICIT_ANALYTIC_NONUNIFORM_KUHN_SOFTWARE_NOT_POKER_RESULTS"


def analytic(salt: int) -> FloatArray:
    tree = toy_context().partition
    weights = np.zeros_like(tree.legal)
    for i, menu in enumerate(tree.actions):
        weights[i, : len(menu)] = [1 + (i + 3 * a + salt) % 7 for a in range(len(menu))]
    return tree.normalize(weights)


def prepare(root: Path, base: dict[str, Any]) -> inputs.Sources:
    import copy

    root.mkdir(parents=True, exist_ok=False)
    config = copy.deepcopy(base)
    config.update(
        status=SCOPE,
        spot_files=["EXPLICIT_ANALYTIC_LOW", "EXPLICIT_ANALYTIC_MEDIUM"],
        work_labels=[1000, 3000, 5000],
    )
    context = toy_context()
    scratch = root / "source-snapshots"
    source_sha = sha(SCOPE)
    rows: list[dict[str, Any]] = []
    currents: list[dict[str, Any]] = []
    selected = paths(config)
    for index, path_spec in enumerate(selected):
        for label_index, label in enumerate(config["work_labels"]):
            guard = sha([SCOPE, index, label])
            own_case = case(path_spec, "linear")
            salt = index * 11 + label_index * 5
            policy = analytic(salt)
            metadata = dict(
                id=f"current-{index:03d}-{label}",
                path_index=index,
                case=own_case,
                batch_size=path_spec["batch_size"],
                work_label=label,
                guard_sha256=guard,
                source_sha256=source_sha,
                current_sha256=array_sha(policy),
                current_movement=None,
            )
            filename = "currents/" + metadata["id"] + ".json.gz"
            currents.append(
                dict(
                    **metadata,
                    file=filename,
                    receipt=write_snapshot(
                        scratch / filename, context.partition, policy, metadata
                    ),
                    metadata_sha256=sha(metadata),
                )
            )
            for weight in ("uniform", "linear"):
                policy = analytic(salt + (1 if weight == "uniform" else 2))
                m = dict(
                    id=f"path-{index:03d}-{weight}-{label}",
                    path_index=index,
                    case=case(path_spec, weight),
                    batch_size=path_spec["batch_size"],
                    work_label=label,
                    guard_sha256=guard,
                    source_sha256=source_sha,
                    iteration=label_index + 1,
                    total_work=label,
                    **score_data(context, context.score(policy)),
                )
                filename = "averages/" + m["id"] + ".json.gz"
                rows.append(
                    dict(
                        **m,
                        file=filename,
                        receipt=write_snapshot(
                            scratch / filename, context.partition, policy, m
                        ),
                        metadata_sha256=sha(m),
                    )
                )
    controls: list[SourcePolicy] = []
    replies = {}
    for game in config["spot_files"]:
        for rep in config["representations"]:
            for clip in ("signed", "clipped"):
                for weight in ("uniform", "linear"):
                    control_case = dict(
                        spot_file=game,
                        representation=rep,
                        traversal="full",
                        seed=None,
                        regret_rule=clip,
                        average_weight=weight,
                        regret_weight="linear",
                        bridge="common",
                    )
                    policy = analytic(len(controls) + 3)
                    m = dict(
                        id=f"EXPLICIT_ANALYTIC_CONTROL_{len(controls)}",
                        case=control_case,
                        receipt=dict(policy_sha256=array_sha(policy)),
                    )
                    control = SourcePolicy(control_case, m, policy)
                    controls.append(control)
                    for target in (0, 1):
                        _, reply, _ = trace(
                            context.partition,
                            policy,
                            target,
                            tuple("TURN" for _ in context.partition.keys),
                            1e-9,
                        )
                        replies[control.identifier, target] = reply
    for game in config["spot_files"]:
        (root / game).write_text(json.dumps(dict(scope=SCOPE, pot=2)))
    contexts = {
        (g, r): context for g in config["spot_files"] for r in config["representations"]
    }
    data = HistoryInputs(
        config,
        Inputs(config, dict(scope=SCOPE), contexts, tuple(controls)),
        {},
        replies,
    )
    own: dict[str, Any] = dict(
        scope=SCOPE,
        config=config,
        source_sha256=source_sha,
        rows=sorted(
            rows,
            key=lambda r: (
                r["path_index"],
                r["case"]["average_weight"],
                r["work_label"],
            ),
        ),
        currents=currents,
    )
    for key, name, points in (
        ("details", "averages", own["rows"]),
        ("current_details", "currents", currents),
    ):
        path = root / ("source-" + name + ".jsonl.gz")
        own[key + "_file"] = path.name
        own[key + "_sha256"] = write_archive(path, scratch, points)
    # Legacy mass bytes are unused by this saved-policy evaluator. Production's
    # full source/audit gate remains separate and cannot accept this fixture.
    unused = root / "EXPLICIT_UNUSED_MASS_BYTES"
    unused.write_text(SCOPE)
    from poker_ai.postflop.river_study import digest

    own["mass_details_file"] = unused.name
    own["mass_details_sha256"] = digest(unused)
    path = root / "source-own.json"
    persist(path, own)
    serialized = dict(
        scope=SCOPE,
        config=config,
        own=own,
        controls=[
            dict(
                case=p.case, row=p.row, policy=pack_policy(context.partition, p.policy)
            )
            for p in controls
        ],
    )
    persist(root / "EXPLICIT_SOFTWARE_SOURCES.json", serialized)
    return inputs.Sources(path, own, data, dict(scope=SCOPE))


def load(root: Path) -> inputs.Sources:
    saved = json.loads((root / "EXPLICIT_SOFTWARE_SOURCES.json").read_text())
    if saved["scope"] != SCOPE:
        raise ArithmeticError("explicit analytic fixture required")
    context = toy_context()
    controls: list[SourcePolicy] = []
    replies = {}
    for p in saved["controls"]:
        policy = unpack_policy(context.partition, p["policy"])
        control = SourcePolicy(p["case"], p["row"], policy)
        controls.append(control)
        for target in (0, 1):
            _, reply, _ = trace(
                context.partition,
                policy,
                target,
                tuple("TURN" for _ in context.partition.keys),
                1e-9,
            )
            replies[control.identifier, target] = reply
    config = saved["config"]
    contexts = {
        (g, r): context for g in config["spot_files"] for r in config["representations"]
    }
    data = HistoryInputs(
        config,
        Inputs(config, dict(scope=SCOPE), contexts, tuple(controls)),
        {},
        replies,
    )
    return inputs.Sources(
        root / "source-own.json", saved["own"], data, dict(scope=SCOPE)
    )


def job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    deadline = Deadline(payload["remaining_seconds"])
    sources = load(Path(payload["root"]))
    return evaluate_paths(indices, payload, send, sources, deadline)
