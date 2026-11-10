"""Full exact-shape OLD corpus; every original B4/B16 label/readout is retained."""

from dataclasses import asdict
from pathlib import Path
from typing import Any

from poker_ai.evaluation.averaging_history_artifacts import (
    array_sha,
    decode_mass,
    write_mass,
)
from poker_ai.evaluation.batch_current_cells import policies
from poker_ai.evaluation.private_prefix_design import OLD, Design
from poker_ai.evaluation.private_prefix_io import archive, gather
from poker_ai.evaluation.private_prefix_sources import Sources
from poker_ai.postflop.cached_nodes import cache_nodes
from poker_ai.postflop.controlled_checkpoints import unpack_policy, write_snapshot
from poker_ai.postflop.learning_artifacts import decode, read_archive, sha
from poker_ai.postflop.private_prefix import PrefixPlan
from poker_ai.postflop.river_study import Deadline


def copy(
    root: Path,
    path: Path,
    saved: dict[str, Any],
    sources: Sources,
    design: Design,
    scratch: Path,
    deadline: Deadline,
) -> None:
    if design.scope != OLD:
        raise ValueError("old corpus cannot masquerade as newly trained policies")
    original = sources.parent.archived
    contexts = {i: sources.context(i) for i in range(48)}
    averages = {
        (r["path_index"], r["work_label"], r["case"]["average_weight"]): r
        for r in sources.averages.values()
    }
    counters = {(i, t): r for (i, t, w), r in averages.items() if w == "linear"}
    plans = {}

    def common(i: int, label: int) -> dict[str, Any]:
        source_index = i + 24
        peer = counters[source_index, label]
        current = sources.currents[source_index, label]
        context = contexts[i]
        key = id(context.partition)
        if key not in plans:
            plans[key] = sha(
                asdict(PrefixPlan.build(cache_nodes(context.partition)[0]))
            )
        label_index = design.labels.index(label)
        previous_guard = (
            counters[source_index, design.labels[label_index - 1]]["guard_sha256"]
            if label_index
            else None
        )
        return dict(
            **{
                k: peer[k]
                for k in (
                    "iteration",
                    "previous_work",
                    "total_work",
                    "last_iteration_visits",
                    "initialization_visits",
                    "sampled_traversals",
                    "guard_sha256",
                    "current_sha256",
                )
            },
            overshoot=peer["total_work"] - label,
            prefix_plan_sha256=plans[key],
            prefix_plan_role="CANDIDATE_IO_SHAPE_ONLY_NOT_OLD_TRAINING_STATE",
            source_sha256=saved["source_sha256"],
            current_movement=current["current_movement"],
            previous_capture_guard_sha256=previous_guard,
            initialization_seconds=0.0,
            prefix_setup_seconds=0.0,
            origin="OLD_IID_SOURCE_COPY_NO_NEW_TRAINING",
            old_source_study_sha256=original.own["source_sha256"],
        )

    def retain(phase: str, i: int, row: dict[str, Any]) -> None:
        saved["events"].append(dict(kind="cell", phase=phase, index=i, row=row))

    for kind in ("current", "average"):
        for row, blob in policies(original, kind):
            deadline.check()
            source_index = row["path_index"]
            if not 24 <= source_index < 72:
                continue
            i, label = source_index - 24, row["work_label"]
            context = contexts[i]
            policy = unpack_policy(
                context.partition, decode(blob, context, row)["policy"]
            )
            readout = (
                "current"
                if kind == "current"
                else row["case"]["average_weight"] + "_average"
            )
            meta = dict(
                **design.profile(i, label, readout),
                **common(i, label),
                old_source_id=row["id"],
                old_source_sha256=row["receipt"]["sha256"],
                old_source_policy_sha256=row["receipt"]["policy_sha256"],
                coverage=None,
            )
            if readout == "current":
                if array_sha(policy) != meta["current_sha256"]:
                    raise ArithmeticError(
                        "old current differs from original checkpoint"
                    )
            else:
                meta["coverage"] = row["coverage"]
            relative = "captures/" + meta["id"] + ".json.gz"
            receipt = write_snapshot(
                scratch / relative, context.partition, policy, meta
            )
            retain(
                "capture",
                i,
                dict(**meta, file=relative, receipt=receipt, metadata_sha256=sha(meta)),
            )
    original_path = original.own_path.with_name(original.own["mass_details_file"])
    for row, blob in read_archive(
        original_path, original.own["mass_details_sha256"], original.own["masses"]
    ):
        deadline.check()
        source_index = row["path_index"]
        if not 24 <= source_index < 72:
            continue
        i, label = source_index - 24, row["work_label"]
        weight = row["case"]["average_weight"]
        context = contexts[i]
        mass = decode_mass(blob, context.partition, row)
        meta = dict(
            **design.mass(i, label, weight),
            **common(i, label),
            old_source_id=row["id"],
            old_source_sha256=row["receipt"]["sha256"],
            old_source_mass_sha256=row["receipt"]["mass_sha256"],
        )
        relative = "masses/" + meta["id"] + ".json.gz"
        receipt = write_mass(scratch / relative, context.partition, mass, meta)
        retain(
            "mass",
            i,
            dict(**meta, file=relative, receipt=receipt, metadata_sha256=sha(meta)),
        )
    gather(saved)
    if (
        len(saved["captures"]) != 432
        or len(saved["masses"]) != 288
        or saved["training_performed"] is not False
    ):
        raise ArithmeticError(
            "complete old432/288 source corpus required, with no training"
        )
    archive(path, saved, scratch, "captures", "captures")
    archive(path, saved, scratch, "masses", "masses")
