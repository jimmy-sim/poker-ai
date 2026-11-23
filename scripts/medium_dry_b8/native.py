"""Comparison-only scalar audit of published batch-eight-update policies."""

import json
import os
import time
from pathlib import Path
from typing import Any

from river_generalization.learning import PathSpec
from river_generalization.native import audit_path, installed_reference

from medium_dry_b8.gate import (
    OWN,
    SOURCE,
    clean_head,
    fingerprint,
    fixed_contract,
    paths,
    require_stage,
)
from medium_dry_b8.learning import context
from medium_dry_b8.study import save
from poker_ai.postflop.river_study import Deadline
from poker_ai.solver_validation.matched_array_reference import ScalarReference


def audit(root: Path, output: Path) -> None:
    """Audit 54 own B8 snapshots; retain each row before the next."""
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
        for index, game, seed, arm in paths():
            deadline.check()
            scoring = context(root, game, arm)
            references = (
                ScalarReference(scoring.exact),
                ScalarReference(scoring.partition),
            )
            folder = root / OWN / "study" / f"path{index:02d}"

            def retain(row: dict[str, Any]) -> None:
                with events.open("a") as stream:
                    stream.write(
                        json.dumps(row, sort_keys=True, allow_nan=False) + "\n"
                    )
                    stream.flush()
                    os.fsync(stream.fileno())

            rows.extend(
                audit_path(
                    scoring,
                    folder,
                    PathSpec(index, game, seed, arm),
                    references,
                    deadline,
                    retain,
                )
            )
        if len(rows) != 54:
            raise ArithmeticError("missing fixed independent scalar comparisons")
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
