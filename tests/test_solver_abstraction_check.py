"""Alias counts distinguish representation collisions from strategy coverage."""

import pytest

from poker_ai.solver_validation.abstraction_check import aliases


def test_collision_mass_counts_entire_merged_group() -> None:
    result = aliases(["a", "a", "b"], [(1, 2)] * 3, [1, 2, 1])
    assert result == {
        "exact_information_sets": 3,
        "abstract_information_sets": 2,
        "merged_groups": 1,
        "information_sets_in_merged_groups": 2,
        "reference_reach_in_merged_groups": 0.75,
    }
    assert aliases(["a", "b"], [(1, 2)] * 2, [1, 2])["merged_groups"] == 0


def test_incompatible_legal_menus_cannot_be_merged() -> None:
    with pytest.raises(ValueError, match="incompatible"):
        aliases(["a", "a"], [(1, 2), (0, 1, 2)], [1, 2])
