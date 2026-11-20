"""Prospective budget admission, classification and guarded toy proof."""

import copy
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from medium_dry_budget.forecast import forecast  # noqa: E402
from medium_dry_budget.gate import GAME, WORK, paths  # noqa: E402
from medium_dry_budget.report import TOP_TURN, decision, row_identity  # noqa: E402
from medium_dry_budget.study import run_stage  # noqa: E402
from river_generalization.learning import context  # noqa: E402
from river_generalization_diagnosis.analysis import (  # noqa: E402
    row_identity as historical_row_identity,
)

from poker_ai.postflop.matrix import MatrixTree  # noqa: E402


def profile_record(slow: float = 2.0) -> dict[str, Any]:
    workers = []
    for slot in range(3):
        rows = []
        for index in range(slot, 18, 3):
            path_index, seed, arm = paths()[index % 6]
            rows.append(
                dict(
                    index=index,
                    repeat=index // 6,
                    path=dict(
                        index=path_index, game="new_medium_dry_oop", seed=seed, arm=arm
                    ),
                    captures=3,
                    final_work=1_000_000,
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


def test_conservative_forecast_uses_slowest_repeat_and_rejects_incomplete() -> None:
    record = profile_record()
    result = forecast(record)
    assert result["status"] == "admitted"
    assert result["per_path_maxima"][1]["maximum_seconds"] == 200.0
    assert result["fixed_worker_sums_seconds"] == [200.0, 300.0, 200.0]
    assert result["strict_bound_seconds"] == 2400.0
    slow = forecast(profile_record(30.0))
    assert slow["status"] == "rejected"
    incomplete = copy.deepcopy(record)
    incomplete["workers"][0]["messages"][0]["summary"]["summaries"].pop()
    with pytest.raises(ArithmeticError, match="missing profile index"):
        forecast(incomplete)


def scores(
    candidate: tuple[float, float, float], control: float = 0.05
) -> list[dict[str, Any]]:
    rows = []
    for index, seed, arm in paths():
        rows.append(
            dict(
                seed=seed,
                arm=arm,
                work_label=WORK[-1],
                readout="linear_average",
                exploitability_fraction_initial_pot=control
                if index % 2 == 0
                else candidate[index // 2],
                whole_coverage=1.0,
                recall_violations=0,
            )
        )
    return rows


def test_classification_keeps_absolute_and_paired_gates_separate() -> None:
    assert decision(scores((0.005, 0.008, 0.009)))["classification"] == "positive"
    assert decision(scores((0.005, 0.008, 0.03)))["classification"] == "negative"
    assert decision(scores((0.03, 0.04, 0.05), 0.001))["classification"] == "negative"
    near = decision(scores((0.005, 0.008, 0.009), 0.008))
    assert near["classification"] == "inconclusive"
    assert near["paired_seed_differences"] == pytest.approx((-0.003, 0.0, 0.001))


def test_source_gate_precedes_toy_output(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from medium_dry_budget import study

    monkeypatch.setattr(study, "fixed_contract", lambda root: {})
    monkeypatch.setattr(study, "clean_head", lambda root: "0" * 40)
    monkeypatch.setattr(study, "fingerprint", lambda root: "a" * 64)

    def fail(*args: object) -> None:
        raise ArithmeticError("source qualification missing")

    monkeypatch.setattr(study, "require_stage", fail)
    output = tmp_path / "proof"
    with pytest.raises(ArithmeticError, match="source qualification missing"):
        run_stage("proof", tmp_path, output)
    assert not output.exists()

    monkeypatch.setattr(study, "require_stage", lambda *args: {})
    run_stage("proof", tmp_path, output)
    assert (output / "result.json").is_file()
    assert (output / "toy/summary.json").is_file()
    with pytest.raises(FileExistsError):
        run_stage("proof", tmp_path, output)


def test_fixed_turn_rows_use_the_original_observable_decisions() -> None:
    exact = context(
        Path(__file__).resolve().parents[1], GAME, "texture_range_q8_b8"
    ).exact
    assert isinstance(exact, MatrixTree)
    for info in TOP_TURN:
        identity = row_identity(exact, info)
        assert identity == historical_row_identity(exact, info)
        assert identity["street"] == "TURN"
        assert len(identity["board"]) == 4
