"""Comparison-only OpenSpiel scalars for published full-pass policies."""

import json
import math
import os
import time
from pathlib import Path
from typing import Any

from river_generalization.native import installed_reference

from medium_dry_full.capture import replay_path
from medium_dry_full.gate import (
    OWN,
    SOURCE,
    clean_head,
    fingerprint,
    fixed_contract,
    paths,
    require_stage,
)
from medium_dry_full.learning import context
from medium_dry_full.study import save
from poker_ai.postflop.controlled_checkpoints import pack_policy, read_snapshot
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.range_reply import compare as own_compare
from poker_ai.postflop.river_study import Deadline
from poker_ai.solver_validation.matched_array_reference import (
    ScalarReference,
    compare,
)


def audit(root: Path, output: Path) -> None:
    """Check all 12 saved scalar rows after own publication, retaining each."""
    fixed_contract(root)
    head = clean_head(root)
    source = fingerprint(root)
    require_stage(root, SOURCE, "source_qualified")
    require_stage(root, OWN, "own_published")
    deadline = Deadline(900)
    output.mkdir(parents=True, exist_ok=False)
    events = output / "events.jsonl"
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    try:
        runtime = installed_reference()
        for index, game, arm in paths():
            deadline.check()
            scoring = context(root, game, arm)
            refs = ScalarReference(scoring.exact), ScalarReference(scoring.partition)
            folder = root / OWN / "study" / f"path{index:02d}"
            summary = replay_path(scoring, folder)
            if summary["path"] != dict(index=index, game=game, arm=arm):
                raise ArithmeticError("candidate own path identity changed")
            for saved in summary["captures"]:
                deadline.check()
                policy = read_snapshot(
                    folder / saved["file"],
                    scoring.partition,
                    saved["receipt"],
                    saved["metadata"],
                )
                own = scoring.score(policy)
                if own_compare(score_data(scoring, own), saved["score"]) > 1e-9:
                    raise ArithmeticError("own scalar changed before native check")
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
                    raise ArithmeticError("independent full-pass scalar gate failed")
                row = dict(
                    path_index=index,
                    game=game,
                    arm=arm,
                    work_label=saved["metadata"]["work_label"],
                    readout=saved["metadata"]["readout"],
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
        if len(rows) != 12:
            raise ArithmeticError("missing fixed full-pass scalar comparisons")
        deadline.check()
        save(
            output / "result.json",
            dict(
                status="completed",
                head=head,
                source_fingerprint=source,
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
                source_fingerprint=source,
                completed_rows=len(rows),
                failure=dict(type=type(error).__name__, reason=str(error)),
            ),
        )
        raise
