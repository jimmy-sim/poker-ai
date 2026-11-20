"""Prospective rule, grid, forecast and classification invariants."""

import copy
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from medium_dry_clipped.capture import capture_path, replay_path  # noqa: E402
from medium_dry_clipped.forecast import forecast  # noqa: E402
from medium_dry_clipped.gate import (  # noqa: E402
    ARMS,
    GAMES,
    SEEDS,
    WORK,
    fingerprint,
    fixed_contract,
    paths,
)
from medium_dry_clipped.learning import context, train  # noqa: E402
from medium_dry_clipped.report import TOP_TURN, decision, row_identity  # noqa: E402
from river_generalization.learning import PathSpec  # noqa: E402
from river_generalization.learning import train as historical_train  # noqa: E402

from poker_ai.evaluation.opponent_learning_contexts import software_context  # noqa: E402
from poker_ai.postflop.matrix import MatrixTree  # noqa: E402
from poker_ai.postflop.river_study import Deadline  # noqa: E402


def profile_record(slow: float = 3.0) -> dict[str, Any]:
    workers = []
    for slot in range(3):
        rows = []
        for index in range(slot, 36, 3):
            path_index, game, seed, arm = paths()[index % 12]
            rows.append(
                dict(
                    index=index,
                    repeat=index // 12,
                    path=dict(index=path_index, game=game, seed=seed, arm=arm),
                    captures=3,
                    final_work=100_000,
                    whole_path_seconds=slow if index == 7 else 1.0,
                )
            )
        workers.append(
            dict(exitcode=0, messages=[dict(kind="done", summary=dict(summaries=rows))])
        )
    return dict(
        status="completed",
        worker_count=3,
        assignments=[list(range(i, 36, 3)) for i in range(3)],
        seconds=10.0,
        workers=workers,
    )


def test_forecast_uses_all_36_paths_and_slowest_repeat() -> None:
    result = forecast(profile_record())
    assert result["status"] == "admitted"
    assert result["per_path_maxima"][7]["maximum_seconds"] == 300.0
    assert result["fixed_worker_sums_seconds"] == [400.0, 600.0, 400.0]
    assert result["strict_bound_seconds"] == 3600.0
    assert forecast(profile_record(15.0))["status"] == "rejected"
    missing = copy.deepcopy(profile_record())
    missing["workers"][0]["messages"][0]["summary"]["summaries"].pop()
    with pytest.raises(ArithmeticError, match="missing profile index"):
        forecast(missing)


def final_scores(
    candidate_medium: tuple[float, float, float],
    candidate_low: tuple[float, float, float] = (0.004, 0.004, 0.004),
) -> list[dict[str, Any]]:
    rows = []
    for _, game, seed, arm in paths():
        values = candidate_medium if game == GAMES[1] else candidate_low
        rows.append(
            dict(
                game=game,
                arm=arm,
                seed=seed,
                work_label=WORK[-1],
                readout="linear_average",
                exploitability_fraction_initial_pot=(
                    0.02 if game == GAMES[1] else 0.004
                )
                if arm == ARMS[0]
                else values[SEEDS.index(seed)],
                whole_coverage=1.0,
                recall_violations=0,
            )
        )
    return rows


def test_classification_keeps_absolute_and_paired_gates() -> None:
    assert decision(final_scores((0.007, 0.008, 0.009)))["classification"] == "positive"
    assert decision(final_scores((0.007, 0.008, 0.03)))["classification"] == "negative"
    assert (
        decision(final_scores((0.007, 0.008, 0.009), (0.006, 0.006, 0.006)))[
            "classification"
        ]
        == "negative"
    )
    near = final_scores((0.007, 0.008, 0.009))
    for row in near:
        if row["game"] == GAMES[1] and row["arm"] == ARMS[0]:
            row["exploitability_fraction_initial_pot"] = 0.008
    assert decision(near)["classification"] == "inconclusive"


def test_signed_rule_matches_historical_and_clipped_is_nonnegative() -> None:
    tree = software_context(0).scoring["coarse"].partition
    signed = train(tree, SEEDS[0], ARMS[0], (80, 240), Deadline(20), lambda *_: None)
    historical = historical_train(
        tree, SEEDS[0], (80, 240), Deadline(20), lambda *_: None
    )
    clipped = train(tree, SEEDS[0], ARMS[1], (80, 240), Deadline(20), lambda *_: None)
    assert signed.rules.regret_rule == "signed"
    assert clipped.rules.regret_rule == "clipped"
    assert signed.nodes_visited == historical.nodes_visited
    assert np.array_equal(signed.regrets, historical.regrets)
    assert np.array_equal(signed.ledger("linear"), historical.ledger("linear"))
    assert np.all(clipped.regrets >= 0)


def test_both_arms_use_identical_river_information() -> None:
    root = Path(__file__).resolve().parents[1]
    for game in GAMES:
        signed = context(root, game, ARMS[0])
        clipped = context(root, game, ARMS[1])
        assert signed.partition.keys == clipped.partition.keys
        assert np.array_equal(signed.exact_to_partition, clipped.exact_to_partition)


def test_preselected_turn_rows_remain_valid_on_medium_spot() -> None:
    root = Path(__file__).resolve().parents[1]
    exact = context(root, GAMES[1], ARMS[0]).exact
    assert isinstance(exact, MatrixTree)
    for info in TOP_TURN:
        identity = row_identity(exact, info)
        assert identity["street"] == "TURN"
        assert len(identity["board"]) == 4


def test_published_contract_and_isolated_source_set() -> None:
    root = Path(__file__).resolve().parents[1]
    assert fixed_contract(root)["seeds"] == list(SEEDS)
    assert len(fingerprint(root)) == 64


def test_both_rules_capture_and_replay_fictional_policies(tmp_path: Path) -> None:
    scoring = software_context(0).scoring["coarse"]
    for index, arm in enumerate(ARMS):
        folder = tmp_path / arm
        saved = capture_path(
            scoring,
            PathSpec(index, "FICTIONAL_SIGNAL_GAME", SEEDS[0], arm),
            folder,
            "a" * 64,
            (80, 240, 720),
            Deadline(20),
        )
        assert len(saved["captures"]) == 9
        assert replay_path(scoring, folder) == saved
        with pytest.raises(FileExistsError):
            capture_path(
                scoring,
                PathSpec(index, "FICTIONAL_SIGNAL_GAME", SEEDS[0], arm),
                folder,
                "a" * 64,
                (80, 240, 720),
                Deadline(20),
            )
