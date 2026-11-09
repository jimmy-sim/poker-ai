"""Toy-only figures and byte-identical report tables; no Hold'em outcomes."""

import copy
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.window_fallback_report import FIGURES, write_report
from poker_ai.evaluation.window_fallback_software import software_roundtrip
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def toy_report(tmp_path_factory: pytest.TempPathFactory) -> tuple[Any, ...]:
    folder = tmp_path_factory.mktemp("fallback-report") / "EXPLICIT_SOFTWARE_FIXTURE"
    data, saved, _ = software_roundtrip(ROOT, folder, Deadline(120))
    return data, saved


@pytest.mark.slow
def test_seven_toy_numerical_files_repeat_byte_for_byte(
    toy_report: tuple[Any, ...], tmp_path: Path
) -> None:
    data, saved = toy_report
    outputs = [tmp_path / "first", tmp_path / "second"]
    for output in outputs:
        report = write_report(
            ROOT,
            data,
            saved,
            output,
            plots=False,
            pot=dict.fromkeys(data.config["spot_files"], 1.0),
            scope="EXPLICIT SOFTWARE FIXTURE — NOT POKER RESULTS",
        )
        assert report["self_profiles"] == 512
        assert report["support_rows"] == 1024
        assert report["additivity_panels"] == 128
        assert report["fixed_target_conditions"] == 2048
        assert report["profile_mean_groups"] == 256
        assert report["fixed_mean_groups"] == 1024
        assert len(report["files"]) == 7
        assert report["figures"] == []
    for path in outputs[0].iterdir():
        assert path.read_bytes() == (outputs[1] / path.name).read_bytes()


@pytest.mark.slow
def test_report_rejects_missing_seed_before_plotting(
    toy_report: tuple[Any, ...], tmp_path: Path
) -> None:
    data, original = toy_report
    saved = copy.deepcopy(original)
    saved["rows"].pop()
    with pytest.raises(ArithmeticError):
        write_report(
            ROOT,
            data,
            saved,
            tmp_path,
            plots=False,
            pot=dict.fromkeys(data.config["spot_files"], 1.0),
        )


@pytest.mark.slow
def test_all_four_explicit_toy_figures_render(
    toy_report: tuple[Any, ...], tmp_path: Path
) -> None:
    pytest.importorskip("matplotlib")
    data, saved = toy_report
    report = write_report(
        ROOT,
        data,
        saved,
        tmp_path,
        pot=dict.fromkeys(data.config["spot_files"], 1.0),
        scope="EXPLICIT SOFTWARE FIXTURE — NOT POKER RESULTS",
    )
    assert report["figures"] == list(FIGURES)
    assert all((tmp_path / name).stat().st_size > 1000 for name in FIGURES)
