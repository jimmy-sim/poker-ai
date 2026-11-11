"""One fixed three-process training path for tiny proofs and admitted real work."""

import json
import math
import sys
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np

from poker_ai.evaluation.opponent_learning_capture import collect
from poker_ai.evaluation.opponent_learning_contexts import Contexts, software_context
from poker_ai.evaluation.opponent_learning_design import (
    REAL,
    TOY,
    TOY_WORK,
    WORK,
    Design,
)
from poker_ai.evaluation.opponent_learning_gate import committed, source
from poker_ai.evaluation.opponent_learning_sources import (
    build_game,
    contract,
    input_pins,
)
from poker_ai.postflop.cell_process import Send, partition
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline, digest

ADMISSION = "results/opponent-information/admission.json"


def worker_admission(root: Path, binding: str, expected: str) -> None:
    """Parent checks all proof/forecast gates; worker binds its unchanged permit."""
    path = root / ADMISSION
    saved = json.loads(path.read_text())
    config = contract(root)
    if (
        digest(path) != expected
        or saved["source_sha256"] != binding
        or saved["status"] != "own_opponent_learning_admitted"
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
    committed(root, path)


def training(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("own worker constructed a reference")

    with (
        patch("poker_ai.solver_validation.reference.Reference.__init__", forbidden),
        patch(
            "poker_ai.solver_validation.matched_array_reference.ScalarReference.__init__",
            forbidden,
        ),
    ):
        return _training(slot, indices, payload, send)


def _training(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
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


def gather(batch: dict[str, Any], design: Design) -> list[dict[str, Any]]:
    assignments = partition(30, 3)
    if (
        batch["status"] != "completed"
        or batch["failure"] is not None
        or not same(batch["worker_count"], 3)
        or not same(batch["assignments"], assignments)
        or len(batch["workers"]) != 3
    ):
        raise ArithmeticError("complete fixed three-process learning batch required")
    results = {}
    for slot, worker in enumerate(batch["workers"]):
        done = [e for e in worker["messages"] if e["kind"] == "done"]
        if (
            not same(worker["slot"], slot)
            or not same(worker["exitcode"], 0)
            or len(done) != 1
            or not same(done[0]["summary"]["paths"], len(assignments[slot]))
            or done[0]["summary"]["scope"] != design.scope
            or any(e["kind"] == "error" for e in worker["messages"])
        ):
            raise ArithmeticError(
                "learning worker did not complete its fixed partition"
            )
        cells = [e for e in worker["messages"] if e["kind"] == "cell"]
        if any(
            e["phase"]
            not in ("path_started", "path_finished", "warm", "capture", "mass")
            for e in cells
        ):
            raise ArithmeticError("unknown own learning event phase")
        if any(
            type(e["index"]) is not int or e["index"] not in assignments[slot]
            for e in cells
        ):
            raise ArithmeticError("learning event outside assigned path partition")
        for index in assignments[slot]:
            events = [e for e in cells if e["index"] == index]
            starts = [e for e in events if e["phase"] == "path_started"]
            finishes = [e for e in events if e["phase"] == "path_finished"]
            warms = [e["row"] for e in events if e["phase"] == "warm"]
            if (
                len(starts) != 1
                or len(finishes) != 1
                or len(warms) != 1
                or not same(starts[0]["path"], design.path(index))
            ):
                raise ArithmeticError(
                    "exactly one initialization and completion per path required"
                )
            if not same(finishes[0]["result"]["path"], design.path(index)):
                raise ArithmeticError("worker completion changed its path identity")
            if any(not same(warms[0].get(k), v) for k, v in design.path(index).items()):
                raise ArithmeticError(
                    "warm initialization event changed its path identity"
                )
            results[index] = dict(
                finishes[0]["result"],
                warm=warms[0],
                captures=[e["row"] for e in events if e["phase"] == "capture"],
                masses=[e["row"] for e in events if e["phase"] == "mass"],
            )
    if set(results) != set(range(30)):
        raise ArithmeticError("all thirty actual paths required")
    paths = [results[i] for i in range(30)]
    design.require_rows("captures", [r for p in paths for r in p["captures"]])
    design.require_rows("masses", [r for p in paths for r in p["masses"]])
    return paths


def independent(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    """The same three-worker scalar path for software, costs and real audits."""
    if (
        type(slot) is not int
        or not 0 <= slot < 3
        or not same(indices, partition(6, 3)[slot])
    ):
        raise ValueError("native worker needs its complete fixed coordinate partition")
    root, own_path = Path(payload["root"]), Path(payload["own"])
    binding = payload["source_sha256"]
    if (
        sha(source(root)["sha256"]) != binding
        or digest(own_path) != payload["own_sha256"]
    ):
        raise ArithmeticError("native worker source or published own receipt changed")
    committed(root, own_path)
    own = json.loads(own_path.read_text())
    if (
        own["source_sha256"] != binding
        or own["status"] != "completed_own_native_pending"
        or own["reference_constructed"] is not False
        or payload["publication"]["own_sha256"] != digest(own_path)
    ):
        raise ArithmeticError("native worker requires the published own checkpoint")
    scope = own["scope"]
    design = Design(scope, TOY_WORK if scope == TOY else WORK)
    deadline = Deadline(180 if scope == TOY else 900)
    if (
        type(payload["deadline_started"]) not in (int, float)
        or not math.isfinite(payload["deadline_started"])
        or not 0 < payload["deadline_started"] <= time.perf_counter()
    ):
        raise ArithmeticError("native worker needs original complete command clock")
    deadline.started = payload["deadline_started"]
    from poker_ai.evaluation.opponent_learning_own import fixture
    from poker_ai.evaluation.opponent_learning_sources import load
    from poker_ai.solver_validation.controlled_pipeline import license_record
    from poker_ai.solver_validation.opponent_learning import audit

    license_record(contract(root))
    if scope == TOY:
        games, opponents = fixture()
    else:
        sources = load(root)
        games, opponents = sources.games, sources.opponents

    def context_for(coordinate: int) -> Contexts:
        design.coordinate(coordinate)
        return games[coordinate // 3]

    result = audit(
        own_path.parent,
        own,
        design,
        context_for,
        opponents,
        send,
        deadline,
        tuple(indices),
    )
    return dict(
        scope=scope,
        profiles=len(result["profiles"]),
        fixed_conditions=len(result["fixed_conditions"]),
        maximum_error_chips=result["maximum_error_chips"],
    )


def gather_independent(batch: dict[str, Any], own: dict[str, Any]) -> dict[str, Any]:
    from poker_ai.solver_validation.opponent_learning import validate_rows

    assignments = partition(6, 3)
    if (
        batch["status"] != "completed"
        or batch["failure"] is not None
        or not same(batch["worker_count"], 3)
        or not same(batch["assignments"], assignments)
        or len(batch["workers"]) != 3
    ):
        raise ArithmeticError("complete fixed three-process independent audit required")
    profiles, fixed = [], []
    for slot, worker in enumerate(batch["workers"]):
        done = [e for e in worker["messages"] if e["kind"] == "done"]
        if (
            not same(worker["slot"], slot)
            or not same(worker["exitcode"], 0)
            or len(done) != 1
            or done[0]["summary"]["scope"] != own["scope"]
            or not same(done[0]["summary"]["profiles"], 144)
            or not same(done[0]["summary"]["fixed_conditions"], 384)
            or any(e["kind"] == "error" for e in worker["messages"])
        ):
            raise ArithmeticError(
                "independent worker did not finish its full inventory"
            )
        rows: list[dict[str, Any]] = []
        targets: list[dict[str, Any]] = []
        for e in worker["messages"]:
            if e["kind"] != "cell":
                continue
            if (
                e["phase"] not in ("self", "fixed")
                or type(e["index"]) is not int
                or e["index"] not in assignments[slot]
                or not same(e["result"]["coordinate"], e["index"])
            ):
                raise ArithmeticError("independent event outside fixed coordinates")
            (rows if e["phase"] == "self" else targets).append(e["result"])
        if len(rows) != 144 or len(targets) != 384:
            raise ArithmeticError("independent worker omitted profile or fixed results")
        if not same(
            max(r["maximum_error_chips"] for r in rows + targets),
            done[0]["summary"]["maximum_error_chips"],
        ):
            raise ArithmeticError("independent worker maximum changed")
        profiles.extend(rows)
        fixed.extend(targets)
    # Stable identity order matches complete own inventories, not process arrival.
    p = {r["id"]: r for r in profiles}
    f = {r["condition_id"]: r for r in fixed}
    if len(p) != len(profiles) or len(f) != len(fixed):
        raise ArithmeticError("duplicate independent profile or fixed condition")
    result = dict(
        profiles=[p[r["id"]] for r in own["rows"]],
        fixed_conditions=[f[r["condition_id"]] for r in own["fixed_conditions"]],
        maximum_error_chips=max(r["maximum_error_chips"] for r in profiles + fixed),
        coordinates=list(range(6)),
        reference_actions_exported=False,
        reference_output_used_in_training=False,
        training_performed=False,
    )
    validate_rows(result, own)
    return result
