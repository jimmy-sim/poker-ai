"""Exact-shape overhead corpus of OLD own B1 policies; never prefix outcomes."""

import copy
from pathlib import Path
from typing import Any

from poker_ai.evaluation import matched_update_inputs as inputs
from poker_ai.evaluation.averaging_history_artifacts import decode_mass, write_mass
from poker_ai.evaluation.averaging_history_replay import archive_path
from poker_ai.evaluation.batch_current_cells import policies
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_checkpoints import unpack_policy, write_snapshot
from poker_ai.postflop.learning_artifacts import decode, read_archive, sha
from poker_ai.postflop.river_study import Deadline

SCOPE = "OLD_OWN_POLICY_TIMING_ALIASES_NOT_NEW_PREFIX_OR_STRENGTH_RESULTS"


def corpus(
    sources: inputs.Sources,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    manifest = copy.deepcopy(sources.manifest)
    right: list[dict[str, Any]] = []
    fixed: list[dict[str, Any]] = []
    for target in manifest["iteration_targets"]:
        index = target["baseline_path_index"]
        target["planned_new_prefix_iteration"] = target["target_iteration"]
        target["target_iteration"] = sources.averages[index, "linear", 10000000][
            "iteration"
        ]
    for pair in manifest["self_pairs"]:
        target = next(
            t for t in manifest["iteration_targets"] if t["id"] == pair["target_id"]
        )
        index, readout = target["baseline_path_index"], pair["readout"]
        original = (
            sources.scored_currents[(sources.currents[index, 10000000]["id"],)]
            if readout == "current"
            else sources.averages[index, readout.removesuffix("_average"), 10000000]
        )
        identifier = "OLD-TIMING-RIGHT-" + pair["planned_prefix_id"]
        right.append(dict(original, id=identifier))
        pair.update(
            target_iteration=target["target_iteration"],
            reused_profile_id=identifier,
            reused_policy_sha256=original["receipt"]["policy_sha256"],
        )
        selected = [r for r in sources.fixed if r["own_snapshot_id"] == original["id"]]
        if len(selected) != 8:
            raise ArithmeticError("old B1 timing source fixed targets incomplete")
        fixed.extend(dict(r, own_snapshot_id=identifier) for r in selected)
    if len(right) != 144 or len(fixed) != 1152:
        raise ArithmeticError("complete old timing corpus required")
    return manifest, right, fixed


def job(
    slot: int, indices: list[int], payload: dict[str, Any], send: Send
) -> dict[str, Any]:
    del slot
    deadline = Deadline(payload["remaining_seconds"])
    sources = inputs.load(Path(payload["root"]))
    scratch = Path(payload["scratch"])
    targets = [
        t
        for t in payload["manifest"]["iteration_targets"]
        if t["baseline_path_index"] in indices
    ]
    aliases: dict[tuple[int, str], list[dict[str, Any]]] = {}
    for target in targets:
        index = target["baseline_path_index"]
        for readout in ("current", "uniform_average", "linear_average"):
            aliases.setdefault((index, readout), []).append(target)
    count = mass_count = 0
    for kind in ("current", "average"):
        for row, blob in policies(sources.archived, kind):
            deadline.check()
            index = row["path_index"]
            if index not in indices or row["work_label"] != 10000000:
                continue
            readout = (
                "current"
                if kind == "current"
                else row["case"]["average_weight"] + "_average"
            )
            context = sources.context(index)
            policy = unpack_policy(
                context.partition, decode(blob, context, row)["policy"]
            )
            peer = sources.original(index, 10000000)
            for target in aliases[index, readout]:
                meta = dict(
                    scope=SCOPE,
                    id=target["id"] + "-" + readout,
                    target_id=target["id"],
                    path_index=index,
                    case=row["case"],
                    batch_size=1,
                    comparison_batch_size=target["comparison_batch_size"],
                    readout=readout,
                    variant=readout,
                    source_sha256=payload["binding"],
                    original_policy_id=row["id"],
                    original_policy_sha256=row["receipt"]["policy_sha256"],
                    original_snapshot_sha256=row["receipt"]["sha256"],
                    planned_new_prefix_iteration=target["planned_new_prefix_iteration"],
                    **{
                        k: peer[k]
                        for k in (
                            "iteration",
                            "total_work",
                            "previous_work",
                            "last_iteration_visits",
                            "initialization_visits",
                            "sampled_traversals",
                            "guard_sha256",
                        )
                    },
                )
                filename = "captures/" + meta["id"] + ".json.gz"
                receipt = write_snapshot(
                    scratch / filename, context.partition, policy, meta
                )
                if receipt["policy_sha256"] != row["receipt"]["policy_sha256"]:
                    raise ArithmeticError("old timing alias changed own policy bits")
                send(
                    dict(
                        kind="cell",
                        phase="capture",
                        index=index,
                        row=dict(
                            **meta,
                            file=filename,
                            receipt=receipt,
                            metadata_sha256=sha(meta),
                        ),
                    )
                )
                count += 1
    own = sources.archived.own
    for row, blob in read_archive(
        archive_path(sources.archived.own_path, own["mass_details_file"]),
        own["mass_details_sha256"],
        own["masses"],
    ):
        deadline.check()
        index = row["path_index"]
        if index not in indices or row["work_label"] != 10000000:
            continue
        weight = row["case"]["average_weight"]
        context = sources.context(index)
        mass = decode_mass(blob, context.partition, row)
        peer = sources.original(index, 10000000)
        for target in aliases[index, weight + "_average"]:
            meta = dict(
                scope=SCOPE,
                id=target["id"] + "-" + weight,
                target_id=target["id"],
                path_index=index,
                case=row["case"],
                batch_size=1,
                comparison_batch_size=target["comparison_batch_size"],
                readout=weight,
                source_sha256=payload["binding"],
                original_mass_id=row["id"],
                original_mass_sha256=row["receipt"]["mass_sha256"],
                planned_new_prefix_iteration=target["planned_new_prefix_iteration"],
                **{
                    k: peer[k]
                    for k in (
                        "iteration",
                        "total_work",
                        "previous_work",
                        "last_iteration_visits",
                        "initialization_visits",
                        "sampled_traversals",
                        "guard_sha256",
                    )
                },
            )
            filename = "masses/" + meta["id"] + ".json.gz"
            receipt = write_mass(scratch / filename, context.partition, mass, meta)
            send(
                dict(
                    kind="cell",
                    phase="mass",
                    index=index,
                    row=dict(
                        **meta,
                        file=filename,
                        receipt=receipt,
                        metadata_sha256=sha(meta),
                    ),
                )
            )
            mass_count += 1
    # Explicit archival identity records, NOT newly observed B1 replay checks.
    for index in indices:
        for label in (100000, 1000000, 10000000):
            send(
                dict(
                    kind="cell",
                    phase="checkpoint",
                    index=index,
                    row=sources.original(index, label),
                )
            )
    return dict(
        paths=len(indices),
        captures=count,
        masses=mass_count,
        source_metadata_checks=3 * len(indices),
        new_training=False,
    )
