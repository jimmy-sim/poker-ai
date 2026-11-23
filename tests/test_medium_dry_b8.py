"""Prospective B8 grid, update identity, forecast and saved-policy gates."""

import copy
import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.random import PCG64, Generator

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from medium_dry_b8.capture import capture_path, replay_path  # noqa: E402
from medium_dry_b8.forecast import forecast  # noqa: E402
from medium_dry_b8.gate import (  # noqa: E402
    ARM,
    CONTROL_ARM,
    CONTROL_NATIVE,
    CONTROL_NATIVE_SHA256,
    CONTROL_OWN,
    CONTROL_OWN_SHA256,
    GAMES,
    SEEDS,
    WORK,
    fingerprint,
    fixed_contract,
    paths,
)
from medium_dry_b8.learning import context, train  # noqa: E402
from medium_dry_b8.report import TOP_RIVER, TOP_TURN, decision, row_identity  # noqa: E402
from medium_dry_clipped.learning import context as control_context  # noqa: E402
from river_generalization.learning import PathSpec  # noqa: E402

from poker_ai.evaluation.opponent_learning_contexts import software_context  # noqa: E402
from poker_ai.postflop.controlled_training import Rules  # noqa: E402
from poker_ai.postflop.frozen_batches import FrozenBatchTrainer, observe  # noqa: E402
from poker_ai.postflop.matrix import MatrixTree  # noqa: E402
from poker_ai.postflop.river_study import Deadline  # noqa: E402


def profile_record(slow: float = 3.0) -> dict[str, Any]:
    workers = []
    for slot in range(3):
        rows = []
        for index in range(slot, 18, 3):
            path_index, game, seed, arm = paths()[index % 6]
            rows.append(
                dict(
                    index=index,
                    repeat=index // 6,
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
        assignments=[list(range(i, 18, 3)) for i in range(3)],
        seconds=10.0,
        workers=workers,
    )


def test_forecast_uses_all_18_paths_and_slowest_repeat() -> None:
    result = forecast(profile_record())
    assert result["status"] == "admitted"
    assert result["per_path_maxima"][1]["maximum_seconds"] == 300.0
    assert result["fixed_worker_sums_seconds"] == [200.0, 400.0, 200.0]
    assert result["strict_bound_seconds"] == 2800.0
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
    for _, game, seed, _ in paths():
        values = candidate_medium if game == GAMES[1] else candidate_low
        for arm in (CONTROL_ARM, ARM):
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
                    if arm == CONTROL_ARM
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
        if row["game"] == GAMES[1] and row["arm"] == CONTROL_ARM:
            row["exploitability_fraction_initial_pot"] = 0.008
    assert decision(near)["classification"] == "inconclusive"


def test_b8_matches_independent_frozen_trainer_at_same_seed() -> None:
    tree = software_context(0).scoring["coarse"].partition
    actual = train(tree, SEEDS[0], ARM, (80, 240), Deadline(20), lambda *_: None)
    reference = FrozenBatchTrainer(
        tree,
        Generator(PCG64(SEEDS[0])),
        batch_size=8,
        rules=Rules("signed", "linear", "linear"),
    )
    reference.initialize_exact()
    observe(reference, (80, 240), lambda _: None, Deadline(20))
    assert actual.batch_size == 8 and actual.rules.regret_rule == "signed"
    assert actual.nodes_visited == reference.nodes_visited
    assert actual.iteration == reference.iteration
    assert np.array_equal(actual.regrets, reference.regrets)
    assert np.array_equal(actual.ledger("linear"), reference.ledger("linear"))
    assert np.array_equal(actual.ledger("uniform"), reference.ledger("uniform"))


def test_b8_and_published_b4_use_identical_information() -> None:
    root = Path(__file__).resolve().parents[1]
    for game in GAMES:
        candidate = context(root, game, ARM)
        control = control_context(root, game, CONTROL_ARM)
        assert candidate.partition.keys == control.partition.keys
        assert np.array_equal(candidate.exact_to_partition, control.exact_to_partition)


def test_preselected_turn_rows_remain_valid() -> None:
    root = Path(__file__).resolve().parents[1]
    exact = context(root, GAMES[1], ARM).exact
    assert isinstance(exact, MatrixTree)
    for info in TOP_TURN:
        identity = row_identity(exact, info)
        assert identity["street"] == "TURN" and len(identity["board"]) == 4
    for info in TOP_RIVER:
        identity = row_identity(exact, info)
        assert identity["street"] == "RIVER" and len(identity["board"]) == 5


def test_published_contract_and_control_pins() -> None:
    root = Path(__file__).resolve().parents[1]
    plan = fixed_contract(root)
    assert plan["seeds"] == list(SEEDS)
    assert plan["control"]["own_manifest_sha256"] == CONTROL_OWN_SHA256
    assert plan["control"]["native_manifest_sha256"] == CONTROL_NATIVE_SHA256
    assert len(fingerprint(root)) == 64


def test_control_pairing_uses_only_published_signed_paths() -> None:
    root = Path(__file__).resolve().parents[1]
    native = json.loads((root / CONTROL_NATIVE / "result.json").read_bytes())
    assert native["status"] == "completed" and len(native["rows"]) == 108
    audited = {row["path_index"] for row in native["rows"]}
    for _, game, seed, _ in paths():
        control_index = (0 if game == GAMES[0] else 6) + 2 * SEEDS.index(seed)
        summary = json.loads(
            (
                root
                / CONTROL_OWN
                / "study"
                / f"path{control_index:02d}"
                / "summary.json"
            ).read_bytes()
        )
        assert summary["path"] == dict(
            index=control_index, game=game, seed=seed, arm=CONTROL_ARM
        )
        assert summary["labels"] == list(WORK)
        assert control_index in audited


def test_b8_capture_replays_and_refuses_overwrite(tmp_path: Path) -> None:
    scoring = software_context(0).scoring["coarse"]
    folder = tmp_path / ARM
    spec = PathSpec(0, "FICTIONAL_SIGNAL_GAME", SEEDS[0], ARM)
    saved = capture_path(scoring, spec, folder, "a" * 64, (80, 240, 720), Deadline(20))
    assert len(saved["captures"]) == 9
    assert all(
        row["metadata"]["rng_state"]["bit_generator"] == "PCG64"
        for row in saved["captures"]
    )
    assert replay_path(scoring, folder) == saved
    with pytest.raises(FileExistsError):
        capture_path(scoring, spec, folder, "a" * 64, (80, 240, 720), Deadline(20))
