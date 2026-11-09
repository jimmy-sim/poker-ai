"""Prospective metadata grid only; no Hold'em learning, scoring or admission."""

import itertools
import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation.batch_current_protocol import require_checks
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation.batch_currents import read as read_currents
from poker_ai.solver_validation.reduced_batches import read as read_batches
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/matched-update-batches.json"
CONFIG_SHA = "3d9d628a1daa0e44ef59ee9cbb8d3b08caf8373e9c8498b5ee479871b682f21c"
FIELDS = ("spot_file", "representation", "regret_rule", "seed")
READOUTS = ("current", "uniform_average", "linear_average")


def config_inputs(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("matched-update prospective config changed")
    config: dict[str, Any] = json.loads((root / CONFIG).read_text())
    if any(digest(root / p) != h for p, h in config["input_sha256"].items()):
        raise ArithmeticError("matched-update source evidence changed")
    return config


def _context(row: dict[str, Any]) -> tuple[Any, ...]:
    return tuple(row["case"][k] for k in FIELDS)


def build_grid(
    config: dict[str, Any],
    currents: list[dict[str, Any]],
    averages: list[dict[str, Any]],
    fixed: list[dict[str, Any]],
) -> dict[str, Any]:
    """All cases/targets selected by identity and iteration/work, never metrics."""
    contexts = list(
        itertools.product(
            config["spot_files"],
            config["representations"],
            config["regret_rules"],
            config["seeds"],
        )
    )
    index: dict[tuple[Any, ...], dict[str, Any]] = {}
    for rows, current in ((currents, True), (averages, False)):
        for row in rows:
            context = _context(row)
            batch, label, iteration, actual = (
                row["batch_size"],
                row["work_label"],
                row["iteration"],
                row["total_work"],
            )
            case = row["case"]
            readout = "current" if current else case["average_weight"] + "_average"
            key = (*context, batch, label, readout)
            if (
                context not in contexts
                or type(case["seed"]) is not int
                or type(batch) is not int
                or batch not in (1, 4, 16)
                or type(label) is not int
                or label not in config["original_work_labels"]
                or type(iteration) is not int
                or iteration < 2
                or type(actual) is not int
                or actual < label
                or readout not in READOUTS
                or case["traversal"] != "external"
                or case["regret_weight"] != "linear"
                or case["bridge"] != "common"
                or type(row["path_index"]) is not int
                or row["path_index"]
                != contexts.index(context) + {1: 0, 4: 24, 16: 48}[batch]
                or case["average_weight"] not in ("uniform", "linear")
                or (
                    current
                    and (
                        case["average_weight"] != "linear"
                        or row.get("variant") != "current"
                    )
                )
                or key in index
            ):
                raise ArithmeticError("invalid/duplicate matched-update source row")
            index[key] = row
    expected = {
        (*c, b, w, r)
        for c, b, w, r in itertools.product(
            contexts, (1, 4, 16), config["original_work_labels"], READOUTS
        )
    }
    if set(index) != expected:
        raise ArithmeticError("incomplete matched-update source grid")
    pairs = []
    targets = []
    final = config["final_work_label"]
    for c in contexts:
        baseline = index[*c, 1, final, "current"]
        for batch in config["comparison_batch_sizes"]:
            right = index[*c, batch, final, "current"]
            iteration = right["iteration"]
            if iteration > baseline["iteration"]:
                raise ArithmeticError(
                    "target exceeds original B1 endpoint; do not extend"
                )
            target_id = f"prefix-{baseline['path_index']:03d}-B{batch}"
            targets.append(
                dict(
                    id=target_id,
                    case={k: v for k, v in zip(FIELDS, c, strict=True)},
                    baseline_path_index=baseline["path_index"],
                    batched_path_index=right["path_index"],
                    target_iteration=iteration,
                    baseline_original_final_iteration=baseline["iteration"],
                    baseline_original_final_work=baseline["total_work"],
                    batched_final_work=right["total_work"],
                    comparison_batch_size=batch,
                )
            )
            for readout in READOUTS:
                row = index[*c, batch, final, readout]
                base_row = index[*c, 1, final, readout]
                if (row["iteration"], row["total_work"]) != (
                    iteration,
                    right["total_work"],
                ) or (base_row["iteration"], base_row["total_work"]) != (
                    baseline["iteration"],
                    baseline["total_work"],
                ):
                    raise ArithmeticError("same-path readouts disagree on update/work")
                pairs.append(
                    dict(
                        target_id=target_id,
                        readout=readout,
                        target_iteration=iteration,
                        planned_prefix_id=target_id + "-" + readout,
                        reused_profile_id=row["id"],
                        reused_policy_sha256=row["receipt"]["policy_sha256"],
                    )
                )
    ids = {r["reused_profile_id"] for r in pairs}
    if len(targets) != 48 or len(pairs) != 144 or len(ids) != 144:
        raise ArithmeticError("matched-update identity inventory incomplete")
    matches = [r for r in fixed if r["own_snapshot_id"] in ids]
    seen = {
        (r["own_snapshot_id"], r["opponent_profile_id"], r["target"]) for r in matches
    }
    if len(matches) != 1152 or len(seen) != 1152:
        raise ArithmeticError("fixed source targets missing or duplicated")
    for identifier in ids:
        rows = [r for r in matches if r["own_snapshot_id"] == identifier]
        opponents = {r["opponent_profile_id"] for r in rows}
        if (
            len(opponents) != 4
            or any(type(r["target"]) is not int for r in rows)
            or {(r["opponent_profile_id"], r["target"]) for r in rows}
            != set(itertools.product(opponents, (0, 1)))
        ):
            raise ArithmeticError("fixed opponents/seats changed")
    return dict(
        status="prospective_grid_only_no_training_admission",
        contexts=24,
        iteration_targets=targets,
        self_pairs=pairs,
        new_profiles_planned=144,
        reused_profiles=144,
        new_fixed_targets_planned=1152,
        reused_fixed_targets=1152,
        expected_original_B1_readout_checks=144,
        training_performed=False,
        reference_constructed=False,
        new_strength_scores=False,
        long_run_admitted=False,
    )


def manifest(root: Path) -> dict[str, Any]:
    config = config_inputs(root)
    require_checks(root, clean=False)
    source_path, current_path = (
        root / config["source_own"],
        root / config["source_currents"],
    )
    source, current = (
        json.loads(source_path.read_text()),
        json.loads(current_path.read_text()),
    )
    read_batches(root, source_path.with_name("native.json"), source, source_path)
    read_currents(root, current_path.with_name("native.json"), current, current_path)
    averages = [r for r in source["rows"] if r["path_index"] < 72]
    result = build_grid(config, current["rows"], averages, current["fixed_matches"])
    return dict(
        **result,
        input_sha256=config["input_sha256"],
        source=source_provenance(
            root, root / CONFIG, entrypoints=("scripts/check_matched_update_grid.py",)
        ),
        scope="protocol/observer foundation only; "
        "no poker replay or strength/admission",
    )
