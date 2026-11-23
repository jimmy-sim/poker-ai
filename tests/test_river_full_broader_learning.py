"""New two-spot grid reuses the qualified math without changing old sources."""

import sys
from pathlib import Path

import pytest

from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import study_river_full_broader as runner  # noqa: E402
from river_full_broader.control_capture import capture_path, replay_path  # noqa: E402
from river_full_broader.forecast import forecast  # noqa: E402
from river_full_broader.learning import (  # noqa: E402
    CANDIDATE,
    CONTROL,
    GAMES,
    LABELS,
    READOUTS,
    SEEDS,
    PathSpec,
    contract,
    paths,
)
from river_full_broader.report import checkpoint_contrasts, decision  # noqa: E402


def test_published_path_order_and_contract() -> None:
    plan = contract(ROOT)
    grid = paths()
    assert len(grid) == plan["paths"] == 8
    assert [row.index for row in grid] == list(range(8))
    assert [(row.game, row.seed, row.arm) for row in grid] == [
        (game, seed, CONTROL) if seed is not None else (game, 0, CANDIDATE)
        for game in GAMES
        for seed in (*SEEDS, None)
    ]
    assert LABELS == (100_000, 1_000_000, 10_000_000)
    assert READOUTS == ("current", "linear_average")


def test_toy_b4_capture_replay_and_refusal_to_replace(tmp_path: Path) -> None:
    scoring = software_context(0).scoring["coarse"]
    spec = PathSpec(0, "FICTIONAL_SIGNAL_GAME", SEEDS[0], CONTROL)
    folder = tmp_path / "control"
    saved = capture_path(scoring, spec, folder, "a" * 64, (80, 240), Deadline(10))
    assert len(saved["captures"]) == 4
    assert saved["path"] == vars(spec)
    assert replay_path(scoring, folder) == saved
    with pytest.raises(FileExistsError):
        capture_path(scoring, spec, folder, "a" * 64, (80, 240), Deadline(10))


def test_fixed_profile_uses_all_repeats_and_strict_cap() -> None:
    specs = paths()

    def profile(slow: bool) -> dict[str, object]:
        rows = []
        for index in range(24):
            spec = specs[index % 8]
            identity = dict(index=spec.index, game=spec.game, arm=spec.arm)
            if spec.arm == CONTROL:
                identity["seed"] = spec.seed
            rows.append(
                dict(
                    index=index,
                    repeat=index // 8,
                    path=identity,
                    captures=2,
                    final_work=1_000_000 if spec.arm == CANDIDATE else 100_000,
                    whole_path_seconds=20.0 if slow and index == 16 else 0.1,
                )
            )
        return dict(
            status="completed",
            worker_count=3,
            assignments=[list(range(slot, 24, 3)) for slot in range(3)],
            seconds=10.0,
            workers=[
                dict(
                    exitcode=0,
                    messages=[dict(kind="done", summary=dict(summaries=rows[slot::3]))],
                )
                for slot in range(3)
            ],
        )

    assert forecast(profile(False))["status"] == "admitted"
    rejected = forecast(profile(True))
    assert rejected["status"] == "rejected"
    assert rejected["per_path_maxima"][0]["maximum_seconds"] == 2000.0
    with pytest.raises(ArithmeticError, match="complete capped"):
        forecast(dict(status="completed", seconds=10.0, workers=[]))


def test_one_shared_candidate_and_historical_absolute_gates() -> None:
    final = []
    for game in GAMES:
        controls = (
            (0.035, 0.039, 0.036) if game == GAMES[0] else (0.001, 0.0012, 0.0009)
        )
        candidate = 0.006 if game == GAMES[0] else 0.0001
        for seed, value in zip(SEEDS, controls, strict=True):
            final.append(
                dict(
                    game=game,
                    seed=seed,
                    arm=CONTROL,
                    work_label=LABELS[-1],
                    readout="linear_average",
                    exploitability_fraction_initial_pot=value,
                    whole_coverage=1.0,
                    recall_violations=0,
                )
            )
        final.append(
            dict(
                game=game,
                seed=0,
                arm=CANDIDATE,
                work_label=LABELS[-1],
                readout="linear_average",
                exploitability_fraction_initial_pot=candidate,
                whole_coverage=1.0,
                recall_violations=0,
            )
        )
    assert decision(final)["classification"] == "positive"
    all_points = [dict(row, work_label=work) for work in LABELS for row in final]
    contrasts = checkpoint_contrasts(all_points)
    assert len(contrasts) == 6
    assert contrasts[0]["candidate_minus_each_control"] == [
        0.006 - value for value in (0.035, 0.039, 0.036)
    ]
    final[3]["whole_coverage"] = 0.94
    assert decision(final)["classification"] == "negative"


def test_fictional_proof_exercises_both_unchanged_learners(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(runner, "clean_revision", lambda root: "a" * 40)
    monkeypatch.setattr(runner, "source_fingerprint", lambda root: "b" * 64)
    monkeypatch.setattr(runner, "require_archive", lambda *args: None)
    output = tmp_path / "proof"
    runner.run_stage("proof", ROOT, output)
    import json

    record = json.loads((output / "result.json").read_bytes())
    assert record["status"] == "completed"
    assert [row["arm"] for row in record["rows"]] == [CONTROL, CANDIDATE]
    assert [row["captures"] for row in record["rows"]] == [6, 6]
    with pytest.raises(FileExistsError):
        runner.run_stage("proof", ROOT, output)
