"""Fresh reference-free compact training workers; no saved policies imported."""

import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.compact_opponent_contexts import build_game
from poker_ai.evaluation.compact_opponent_contract import FOLDER, contract, input_pins
from poker_ai.evaluation.compact_opponent_guard import isolated
from poker_ai.evaluation.compact_opponent_source import source
from poker_ai.evaluation.opponent_learning_capture import collect
from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.evaluation.opponent_learning_design import (
    REAL,
    TOY,
    TOY_WORK,
    WORK,
    Design,
)
from poker_ai.postflop.cell_process import Send, partition
from poker_ai.postflop.compact_full_artifacts import published
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline, digest

ADMISSION = FOLDER + "/admission.json"


def worker_admission(root: Path, binding: str, expected: str) -> None:
    """Parent checks all proof/forecast gates; worker binds its unchanged permit."""
    path = root / ADMISSION
    saved = json.loads(path.read_text())
    config = contract(root)
    if (
        digest(path) != expected
        or saved["source_sha256"] != binding
        or saved["status"] != "compact_own_opponent_learning_admitted"
        or saved["long_run_admitted"] is not True
        or saved["new_agent_default"] is not False
        or saved["fresh_global_admission"] is not False
        or saved["maximum_own_seconds"] != 7200
        or saved["maximum_native_seconds"] != 900
        or sys.version.split()[0] != config["prefix_runtime"]["python"]
        or np.__version__ != config["prefix_runtime"]["numpy"]
    ):
        raise ArithmeticError(
            "worker needs the unchanged checked original-runtime permit"
        )
    published(root, path)


def training(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    with isolated(worker=True):
        return _training(slot, indices, payload, send)


def _training(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    required = {
        "root",
        "source_sha256",
        "scope",
        "admission_sha256",
        "scratch",
        "deadline_started",
        "context_sha256",
    }
    if set(payload) != required:
        raise ValueError("worker accepts only structural/source/clock inputs")
    if (
        type(slot) is not int
        or not 0 <= slot < 3
        or not same(indices, partition(30, 3)[slot])
    ):
        raise ValueError("worker must execute its complete fixed path partition")
    root = Path(payload["root"])
    binding = payload["source_sha256"]
    if sha(source(root)["sha256"]) != binding:
        raise ArithmeticError("worker differs from checked source")
    scope = payload["scope"]
    if scope not in (TOY, REAL):
        raise ValueError("cost stand-ins cannot enter the learning worker")
    design = Design(scope, TOY_WORK if scope == TOY else WORK)
    if scope == REAL:
        worker_admission(root, binding, payload["admission_sha256"])
        input_pins(root)
    deadline = Deadline(180 if scope == TOY else 7200)
    if (
        type(payload["deadline_started"]) not in (int, float)
        or not math.isfinite(payload["deadline_started"])
        or not 0 < payload["deadline_started"] <= time.perf_counter()
    ):
        raise ValueError("worker needs the original finite command clock")
    deadline.started = payload["deadline_started"]
    games = (
        (software_context(0), software_context(1))
        if scope == TOY
        else (build_game(root, 0), build_game(root, 1))
    )
    actual = [
        {
            kind: tree_digest(c.tree(kind))
            for kind in ("coarse", "mixed0", "mixed1", "fine")
        }
        for c in games
    ]
    if not same(actual, payload["context_sha256"]):
        raise ArithmeticError("worker source/context factory changed the finite games")
    send(dict(kind="prepared", phase="same_source_games_built", scope=scope))
    for index in indices:
        deadline.check()
        path = design.path(index)
        send(dict(kind="cell", phase="path_started", index=index, path=path))
        result = collect(
            games[path["coordinate"] // 3].tree(path["tree_kind"]),
            design,
            index,
            Path(payload["scratch"]),
            binding,
            send,
            deadline,
        )
        summary = {
            k: v for k, v in result.items() if k not in {"captures", "masses", "warm"}
        }
        send(dict(kind="cell", phase="path_finished", index=index, result=summary))
    return dict(paths=len(indices), scope=scope)
