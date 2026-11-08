"""Hand-computed binary-factor examples, deliberately not poker results."""

from typing import Any

import pytest

from poker_ai.postflop.learning_analysis import FACTORS, LEVELS, contrasts
from poker_ai.postflop.learning_report import PRIMARY, analyze


def polynomial(levels: tuple[str, ...]) -> float:
    z = [-1 if levels[i] == pair[0] else 1 for i, pair in enumerate(FACTORS.values())]
    return float(
        7
        + 2 * z[0]
        + 3 * z[0] * z[2]
        - 2 * z[1] * z[2] * z[3]
        + 5 * z[0] * z[1] * z[2] * z[3]
    )


def test_hand_computed_all_factorial_orders_and_conditional_pairing() -> None:
    result = contrasts({levels: polynomial(levels) for levels in LEVELS})
    assert len(result["conditional"]) == 32
    assert len(result["factorial"]) == 15
    expected = {
        ("traversal",): 4.0,
        ("traversal", "regret_weight"): 12.0,
        ("regret_rule", "regret_weight", "average_weight"): -16.0,
        tuple(FACTORS): 80.0,
    }
    for row in result["factorial"]:
        assert row["difference"] == expected.get(tuple(row["factors"]), 0)
    row = next(
        r
        for r in result["conditional"]
        if r["factor"] == "traversal"
        and r["held"]
        == dict(regret_rule="signed", regret_weight="uniform", average_weight="uniform")
    )
    assert row["difference"] == -12  # 4 + 6*(-1) + 10*(-1)^3.


def test_self_comparison_and_constant_offsets_have_zero_contrasts() -> None:
    assert all(
        r["difference"] == 0
        for group in contrasts(dict.fromkeys(LEVELS, 123.0)).values()
        for r in group
    )


@pytest.mark.parametrize("mode", ["missing", "extra", "nan", "infinity", "bool"])
def test_invalid_balanced_grid_refused(mode: str) -> None:
    values: dict[tuple[str, ...], Any] = dict.fromkeys(LEVELS, 0.0)
    if mode == "missing":
        values.pop(LEVELS[0])
    elif mode == "extra":
        values[("other",)] = 0.0
    else:
        values[LEVELS[0]] = {
            "nan": float("nan"),
            "infinity": float("inf"),
            "bool": True,
        }[mode]
    with pytest.raises(ValueError):
        contrasts(values)


def synthetic_rows() -> list[dict[str, Any]]:
    rows = []
    for levels in LEVELS:
        for seed in [1, 2, 3] if levels[0] == "external" else [None]:
            value = polynomial(levels) + (float(seed) - 2 if seed is not None else 0)
            rows.append(
                dict(
                    spot_file="fixture.json",
                    representation="fixture",
                    axis="work",
                    target=100,
                    bridge="common",
                    seed=seed,
                    **dict(zip(FACTORS, levels, strict=True)),
                    id=f"fixture-{levels}-{seed}",
                    iteration=4,
                    total_work=110,
                    **dict.fromkeys(PRIMARY, value),
                )
            )
    for bridge in (
        "cold_target_history_mass",
        "warm_target_history_mass",
        "warm_target_chance_mass",
    ):
        source = next(
            r
            for r in rows
            if r["traversal"] == "full"
            and r["regret_rule"] == "clipped"
            and r["regret_weight"] == "uniform"
            and r["average_weight"] == "linear"
        )
        rows.append({**source, "bridge": bridge, "id": bridge})
    return rows


def test_seed_pairing_matches_means_and_common_bridge_is_aliased() -> None:
    rows = synthetic_rows()
    means, effects, bridges = analyze(rows, [1, 2, 3])
    assert len(means) == 16 * 4
    assert len(effects) == 47 * 4
    assert len(bridges) == 4
    assert bridges[-1]["aliases_common"]
    assert bridges[-1]["source_id"].startswith("fixture-")
    for effect in effects:
        paired = effect["paired_seed_differences"]
        assert sum(paired.values()) / 3 == effect["difference"]
    traversal = next(
        r for r in effects if r["kind"] == "factorial" and r["factors"] == ["traversal"]
    )
    assert traversal["difference"] == 4
    assert traversal["paired_seed_differences"] == {1: 3, 2: 4, 3: 5}


@pytest.mark.parametrize("mode", ["drop_seed", "duplicate_full", "missing_bridge"])
def test_report_cannot_silently_average_incomplete_or_repeated_cells(mode: str) -> None:
    rows = synthetic_rows()
    if mode == "drop_seed":
        rows.pop(next(i for i, r in enumerate(rows) if r["seed"] == 2))
    elif mode == "duplicate_full":
        rows.append(rows[0])
    else:
        rows.pop()
    with pytest.raises(ArithmeticError):
        analyze(rows, [1, 2, 3])
