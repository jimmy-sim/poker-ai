"""Explicit toy reporting fixtures; numerical grids and optional six-figure layout."""

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.averaging_history_correctness import software_roundtrip
from poker_ai.evaluation.averaging_history_inputs import inputs
from poker_ai.evaluation.averaging_history_replay import replay_archives
from poker_ai.evaluation.averaging_history_report import FIGURES, write_report
from poker_ai.evaluation.averaging_history_software import software_inputs
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def explicit_toy_report(tmp_path_factory: pytest.TempPathFactory) -> tuple[Any, ...]:
    folder = tmp_path_factory.mktemp("averaging-report") / "EXPLICIT_SOFTWARE_FIXTURE"
    config = inputs(ROOT)
    software_roundtrip(config, folder, "f" * 64, Deadline(120))
    data = software_inputs(config, Deadline(120))
    path = folder / "own.json"
    saved = json.loads(path.read_text())
    _, matches = replay_archives(folder, path, saved, data, Deadline(120))
    saved["fixed_matches"] = matches
    return folder, data, saved


@pytest.mark.slow
def test_all_toy_numerical_tables_are_byte_identical_without_optional_packages(
    explicit_toy_report: tuple[Any, ...],
    tmp_path: Path,
) -> None:
    root, data, saved = explicit_toy_report
    outputs = (tmp_path / "first", tmp_path / "second")
    for output in outputs:
        report = write_report(
            root,
            data,
            saved,
            output,
            plots=False,
            pot=dict.fromkeys(data.config["spot_files"], 1.0),
            scope="EXPLICIT SOFTWARE FIXTURE — NOT POKER RESULTS",
        )
        assert report["profiles"] == 512
        assert report["fixed_opponent_target_conditions"] == 2048
        assert report["profile_mean_groups"] == 256
        assert report["fixed_mean_groups"] == 1024
        assert len(report["files"]) == 6
        assert report["figures"] == []
    for path in outputs[0].iterdir():
        assert path.read_bytes() == (outputs[1] / path.name).read_bytes()


@pytest.mark.slow
def test_toy_reporting_rejects_a_missing_seed_before_plotting(
    explicit_toy_report: tuple[Any, ...],
    tmp_path: Path,
) -> None:
    root, data, original = explicit_toy_report
    saved = copy.deepcopy(original)
    saved["rows"].pop()
    with pytest.raises(ArithmeticError):
        write_report(
            root,
            data,
            saved,
            tmp_path,
            plots=False,
            pot=dict.fromkeys(data.config["spot_files"], 1.0),
        )


@pytest.mark.slow
def test_all_six_toy_figures_exist_with_explicit_scope(
    explicit_toy_report: tuple[Any, ...],
    tmp_path: Path,
) -> None:
    pytest.importorskip("matplotlib")
    root, data, saved = explicit_toy_report
    report = write_report(
        root,
        data,
        saved,
        tmp_path,
        pot=dict.fromkeys(data.config["spot_files"], 1.0),
        scope="EXPLICIT SOFTWARE FIXTURE — NOT POKER RESULTS",
    )
    assert report["figures"] == list(FIGURES)
    assert all((tmp_path / name).stat().st_size > 1000 for name in FIGURES)
