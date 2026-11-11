"""Own-engine integration on uniform UNIT fixtures; no learned-policy study."""

import copy
import gzip
import json
import time
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import numpy as np
import pytest

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.opponent_decision_inputs import Profile
from poker_ai.evaluation.opponent_learning_sources import build_game
from poker_ai.evaluation.river_range_case import Inventory, analyse_profile, grouped
from poker_ai.evaluation.river_range_io import validate_suffix
from poker_ai.evaluation.river_range_math import RangeMixture
from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.opponent_views import tree_digest
from poker_ai.postflop.reply_diagnosis import analyse

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module", params=[0, 1])
def uniform(
    request: pytest.FixtureRequest,
) -> tuple[Profile, dict[str, Any], dict[str, Any]]:
    game = int(request.param)
    context = build_game(ROOT, game)
    policy = context.coarse.normalize(context.coarse.legal)
    row = dict(
        id="UNIT_ONLY_UNIFORM",
        **score_data(
            context.scoring["coarse"], context.scoring["coarse"].score(policy)
        ),
        origin="UNIT_ONLY_COMPOSED_PROFILE",
        receipt=dict(policy_sha256=array_sha(policy)),
    )
    fine = context.scoring["coarse"].expand(policy)
    policy.flags.writeable = fine.flags.writeable = False
    profile = Profile(
        3 * game,
        ("dev_low_oop", "dev_medium_oop")[game],
        20261301,
        "coarse_self",
        row,
        context,
        policy,
        fine,
    )
    s, d = analyse(
        cast(MatrixTree, context.fine),
        cast(MatrixTree, context.coarse),
        fine,
        top=10,
        examples=4,
        tolerance=1e-9,
    )
    return profile, json.loads(canonical(s)), json.loads(canonical(d))


def config() -> dict[str, Any]:
    value: dict[str, Any] = json.loads(
        (ROOT / "configs/river-range-reweighting.json").read_text()
    )
    return value


def test_uniform_own_engine_reconstructs_every_river_row_and_frozen_suffix(
    uniform: tuple[Profile, dict[str, Any], dict[str, Any]],
) -> None:
    p, s, d = uniform
    before = (
        array_sha(p.policy),
        array_sha(p.fine_policy),
        tree_digest(p.contexts.fine),
    )
    cache: dict[tuple[str, int], Inventory] = {}
    summary, detail = analyse_profile(p, s, d, config(), cache)
    assert len(cache) == 2
    assert [r["target"] for r in summary["responses"]] == [0, 1]
    for response, full in zip(summary["responses"], detail["responses"], strict=True):
        target = response["target"]
        mask = cache[p.game, target].river
        expected = list(np.flatnonzero(mask))
        assert len(full["declared_opponent_range"]) == 2
        for suffix, rows in zip(response["suffixes"], full["suffixes"], strict=True):
            validate_suffix(suffix, rows, len(full["declared_opponent_range"]))
            assert suffix["river_info_ids"] == expected
            assert [r["exact_info"] for r in rows["rows"]] == expected
            assert suffix["maximum_source_chip_error"] < 1e-9
            assert suffix["maximum_unitless_error"] < 1e-12
            assert [m["range_weights"] for m in suffix["panels"]] == [
                "actual_posterior",
                "compatible_prior",
            ]
            for row in rows["rows"]:
                assert len(row["actual_action_values_chips"]) == len(row["actions"])
                assert len(row["combo_action_values_chips"]) == 2
                assert row["saved_reach_mass"] >= 0
            a, b = suffix["panels"]
            assert (
                a["group_controls"]["declared_partition"][
                    "supported_uniform_decision_weight"
                ]
                == b["group_controls"]["declared_partition"][
                    "supported_uniform_decision_weight"
                ]
            )
    assert before == (
        array_sha(p.policy),
        array_sha(p.fine_policy),
        tree_digest(p.contexts.fine),
    )


def test_wrong_cached_game_inventory_is_rejected(
    uniform: tuple[Profile, dict[str, Any], dict[str, Any]],
) -> None:
    from poker_ai.evaluation.river_range_case import inventory

    p, s, d = uniform
    wrong = replace(
        inventory(cast(MatrixTree, p.contexts.fine), 0), tree_sha256="NOT_THIS_GAME"
    )
    with pytest.raises(ArithmeticError, match="another game"):
        analyse_profile(p, s, d, config(), {(p.game, 0): wrong})


@pytest.mark.parametrize("change", ["reply", "root", "row", "mass"])
def test_uniform_source_corruption_is_rejected(
    uniform: tuple[Profile, dict[str, Any], dict[str, Any]], change: str
) -> None:
    p, old_s, old_d = uniform
    s, d = copy.deepcopy(old_s), copy.deepcopy(old_d)
    if change == "reply":
        row = d["responses"][0]["exact_reply_profile"][0]
        changed = (int(np.argmax(row)) + 1) % len(row)
        row[:] = [float(i == changed) for i in range(len(row))]
    elif change == "root":
        s["responses"][0]["exact_reply_value_chips"] += 1
    elif change == "row":
        d["responses"][0]["infos"].pop()
    else:
        # Pick an actual river row, not a turn row outside this diagnostic.
        from poker_ai.evaluation.river_range_case import inventory

        inv = inventory(cast(MatrixTree, p.contexts.fine), 0)
        info = inv.rows[0]["exact_info"]
        next(r for r in d["responses"][0]["infos"] if r["exact_info"] == info)[
            "counterfactual_mass"
        ] += 1
    with pytest.raises(ArithmeticError):
        analyse_profile(p, s, d, config(), {})


def group_fixture() -> tuple[RangeMixture, list[dict[str, Any]]]:
    q = np.array([[4.0, 0.0], [0.0, 2.0]])
    data = RangeMixture(
        np.array([[0.2, 0.8], [0.8, 0.2]]),
        np.array([[0.5, 0.5], [0.5, 0.5]]),
        np.zeros((2, 2, 2)),
        q,
        q.copy(),
        np.ones(2),
        np.array([0.25, 0.75]),
        0.0,
        0.0,
    )
    features = dict(
        own_rank=[1, 2], range_compatibility=[True, True], range_relations=[1, -1]
    )
    rows = [
        dict(exact_info=i, actions=["a", "b"], static_features=copy.deepcopy(features))
        for i in (0, 1)
    ]
    return data, rows


def test_group_costs_keep_denominators_weights_and_refinement_control() -> None:
    data, rows = group_fixture()
    mapping = np.array([0, 0])
    metrics, detail = grouped(data, rows, mapping, data.actual_values)
    assert (
        metrics["declared_partition"]["local_sharing_cost_chips_per_weighted_decision"]
        == 1
    )
    assert metrics["declared_partition"]["strict_conflicting_groups"] == 1
    assert metrics["declared_partition"]["total_groups"] == 1
    assert metrics["full_static_probe_refinement"]["total_groups"] == 1
    assert detail["declared_partition"][0][
        "maximum_posterior_total_variation"
    ] == pytest.approx(0.6)
    rows[1]["static_features"]["own_rank"] = [1, 3]
    refined, _ = grouped(data, rows, mapping, data.actual_values)
    assert refined["full_static_probe_refinement"]["total_groups"] == 2
    assert (
        refined["full_static_probe_refinement"][
            "local_sharing_cost_chips_per_weighted_decision"
        ]
        == 0
    )


def test_group_support_filter_does_not_rescale_weights_and_singletons_are_zero() -> (
    None
):
    data, rows = group_fixture()
    data = replace(
        data, support=np.array([1.0, 0.0]), posterior=np.array([[0.2, 0.8], [0.0, 0.0]])
    )
    metrics, _ = grouped(data, rows, np.array([0, 0]), data.prior_values)
    assert metrics["declared_partition"]["supported_uniform_decision_weight"] == 0.25
    assert (
        metrics["declared_partition"]["local_sharing_cost_chips_per_weighted_decision"]
        == 0
    )
    assert metrics["declared_partition"]["strict_conflicting_groups"] == 0


def test_group_rejects_different_concrete_menus_and_inconsistent_static_prior() -> None:
    data, rows = group_fixture()
    rows[1]["actions"] = ["different", "b"]
    with pytest.raises(ArithmeticError, match="menu"):
        grouped(data, rows, np.array([0, 0]), data.actual_values)

    data, rows = group_fixture()
    data = replace(data, prior=np.array([[0.5, 0.5], [0.75, 0.25]]))
    with pytest.raises(ArithmeticError, match="compatible prior"):
        grouped(data, rows, np.array([0, 0]), data.actual_values)


def test_interruption_retains_first_complete_uniform_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    uniform: tuple[Profile, dict[str, Any], dict[str, Any]],
) -> None:
    from poker_ai.evaluation import river_range_run as runner

    p, s, d = uniform
    old_file = tmp_path / "UNIT-old-detail.json.gz"
    old_file.write_bytes(gzip.compress(canonical(d), mtime=0))
    previous = dict(s, source_id=p.row["id"], details_file=str(old_file))
    monkeypatch.setattr(runner, "contract", lambda r: config())
    monkeypatch.setattr(
        runner,
        "source_provenance",
        lambda *a, **k: dict(dirty=False, sha256={"UNIT_ONLY": "a" * 64}),
    )
    monkeypatch.setattr(runner, "prior", lambda *a: [previous])
    monkeypatch.setattr(runner, "checked", lambda *a: {"unit_only": True})
    monkeypatch.setattr(runner, "profiles", lambda *a: [p, p])
    actual = analyse_profile
    calls = 0

    def interrupted(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise KeyboardInterrupt("UNIT after first complete local profile")
        return actual(*args, **kwargs)

    monkeypatch.setattr(runner, "analyse_profile", interrupted)
    output = tmp_path / "partial"
    with pytest.raises(KeyboardInterrupt):
        runner.run(ROOT, output, time.perf_counter())
    assert len(json.loads((output / "partial.json").read_text())["profiles"]) == 1
    assert (output / f"details/{p.coordinate:02d}-{p.arm}.json.gz").is_file()
    assert json.loads((output / "failure.json").read_text())["completed_profiles"] == 1
