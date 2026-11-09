"""Explicit nonuniform-Kuhn software fixtures, never Hold'em research results."""

import copy
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.averaging_history_training import train_one
from poker_ai.evaluation.controlled_reply_inputs import (
    Inputs,
    SourcePolicy,
    expected,
    identity,
    modes,
)
from poker_ai.evaluation.controlled_reply_math import cross, trace
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.node_profile import trainer
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.row_profile import fingerprint
from poker_ai.postflop.training_isolation import sentinel_tree


def toy_context() -> ScoringContext:
    tree = sentinel_tree()
    zero = np.zeros(len(tree.keys), dtype=np.bool_)
    return ScoringContext(
        tree, tree, np.arange(len(tree.keys), dtype=np.int64), (zero, zero)
    )


def software_inputs(config: dict[str, Any], deadline: Deadline) -> HistoryInputs:
    """Generate independent unobserved baselines for a full explicit toy grid.

    Same logical inventory as the new IO wrapper, different tiny toy work labels
    and deliberately marked game names. No real spot, native solver or original
    Hold'em training is loaded; these values must never appear in research tables.
    """
    config = copy.deepcopy(config)
    config["status"] = "EXPLICIT_SOFTWARE_FIXTURE_NOT_POKER_RESULTS"
    config["spot_files"] = ["EXPLICIT_TOY_LOW", "EXPLICIT_TOY_MEDIUM"]
    context = toy_context()
    initial = 2 * len(context.partition.player)
    labels = [initial + k for k in (1000, 2000, 3000, 4000, 5000)]
    config.update(
        source_target=labels[-1],
        current_work_labels=labels,
        original_average_replay_labels=[labels[0], labels[2], labels[4]],
        cumulative_mass_work_labels=labels[2:],
        suffix_windows=[[labels[2], labels[4]], [labels[3], labels[4]]],
    )
    policies, prefixes, replies = [], {}, {}
    cases = [
        dict(json.loads(k), bridge="common", regret_weight="linear")
        for k in sorted(expected(config))
    ]
    for index, case in enumerate(cases):
        deadline.check()
        # Plain dense implementation is separate from the observed cached backend.
        solver = trainer(context.partition, case, "parent")
        solver.initialize_exact()
        identifier = identity(case)
        final = {}
        for label in config["original_average_replay_labels"]:
            previous = solver.nodes_visited
            while solver.nodes_visited < label:
                deadline.check()
                previous = solver.nodes_visited
                solver.step()
            final = dict(
                id=f"EXPLICIT-toy-source-{index}-work-{label}",
                index=index,
                case=case,
                iteration=solver.iteration,
                previous_work=previous,
                total_work=solver.nodes_visited,
                last_iteration_visits=solver.nodes_visited - previous,
                initialization_visits=solver.initialization_visits,
                state_sha256=fingerprint(solver),
                receipt=dict(policy_sha256=array_sha(solver.average_policy)),
                **score_data(context, context.score(solver.average_policy)),
            )
            prefixes[identifier, label] = final
        policy = solver.average_policy.copy()
        policy.flags.writeable = False
        source = SourcePolicy(case, final, policy)
        policies.append(source)
        for target in (0, 1):
            _, reply, _ = trace(
                context.partition,
                policy,
                target,
                ("TURN",) * len(context.partition.keys),
                1e-9,
            )
            replies[identifier, target] = reply
    contexts = {
        (game, name): context
        for game in config["spot_files"]
        for name in config["representations"]
    }
    return HistoryInputs(
        config,
        Inputs(config, {"rows": list(prefixes.values())}, contexts, tuple(policies)),
        prefixes,
        replies,
    )


def software_controls(root: Path, data: HistoryInputs) -> Path:
    """Own toy controls only, explicitly not an independent native audit."""
    controls = []
    order = {m: i for i, m in enumerate(modes(data.config))}
    for group in sorted({p.group for p in data.base.policies}):
        members = sorted(
            (p for p in data.base.policies if p.group == group),
            key=lambda p: order[p.mode],
        )
        for a in members:
            for b in members:
                result = cross(
                    data.base.context(a.case).partition,
                    a.policy,
                    b.policy,
                    data.replies[b.identifier, 0],
                    data.replies[a.identifier, 1],
                    tolerance=1e-9,
                )
                for target, response in enumerate(result["responses"]):
                    own, opponent = (a, b) if target == 0 else (b, a)
                    response.update(
                        own_profile_id=own.identifier,
                        opponent_profile_id=opponent.identifier,
                    )
                controls.append(result)
    path = root / "results/controlled-replies/own.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        raise FileExistsError("retain explicit software controls")
    path.write_text(
        json.dumps(
            dict(scope="EXPLICIT_SOFTWARE_FIXTURE_NO_NATIVE_AUDIT", crosses=controls),
            sort_keys=True,
        )
        + "\n"
    )
    return path


def software_job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    """Spawn-safe IO/trajectory correctness job that cannot load poker spots."""
    del slot
    context = toy_context()
    deadline = Deadline(payload["remaining_seconds"])
    started = time.perf_counter()
    send(dict(kind="prepared", seconds=time.perf_counter() - started))
    for index in indices:
        cell = payload["cells"][index]
        if not cell["case"]["spot_file"].startswith("EXPLICIT_TOY_"):
            raise ValueError("software fixture cannot run a real poker spot")
        train_one(
            context,
            cell["case"],
            cell["source_id"],
            index,
            cell["prefixes"],
            payload["config"],
            Path(payload["scratch"]),
            payload["binding"],
            deadline,
            send,
        )
    return dict(
        cells=len(indices),
        profiles=8 * len(indices),
        masses=3 * len(indices),
        prefixes=3 * len(indices),
    )
