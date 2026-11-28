"""Data-only cap admission and comparison-only OpenSpiel candidate audit."""

import json
import math
import os
import time
from pathlib import Path
from typing import Any

from river_generalization.gate import require_archive
from river_generalization.native import installed_reference
from turn_exact_transfer.capture import replay_path

from known_turn_uniform_regret_transfer.gate import (
    AUDIT_ADMISSION,
    OWN,
    clean_head,
    require_own,
    source_fingerprint,
)
from known_turn_uniform_regret_transfer.plan import (
    LABELS,
    READOUTS,
    context,
    contract,
    paths,
)
from poker_ai.postflop.controlled_checkpoints import pack_policy, read_snapshot
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.range_reply import compare as own_compare
from poker_ai.postflop.river_study import Deadline
from poker_ai.solver_validation.matched_array_reference import ScalarReference, compare

PRIOR_CLOCK = Path("results/known-turn-collision-medium-transfer/native/job-state.json")


def save(path: Path, value: dict[str, Any]) -> None:
    """Create a durable, never-overwritten result or failure."""
    with path.open("x") as stream:
        json.dump(value, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())


def audit_forecast(root: Path) -> dict[str, Any]:
    """Apply only the fixed 48-to-24 data-only native timing bound."""
    contract(root)
    clock: dict[str, Any] = json.loads((root / PRIOR_CLOCK).read_bytes())
    seconds = clock["observed_wall_seconds"]
    if clock["status"] != "passed" or not math.isfinite(seconds) or seconds <= 0:
        raise ArithmeticError("prior pinned native clock invalid")
    ceil_millis = math.ceil(seconds * 1000) / 1000
    bound = 2 * ceil_millis + 120
    return dict(
        status="admitted" if bound < 900 else "rejected",
        prior_clock_seconds=seconds,
        prior_ceil_millis_seconds=ceil_millis,
        strict_bound_seconds=bound,
        native_cap_seconds=900,
        candidate_cases=24,
        prior_cases=48,
        reserve_within_cap_seconds=120,
    )


def admit(root: Path, output: Path) -> None:
    """Publish the independent data-only audit admission before reference use."""
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_own(root, fingerprint)
    output.mkdir(parents=True, exist_ok=False)
    decision = audit_forecast(root)
    save(output / "decision.json", decision)
    save(
        output / "receipt.json",
        dict(head=head, source_fingerprint=fingerprint, status=decision["status"]),
    )
    if decision["status"] != "admitted":
        raise ArithmeticError("strict native audit forecast rejected")


def audit(root: Path, output: Path) -> None:
    """Audit exactly 24 candidates with comparison-only reference scalars."""
    contract(root)
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_own(root, fingerprint)
    require_archive(root, root / AUDIT_ADMISSION, "admitted", fingerprint)
    decision = json.loads((root / AUDIT_ADMISSION / "decision.json").read_bytes())
    if decision != audit_forecast(root) or decision["status"] != "admitted":
        raise ArithmeticError("published native admission changed")
    deadline = Deadline(780)
    output.mkdir(parents=True, exist_ok=False)
    events = output / "events.jsonl"
    started = time.perf_counter()
    rows: list[dict[str, Any]] = []
    try:
        runtime = installed_reference()
        for spec in paths():
            deadline.check()
            scoring = context(root, spec.game)
            refs = ScalarReference(scoring.exact), ScalarReference(scoring.partition)
            folder = root / OWN / "study" / f"path{spec.index:02d}"
            summary = replay_path(scoring, folder)
            if (
                summary["path"]
                != dict(index=spec.index, game=spec.game, arm=spec.arm, seed=0)
                or summary["labels"] != list(LABELS)
                or len(summary["captures"]) != 6
            ):
                raise ArithmeticError("fixed own candidate path changed")
            for saved in summary["captures"]:
                deadline.check()
                meta = saved["metadata"]
                if meta["work_label"] not in LABELS or meta["readout"] not in READOUTS:
                    raise ArithmeticError("unregistered candidate saved policy")
                policy = read_snapshot(
                    folder / saved["file"], scoring.partition, saved["receipt"], meta
                )
                own = scoring.score(policy)
                if own_compare(score_data(scoring, own), saved["score"]) > 1e-9:
                    raise ArithmeticError("own scalar changed before reference audit")
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
                    raise ArithmeticError("fixed independent scalar tolerance failed")
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
            raise ArithmeticError("24 fixed independent scalar checks missing")
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
