"""Old OWN archive projections for complete cost measurement, never training.

Half labels explicitly reuse the next original endpoint. Mixed tables combine
old coarse own rows and old fine opponent rows; they were NOT learned together.
No new iteration, regret, guard, crossing or learning RNG history is invented.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_artifacts import (
    array_sha,
    decode_mass,
    write_mass,
)
from poker_ai.evaluation.averaging_history_math import validate_mass, window_mass
from poker_ai.evaluation.averaging_history_replay import archive_path
from poker_ai.evaluation.frozen_batch_replay import warm_mass
from poker_ai.evaluation.opponent_learning_contexts import Contexts
from poker_ai.evaluation.opponent_learning_design import (
    COST,
    READOUTS,
    WEIGHTS,
    WORK,
    Design,
)
from poker_ai.evaluation.opponent_learning_replay import ContextFor, member, metadata
from poker_ai.evaluation.opponent_learning_sources import Sources, cost_contract
from poker_ai.finite import FloatArray
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_checkpoints import (
    read_snapshot,
    unpack_policy,
    write_snapshot,
)
from poker_ai.postflop.learning_artifacts import decode, read_archive, sha
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline

LABELS = {
    50_000: 100_000,
    100_000: 100_000,
    500_000: 1_000_000,
    1_000_000: 1_000_000,
    5_000_000: 10_000_000,
    10_000_000: 10_000_000,
}


@dataclass(frozen=True)
class OldMember:
    values: FloatArray
    identity: dict[str, Any]


@dataclass(frozen=True)
class Standins:
    """Every signed B4 old coarse/fine endpoint and both OWN books, immutable."""

    members: dict[tuple[int, str, int, str], OldMember]
    context_for: ContextFor

    def project(self, path: dict[str, Any], label: int, readout: str) -> OldMember:
        if path["scope"] != COST or label not in LABELS:
            raise ValueError("old stand-ins need explicit cost scope and frozen labels")
        context = self.context_for(path["coordinate"])
        kind = path["tree_kind"]
        source_kinds = ("coarse", "fine") if kind.startswith("mixed") else (kind,)
        selected = [
            self.members[path["coordinate"], k, LABELS[label], readout]
            for k in source_kinds
        ]
        values = (
            project_mixed(context, path["role"], *[s.values for s in selected])
            if len(selected) == 2
            else selected[0].values.copy()
        )
        tree = context.tree(kind)
        if readout in WEIGHTS:
            validate_mass(tree, values)
        else:
            tree.validate_policy(values)
        values.flags.writeable = False
        return OldMember(
            values,
            dict(
                nominal_work_label=label,
                actual_old_work_label=LABELS[label],
                old_own_source_members=[s.identity for s in selected],
                mixed_tables_learned_together=False if len(selected) == 2 else None,
            ),
        )

    def warm(self, path: dict[str, Any]) -> FloatArray:
        context = self.context_for(path["coordinate"])
        kind = path["tree_kind"]
        if kind.startswith("mixed"):
            result = project_mixed(
                context,
                path["role"],
                warm_mass(context.coarse),
                warm_mass(context.fine),
            )
        else:
            result = warm_mass(context.tree(kind))
        result.flags.writeable = False
        return result


def project_mixed(
    context: Contexts, role: int, coarse: FloatArray, fine: FloatArray
) -> FloatArray:
    """Copy legal own coarse/other fine rows; no iteration or policy updating."""
    if type(role) is not int or role not in (0, 1):
        raise ValueError("cost projection needs one declared coarse role")
    view = context.views[role]
    result = np.zeros_like(view.tree.legal)
    own = context.coarse.owners == role
    result[view.coarse_own_to_view[own]] = coarse[own]
    other = context.fine.owners != role
    result[view.fine_to_view[other]] = fine[other]
    return result


def load(root: Path, sources: Sources, deadline: Deadline) -> Standins:
    """Decode original archives once, retaining every coordinate and source ID."""
    contract = cost_contract(root)
    if {int(k): v for k, v in contract["source_label_map"].items()} != LABELS:
        raise ArithmeticError("frozen old endpoint mapping changed")
    archived = sources.historical
    wanted: dict[str, tuple[int, str, int, str]] = {}
    endpoints = {}
    for peer in sources.original_boundaries:
        coordinate, kind = divmod(peer["path_index"], 5)
        tree_kind = "fine" if kind == 4 else "coarse"
        endpoints[coordinate, tree_kind, peer["work_label"]] = peer
        for stream in ("rows", "currents", "masses"):
            for row in archived.own[stream]:
                if (
                    row["path_index"] == peer["original_path_index"]
                    and row["work_label"] == peer["work_label"]
                ):
                    readout = (
                        "current"
                        if stream == "currents"
                        else row["case"]["average_weight"]
                        + ("_average" if stream == "rows" else "")
                    )
                    wanted[row["id"]] = (
                        coordinate,
                        tree_kind,
                        peer["work_label"],
                        readout,
                    )
    result = {}
    for rows_key, prefix in (
        ("rows", "details"),
        ("currents", "current_details"),
        ("masses", "mass_details"),
    ):
        filename = archived.own[prefix + "_file"]
        archive_sha = archived.own[prefix + "_sha256"]
        for row, blob in read_archive(
            archive_path(archived.own_path, filename),
            archive_sha,
            archived.own[rows_key],
        ):
            deadline.check()
            if row["id"] not in wanted:
                continue
            key = wanted[row["id"]]
            context = sources.context(key[0])
            tree = context.tree(key[1])
            if rows_key == "masses":
                values = decode_mass(blob, tree, row)
            else:
                values = unpack_policy(
                    tree, decode(blob, context.scoring[key[1]], row)["policy"]
                )
                values.flags.writeable = False
            if key in result:
                raise ArithmeticError("duplicate original cost source")
            endpoint = endpoints[key[:3]]
            result[key] = OldMember(
                values,
                dict(
                    archive_file=filename,
                    archive_sha256=archive_sha,
                    id=row["id"],
                    original_path_index=row["path_index"],
                    old_work_label=row["work_label"],
                    old_total_work=endpoint["total_work"],
                    old_iteration=endpoint["iteration"],
                    old_work_endpoint=endpoint,
                    receipt=row["receipt"],
                    metadata_sha256=row["metadata_sha256"],
                ),
            )
    expected = {
        (c, k, w, r)
        for c in range(6)
        for k in ("coarse", "fine")
        for w in WORK
        for r in (*READOUTS, *WEIGHTS)
    }
    if set(result) != expected or len(wanted) != 180:
        raise ArithmeticError("complete180 old own policy/book members required")
    return Standins(result, sources.context)


def collect(
    standins: Standins,
    folder: Path,
    design: Design,
    index: int,
    binding: str,
    send: Send,
    deadline: Deadline,
) -> dict[str, Any]:
    if design.scope != COST:
        raise ValueError("old projections cannot enter an actual learning design")
    path = design.path(index)
    tree = standins.context_for(path["coordinate"]).tree(path["tree_kind"])
    common = dict(
        source_sha256=binding,
        tree_sha256=tree_digest(tree),
        new_training_nodes=0,
        iteration=None,
        guard_sha256=None,
        learning_rng_entropy=None,
        original_B4_crossing_proof=False,
    )
    warm_meta = dict(
        **path,
        **common,
        id=f"opponent-warm-{COST}-{index:02d}",
        origin="old_own_analytic_warm_mass_projection",
        initialization_visits=0,
    )
    filename = f"warm/{index:02d}.json.gz"
    receipt = write_mass(folder / filename, tree, standins.warm(path), warm_meta)
    warm: dict[str, Any] = dict(
        warm_meta, file=filename, receipt=receipt, metadata_sha256=sha(warm_meta)
    )
    send(dict(kind="cell", phase="warm", index=index, row=warm))
    captures: list[dict[str, Any]] = []
    masses: list[dict[str, Any]] = []
    for label in design.boundaries(index):
        for readout in (*READOUTS, *WEIGHTS):
            deadline.check()
            old = standins.project(path, label, readout)
            mass = readout in WEIGHTS
            meta = dict(
                **(
                    design.mass(index, label, readout)
                    if mass
                    else design.raw(index, label, readout)
                ),
                **common,
                **old.identity,
                warm_mass_sha256=warm["receipt"]["mass_sha256"],
            )
            directory = "masses" if mass else "captures"
            filename = f"{directory}/{index:02d}-{label}-{readout}.json.gz"
            receipt = (write_mass if mass else write_snapshot)(
                folder / filename, tree, old.values, meta
            )
            row = dict(meta, file=filename, receipt=receipt, metadata_sha256=sha(meta))
            (masses if mass else captures).append(row)
            send(
                dict(
                    kind="cell",
                    phase="mass" if mass else "capture",
                    index=index,
                    row=row,
                )
            )
    return dict(
        path=path,
        captures=captures,
        masses=masses,
        warm=warm,
        new_training_nodes=0,
        final_iteration=None,
    )


def replay(
    folder: Path,
    design: Design,
    captures: list[dict[str, Any]],
    masses: list[dict[str, Any]],
    warms: list[dict[str, Any]],
    context_for: ContextFor,
    binding: str,
    deadline: Deadline,
    standins: Standins,
) -> dict[str, FloatArray]:
    """Reconstruct old source projections, not new crossings or regret history."""
    if design.scope != COST:
        raise ValueError("cost replay must never replace actual trajectory replay")
    design.require_rows("captures", captures)
    design.require_rows("masses", masses)
    if len(warms) != 30 or {r["path_index"] for r in warms} != set(range(30)):
        raise ArithmeticError("all thirty old warm projections required")
    warm_rows = {r["path_index"]: r for r in warms}
    result = {}
    for index in range(30):
        path = design.path(index)
        tree = context_for(path["coordinate"]).tree(path["tree_kind"])
        common = dict(
            source_sha256=binding,
            tree_sha256=tree_digest(tree),
            new_training_nodes=0,
            iteration=None,
            guard_sha256=None,
            learning_rng_entropy=None,
            original_B4_crossing_proof=False,
        )
        warm = warm_rows[index]
        expected = dict(
            **path,
            **common,
            id=f"opponent-warm-{COST}-{index:02d}",
            origin="old_own_analytic_warm_mass_projection",
            initialization_visits=0,
        )
        if not same(metadata(warm), expected):
            raise ArithmeticError("old cost warm identity changed")
        actual_warm = decode_mass(member(folder, warm["file"]).read_bytes(), tree, warm)
        if actual_warm.tobytes() != standins.warm(path).tobytes():
            raise ArithmeticError("old cost warm projection changed")
        books = {}
        for row in [r for r in captures + masses if r["path_index"] == index]:
            deadline.check()
            mass = row in masses
            old = standins.project(path, row["work_label"], row["readout"])
            expected = dict(
                **(
                    design.mass(index, row["work_label"], row["readout"])
                    if mass
                    else design.raw(index, row["work_label"], row["readout"])
                ),
                **common,
                **old.identity,
                warm_mass_sha256=warm["receipt"]["mass_sha256"],
            )
            if not same(metadata(row), expected):
                raise ArithmeticError(
                    "old cost source identity or zero-work claim changed"
                )
            actual = (
                decode_mass(member(folder, row["file"]).read_bytes(), tree, row)
                if mass
                else read_snapshot(
                    member(folder, row["file"]), tree, row["receipt"], expected
                )
            )
            if actual.tobytes() != old.values.tobytes():
                raise ArithmeticError(
                    "cost stand-in differs from pinned old OWN source"
                )
            if mass:
                window_mass(tree, actual_warm, actual)
                books[row["work_label"], row["readout"]] = actual
            else:
                actual.flags.writeable = False
                result[row["id"]] = actual
        for row in [
            r
            for r in captures
            if r["path_index"] == index and r["readout"] != "current"
        ]:
            book = books[row["work_label"], row["readout"].removesuffix("_average")]
            if array_sha(tree.normalize(book)) != array_sha(result[row["id"]]):
                raise ArithmeticError(
                    "old cost policy no longer matches its projected book"
                )
    return result
