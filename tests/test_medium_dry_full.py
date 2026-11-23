"""Tiny-game math and capture guards for prospective full-pass river study."""

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.random import PCG64, Generator

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from medium_dry_clipped.learning import context as control_context  # noqa: E402
from medium_dry_full.capture import capture_path, replay_path  # noqa: E402
from medium_dry_full.forecast import forecast  # noqa: E402
from medium_dry_full.gate import (  # noqa: E402
    ARM,
    GAMES,
    PROFILE_WORK,
    SEEDS,
    WORK,
    fingerprint,
    fixed_contract,
    paths,
)
from medium_dry_full.learning import context as candidate_context  # noqa: E402
from medium_dry_full.learning import guard, readouts, train  # noqa: E402
from medium_dry_full.report import decision  # noqa: E402
from medium_dry_full.study import run_stage, save  # noqa: E402

from poker_ai.evaluation.opponent_learning_contexts import software_context  # noqa: E402
from poker_ai.postflop.controlled_training import (  # noqa: E402
    ArrayState,
    ControlledTrainer,
    Rules,
    expected_pass,
)
from poker_ai.postflop.river_study import Deadline  # noqa: E402
from poker_ai.training.mccfr import Updates, external_updates  # noqa: E402


class NeedChoice(Exception):
    def __init__(self, probabilities: np.ndarray[Any, Any]) -> None:
        self.probabilities = probabilities


def enumerate_external_mean(
    tree: Any, policy: np.ndarray[Any, Any], target: int
) -> tuple[np.ndarray[Any, Any], np.ndarray[Any, Any]]:
    """Enumerate every chance/opponent selector tape, including zero rows."""
    regrets = np.zeros_like(tree.legal)
    averages = np.zeros_like(tree.legal)
    lookup = {key: i for i, key in enumerate(tree.keys)}
    probability_total = 0.0

    def visit(prefix: tuple[int, ...], weight: float) -> None:
        nonlocal probability_total
        used = 0

        def select(probabilities: np.ndarray[Any, Any]) -> int:
            nonlocal used
            if used == len(prefix):
                raise NeedChoice(probabilities)
            choice = prefix[used]
            used += 1
            return choice

        def fixed(key: str, actions: tuple[int, ...]) -> np.ndarray[Any, Any]:
            return policy[lookup[key], : len(actions)]

        try:
            update: Updates = external_updates(ArrayState(tree), target, fixed, select)
        except NeedChoice as missing:
            for choice, probability in enumerate(missing.probabilities):
                if probability:
                    visit((*prefix, choice), weight * float(probability))
            return
        assert used == len(prefix)
        probability_total += weight
        for incoming, outgoing in (
            (update.regrets, regrets),
            (update.averages, averages),
        ):
            for key, values in incoming.items():
                outgoing[lookup[key], : len(values)] += weight * values

    visit((), 1.0)
    assert probability_total == pytest.approx(1.0)
    return regrets, averages


@pytest.mark.parametrize("target", [0, 1])
def test_full_pass_is_enumerated_external_mean(target: int) -> None:
    tree = software_context(0).scoring["coarse"].partition
    uniform = tree.normalize(tree.legal)
    expected = expected_pass(tree, uniform, target)
    regret_mean, average_mean = enumerate_external_mean(tree, uniform, target)
    for key, values in expected.regrets.items():
        i = tree.keys.index(key)
        assert np.allclose(values, regret_mean[i, : len(values)], atol=1e-11)
    for key, values in expected.averages.items():
        i = tree.keys.index(key)
        assert np.allclose(values, average_mean[i, : len(values)], atol=1e-11)
    assert expected.visited == len(tree.player)


def test_full_path_charges_exact_nodes_and_never_draws_rng() -> None:
    tree = software_context(0).scoring["coarse"].partition
    labels = (80, 240, 720)
    captured: list[tuple[int, int, int, str]] = []

    def at(point: Any, solver: ControlledTrainer, policies: dict[str, Any]) -> None:
        assert set(policies) == {"current", "linear_average"}
        assert all(not x.flags.writeable for x in policies.values())
        assert point.guard_sha256 == guard(solver)
        captured.extend(
            (label, point.previous_work, point.total_work, point.guard_sha256)
            for label in point.labels
        )

    solver = train(tree, labels, Deadline(10), at)
    assert [x[0] for x in captured] == list(labels)
    assert solver.initialization_visits == 2 * len(tree.player)
    assert solver.nodes_visited == 2 * len(tree.player) * solver.iteration
    assert all(before < label <= after for label, before, after, _ in captured)
    assert all(
        after - before == 2 * len(tree.player) for _, before, after, _ in captured
    )
    assert solver.rng.bit_generator.state == Generator(PCG64(0)).bit_generator.state
    assert np.all(np.isfinite(readouts(solver)["linear_average"]))


def test_adaptive_signed_linear_step_matches_enumerated_mean() -> None:
    tree = software_context(0).scoring["coarse"].partition
    solver = ControlledTrainer(
        tree,
        Generator(PCG64(0)),
        traversal="full",
        rules=Rules("signed", "linear", "linear"),
        average_phase="opponent_pass",
        average_mass="chance_own_reach",
    )
    regrets = np.zeros_like(tree.legal)
    averages = np.zeros_like(tree.legal)
    uniform = tree.normalize(tree.legal)
    for target in (0, 1):
        raw_regret, raw_average = enumerate_external_mean(tree, uniform, target)
        regrets[tree.owners == target] += raw_regret[tree.owners == target]
        averages[tree.owners != target] += raw_average[tree.owners != target]
    solver.initialize_exact()
    assert np.allclose(solver.regrets, regrets, atol=1e-11)
    assert np.allclose(solver.strategy_sum, averages, atol=1e-11)
    for target in (0, 1):
        policy = tree.normalize(np.maximum(regrets, 0))
        raw_regret, raw_average = enumerate_external_mean(tree, policy, target)
        regrets[tree.owners == target] += 2 * raw_regret[tree.owners == target]
        averages[tree.owners != target] += 2 * raw_average[tree.owners != target]
    solver.step()
    assert np.allclose(solver.regrets, regrets, atol=1e-11)
    assert np.allclose(solver.strategy_sum, averages, atol=1e-11)
    assert solver.nodes_visited == 4 * len(tree.player)


def test_candidate_preserves_known_game_information_keys() -> None:
    root = Path(__file__).resolve().parents[1]
    for game in GAMES:
        candidate = candidate_context(root, game, ARM)
        control = control_context(root, game, "signed_linear")
        assert candidate.partition.keys == control.partition.keys
        assert np.array_equal(candidate.exact_to_partition, control.exact_to_partition)


def test_callback_mutation_is_rejected_and_original_capture_is_retained() -> None:
    tree = software_context(0).scoring["coarse"].partition

    def corrupt(
        _point: Any, solver: ControlledTrainer, _policies: dict[str, Any]
    ) -> None:
        solver.regrets[0, 0] += 1.0

    with pytest.raises(ArithmeticError, match="observer mutated"):
        train(tree, (80,), Deadline(10), corrupt)


def test_fictional_capture_replays_exact_scores_and_support(tmp_path: Path) -> None:
    scoring = software_context(0).scoring["coarse"]
    folder = tmp_path / "full"
    saved = capture_path(
        scoring, 0, "FICTIONAL_SIGNAL_GAME", folder, "a" * 64, (80, 240), Deadline(10)
    )
    replayed = replay_path(scoring, folder)
    assert saved == replayed
    assert len(saved["captures"]) == 4
    assert saved["final_work"] >= 240
    assert saved["warm"]["metadata"]["origin"] == "warm"
    for row in saved["captures"]:
        if row["metadata"]["readout"] == "linear_average":
            assert row["support"]["whole"]["all"]["uniform_reach_fraction"] == 1
    with pytest.raises(FileExistsError):
        capture_path(
            scoring, 0, "FICTIONAL_SIGNAL_GAME", folder, "a" * 64, (80,), Deadline(10)
        )


def test_stage_failure_keeps_started_and_failure_receipts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from medium_dry_full import study

    monkeypatch.setattr(study, "fixed_contract", lambda _root: {})
    monkeypatch.setattr(study, "clean_head", lambda _root: "a" * 40)
    monkeypatch.setattr(study, "fingerprint", lambda _root: "b" * 64)
    monkeypatch.setattr(study, "require_stage", lambda *_args: {})

    def fail(*_args: Any) -> Any:
        raise ArithmeticError("deliberate fixture failure")

    monkeypatch.setattr(study, "capture_path", fail)
    output = tmp_path / "failed-proof"
    with pytest.raises(ArithmeticError, match="deliberate fixture failure"):
        run_stage("proof", Path(__file__).resolve().parents[1], output)
    started = json.loads((output / "started.json").read_text())
    failed = json.loads((output / "failure.json").read_text())
    assert started["status"] == "running"
    assert failed["status"] == "failed_retained"
    assert failed["failure"]["reason"] == "deliberate fixture failure"
    with pytest.raises(FileExistsError, match="retain existing"):
        save(output / "failure.json", {})


def test_protocol_and_parent_source_pins() -> None:
    root = Path(__file__).resolve().parents[1]
    plan = fixed_contract(root)
    assert tuple(plan["known_spots"]) == GAMES
    assert tuple(plan["control"]["seeds"]) == SEEDS
    assert tuple(plan["node_work_labels"]) == WORK
    assert len(paths()) == 2
    assert len(fingerprint(root)) == 64


def profile_record(slow: float = 10.0) -> dict[str, Any]:
    rows = []
    for index in range(6):
        path_index, game, arm = paths()[index % 2]
        rows.append(
            dict(
                index=index,
                repeat=index // 2,
                path=dict(index=path_index, game=game, arm=arm),
                captures=2,
                final_work=PROFILE_WORK,
                whole_path_seconds=slow if index == 3 else 1.0,
            )
        )
    return dict(
        status="completed",
        worker_count=1,
        assignments=[list(range(6))],
        seconds=100.0,
        workers=[
            dict(exitcode=0, messages=[dict(kind="done", summary=dict(summaries=rows))])
        ],
    )


def test_forecast_uses_all_six_repeats_and_strict_cap() -> None:
    result = forecast(profile_record())
    assert result["status"] == "admitted"
    assert result["per_path_maxima"][0]["maximum_seconds"] == 10.0
    assert result["per_path_maxima"][1]["maximum_seconds"] == 100.0
    assert result["strict_bound_seconds"] == 1640.0
    assert forecast(profile_record(200.0))["status"] == "rejected"
    missing = profile_record()
    missing["workers"][0]["messages"][0]["summary"]["summaries"].pop()
    with pytest.raises(ArithmeticError, match="missing profile index"):
        forecast(missing)


def final_scores(
    candidate_medium: float, candidate_low: float = 0.004
) -> list[dict[str, Any]]:
    rows = []
    for game in GAMES:
        for seed in SEEDS:
            rows.append(
                dict(
                    game=game,
                    arm="signed_linear",
                    seed=seed,
                    work_label=WORK[-1],
                    readout="linear_average",
                    exploitability_fraction_initial_pot=(
                        0.02 if game == GAMES[1] else 0.004
                    ),
                    whole_coverage=1.0,
                    recall_violations=0,
                )
            )
        rows.append(
            dict(
                game=game,
                arm=ARM,
                seed=None,
                work_label=WORK[-1],
                readout="linear_average",
                exploitability_fraction_initial_pot=(
                    candidate_medium if game == GAMES[1] else candidate_low
                ),
                whole_coverage=1.0,
                recall_violations=0,
            )
        )
    return rows


def test_classification_retains_absolute_and_shared_control_contrasts() -> None:
    assert decision(final_scores(0.007))["classification"] == "positive"
    assert decision(final_scores(0.03))["classification"] == "negative"
    assert decision(final_scores(0.007, 0.006))["classification"] == "negative"
    assert decision(final_scores(0.02))["classification"] == "negative"
    rows = final_scores(0.0095)
    for row in rows:
        if row["game"] == GAMES[1] and row["arm"] == "signed_linear":
            row["exploitability_fraction_initial_pot"] = 0.0095
    assert decision(rows)["classification"] == "inconclusive"


@pytest.mark.parametrize("labels", [(), (0,), (240, 80), (80, 80), (True,)])
def test_invalid_work_labels_rejected(labels: tuple[int, ...]) -> None:
    tree = software_context(0).scoring["coarse"].partition
    with pytest.raises(ValueError, match="fresh prescribed"):
        train(tree, labels, Deadline(10), lambda *_: None)
