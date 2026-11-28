"""One capped four-game read of the fixed saved policies and own exact scores."""

import json
import math
import os
import resource
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

from known_turn_half_policy_mixture.gate import (
    clean_head,
    require_admission,
    source_fingerprint,
)
from known_turn_half_policy_mixture.math import half_mix
from known_turn_half_policy_mixture.plan import (
    ARMS,
    GAMES,
    contract,
    parent_context,
    parent_policy,
)
from poker_ai.postflop.controlled_checkpoints import write_snapshot
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment


def _save(path: Path, record: dict[str, Any]) -> None:
    """Write a new immutable result or failure record and flush it durably."""
    with path.open("x") as stream:
        json.dump(record, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def _event(path: Path, record: dict[str, Any]) -> None:
    """Append each completed game before the next input is opened."""
    with path.open("a") as stream:
        stream.write(json.dumps(record, sort_keys=True, allow_nan=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _rss_bytes() -> int:
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (
        1 if sys.platform == "darwin" else 1024
    )


def _same_exact_game(a: Any, b: Any) -> None:
    """Reject any change to chance, payoff, legal menu or information owner."""
    if a.keys != b.keys or a.actions != b.actions:
        raise ArithmeticError("parent exact information/actions changed")
    for name in (
        "children",
        "valid",
        "player",
        "information",
        "chance_edges",
        "chance_reach",
        "terminal_values",
        "legal",
        "owners",
    ):
        if not np.array_equal(getattr(a, name), getattr(b, name)):
            raise ArithmeticError("parent exact game changed: " + name)


def run(root: Path, output: Path) -> None:
    """Build exactly four 50:50 exact policies, retaining every partial/failure."""
    started = time.perf_counter()
    data = contract(root)
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_admission(root, fingerprint)
    if output.exists():
        raise FileExistsError("retain any prior half-mixture own attempt")
    output.mkdir(parents=True)
    events = output / "events.jsonl"
    _save(
        output / "started.json",
        {
            "status": "started",
            "head": head,
            "source_fingerprint": fingerprint,
            "runtime": runtime_environment(),
            "input_count": 8,
            "game_count": 4,
        },
    )
    deadline = Deadline(780)
    rows: list[dict[str, Any]] = []
    try:
        for index, game in enumerate(GAMES):
            deadline.check()
            q8 = parent_context(root, game, ARMS[0])
            exact = parent_context(root, game, ARMS[1])
            _same_exact_game(q8.exact, exact.exact)
            if len(exact.exact.keys) != 8340 or len(exact.partition.keys) != 8340:
                raise ArithmeticError("fixed exact information row count changed")
            control = parent_policy(root, data["inputs"][2 * index], q8)
            other = parent_policy(root, data["inputs"][2 * index + 1], exact)
            lifted = q8.expand(control)
            mixed = half_mix(lifted, other, exact.exact.legal)
            exact.exact.validate_policy(mixed)
            if _rss_bytes() >= data["peak_rss_bytes_exclusive"]:
                raise MemoryError("half-mixture RSS cap reached")
            metadata = {
                "game": game,
                "index": index,
                "source_fingerprint": fingerprint,
                "control_policy_sha256": data["inputs"][2 * index]["policy_sha256"],
                "other_policy_sha256": data["inputs"][2 * index + 1]["policy_sha256"],
                "weight_control": 0.5,
                "weight_other": 0.5,
                "readout": "linear_average",
                "work_label": 40_000_000,
            }
            receipt = write_snapshot(
                output / f"game{index:02d}-mixed.json.gz", exact.exact, mixed, metadata
            )
            deadline.check()
            own = exact.score(mixed)
            score = score_data(exact, own)
            value = score["metrics"]["exact_exploitability_chips"]
            if not math.isfinite(value) or value < -data["arithmetic_tolerance_chips"]:
                raise ArithmeticError("invalid own exact exploitability")
            row = {
                "index": index,
                "game": game,
                "metadata": metadata,
                "receipt": receipt,
                "score": score,
                "exploitability_fraction_initial_pot": value / 36,
                "peak_rss_bytes": _rss_bytes(),
                "elapsed_seconds": time.perf_counter() - started,
            }
            _event(events, {"kind": "case", "row": row})
            rows.append(row)
            if _rss_bytes() >= data["peak_rss_bytes_exclusive"]:
                raise MemoryError("half-mixture RSS cap reached")
        elapsed = time.perf_counter() - started
        if len(rows) != 4 or elapsed >= data["own_cap_seconds"]:
            raise ArithmeticError("half-mixture fixed own grid/cap failed")
        _save(
            output / "result.json",
            {
                "status": "completed",
                "head": head,
                "source_fingerprint": fingerprint,
                "seconds": elapsed,
                "peak_rss_bytes": _rss_bytes(),
                "rows": rows,
            },
        )
    except BaseException as error:
        _save(
            output / "failure.json",
            {
                "status": "failed_retained",
                "head": head,
                "source_fingerprint": fingerprint,
                "completed_rows": len(rows),
                "seconds": time.perf_counter() - started,
                "peak_rss_bytes": _rss_bytes(),
                "failure": {"type": type(error).__name__, "reason": str(error)},
            },
        )
        raise
