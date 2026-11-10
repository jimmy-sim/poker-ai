"""Independent units/signs and complete joins; all numeric fixtures are invented."""

import copy
import json
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

import pytest

from poker_ai.evaluation.matched_update_data import SEEDS, Data, final_endpoints
from poker_ai.evaluation.matched_update_inputs import Sources
from poker_ai.evaluation.matched_update_presentation import (
    GROUP,
    METRICS,
    contrast,
    csv_file,
    means,
    number,
    views,
)


def metrics(value: float) -> dict[str, float]:
    return {
        m + "_chips": value * f
        for m, f in zip(METRICS, (1.0, 0.25, 0.75, 0.125, 0.5), strict=True)
    }


def fixture(tmp_path: Path) -> Data:
    prefixes = []
    pairs = []
    right: dict[str, dict[str, Any]] = {}
    full: dict[tuple[int, str], dict[str, Any]] = {}
    old_fixed = []
    new_fixed = []
    for i, seed in enumerate(SEEDS):
        case: dict[str, Any] = dict(
            spot_file="EXPLICIT-fixture.json",
            representation="EXPLICIT",
            regret_rule="signed",
            seed=seed,
        )
        common: dict[str, Any] = dict(
            case=case, batch_size=4, work_label=1000, total_work=1000, iteration=100
        )
        batch = dict(**common, id=f"right{i}", metrics=metrics(10 + i))
        endpoint = dict(common, id=f"full{i}", metrics=metrics(5 + i), iteration=400)
        prefix = dict(
            common,
            id=f"prefix{i}",
            metrics=metrics(20 + i),
            path_index=i,
            total_work=250,
        )
        prefixes.append(prefix)
        right[batch["id"]] = batch
        full[i, "linear_average"] = endpoint
        pairs.append(
            dict(
                target_id=f"target{i}",
                readout="linear_average",
                planned_prefix_id=prefix["id"],
                reused_profile_id=batch["id"],
                target_iteration=100,
            )
        )
        for op in range(4):
            for seat in (0, 1):
                fields = dict(
                    opponent_profile_id=f"EXPLICIT-op{op}",
                    target=seat,
                    opponent_policy_sha256="EXPLICIT-policy",
                    reply_sha256="EXPLICIT-reply",
                    restricted_reply_value_chips=15,
                    achieved_reply_value_chips=15,
                )
                old_fixed += [
                    dict(
                        **fields,
                        own_snapshot_id=batch["id"],
                        baseline_value_chips=10,
                        gain_chips=5,
                    ),
                    dict(
                        **fields,
                        own_snapshot_id=endpoint["id"],
                        baseline_value_chips=12,
                        gain_chips=3,
                    ),
                ]
                new_fixed.append(
                    dict(
                        **fields,
                        own_snapshot_id=prefix["id"],
                        baseline_value_chips=11,
                        gain_chips=4,
                    )
                )
    sources = cast(Sources, SimpleNamespace(fixed=old_fixed))
    return Data(
        tmp_path,
        dict(rows=prefixes, self_pairs=pairs, fixed_matches=new_fixed),
        sources,
        {},
        right,
        full,
        {"EXPLICIT-fixture.json": 100.0},
    )


def test_chips_to_percentage_points_and_self_zero() -> None:
    a = dict(metrics=metrics(9))
    b = dict(metrics=metrics(5))
    expected = contrast(a, b, 50)
    for m, factor in zip(METRICS, (1.0, 0.25, 0.75, 0.125, 0.5), strict=True):
        assert expected[m + "_delta_chips"] == 4 * factor
        assert expected[m + "_delta_pct_pot"] == 8 * factor
        assert contrast(a, a, 50)[m + "_delta_chips"] == 0
    assert expected["left_exact_pct_pot"] == 18
    assert expected["right_exact_pct_pot"] == 10


@pytest.mark.parametrize("bad", [True, float("nan"), float("inf")])
def test_nonfinite_and_boolean_values_rejected(bad: Any) -> None:
    with pytest.raises(ArithmeticError):
        number(bad)


@pytest.mark.parametrize("pot", [0, -1, float("inf"), True])
def test_invalid_pot_rejected(pot: float) -> None:
    with pytest.raises(ArithmeticError):
        contrast(dict(metrics=metrics(1)), dict(metrics=metrics(0)), pot)


def test_finite_input_overflow_rejected() -> None:
    with pytest.raises(ArithmeticError):
        contrast(dict(metrics=metrics(1e308)), dict(metrics=metrics(-1e308)), 1)


def test_both_axes_have_opposite_known_directions_and_fixed_signs(
    tmp_path: Path,
) -> None:
    data = fixture(tmp_path)
    points, fixed = views(data)
    assert len(points) == 6 and len(fixed) == 48
    for row in points:
        assert row["exact_exploitability_delta_pct_pot"] == (
            10 if row["axis"] == "same_updates" else -5
        )
        assert row["node_work_ratio"] == (0.25 if row["axis"] == "same_updates" else 1)
    for row in fixed:
        assert row["ev_delta_chips"] == (1 if row["axis"] == "same_updates" else 2)
        assert row["gain_delta_chips"] == -row["ev_delta_chips"]
    groups = means(points, GROUP, ("exact_exploitability_delta_pct_pot",))
    assert [r["mean_exact_exploitability_delta_pct_pot"] for r in groups] == [10, -5]
    # Original dictionaries and source metrics are unchanged.
    assert data.own["rows"][0]["metrics"]["exact_exploitability_chips"] == 20


@pytest.mark.parametrize(
    "fault", ["case", "iteration", "work_label", "opponent", "reply_root", "gain_sign"]
)
def test_crossed_identity_coordinate_or_fixed_root_rejected(
    tmp_path: Path, fault: str
) -> None:
    data = fixture(tmp_path)
    first = data.right["right0"]
    if fault == "case":
        first["case"] = dict(first["case"], seed=999)
    elif fault == "iteration":
        first["iteration"] += 1
    elif fault == "work_label":
        first["work_label"] += 1
    elif fault == "opponent":
        data.own["fixed_matches"][0]["opponent_policy_sha256"] = "changed"
    elif fault == "reply_root":
        data.own["fixed_matches"][0]["restricted_reply_value_chips"] += 1
    else:
        data.own["fixed_matches"][0]["gain_chips"] += 1
    with pytest.raises(ArithmeticError):
        views(data)


def test_all_seeds_required_no_duplicate_or_nonfinite_means() -> None:
    rows = [
        dict(group="EXPLICIT", seed=s, x=v)
        for s, v in zip(SEEDS, (1.0, 4.0, 7.0), strict=True)
    ]
    result = means(rows, ("group",), ("x",))[0]
    assert result["mean_x"] == 4 and result["min_x"] == 1 and result["max_x"] == 7
    for bad in (
        rows[:-1],
        [rows[0], rows[0], rows[2]],
        [*rows[:-1], dict(rows[-1], x=float("nan"))],
    ):
        with pytest.raises(ArithmeticError):
            means(bad, ("group",), ("x",))
    assert means(list(reversed(rows)), ("group",), ("x",)) == means(
        rows, ("group",), ("x",)
    )


def test_json_key_order_and_pair_order_do_not_change_export(tmp_path: Path) -> None:
    data = fixture(tmp_path)
    points, fixed = views(data)
    other = copy.deepcopy(data)
    other.own["self_pairs"].reverse()
    assert views(other) == (points, fixed)
    path = tmp_path / "a.csv"
    second = tmp_path / "b.csv"
    csv_file(path, points)
    csv_file(second, json.loads(json.dumps(points, sort_keys=True)))
    assert path.read_bytes() == second.read_bytes()
    with pytest.raises(FileExistsError):
        csv_file(path, points)


def test_final_current_join_uses_ids_not_older_tuple_index_shape() -> None:
    currents = {}
    scored = {}
    averages = {}
    for i in range(24):
        row = {"id": f"EXPLICIT-current-{i}"}
        currents[i, 10_000_000] = row
        scored[row["id"],] = dict(row, metrics=metrics(i))
        for weight in ("uniform", "linear"):
            averages[i, weight, 10_000_000] = {"id": f"EXPLICIT-{i}-{weight}"}
    sources = cast(
        Sources,
        SimpleNamespace(currents=currents, scored_currents=scored, averages=averages),
    )
    result = final_endpoints(sources)
    assert len(result) == 72
    for i in range(24):
        assert result[i, "current"]["id"] == f"EXPLICIT-current-{i}"
        assert result[i, "uniform_average"]["id"] == f"EXPLICIT-{i}-uniform"
        assert result[i, "linear_average"]["id"] == f"EXPLICIT-{i}-linear"


def test_optional_plot_boundary_renders_explicit_software_fixture(
    tmp_path: Path,
) -> None:
    pytest.importorskip("matplotlib")
    from poker_ai.evaluation.matched_update_data import READOUTS
    from poker_ai.evaluation.matched_update_presentation import AXES, plots

    groups = []
    for readout in READOUTS:
        for axis in AXES:
            for batch in (4, 16):
                groups.append(
                    dict(
                        spot_file="EXPLICIT-no-poker.json",
                        representation="exact",
                        regret_rule="signed",
                        readout=readout,
                        axis=axis,
                        batch=batch,
                        mean_exact_exploitability_delta_pct_pot=(
                            -1 if axis == AXES[0] else 1
                        ),
                    )
                )
    plots(groups, tmp_path)
    assert {p.name for p in tmp_path.iterdir()} == {r + ".png" for r in READOUTS}
    assert all(
        p.read_bytes().startswith(b"\x89PNG\r\n\x1a\n") for p in tmp_path.iterdir()
    )
