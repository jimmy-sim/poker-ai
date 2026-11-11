"""Shared own capture/archive/scoring path, separate from admission and native."""

import tempfile
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.opponent_learning_capture import collect
from poker_ai.evaluation.opponent_learning_contexts import Contexts, software_context
from poker_ai.evaluation.opponent_learning_cost import Standins
from poker_ai.evaluation.opponent_learning_cost import replay as cost_replay
from poker_ai.evaluation.opponent_learning_design import (
    COST,
    REAL,
    TOY,
    TOY_WORK,
    Design,
    is_composed,
)
from poker_ai.evaluation.opponent_learning_replay import (
    ContextFor,
    compose_profiles,
    member,
    metadata,
    profile_replay,
    raw_replay,
)
from poker_ai.evaluation.opponent_learning_score import (
    Books,
    fixed_conditions,
    fixed_inventory,
    score_profiles,
    scoring,
)
from poker_ai.evaluation.opponent_learning_sources import (
    Opponent,
    frozen_opponent,
    verify_boundaries,
)
from poker_ai.finite import FloatArray
from poker_ai.postflop.cell_process import Send
from poker_ai.postflop.controlled_checkpoints import read_snapshot
from poker_ai.postflop.learning_artifacts import read_archive, write_archive
from poker_ai.postflop.learning_training import replay_snapshot
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.range_reply import compare
from poker_ai.postflop.river_study import Deadline

FORMAT = "poker-ai-own-opponent-learning-own-v1"


def fixture() -> tuple[tuple[Contexts, Contexts], tuple[Opponent, ...]]:
    """Two fictional sign mirrors and eight scripted OWN controls per mirror.

    These are deterministic probability tables to exercise the full inventory,
    not poker policies, independently learned agents or reference outputs.
    """
    contexts = (software_context(0), software_context(1))
    opponents = []
    for game, context in enumerate(contexts):
        for control in range(8):
            weights = np.array(
                [
                    [(i + 1) * (control + 1) + 1, (i + 2) * (control + 2) + 3]
                    for i in range(len(context.fine.keys))
                ],
                dtype=np.float64,
            )
            policy = context.fine.normalize(weights)
            opponents.append(
                frozen_opponent(
                    context,
                    f"FICTIONAL_SCRIPTED_OWN_{game}_{control}",
                    game,
                    policy,
                    array_sha(policy),
                )
            )
    return contexts, tuple(opponents)


def archive(folder: Path, scratch: Path, saved: dict[str, Any]) -> None:
    streams = dict(
        captures=saved["captures"],
        masses=saved["masses"],
        warms=saved["warms"],
        composed=[r for r in saved["profiles"] if is_composed(r)],
        details=saved["rows"],
    )
    for name, rows in streams.items():
        filename = f"own-{name}.jsonl.gz"
        saved[name + "_file"] = filename
        saved[name + "_sha256"] = write_archive(folder / filename, scratch, rows)


def software_data(
    folder: Path,
    scratch: Path,
    binding: str,
    send: Send,
    deadline: Deadline,
) -> dict[str, Any]:
    """Execute all30 fictional paths and432/1152 own scores, without a reference.

    An outer source-bound driver owns the fresh running/failing receipt and raw
    journal. This function can only create the explicit fictional design; it has
    no real mode and cannot authorize a later real study.
    """
    design = Design(TOY, TOY_WORK)
    contexts, opponents = fixture()

    def context_for(coordinate: int) -> Contexts:
        design.coordinate(coordinate)
        return contexts[coordinate // 3]

    paths = []
    for index in range(30):
        path = design.path(index)
        send(dict(kind="cell", phase="path_started", index=index, path=path))
        result = collect(
            context_for(path["coordinate"]).tree(path["tree_kind"]),
            design,
            index,
            scratch,
            binding,
            send,
            deadline,
        )
        paths.append(result)
        send(
            dict(
                kind="cell",
                phase="path_finished",
                index=index,
                total_work=result["final_total_work"],
                seconds=result["seconds"],
            )
        )
    return finish_own(
        folder, scratch, design, paths, context_for, opponents, binding, send, deadline
    )


def finish_own(
    folder: Path,
    scratch: Path,
    design: Design,
    paths: list[dict[str, Any]],
    context_for: ContextFor,
    opponents: tuple[Opponent, ...],
    binding: str,
    send: Send,
    deadline: Deadline,
    *,
    originals: tuple[dict[str, Any], ...] = (),
    standins: Standins | None = None,
) -> dict[str, Any]:
    """Same checked capture/archive/scoring path after serial fixtures or workers."""
    if len(paths) != 30 or (design.scope == COST) != (standins is not None):
        raise ArithmeticError(
            "complete actual paths or explicitly sourced cost projections required"
        )
    captures = [r for p in paths for r in p["captures"]]
    masses = [r for p in paths for r in p["masses"]]
    warms = [p["warm"] for p in paths]
    if design.scope == REAL:
        verify_boundaries(design, captures, masses, originals)
    policies = replay_raw(
        scratch,
        design,
        captures,
        masses,
        warms,
        context_for,
        binding,
        deadline,
        standins,
    )
    profiles, arms = compose_profiles(
        scratch,
        design,
        captures,
        policies,
        context_for,
        binding,
        deadline,
    )
    rows = score_profiles(
        scratch,
        design,
        profiles,
        captures,
        policies,
        Books(scratch, design, masses, warms, context_for),
        context_for,
        binding,
        send,
        deadline,
    )
    fixed = fixed_conditions(
        design,
        policies,
        context_for,
        opponents,
        binding,
        send,
        deadline,
    )
    saved = dict(
        format=FORMAT,
        status="completed_own_native_pending",
        failure=None,
        scope=design.scope,
        manifest=design.manifest(),
        source_sha256=binding,
        captures=captures,
        masses=masses,
        warms=warms,
        profiles=profiles,
        arms=arms,
        rows=rows,
        fixed_conditions=fixed,
        training_paths=[
            {k: v for k, v in p.items() if k not in {"captures", "masses", "warm"}}
            for p in paths
        ]
        if design.scope != COST
        else [],
        cost_paths=[
            dict(path=p["path"], new_training_nodes=0, final_iteration=None)
            for p in paths
        ]
        if design.scope == COST
        else [],
        initialized_training_paths=0 if design.scope == COST else 30,
        actual_toy_training_work=sum(p["final_total_work"] for p in paths)
        if design.scope == TOY
        else 0,
        actual_poker_training_work=sum(p["final_total_work"] for p in paths)
        if design.scope == REAL
        else 0,
        toy_learning_performed=design.scope == TOY,
        poker_training_performed=design.scope == REAL,
        reference_constructed=False,
        reference_output_used_in_training=False,
        long_run_admitted=design.scope == REAL,
        new_agent_default=False,
        fresh_global_admission=False,
        original_B4_boundaries=list(originals),
        limits=(
            "Two fictional signal-game sign mirrors with repeated logical "
            "game/seed labels. Scripted own opponents. Software coverage only; "
            "values are fictional payoff units, not Holdem chips, strength, "
            "fresh evidence or training admission."
        )
        if design.scope == TOY
        else (
            "Old OWN policy/book cost stand-ins only; mixed tables were not "
            "learned together. Zero new learning or original B4 crossing proof. "
            "Not playing-strength, trajectory, compute or fresh/global admission."
        )
        if design.scope == COST
        else (
            "Known separately trained Holdem games only; all seeds/readouts "
            "and paired work retained. "
            "Real compute admitted, not a stronger/default/fresh/global policy."
        ),
    )
    archive(folder, scratch, saved)
    saved["own_replay"] = replay(
        folder,
        saved,
        design,
        context_for,
        opponents,
        binding,
        deadline,
        standins=standins,
    )
    deadline.check()
    return saved


def replay(
    folder: Path,
    saved: dict[str, Any],
    design: Design,
    context_for: ContextFor,
    opponents: tuple[Opponent, ...],
    binding: str,
    deadline: Deadline,
    *,
    standins: Standins | None = None,
) -> dict[str, Any]:
    """Materialize complete hashed archives, reconstruct every book/role and score.

    No source trainer or native constructor is needed. Recompute every own scalar,
    reply fingerprint, support statistic and fixed condition. File/identity checks
    remain exact; recalculated numerical scores allow only1e-9 absolute roundoff.
    """
    if (
        saved["format"] != FORMAT
        or saved["source_sha256"] != binding
        or not same(saved["manifest"], design.manifest())
    ):
        raise ArithmeticError("own artifact format/source/manifest changed")
    if saved["scope"] != design.scope:
        raise ArithmeticError("own artifact scope changed")
    if (
        saved["status"] != "completed_own_native_pending"
        or saved["failure"] is not None
        or type(saved["initialized_training_paths"]) is not int
        or saved["initialized_training_paths"] != (0 if design.scope == COST else 30)
        or len(saved["training_paths"]) != (0 if design.scope == COST else 30)
        or any(
            saved[k] is not False
            for k in (
                "reference_constructed",
                "reference_output_used_in_training",
                "new_agent_default",
                "fresh_global_admission",
            )
        )
    ):
        raise ArithmeticError("complete own-only nonadmitting header required")
    if saved["long_run_admitted"] is not (design.scope == REAL):
        raise ArithmeticError("own compute admission flag does not match its scope")
    if (design.scope == COST) != (standins is not None):
        raise ArithmeticError("cost replay requires the pinned old own sources")
    if design.scope == COST:
        if (
            not same(
                saved["cost_paths"],
                [
                    dict(
                        path=design.path(i), new_training_nodes=0, final_iteration=None
                    )
                    for i in range(30)
                ],
            )
            or saved["poker_training_performed"] is not False
            or saved["toy_learning_performed"] is not False
            or not same(saved["actual_poker_training_work"], 0)
            or not same(saved["actual_toy_training_work"], 0)
            or saved["original_B4_boundaries"] != []
        ):
            raise ArithmeticError("cost stand-ins cannot claim new learning history")
    for index, result in enumerate(saved["training_paths"]):
        if not same(result["path"], design.path(index)):
            raise ArithmeticError("own initialized path inventory changed")
        endpoint = next(
            r
            for r in saved["captures"]
            if (
                r["path_index"] == index
                and r["work_label"] == design.boundaries(index)[-1]
                and r["readout"] == "current"
            )
        )
        if not same(result["final_total_work"], endpoint["total_work"]) or not same(
            result["final_iteration"], endpoint["iteration"]
        ):
            raise ArithmeticError("own path completion differs from captured endpoint")
    if design.scope == TOY and (
        saved["toy_learning_performed"] is not True
        or saved["poker_training_performed"] is not False
        or type(saved["actual_poker_training_work"]) is not int
        or saved["actual_poker_training_work"] != 0
        or saved["original_B4_boundaries"] != []
        or not same(
            saved["actual_toy_training_work"],
            sum(r["final_total_work"] for r in saved["training_paths"]),
        )
    ):
        raise ArithmeticError(
            "fictional software cannot claim real poker work or admission"
        )
    if design.scope == REAL:
        if (
            saved["poker_training_performed"] is not True
            or saved["toy_learning_performed"] is not False
            or not same(saved["actual_toy_training_work"], 0)
            or not same(
                saved["actual_poker_training_work"],
                sum(r["final_total_work"] for r in saved["training_paths"]),
            )
        ):
            raise ArithmeticError(
                "real work counters differ from complete executed paths"
            )
        verify_boundaries(
            design,
            saved["captures"],
            saved["masses"],
            tuple(saved["original_B4_boundaries"]),
        )
    design.require_rows("profiles", saved["rows"])
    fixed_inventory(design, saved["fixed_conditions"], opponents)
    if not same([r["id"] for r in saved["rows"]], [r["id"] for r in saved["profiles"]]):
        raise ArithmeticError("scored own profile order changed")
    streams = dict(
        captures=saved["captures"],
        masses=saved["masses"],
        warms=saved["warms"],
        composed=[r for r in saved["profiles"] if is_composed(r)],
        details=saved["rows"],
    )
    maximum = 0.0
    with tempfile.TemporaryDirectory(prefix="own-opponent-replay-") as name:
        scratch = Path(name)
        for stream, rows in streams.items():
            for row, blob in read_archive(
                member(folder, saved[stream + "_file"]),
                saved[stream + "_sha256"],
                rows,
            ):
                deadline.check()
                path = member(scratch, row["file"])
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("xb") as output:
                    output.write(blob)
        raw = replay_raw(
            scratch,
            design,
            saved["captures"],
            saved["masses"],
            saved["warms"],
            context_for,
            binding,
            deadline,
            standins,
        )
        policies: dict[str, FloatArray] = profile_replay(
            scratch,
            design,
            saved["captures"],
            saved["profiles"],
            saved["arms"],
            raw,
            context_for,
            binding,
            deadline,
        )
        books = Books(scratch, design, saved["masses"], saved["warms"], context_for)
        captures = {r["id"]: r for r in saved["captures"]}
        sources = {r["id"]: r for r in saved["profiles"]}
        for row in saved["rows"]:
            deadline.check()
            contexts = context_for(row["coordinate"])
            context = scoring(contexts, row)
            blob = member(scratch, row["file"]).read_bytes()
            maximum = max(maximum, replay_snapshot(context, row, blob, 1e-9))
            stored = read_snapshot(
                member(scratch, row["file"]),
                context.partition,
                row["receipt"],
                metadata(row),
            )
            if stored.tobytes() != policies[row["id"]].tobytes():
                raise ArithmeticError(
                    "scored archive changed captured/composed own policy"
                )
            source = sources[row["id"]]
            if any(
                not same(metadata(row).get(k), v) for k, v in metadata(source).items()
            ) or not same(row["source_policy_receipt"], source["receipt"]):
                raise ArithmeticError("scored own source binding changed")
            maximum = max(
                maximum,
                compare(
                    books.support(contexts, source, captures),
                    row["coverage"],
                ),
            )
        measured = fixed_conditions(
            design,
            policies,
            context_for,
            opponents,
            binding,
            lambda e: None,
            deadline,
        )
        maximum = max(maximum, compare(measured, saved["fixed_conditions"]))
    if maximum > 1e-9:
        raise ArithmeticError(
            "own opponent-information replay changed numerical values"
        )
    deadline.check()
    return dict(
        status="all_own_books_roles_scores_and_fixed_conditions_replayed",
        raw_profiles=324,
        raw_ledgers=216,
        warm_origins=30,
        composed_profiles=108,
        unique_profiles=432,
        logical_profiles=216,
        fixed_conditions=1152,
        maximum_error=maximum,
        policy_and_ledger_bits_exact=True,
        new_training_admission=False,
    )


def replay_raw(
    folder: Path,
    design: Design,
    captures: list[dict[str, Any]],
    masses: list[dict[str, Any]],
    warms: list[dict[str, Any]],
    context_for: ContextFor,
    binding: str,
    deadline: Deadline,
    standins: Standins | None,
) -> dict[str, FloatArray]:
    if design.scope == COST:
        if standins is None:
            raise ArithmeticError("cost projection needs pinned old own sources")
        return cost_replay(
            folder,
            design,
            captures,
            masses,
            warms,
            context_for,
            binding,
            deadline,
            standins,
        )
    if standins is not None:
        raise ArithmeticError("old cost sources cannot replace real or toy training")
    return raw_replay(
        folder, design, captures, masses, warms, context_for, binding, deadline
    )
