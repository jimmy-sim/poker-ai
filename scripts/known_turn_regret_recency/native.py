"""Comparison-only OpenSpiel scalars for the two new candidate paths."""

import json
import math
import os
import time
from pathlib import Path
from typing import Any

from river_generalization.native import installed_reference
from study_known_turn_regret_recency import save
from turn_exact_transfer.capture import replay_path

from known_turn_regret_recency.gate import (
    OWN,
    SOURCE,
    clean_head,
    require_archive,
    source_fingerprint,
)
from known_turn_regret_recency.plan import context, contract, paths
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
    contract(root)
    head = clean_head(root)
    source = source_fingerprint(root)
    require_archive(root, root / SOURCE, "source_qualified", source)
    require_archive(root, root / OWN, "own_published", source)
    deadline = Deadline(900)
    output.mkdir(parents=True, exist_ok=False)
    events = output / "events.jsonl"
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    try:
        runtime = installed_reference()
        for spec in paths():
            index, game, arm = spec.index, spec.game, spec.arm
            deadline.check()
            scoring = context(root, game)
            refs = ScalarReference(scoring.exact), ScalarReference(scoring.partition)
            folder = root / OWN / "study" / f"path{index:02d}"
            summary = replay_path(scoring, folder)
            expected = dict(index=index, game=game, arm=arm, seed=spec.seed)
            if summary["path"] != expected:
                raise ArithmeticError("own path identity changed")
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
                    raise ArithmeticError("independent recency scalar gate failed")
                row = dict(
                    path_index=index,
                    game=game,
                    arm=arm,
                    seed=spec.seed,
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
            raise ArithmeticError("missing fixed recency scalar comparisons")
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
