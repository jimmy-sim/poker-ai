"""Original archive factories stay read-only and all current labels remain used."""

from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from poker_ai.evaluation.private_prefix_sources import contract, load


def test_corrected_contract_preserves_required_core_and_all_caps() -> None:
    root = Path(__file__).resolve().parents[1]
    config, driver = contract(root)
    assert driver["schema_version"] == 2
    assert driver["old_overhead"]["additional_unscored_B1_early_currents"] == 0
    assert driver["old_overhead"]["required_core_profiles"] == 432
    assert driver["old_overhead"]["required_core_ledgers"] == 288
    assert driver["old_overhead"]["required_core_fixed_targets"] == 1152
    for key in (
        "maximum_own_seconds",
        "maximum_native_seconds",
        "maximum_profile_seconds",
    ):
        assert driver[key] == config[key]
    assert config["seeds"] == [20261301, 20261302, 20261303]


@pytest.mark.slow
def test_actual_sources_and_72_B1_crossings_without_learner_or_reference() -> None:
    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("read-only factory constructed learner or reference")

    root = Path(__file__).resolve().parents[1]
    with ExitStack() as stack:
        for name in (
            "poker_ai.postflop.controlled_training.ControlledTrainer.__init__",
            "poker_ai.solver_validation.matched_array_reference.ScalarReference.__init__",
            "poker_ai.solver_validation.reference.Reference.__init__",
        ):
            stack.enter_context(patch(name, forbidden))
        sources = load(root)
        assert len(sources.design.paths) == 48
        assert len(sources.averages) == len(sources.masses) == 432
        assert len(sources.currents) == len(sources.scored_currents) == 216
        # Regression for the assistant's superseded final-only reading error.
        B1 = [r for r in sources.scored_currents.values() if r["batch_size"] == 1]
        assert len(B1) == 72
        assert {
            label: sum(r["work_label"] == label for r in B1)
            for label in (100000, 1000000, 10000000)
        } == {100000: 24, 1000000: 24, 10000000: 24}
        assert all("metrics" in row for row in B1)
