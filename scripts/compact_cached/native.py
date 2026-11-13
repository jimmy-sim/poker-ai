"""Three-process independent scalar comparison, never a training target."""

import json
import math
import time
from pathlib import Path
from typing import Any

from compact_cached.cache import cached, check_execution
from compact_cached.contract import CONFIG_SHA, contract
from compact_cached.source import source
from poker_ai.evaluation.opponent_learning_contexts import Contexts
from poker_ai.evaluation.opponent_learning_design import TOY, TOY_WORK, WORK, Design
from poker_ai.postflop.cell_process import Send, partition
from poker_ai.postflop.compact_full_artifacts import published
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline, digest


def _independent(
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
    published(root, own_path)
    own = json.loads(own_path.read_text())
    if (
        own["source_sha256"] != binding
        or own["status"] != "completed_own_native_pending"
        or own["reference_constructed"] is not False
        or payload["publication"]["own_sha256"] != digest(own_path)
    ):
        raise ArithmeticError("native worker requires the published own checkpoint")
    check_execution(root, own)
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
    from poker_ai.evaluation.compact_opponent_sources import load
    from poker_ai.evaluation.opponent_learning_own import fixture
    from poker_ai.solver_validation.controlled_pipeline import license_record
    from poker_ai.solver_validation.opponent_learning import audit

    license_record(contract(root))
    if scope == TOY:
        games, opponents = fixture()
    else:
        sources = load(root, deadline)
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


def independent(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    with cached(Path(payload["root"])) as cache:
        result = _independent(slot, indices, payload, send)
        return dict(
            result, validation_cache=cache.summary(), implementation_sha256=CONFIG_SHA
        )
