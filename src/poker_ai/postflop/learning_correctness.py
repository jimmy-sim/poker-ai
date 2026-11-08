"""Source-bound toy trajectory/storage/contrast receipt before poker learning."""

import itertools
import json
import time
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.postflop import controlled_profile, learning_protocol, node_profile
from poker_ai.postflop.controlled_checkpoints import (
    Observation,
    observe,
    write_snapshot,
)
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_analysis import FACTORS, LEVELS, contrasts
from poker_ai.postflop.learning_artifacts import decode, sha
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.row_profile import assert_equal
from poker_ai.postflop.training_isolation import sentinel_tree
from poker_ai.validation.five_card import source_provenance


def evidence(scratch: Path) -> dict[str, Any]:
    tree = sentinel_tree()
    empty = np.zeros(len(tree.keys), dtype=np.bool_)
    context = ScoringContext(tree, tree, np.arange(len(tree.keys)), (empty, empty))
    trajectories: list[dict[str, Any]] = []
    snapshots = 0
    for traversal, warm, clip, rw, aw in itertools.product(
        ["full", "external"],
        [False, True],
        ["signed", "clipped"],
        ["uniform", "linear"],
        ["uniform", "linear"],
    ):
        cell = dict(
            traversal=traversal,
            bridge="common",
            seed=20261301,
            regret_rule=clip,
            regret_weight=rw,
            average_weight=aw,
        )
        engine = "nodes" if traversal == "external" else "parent"
        a, b = (node_profile.trainer(tree, cell, engine) for _ in range(2))
        if warm:
            a.initialize_exact()
            b.initialize_exact()
        packets: list[Observation] = []
        observe(a, [150, 500], [2, 4, 8], empty, packets.append, Deadline(10))
        while b.iteration < a.iteration:
            b.step()
        signature = assert_equal(a, b)
        for number, packet in enumerate(packets):
            metadata = dict(
                id=f"toy-{len(trajectories)}-{number}",
                **score_data(context, context.score(packet.policy)),
            )
            path = scratch / (metadata["id"] + ".json.gz")
            receipt = write_snapshot(path, tree, packet.policy, metadata)
            detail = decode(
                path.read_bytes(),
                context,
                dict(
                    id=metadata["id"],
                    metrics=metadata["metrics"],
                    receipt=receipt,
                    metadata_sha256=sha(metadata),
                ),
            )
            if detail["policy"] != [
                packet.policy[i, : len(menu)].tolist()
                for i, menu in enumerate(tree.actions)
            ]:
                raise ArithmeticError("toy checkpoint storage changed policy")
            snapshots += 1
        trajectories.append(
            dict(
                **cell,
                warm=warm,
                iteration=a.iteration,
                work=a.nodes_visited,
                state_sha256=signature,
                snapshots=len(packets),
            )
        )
    # Explicit synthetic polynomial: y=7+2*z0+3*z0*z2-2*z1*z2*z3+5*z0*z1*z2*z3.
    values = {}
    for levels in LEVELS:
        z = [
            -1 if levels[i] == pair[0] else 1 for i, pair in enumerate(FACTORS.values())
        ]
        values[levels] = (
            7.0
            + 2 * z[0]
            + 3 * z[0] * z[2]
            - 2 * z[1] * z[2] * z[3]
            + 5 * np.prod(z).item()
        )
    effects = contrasts(values)
    expected = {
        ("traversal",): 4.0,
        ("traversal", "regret_weight"): 12.0,
        ("regret_rule", "regret_weight", "average_weight"): -16.0,
        tuple(FACTORS): 80.0,
    }
    if any(
        r["difference"] != expected.get(tuple(r["factors"]), 0.0)
        for r in effects["factorial"]
    ):
        raise ArithmeticError("synthetic factorial normalization changed")
    return dict(
        trajectories=trajectories,
        trajectory_count=len(trajectories),
        own_snapshot_roundtrips=snapshots,
        synthetic_contrasts=effects,
        postflop_training_performed=False,
    )


def run(root: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain correctness receipt")
    config, _, _ = learning_protocol.inputs(root)
    provenance = source_provenance(
        root, root / learning_protocol.CONFIG, entrypoints=learning_protocol.ENTRIES
    )
    if provenance["dirty"] is not False:
        raise ValueError("publish runner before correctness receipt")
    started = time.perf_counter()
    scratch = (
        root / "results/runs/controlled-learning-correctness" / str(time.time_ns())
    )
    scratch.mkdir(parents=True, exist_ok=False)
    controlled_profile.replay_correctness(
        root, root / "results/training-isolation/correctness.json"
    )
    result = dict(
        format=learning_protocol.CORRECTNESS,
        status="passed_toy_correctness_no_postflop_learning",
        config=config,
        source=provenance,
        **evidence(scratch),
        seconds=time.perf_counter() - started,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, sort_keys=True, indent=2, allow_nan=False) + "\n"
    )
    return result
