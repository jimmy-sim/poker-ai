"""Report every synthetic cell/axis; figures here are explicitly fictional fixtures."""

import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.postflop import learning_protocol
from poker_ai.postflop.learning_report import logical_rows, render, write_report

ROOT = Path(__file__).resolve().parents[1]


def synthetic_study() -> tuple[dict[str, Any], dict[str, Any], dict[str, float]]:
    config, comparison, cells = learning_protocol.inputs(ROOT)
    rows = []
    for index, cell in enumerate(cells):
        for axis, labels in config["checkpoint_labels"].items():
            for target in labels:
                rows.append(
                    dict(
                        case=cell,
                        id=f"explicit-synthetic-{index}-{axis}-{target}",
                        labels=[[axis, target]],
                        iteration=target if axis == "iteration" else 2,
                        total_work=target + 1 if axis == "work" else 2,
                        previous_work=0,
                        state_sha256="f" * 64,
                        receipt=dict(policy_sha256="f" * 64),
                        diagnostics=dict(
                            regret_norm=0.0,
                            positive_average_coverage=1.0,
                            river_visit_coverage=None,
                            river_partition_rows=0,
                            river_partition_rows_visited=0,
                        ),
                        metrics=dict(
                            exact_exploitability_chips=0.0,
                            within_partition_gain_chips=0.0,
                            extra_information_gap_chips=0.0,
                            river_only_gain_exact_prefix_chips=0.0,
                            value_player_zero_chips=0.0,
                        ),
                    )
                )
    return (
        dict(rows=rows, batch=dict(seconds=1.0)),
        comparison,
        {g: 10.0 for g in comparison["spot_files"]},
    )


def test_all_tables_rebuild_identically_without_plotting_or_native(
    tmp_path: Path,
) -> None:
    saved, comparison, pots = synthetic_study()
    first = tmp_path / "first"
    second = tmp_path / "second"
    summary = write_report(saved, comparison, pots, first, plots=False)
    assert summary["logical_checkpoints"] == 840
    assert summary["factor_means"] == 1536
    assert summary["contrasts"] == 4512
    assert summary["bridge_rows"] == 96
    write_report(saved, comparison, pots, second, plots=False)
    for path in first.iterdir():
        assert path.read_bytes() == (second / path.name).read_bytes()
    assert all(
        r["overshoot"] == 1
        for r in logical_rows(saved["rows"], pots)
        if r["axis"] == "work"
    )
    assert "no default" in json.loads((first / "summary.json").read_text())["scope"]


@pytest.mark.slow
def test_all_eight_figures_mark_synthetic_scope_and_have_legends(
    tmp_path: Path,
) -> None:
    pytest.importorskip("matplotlib")
    saved, _, pots = synthetic_study()
    figures = render(
        logical_rows(saved["rows"], pots),
        tmp_path,
        scope="EXPLICIT SYNTHETIC SOFTWARE FIXTURE — NOT LEARNING RESULTS",
    )
    assert len(figures) == 8
    assert len(set(figures)) == 8
    for name in figures:
        assert (tmp_path / name).stat().st_size > 1000
    Image = pytest.importorskip("PIL.Image")

    with Image.open(tmp_path / figures[0]) as image:
        assert image.size == (1960, 1400)
