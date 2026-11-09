"""Fixed batch-study inputs, path identities and original own prefix controls."""

import hashlib
import itertools
import json
from pathlib import Path
from typing import Any

from numpy.random import PCG64, Generator

from poker_ai.evaluation.averaging_history_inputs import HistoryInputs, load
from poker_ai.evaluation.controlled_reply_inputs import identity
from poker_ai.finite import ArrayTree
from poker_ai.postflop.controlled_training import Rules, Weight
from poker_ai.postflop.frozen_batches import BatchPoint, FrozenBatchTrainer
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import digest
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/frozen-pass-batches.json"
CONFIG_SHA256 = "91b2c1979257fe826477de172c279ff5a5f96553e3f177aac345187dabbeb02b"
ENTRIES = tuple(
    "scripts/" + name + "_frozen_batches.py"
    for name in ("check", "profile", "study", "audit", "report")
)
FORMAT = "poker-ai-frozen-pass-batches-v1"
PROFILE = "poker-ai-frozen-pass-batches-timing-v1"
CORRECTNESS = "poker-ai-frozen-pass-batches-software-v1"
ADMISSION = "poker-ai-frozen-pass-batches-admission-v1"
WEIGHTS: tuple[Weight, ...] = ("uniform", "linear")


def config_inputs(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA256:
        raise ArithmeticError("fixed batch protocol bytes changed")
    config: dict[str, Any] = json.loads((root / CONFIG).read_text())
    if any(digest(root / p) != h for p, h in config["input_sha256"].items()):
        raise ArithmeticError("batch prerequisite bytes changed")
    return config


def source(root: Path) -> dict[str, Any]:
    return source_provenance(root, root / CONFIG, entrypoints=ENTRIES)


def paths(config: dict[str, Any]) -> list[dict[str, Any]]:
    """B numeric-major order; each block has 24 paths and balanced seed slots."""
    return [
        dict(
            batch_size=batch,
            spot_file=game,
            representation=rep,
            regret_rule=clip,
            seed=seed,
        )
        for batch, game, rep, clip, seed in itertools.product(
            config["batch_sizes"],
            config["spot_files"],
            config["representations"],
            config["regret_rules"],
            config["seeds"],
        )
    ]


def case(path: dict[str, Any], weight: Weight) -> dict[str, Any]:
    return dict(
        spot_file=path["spot_file"],
        representation=path["representation"],
        traversal="external",
        seed=path["seed"],
        regret_rule=path["regret_rule"],
        regret_weight="linear",
        average_weight=weight,
        bridge="common",
    )


def trainer(tree: ArrayTree, path: dict[str, Any]) -> FrozenBatchTrainer:
    return FrozenBatchTrainer(
        tree,
        Generator(PCG64(path["seed"])),
        batch_size=path["batch_size"],
        rules=Rules(path["regret_rule"], "linear", "linear"),
    )


def prerequisites(root: Path) -> HistoryInputs:
    """Archived own source/context load only; no fallback fills enter training.

    Old native receipts are read as prerequisites without reference construction.
    The two fallback result files are pinned rationale bytes, not agent inputs.
    """
    config_inputs(root)
    return load(root)


def prefix_map(data: HistoryInputs, path: dict[str, Any]) -> dict[str, dict[int, Any]]:
    return {
        weight: {
            t: data.prefixes[identity(case(path, weight)), t]
            for t in data.config["original_average_replay_labels"]
        }
        for weight in WEIGHTS
    }


def check_prefix(
    solver: FrozenBatchTrainer,
    point: BatchPoint,
    label: int,
    original: dict[str, dict[int, Any]],
) -> list[dict[str, Any]]:
    if solver.batch_size != 1:
        raise ValueError("only B1 has an original prefix identity")
    tree, found = solver.tree, []
    weights: tuple[Weight, ...] = ("uniform", "linear")
    for weight in weights:
        peer = original[weight][label]
        state = solver.readout_fingerprint(weight)
        policy_hash = hashlib.sha256(
            tree.normalize(solver.ledger(weight)).astype("<f8").tobytes()
        ).hexdigest()
        actual = dict(
            iteration=point.iteration,
            previous_work=point.previous_work,
            total_work=point.total_work,
            last_iteration_visits=point.last_iteration_visits,
            initialization_visits=solver.initialization_visits,
            state_sha256=state,
        )
        if (
            any(not same(v, peer[k]) for k, v in actual.items())
            or policy_hash != peer["receipt"]["policy_sha256"]
        ):
            raise ArithmeticError("original B1 dual-book prefix changed")
        found.append(
            dict(
                average_weight=weight,
                work_label=label,
                original_id=peer["id"],
                policy_sha256=policy_hash,
                **actual,
            )
        )
    return found


def binding(root: Path) -> tuple[dict[str, Any], str]:
    current = source(root)
    if current["dirty"] is not False:
        raise ValueError("publish checked batch source before measurement")
    return current, sha(current["sha256"])
