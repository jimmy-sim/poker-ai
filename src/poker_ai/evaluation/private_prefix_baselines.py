"""Reuse every original B1/IID readout and fixed target by exact saved identity.

All216 original current profiles already have scalar scores at all three work
labels. This module does not fit, select or train a replacement baseline.
"""

from pathlib import Path
from typing import Any

from poker_ai.evaluation.batch_current_math import matches
from poker_ai.evaluation.private_prefix_design import READOUTS, Design
from poker_ai.evaluation.private_prefix_sources import Sources
from poker_ai.finite import FloatArray
from poker_ai.postflop.parallel_profile import same


def rows(sources: Sources) -> list[dict[str, Any]]:
    result = []
    for row in sources.averages.values():
        result.append(
            dict(
                row,
                readout=row["case"]["average_weight"] + "_average",
                baseline_origin="REUSED_ORIGINAL_AUDITED_AVERAGE",
            )
        )
    for row in sources.scored_currents.values():
        if row["variant"] != "current":
            raise ArithmeticError("original current inventory contains another readout")
        result.append(
            dict(
                row,
                readout="current",
                baseline_origin="REUSED_ORIGINAL_AUDITED_CURRENT",
            )
        )
    expected = {
        (i, t, r)
        for i in range(72)
        for t in (100000, 1000000, 10000000)
        for r in READOUTS
    }
    observed = {(r["path_index"], r["work_label"], r["readout"]) for r in result}
    if len(result) != 648 or observed != expected:
        raise ArithmeticError("all648 original baseline readouts required")
    return sorted(result, key=lambda r: r["id"])


def maps(
    design: Design,
    baseline_rows: list[dict[str, Any]],
    baseline_fixed: list[dict[str, Any]],
) -> tuple[dict[Any, Any], dict[Any, Any]]:
    by_coordinate = {}
    for row in baseline_rows:
        key = row["path_index"], row["work_label"], row["readout"]
        if key in by_coordinate:
            raise ArithmeticError("duplicate original baseline coordinate")
        by_coordinate[key] = row
    fixed_by_id = {}
    for row in baseline_fixed:
        key = row["own_snapshot_id"], row["opponent_profile_id"], row["target"]
        if key in fixed_by_id:
            raise ArithmeticError("duplicate original fixed baseline")
        fixed_by_id[key] = row
    if len(by_coordinate) != 648 or len(fixed_by_id) != 1728:
        raise ArithmeticError("complete original baseline/fixed inventory required")
    selves, targets = {}, {}
    for i in range(48):
        for t in design.labels:
            for readout in READOUTS:
                for kind, index in (("B1", i % 24), ("IID", i + 24)):
                    row = by_coordinate[index, t, readout]
                    if not same(
                        row["batch_size"],
                        1 if kind == "B1" else design.paths[i]["batch_size"],
                    ):
                        raise ArithmeticError("original baseline batch changed")
                    selves[kind, i, t, readout] = row
                    if t != design.labels[-1]:
                        continue
                    candidate = design.profile(i, t, readout)["id"]
                    for (identifier, opponent, target), fixed in fixed_by_id.items():
                        if identifier == row["id"]:
                            targets[kind, candidate, opponent, target] = fixed
    if len(selves) != 864 or len(targets) != 2304:
        raise ArithmeticError("complete original paired baseline mapping required")
    return selves, targets


def verify_saved(saved: dict[str, Any], sources: Sources) -> None:
    if not same(saved["baseline_rows"], rows(sources)) or not same(
        saved["baseline_fixed"], sources.parent.fixed
    ):
        raise ArithmeticError("reused original baseline scores/fixed targets changed")


def fixed_for(
    sources: Sources, row: dict[str, Any], policy: FloatArray, binding: str
) -> list[dict[str, Any]]:
    return matches(sources.parent.archived, row, policy, binding)


def source_hashes(root: Path, sources: Sources) -> dict[str, str]:
    from poker_ai.evaluation.batch_current_inputs import source_hashes as old_hashes
    from poker_ai.postflop.river_study import digest

    result = dict(sources.input_sha256)
    result.update(old_hashes(root, sources.parent.archived))
    # The complete current own/native receipts are pinned in the parent contract;
    # the used source archives are above. No unused new-prefix archive is claimed.
    for path in (
        "results/batch-current-diagnosis/own.json",
        "results/batch-current-diagnosis/native.json",
    ):
        result[path] = digest(root / path)
    return result
