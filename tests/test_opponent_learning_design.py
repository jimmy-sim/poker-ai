"""Whole prospective grid and matched work; no Hold'em learning in unit tests."""

import copy

import pytest

from poker_ai.evaluation.opponent_learning_design import (
    ARMS,
    REAL,
    TOY,
    TOY_WORK,
    WORK,
    Design,
    paired_work,
)


@pytest.mark.parametrize("scope,labels", [(REAL, WORK), (TOY, TOY_WORK)])
def test_complete_grid_and_reused_prefixes(
    scope: str, labels: tuple[int, int, int]
) -> None:
    design = Design(scope, labels)
    manifest = design.manifest()
    assert len(manifest["paths"]) == 30
    assert len(manifest["captures"]) == 324
    assert len(manifest["masses"]) == 216
    assert len(manifest["arms"]) == 216
    assert len(manifest["profiles"]) == 432
    assert len({r["id"] for r in manifest["profiles"]}) == 432
    assert sum(len(design.boundaries(i)) for i in range(30)) == 108
    assert len({r["coordinate"] for r in manifest["paths"]}) == 6
    assert sum(manifest["actual_last_work_labels"]) == 21 * labels[-1]
    for name in ("captures", "masses", "arms", "profiles"):
        design.require_rows(name, manifest[name])
    for coordinate in range(6):
        for label in labels:
            rows = {a: design.arm(coordinate, label, "current", a) for a in ARMS}
            coarse_prefix = rows["coarse_pair"]["components"][0]
            assert (
                coarse_prefix == design.raw(5 * coordinate, label // 2, "current")["id"]
            )
            assert (
                rows["coarse_self"]["id"]
                == design.raw(5 * coordinate, label, "current")["id"]
            )
            assert (
                rows["fine_self"]["id"]
                == design.raw(5 * coordinate + 4, label, "current")["id"]
            )
            assert rows["mixed_pair"]["component_work_labels"] == [label // 2] * 2


def test_paired_role_entropy_is_shared_but_second_role_is_distinct() -> None:
    d = Design(REAL, WORK)
    for i in range(6):
        p = [d.path(5 * i + j) for j in range(5)]
        seed = p[0]["seed"]
        assert p[0]["rng_entropy"] == p[2]["rng_entropy"] == p[4]["rng_entropy"] == seed
        assert p[1]["rng_entropy"] == p[3]["rng_entropy"] == [seed, 1]
        assert p[0]["tree_kind"] == p[1]["tree_kind"] == "coarse"


@pytest.mark.parametrize(
    "change", ["missing", "extra", "duplicate", "bool", "scope", "source"]
)
def test_inventory_rejects_coordinate_changes(change: str) -> None:
    d = Design(REAL, WORK)
    rows = copy.deepcopy(d.manifest()["profiles"])
    if change == "missing":
        rows.pop()
    elif change in ("extra", "duplicate"):
        rows.append(dict(rows[0]))
        if change == "extra":
            rows[-1]["id"] = "unplanned"
    elif change == "bool":
        rows[0]["coordinate"] = False
    elif change == "scope":
        rows[0]["scope"] = TOY
    else:
        rows[-1]["components"].reverse()
    with pytest.raises(ArithmeticError):
        d.require_rows("profiles", rows)


def crossing(label: int, overshoot: int = 3) -> dict[str, int]:
    return dict(
        work_label=label,
        previous_work=label - 5,
        total_work=label + overshoot,
        last_iteration_visits=5 + overshoot,
        initialization_visits=22,
        iteration=19,
    )


def test_pair_charges_both_initializations_and_both_overshoots() -> None:
    result = paired_work([crossing(50), crossing(50, 7)], 100)
    assert result["total_work"] == 110
    assert result["initialization_visits"] == 44
    assert result["overshoot"] == 10
    assert result["overshoot_bound_exclusive"] == 20
    assert result["component_total_work"] == [53, 57]
    assert result["component_count"] == 2
    assert paired_work([crossing(100)], 100)["initialization_visits"] == 22


@pytest.mark.parametrize(
    "field,value",
    [
        ("work_label", 100),
        ("total_work", 49),
        ("previous_work", 50),
        ("last_iteration_visits", 2),
        ("initialization_visits", 0),
        ("iteration", True),
        ("total_work", 53.0),
    ],
)
def test_pair_rejects_invalid_crossings(field: str, value: int | float) -> None:
    a, b = crossing(50), crossing(50)
    b[field] = value  # type: ignore[assignment]
    with pytest.raises(ArithmeticError):
        paired_work([a, b], 100)


def test_fixed_scopes_and_labels_cannot_be_adjusted() -> None:
    with pytest.raises(ValueError):
        Design(REAL, TOY_WORK)
    with pytest.raises(ValueError):
        Design(TOY, WORK)
    d = Design(REAL, WORK)
    for index in (-1, 30, True):
        with pytest.raises(ValueError):
            d.path(index)
    with pytest.raises(ValueError):
        d.raw(0, 200_000, "current")
    with pytest.raises(ValueError):
        d.arm(0, 100_000, "picked_best", "mixed_pair")
    with pytest.raises(ValueError):
        paired_work([crossing(50), crossing(50)], 101)
