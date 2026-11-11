"""Complete tiny own artifacts, independent terminal math and failure retention."""

import copy
import itertools
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest

from poker_ai.evaluation.opponent_learning_contexts import Contexts
from poker_ai.evaluation.opponent_learning_design import (
    REAL,
    SEEDS,
    TOY,
    TOY_WORK,
    WORK,
    Design,
)
from poker_ai.evaluation.opponent_learning_own import fixture, replay, software_data
from poker_ai.evaluation.opponent_learning_replay import metadata
from poker_ai.evaluation.opponent_learning_report import assessment, write
from poker_ai.evaluation.opponent_learning_score import fixed_inventory, scoring
from poker_ai.evaluation.opponent_learning_workers import gather_independent
from poker_ai.finite import FloatArray
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.controlled_checkpoints import unpack_policy, write_snapshot
from poker_ai.postflop.learning_artifacts import (
    decode,
    read_archive,
    sha,
    write_archive,
)
from poker_ai.postflop.river_study import Deadline
from poker_ai.solver_validation import opponent_learning as native

BINDING = "a" * 64


@pytest.fixture(scope="module")
def complete(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    folder = tmp_path_factory.mktemp("opponent-own-pipeline")
    events: list[dict[str, Any]] = []

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("own pipeline constructed a reference")

    with (
        patch("poker_ai.solver_validation.reference.Reference.__init__", forbidden),
        patch(
            "poker_ai.solver_validation.matched_array_reference.ScalarReference.__init__",
            forbidden,
        ),
    ):
        saved = software_data(
            folder, folder / "scratch", BINDING, events.append, Deadline(180)
        )
    json.dumps(saved, allow_nan=False)
    contexts, opponents = fixture()
    return dict(
        folder=folder,
        saved=saved,
        events=events,
        contexts=contexts,
        opponents=opponents,
    )


def test_complete_own_shape_and_replay_without_any_reference(
    complete: dict[str, Any],
) -> None:
    s = complete["saved"]
    assert s["own_replay"]["maximum_error"] == 0
    assert s["own_replay"]["policy_and_ledger_bits_exact"] is True
    assert len(s["captures"]) == 324
    assert len(s["masses"]) == 216
    assert len(s["warms"]) == 30
    assert len(s["profiles"]) == len(s["rows"]) == 432
    assert len(s["arms"]) == 216
    assert len(s["fixed_conditions"]) == 1152
    assert len(complete["events"]) == 2214
    assert s["actual_poker_training_work"] == 0
    assert s["toy_learning_performed"] is True
    assert s["poker_training_performed"] is False
    assert s["reference_constructed"] is False
    assert s["long_run_admitted"] is False
    assert s["new_agent_default"] is s["fresh_global_admission"] is False
    assert s["original_B4_boundaries"] == []
    assert s["actual_toy_training_work"] == sum(
        r["final_total_work"] for r in s["training_paths"]
    )


def signal_value(fine: FloatArray, game: int) -> float:
    # Four terminal branches; no finite-tree value or best-response algorithm.
    a, b, c, d = fine
    target_value = 0.5 * (a[1] * (c[0] - c[1]) + b[1] * (-d[0] + d[1]))
    return float(target_value if game == 0 else -target_value)


def pure_root(policy: FloatArray, target: int, game: int) -> float:
    owned = (0, 1) if target == game else (2, 3)
    roots = []
    for moves in itertools.product((0, 1), repeat=2):
        candidate = policy.copy()
        for row, action in zip(owned, moves, strict=True):
            candidate[row] = 0
            candidate[row, action] = 1
        roots.append((1 if target == 0 else -1) * signal_value(candidate, game))
    return max(roots)


def test_all432_scored_profiles_match_independent_terminal_and_pure_reply_math(
    complete: dict[str, Any],
) -> None:
    saved, folder = complete["saved"], complete["folder"]
    for row, blob in read_archive(
        folder / saved["details_file"], saved["details_sha256"], saved["rows"]
    ):
        game = row["coordinate"] // 3
        contexts = complete["contexts"][game]
        context = scoring(contexts, row)
        detail = decode(blob, context, row)
        policy = unpack_policy(context.partition, detail["policy"])
        fine = policy[context.exact_to_partition]
        expected = 0.5 * sum(pure_root(fine, target, game) for target in (0, 1))
        assert abs(expected - row["metrics"]["exact_exploitability_chips"]) < 1e-12
        assert (
            abs(signal_value(fine, game) - row["metrics"]["value_player_zero_chips"])
            < 1e-12
        )
        for target in (0, 1):
            assert (
                abs(
                    pure_root(fine, target, game)
                    - row["responses"][target]["exact_reply_value_chips"]
                )
                < 1e-12
            )
        assert (row["coverage"] is None) == (row["readout"] == "current")


def test_all1152_fixed_conditions_match_independent_terminal_math(
    complete: dict[str, Any],
) -> None:
    saved, folder = complete["saved"], complete["folder"]
    policies = {}
    for row, blob in read_archive(
        folder / saved["details_file"], saved["details_sha256"], saved["rows"]
    ):
        context = scoring(complete["contexts"][row["coordinate"] // 3], row)
        policies[row["id"]] = unpack_policy(
            context.partition, decode(blob, context, row)["policy"]
        )[context.exact_to_partition]
    opponents = {p.identifier: p for p in complete["opponents"]}
    for row in saved["fixed_conditions"]:
        game, target = row["coordinate"] // 3, row["target"]
        opponent = opponents[row["opponent_id"]]
        candidate = policies[row["id"]]
        own_rows = (0, 1) if target == game else (2, 3)
        mixed = opponent.policy.copy()
        mixed[list(own_rows)] = candidate[list(own_rows)]
        ev = (1 if target == 0 else -1) * signal_value(mixed, game)
        root = pure_root(mixed, target, game)
        assert abs(ev - row["target_ev_chips"]) < 1e-12
        assert abs(root - row["fine_reply_value_chips"]) < 1e-12
        assert abs(root - ev - row["fine_reply_gain_chips"]) < 1e-12


@pytest.mark.parametrize(
    "field,value",
    [
        ("status", "failed"),
        ("failure", {"type": "interrupted"}),
        ("initialized_training_paths", True),
        ("reference_constructed", True),
        ("reference_output_used_in_training", True),
        ("long_run_admitted", True),
        ("new_agent_default", True),
        ("fresh_global_admission", True),
        ("poker_training_performed", True),
        ("actual_poker_training_work", False),
        ("actual_toy_training_work", 0),
        ("scope", "REAL"),
    ],
)
def test_partial_or_inflated_header_cannot_replay_as_complete(
    complete: dict[str, Any],
    field: str,
    value: Any,
) -> None:
    bad = copy.deepcopy(complete["saved"])
    bad[field] = value
    with pytest.raises(ArithmeticError):
        replay(
            complete["folder"],
            bad,
            Design(TOY, TOY_WORK),
            lambda i: complete["contexts"][i // 3],
            complete["opponents"],
            BINDING,
            Deadline(180),
        )


@pytest.mark.parametrize(
    "change", ["missing", "duplicate", "bool_target", "wrong_opponent"]
)
def test_fixed_inventory_rejects_incomplete_or_changed_conditions(
    complete: dict[str, Any],
    change: str,
) -> None:
    rows = copy.deepcopy(complete["saved"]["fixed_conditions"])
    if change == "missing":
        rows.pop()
    elif change == "duplicate":
        rows.append(dict(rows[0]))
    elif change == "bool_target":
        rows[0]["target"] = False
    else:
        rows[0]["opponent_id"] = "unplanned opponent"
    with pytest.raises(ArithmeticError):
        fixed_inventory(Design(TOY, TOY_WORK), rows, complete["opponents"])


def test_replay_detects_changed_scores_archive_identity_and_path(
    complete: dict[str, Any],
) -> None:
    for change in ("score", "archive", "path", "source"):
        bad = copy.deepcopy(complete["saved"])
        if change == "score":
            bad["rows"][0]["metrics"]["exact_exploitability_chips"] += 0.1
        elif change == "archive":
            bad["details_sha256"] = "0" * 64
        elif change == "path":
            bad["training_paths"][0]["final_total_work"] -= 1
        else:
            bad["source_sha256"] = "b" * 64
        with pytest.raises(ArithmeticError):
            replay(
                complete["folder"],
                bad,
                Design(TOY, TOY_WORK),
                lambda i: complete["contexts"][i // 3],
                complete["opponents"],
                BINDING,
                Deadline(180),
            )


def test_combined_raw_mass_preserves_zero_support_and_own_rows() -> None:
    c: Contexts = fixture()[0][0]
    for arm in ("coarse_pair", "mixed_pair"):
        trees = (
            (c.coarse, c.coarse)
            if arm == "coarse_pair"
            else (c.views[0].tree, c.views[1].tree)
        )
        first, second = (np.zeros_like(tree.legal) for tree in trees)
        own0, own1 = c.coarse.owners == 0, c.coarse.owners == 1
        if arm == "mixed_pair":
            first[c.views[0].coarse_own_to_view[own0]] = [4, 6]
            second[c.views[1].coarse_own_to_view[own1]] = [0, 0]
            second[c.views[1].tree.owners == 0] = [90, 10]
        else:
            first[own0] = [4, 6]
            second[own1] = [0, 0]
            second[own0] = [90, 10]
        mass = c.combine_mass(arm, first, second)
        np.testing.assert_array_equal(mass[own0], [[4, 6]])
        np.testing.assert_array_equal(mass[own1], [[0, 0]])
        assert not mass.flags.writeable


@pytest.mark.parametrize(
    "phase,delta,accepted",
    [("whole", 5e-10, False), ("post_warm", 5e-10, False), ("whole", 5e-13, True)],
)
def test_repacked_support_uses_frozen_unitless_not_chip_tolerance(
    complete: dict[str, Any],
    tmp_path: Path,
    phase: str,
    delta: float,
    accepted: bool,
) -> None:
    s = copy.deepcopy(complete["saved"])
    # Repack a fully valid archive with unchanged policy bits and consistent
    # metadata/file hashes. Only independent support recomputation can catch it.
    chosen = next(r for r in s["rows"] if r["coverage"] is not None)
    for row, blob in read_archive(
        complete["folder"] / s["details_file"], s["details_sha256"], s["rows"]
    ):
        destination = tmp_path / row["file"]
        destination.parent.mkdir(parents=True, exist_ok=True)
        if row is chosen:
            context = scoring(complete["contexts"][row["coordinate"] // 3], row)
            detail = decode(blob, context, row)
            value = row["coverage"][phase]["all"]["uniform_reach_fraction"]
            row["coverage"][phase]["all"]["uniform_reach_fraction"] = (
                value - delta if value > 0 else value + delta
            )
            meta = {
                k: v
                for k, v in row.items()
                if k not in {"receipt", "metadata_sha256", "file"}
            }
            row["receipt"] = write_snapshot(
                destination,
                context.partition,
                unpack_policy(context.partition, detail["policy"]),
                meta,
            )
            row["metadata_sha256"] = sha(meta)
            metadata(row)
        else:
            destination.write_bytes(blob)
    archive = complete["folder"] / (tmp_path.name + "-details.jsonl.gz")
    s["details_file"] = archive.name
    s["details_sha256"] = write_archive(archive, tmp_path, s["rows"])

    def check() -> dict[str, Any]:
        return replay(
            complete["folder"],
            s,
            Design(TOY, TOY_WORK),
            lambda i: complete["contexts"][i // 3],
            complete["opponents"],
            BINDING,
            Deadline(180),
        )

    if accepted:
        result = check()
        assert result["maximum_error"] == 0
        assert 0 < result["maximum_unitless_error"] <= 1e-12
    else:
        with pytest.raises(ArithmeticError, match="unitless"):
            check()


@pytest.fixture(scope="module")
def schema_standin(complete: dict[str, Any]) -> dict[str, Any]:
    """MOCK copied own scalars for schema tests, NOT an independent native audit."""
    own = complete["saved"]
    profiles = []
    names = dict(
        exact_root_chips="exact_reply_value_chips",
        restricted_root_chips="restricted_reply_value_chips",
        achieved_exact_chips="exact_reply_value_chips",
        achieved_restricted_chips="restricted_reply_value_chips",
        achieved_river_before_chips="river_before_value_chips",
    )
    for row in own["rows"]:
        profiles.append(
            dict(
                id=row["id"],
                coordinate=row["coordinate"],
                scope=row["scope"],
                policy_sha256=row["receipt"]["policy_sha256"],
                own_reply_sha256=copy.deepcopy(row["reply_sha256"]),
                native_metrics=dict(row["metrics"]),
                maximum_error_chips=0.0,
                responses=[
                    dict(
                        target=t,
                        **{k: row["responses"][t][v] for k, v in names.items()},
                    )
                    for t in (0, 1)
                ],
            )
        )
    fixed = [
        dict(
            **{k: r[k] for k in (*native.FIXED_IDENTITY, *native.FIXED_VALUES)},
            maximum_error_chips=0.0,
        )
        for r in own["fixed_conditions"]
    ]
    return dict(
        profiles=profiles,
        fixed_conditions=fixed,
        coordinates=list(range(6)),
        maximum_error_chips=0.0,
        reference_actions_exported=False,
        reference_output_used_in_training=False,
        training_performed=False,
    )


def test_mock_native_schema_complete_inventory_only(
    complete: dict[str, Any],
    schema_standin: dict[str, Any],
) -> None:
    checked = native.validate_rows(schema_standin, complete["saved"])
    assert checked["profiles"] == 432 and checked["fixed_conditions"] == 1152
    # No reference was constructed. A zero mock error proves schema acceptance
    # only; it is never saved or reported as independent numerical agreement.


@pytest.fixture(scope="module")
def mock_native_workers(schema_standin: dict[str, Any]) -> dict[str, Any]:
    # Copied own scalars test worker schema ONLY. Not native agreement evidence.
    workers = []
    for slot, indices in enumerate(partition(6, 3)):
        events = [
            dict(kind="cell", phase=phase, index=r["coordinate"], result=r)
            for name, phase in (("profiles", "self"), ("fixed_conditions", "fixed"))
            for r in schema_standin[name]
            if r["coordinate"] in indices
        ]
        events.append(
            dict(
                kind="done",
                summary=dict(
                    scope=TOY,
                    profiles=144,
                    fixed_conditions=384,
                    maximum_error_chips=0.0,
                ),
            )
        )
        workers.append(dict(slot=slot, exitcode=0, messages=events))
    return dict(
        status="completed",
        failure=None,
        worker_count=3,
        assignments=partition(6, 3),
        workers=workers,
    )


@pytest.mark.parametrize(
    "change",
    [
        "none",
        "missing",
        "duplicate",
        "coordinate",
        "assignment",
        "exit",
        "done",
        "maximum",
    ],
)
def test_native_worker_schema_requires_every_coordinate_and_raw_result(
    complete: dict[str, Any],
    mock_native_workers: dict[str, Any],
    change: str,
) -> None:
    batch = copy.deepcopy(mock_native_workers)
    worker = batch["workers"][0]
    if change == "none":
        result = gather_independent(batch, complete["saved"])
        assert len(result["profiles"]) == 432
        assert len(result["fixed_conditions"]) == 1152
        return
    if change == "missing":
        worker["messages"].pop(0)
    elif change == "duplicate":
        worker["messages"].insert(0, copy.deepcopy(worker["messages"][0]))
    elif change == "coordinate":
        worker["messages"][0]["index"] = False
    elif change == "assignment":
        batch["assignments"][0].reverse()
    elif change == "exit":
        worker["exitcode"] = 1
    elif change == "done":
        worker["messages"].pop()
    else:
        worker["messages"][-1]["summary"]["maximum_error_chips"] = 1.0
    with pytest.raises(ArithmeticError):
        gather_independent(batch, complete["saved"])


@pytest.mark.parametrize(
    "change",
    [
        "missing_profile",
        "duplicate_profile",
        "missing_fixed",
        "duplicate_fixed",
        "bool_coordinate",
        "bool_target",
        "reply",
        "nan_metric",
        "nan_root",
        "root_error",
        "fixed_error",
        "max_error",
        "coordinates",
        "export",
        "training",
    ],
)
def test_mock_native_schema_rejects_incomplete_nonfinite_or_wrong_source(
    complete: dict[str, Any],
    schema_standin: dict[str, Any],
    change: str,
) -> None:
    bad = copy.deepcopy(schema_standin)
    if change == "missing_profile":
        bad["profiles"].pop()
    elif change == "duplicate_profile":
        bad["profiles"].append(copy.deepcopy(bad["profiles"][0]))
    elif change == "missing_fixed":
        bad["fixed_conditions"].pop()
    elif change == "duplicate_fixed":
        bad["fixed_conditions"].append(dict(bad["fixed_conditions"][0]))
    elif change == "bool_coordinate":
        bad["profiles"][0]["coordinate"] = False
    elif change == "bool_target":
        bad["fixed_conditions"][0]["target"] = False
    elif change == "reply":
        bad["profiles"][0]["own_reply_sha256"][0]["exact"] = "b" * 64
    elif change == "nan_metric":
        bad["profiles"][0]["native_metrics"]["value_player_zero_chips"] = float("nan")
    elif change == "nan_root":
        bad["profiles"][0]["responses"][1]["exact_root_chips"] = float("nan")
    elif change == "root_error":
        bad["profiles"][0]["responses"][1]["exact_root_chips"] += 0.1
        bad["profiles"][0]["maximum_error_chips"] = 0.1
    elif change == "fixed_error":
        bad["fixed_conditions"][0]["fine_reply_gain_chips"] += 0.1
        bad["fixed_conditions"][0]["maximum_error_chips"] = 0.1
    elif change == "max_error":
        bad["maximum_error_chips"] = 0.1
    elif change == "coordinates":
        bad["coordinates"] = [False, 1, 2, 3, 4, 5]
    elif change == "export":
        bad["reference_actions_exported"] = True
    else:
        bad["training_performed"] = True
    with pytest.raises(ArithmeticError):
        native.validate_rows(bad, complete["saved"])


def test_complete_numeric_report_retains_all_conditions_and_toy_scope(
    complete: dict[str, Any],
    tmp_path: Path,
) -> None:
    design = Design(TOY, TOY_WORK)
    first = write(
        tmp_path / "first", complete["saved"], design, (1.0, 1.0), no_plots=True
    )
    second = write(
        tmp_path / "second", complete["saved"], design, (1.0, 1.0), no_plots=True
    )
    assert first == second
    assert set(first) == {"arm-points.csv", "fixed-conditions.csv", "summary.json"}
    summary = json.loads((tmp_path / "first/summary.json").read_text())
    assert summary["arm_points"] == 216 and summary["fixed_conditions"] == 1152
    assert summary["poker_results"] is False
    assert summary["new_agent_default"] is summary["fresh_global_admission"] is False
    assert all(
        g["accuracy_limits_pass"] is g["paired_improvement_pass"] is None
        for g in summary["primary"]["groups"]
    )
    with pytest.raises(FileExistsError):
        write(tmp_path / "first", complete["saved"], design, (1.0, 1.0), no_plots=True)


def synthetic_primary() -> list[dict[str, Any]]:
    """Invented boundary-test inputs, never experiment results or archived evidence."""
    return [
        dict(
            game=g,
            arm=arm,
            seed=seed,
            readout="linear_average",
            work_label=10_000_000,
            exact_exploitability=0.5 if arm == "mixed_pair" else 3.0,
            whole_all_uniform_reach_fraction=0.95,
            post_warm_all_uniform_reach_fraction=0.1,
        )
        for g in (0, 1)
        for arm in ("coarse_self", "coarse_pair", "mixed_pair", "fine_self")
        for seed in SEEDS
    ]


@pytest.mark.parametrize(
    "change", ["none", "median", "worst", "coverage", "paired", "one_game", "secondary"]
)
def test_primary_boundaries_and_both_games_remain_separate(change: str) -> None:
    rows = synthetic_primary()
    selected = [r for r in rows if r["game"] == 1 and r["arm"] == "mixed_pair"]
    if change == "median":
        for r in selected:
            r["exact_exploitability"] = 1.0000001
    elif change == "worst":
        selected[0]["exact_exploitability"] = 2.5000001
    elif change == "coverage":
        selected[0]["whole_all_uniform_reach_fraction"] = 0.9499999
    elif change in ("paired", "one_game"):
        for r in rows:
            if r["game"] == 1 and r["arm"] == "coarse_pair":
                r["exact_exploitability"] = 0.5 if change == "paired" else 0.1
    elif change == "secondary":
        for r in selected:
            r["exact_exploitability"] = 5.0
        rows.extend(
            [
                dict(r, readout="uniform_average", exact_exploitability=0.0)
                for r in selected
            ]
        )
    groups = assessment(rows, Design(REAL, WORK))["groups"]
    assert groups[0]["accuracy_limits_pass"] and groups[0]["paired_improvement_pass"]
    if change == "none":
        assert (
            groups[1]["accuracy_limits_pass"] and groups[1]["paired_improvement_pass"]
        )
        assert groups[1]["historical_whole_average_coverage_pass"]
    elif change in ("median", "worst", "secondary"):
        assert groups[1]["accuracy_limits_pass"] is False
    elif change == "coverage":
        assert groups[1]["historical_whole_average_coverage_pass"] is False
    else:
        assert groups[1]["paired_improvement_pass"] is False
