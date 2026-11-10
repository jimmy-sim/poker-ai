"""Explicit fictional report fixtures, not new training or native agreement."""

import copy
import importlib.util
import itertools
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "diagnostic_cli", ROOT / "scripts/diagnose_private_prefix.py"
)
assert SPEC is not None and SPEC.loader is not None
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)


def fixture() -> tuple[dict[str, Any], dict[str, Any], dict[str, float]]:
    config = json.loads((ROOT / CLI.CONFIG).read_text())
    own: dict[str, Any] = dict(rows=[], baseline_rows=[], self_pairs=[])
    names = config["metrics"]
    for i, (game, representation, readout, label, seed) in enumerate(
        itertools.product(
            config["games"],
            config["representations"],
            config["readouts"],
            config["work_labels"],
            config["seeds"],
        )
    ):

        def row(
            role: str,
            total: float,
            within: float,
            river: float,
            value: float,
            i: int = i,
            game: str = game,
            representation: str = representation,
            seed: int = seed,
            label: int = label,
            readout: str = readout,
        ) -> dict[str, Any]:
            return dict(
                id=f"FICTIONAL-{role}-{i}",
                case=dict(
                    spot_file=f"configs/learning-spots/{game}.json",
                    representation=representation,
                    regret_rule="signed",
                    seed=seed,
                ),
                batch_size=4 if role != "B1" else 1,
                work_label=label,
                readout=readout,
                iteration=20,
                total_work=label + 10,
                metrics=dict(
                    zip(names, (total, within, 2.0, river, value), strict=True)
                ),
            )

        candidate = row("new", 3.0, 1.0, 10.0, 0.5)
        own["rows"].append(candidate)
        for kind, data, delta in (
            ("B1", (4.0, 2.0, 11.0, 0.25), (1.0, 1.0, 0.0, 1.0, -0.25)),
            ("IID", (2.0, 0.0, 9.0, 0.75), (-1.0, -1.0, 0.0, -1.0, 0.25)),
        ):
            peer = row(kind, *data)
            own["baseline_rows"].append(peer)
            own["self_pairs"].append(
                dict(
                    candidate_id=candidate["id"],
                    baseline_id=peer["id"],
                    baseline_kind=kind,
                    baseline_minus_candidate_chips=dict(zip(names, delta, strict=True)),
                )
            )
    return config, own, dict.fromkeys(config["games"], 100.0)


def test_full_panel_and_additive_components_keep_river_separate() -> None:
    config, own, pots = fixture()
    points, paired = CLI.panel(config, own, pots)
    assert len(points) == 324 and len(paired) == 216
    assert len(CLI.groups(points, "role", config)) == 108
    assert len(CLI.groups(paired, "baseline_kind", config)) == 72
    new = next(r for r in points if r["role"] == "stratified")
    assert new["exact_exploitability_pct_pot"] == 3.0
    assert (
        new["within_partition_gain_pct_pot"] + new["extra_information_gap_pct_pot"]
        == 3.0
    )
    assert new["river_only_gain_exact_prefix_pct_pot"] == 10.0
    assert new["post_warm_row_coverage"] is None
    assert {
        r["exact_exploitability_pct_pot"] for r in paired if r["baseline_kind"] == "B1"
    } == {1.0}
    assert {
        r["exact_exploitability_pct_pot"] for r in paired if r["baseline_kind"] == "IID"
    } == {-1.0}


@pytest.mark.parametrize(
    "bad",
    ["missing", "duplicate", "seed_type", "nan", "identity", "changed_gap", "pot"],
)
def test_reject_bad_panel_or_metric(bad: str) -> None:
    config, own, pots = fixture()
    if bad == "missing":
        own["rows"].pop()
    elif bad == "duplicate":
        own["rows"].append(copy.deepcopy(own["rows"][0]))
    elif bad == "seed_type":
        own["rows"][0]["case"]["seed"] = float(config["seeds"][0])
    elif bad == "nan":
        own["baseline_rows"][0]["metrics"]["value_player_zero_chips"] = float("nan")
    elif bad == "identity":
        own["rows"][0]["metrics"]["extra_information_gap_chips"] = 0.0
        for pair in own["self_pairs"][:2]:
            pair["baseline_minus_candidate_chips"]["extra_information_gap_chips"] = 2.0
    elif bad == "changed_gap":
        own["self_pairs"][0]["baseline_minus_candidate_chips"][
            "exact_exploitability_chips"
        ] = 0.0
    else:
        pots[config["games"][0]] = float("inf")
    with pytest.raises(ArithmeticError):
        CLI.panel(config, own, pots)


def test_self_comparison_gaps_remain_zero() -> None:
    config, own, pots = fixture()
    by_id = {r["id"]: r for r in own["rows"]}
    baseline = {r["id"]: r for r in own["baseline_rows"]}
    for pair in own["self_pairs"]:
        baseline[pair["baseline_id"]]["metrics"] = dict(
            by_id[pair["candidate_id"]]["metrics"]
        )
        pair["baseline_minus_candidate_chips"] = dict.fromkeys(config["metrics"], 0.0)
    _, paired = CLI.panel(config, own, pots)
    assert all(
        v == 0.0 for row in paired for k, v in row.items() if k.endswith("_pct_pot")
    )


def test_missing_seed_or_nonfinite_group_rejected() -> None:
    config, own, pots = fixture()
    points, _ = CLI.panel(config, own, pots)
    with pytest.raises(ArithmeticError):
        CLI.groups(points[1:], "role", config)
    points[0]["exact_exploitability_pct_pot"] = float("inf")
    with pytest.raises(ArithmeticError):
        CLI.groups(points, "role", config)


def test_no_overwrite_before_expensive_replay(tmp_path: Path) -> None:
    with (
        patch("sys.argv", ["diagnostic", "--output", str(tmp_path)]),
        patch.object(
            CLI, "read", side_effect=AssertionError("replay should not start")
        ),
    ):
        with pytest.raises(FileExistsError):
            CLI.main()


def test_optional_figure_smoke(tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    config, own, pots = fixture()
    points, _ = CLI.panel(config, own, pots)
    CLI.figure(points, config, tmp_path)
    assert (tmp_path / "components.png").read_bytes().startswith(b"\x89PNG")
