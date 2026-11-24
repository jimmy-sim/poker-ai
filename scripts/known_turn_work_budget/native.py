"""Pinned comparison-only OpenSpiel scalar checks after own publication."""

import json
import math
import os
import time
from pathlib import Path
from typing import Any

from river_generalization.native import installed_reference
from study_known_turn_work_budget import save
from turn_exact_transfer.capture import replay_path

from known_turn_work_budget.gate import (
    OWN,
    SOURCE,
    clean_revision,
    require_archive,
    source_fingerprint,
)
from known_turn_work_budget.plan import LABELS, READOUTS, context, contract, paths
from poker_ai.postflop.controlled_checkpoints import pack_policy, read_snapshot
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.range_reply import compare as own_compare
from poker_ai.postflop.river_study import Deadline
from poker_ai.solver_validation.matched_array_reference import ScalarReference, compare


def audit(root: Path, output: Path) -> None:
    """Check 4 paths × 3 work labels × 2 policies, retaining every row."""
    contract(root)
    head = clean_revision(root)
    fingerprint = source_fingerprint(root)
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    require_archive(root, root / OWN, "own_published", fingerprint)
    deadline = Deadline(780)
    output.mkdir(parents=True, exist_ok=False)
    events = output / "events.jsonl"
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    try:
        runtime = installed_reference()
        for spec in paths():
            deadline.check()
            scoring = context(root, spec.game, spec.arm)
            refs = ScalarReference(scoring.exact), ScalarReference(scoring.partition)
            folder = root / OWN / "study" / f"path{spec.index:02d}"
            summary = replay_path(scoring, folder)
            expected = dict(index=spec.index, game=spec.game, arm=spec.arm, seed=0)
            if (
                summary["path"] != expected
                or summary["labels"] != list(LABELS)
                or len(summary["captures"]) != 6
            ):
                raise ArithmeticError("fixed own path or captures changed")
            for saved in summary["captures"]:
                deadline.check()
                meta = saved["metadata"]
                if meta["work_label"] not in LABELS or meta["readout"] not in READOUTS:
                    raise ArithmeticError("unregistered saved policy")
                policy = read_snapshot(
                    folder / saved["file"], scoring.partition, saved["receipt"], meta
                )
                own = scoring.score(policy)
                if own_compare(score_data(scoring, own), saved["score"]) > 1e-9:
                    raise ArithmeticError("own scalar changed before native audit")
                detail = dict(
                    policy=pack_policy(scoring.partition, policy),
                    metrics=own.metrics,
                    responses=own.responses,
                    replies=[
                        {
                            name: pack_policy(scoring.exact, reply)
                            for name, reply in group.items()
                        }
                        for group in own.replies
                    ],
                )
                native = compare(scoring, refs, detail)
                if (
                    not math.isfinite(native["maximum_error_chips"])
                    or native["maximum_error_chips"] > 1e-9
                ):
                    raise ArithmeticError("fixed independent scalar gate failed")
                row = dict(
                    path_index=spec.index,
                    game=spec.game,
                    arm=spec.arm,
                    seed=0,
                    work_label=meta["work_label"],
                    readout=meta["readout"],
                    own_policy_sha256=saved["receipt"]["policy_sha256"],
                    native=native,
                )
                with events.open("a") as stream:
                    stream.write(
                        json.dumps(row, sort_keys=True, allow_nan=False) + "\n"
                    )
                    stream.flush()
                    os.fsync(stream.fileno())
                rows.append(row)
        if len(rows) != 24:
            raise ArithmeticError("24 fixed scalar checks missing")
        deadline.check()
        save(
            output / "result.json",
            dict(
                status="completed",
                head=head,
                source_fingerprint=fingerprint,
                runtime=runtime,
                seconds=time.perf_counter() - started,
                rows=rows,
                maximum_error_chips=max(
                    row["native"]["maximum_error_chips"] for row in rows
                ),
            ),
        )
    except BaseException as error:
        save(
            output / "failure.json",
            dict(
                status="failed_retained",
                head=head,
                source_fingerprint=fingerprint,
                completed_rows=len(rows),
                failure=dict(type=type(error).__name__, reason=str(error)),
            ),
        )
        raise
