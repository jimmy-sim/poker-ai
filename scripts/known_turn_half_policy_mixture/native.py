"""Comparison-only pinned OpenSpiel scalar audit after own publication."""

import json
import math
import time
from pathlib import Path
from typing import Any

from river_generalization.native import installed_reference

from known_turn_half_policy_mixture.gate import (
    OWN,
    clean_head,
    require_own,
    source_fingerprint,
)
from known_turn_half_policy_mixture.own import _event, _rss_bytes, _save
from known_turn_half_policy_mixture.plan import ARMS, GAMES, contract, parent_context
from poker_ai.postflop.controlled_checkpoints import pack_policy, read_snapshot
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.range_reply import compare as own_compare
from poker_ai.postflop.river_study import Deadline
from poker_ai.solver_validation.matched_array_reference import ScalarReference, compare


def audit(root: Path, output: Path) -> None:
    """Compare only four saved mixed-policy scalars, retaining partial rows."""
    started = time.perf_counter()
    data = contract(root)
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_own(root, fingerprint)
    if output.exists():
        raise FileExistsError("retain prior half-mixture native attempt")
    output.mkdir(parents=True)
    _save(
        output / "started.json",
        {
            "status": "started",
            "head": head,
            "source_fingerprint": fingerprint,
            "reference": data["reference"],
            "reference_license_sha256": data["reference_license_sha256"],
        },
    )
    rows: list[dict[str, Any]] = []
    deadline = Deadline(780)
    try:
        runtime = installed_reference()
        own: dict[str, Any] = json.loads((root / OWN / "result.json").read_bytes())
        if own["status"] != "completed" or len(own["rows"]) != 4:
            raise ArithmeticError("four published own policies required")
        for index, game in enumerate(GAMES):
            deadline.check()
            saved = own["rows"][index]
            if saved["game"] != game or saved["index"] != index:
                raise ArithmeticError("published own grid changed")
            scoring = parent_context(root, game, ARMS[1])
            policy = read_snapshot(
                root / OWN / f"game{index:02d}-mixed.json.gz",
                scoring.exact,
                saved["receipt"],
                saved["metadata"],
            )
            score = scoring.score(policy)
            if own_compare(score_data(scoring, score), saved["score"]) > 1e-9:
                raise ArithmeticError("own mixed score changed before native audit")
            detail = {
                "policy": pack_policy(scoring.exact, policy),
                "metrics": score.metrics,
                "responses": score.responses,
                "replies": [
                    {
                        name: pack_policy(scoring.exact, reply)
                        for name, reply in group.items()
                    }
                    for group in score.replies
                ],
            }
            refs = ScalarReference(scoring.exact), ScalarReference(scoring.partition)
            native = compare(scoring, refs, detail)
            if (
                not math.isfinite(native["maximum_error_chips"])
                or native["maximum_error_chips"] > data["reference_tolerance_chips"]
            ):
                raise ArithmeticError("half-mixture independent scalar gate failed")
            row = {
                "index": index,
                "game": game,
                "own_policy_sha256": saved["receipt"]["policy_sha256"],
                "native": native,
                "peak_rss_bytes": _rss_bytes(),
            }
            _event(output / "events.jsonl", {"kind": "case", "row": row})
            rows.append(row)
            if _rss_bytes() >= data["peak_rss_bytes_exclusive"]:
                raise MemoryError("half-mixture native RSS cap reached")
        elapsed = time.perf_counter() - started
        if (
            len(rows) != 4
            or elapsed >= data["native_cap_seconds"]
            or _rss_bytes() >= data["peak_rss_bytes_exclusive"]
        ):
            raise ArithmeticError("half-mixture reference grid/cap failed")
        _save(
            output / "result.json",
            {
                "status": "completed",
                "head": head,
                "source_fingerprint": fingerprint,
                "seconds": elapsed,
                "reference_runtime": runtime,
                "peak_rss_bytes": _rss_bytes(),
                "rows": rows,
                "maximum_error_chips": max(
                    row["native"]["maximum_error_chips"] for row in rows
                ),
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
                "failure": {"type": type(error).__name__, "reason": str(error)},
            },
        )
        raise
