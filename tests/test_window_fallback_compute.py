"""Complete tiny toy intervention inventory; never a Hold'em result."""

import copy
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.window_fallback_compute import evaluate_window, fixed_targets
from poker_ai.evaluation.window_fallback_inputs import windows
from poker_ai.evaluation.window_fallback_software import software_inputs
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]


def forbidden(*args: Any, **kwargs: Any) -> None:
    raise AssertionError(
        "new learning/reference construction forbidden in offline stage"
    )


@pytest.fixture(scope="module")
def toy_interventions(tmp_path_factory: pytest.TempPathFactory) -> tuple[Any, ...]:
    folder = tmp_path_factory.mktemp("window-fill") / "EXPLICIT_SOFTWARE_FIXTURE"
    data = software_inputs(ROOT, folder, Deadline(120))
    results = []
    from poker_ai.solver_validation.reference import Reference

    with pytest.MonkeyPatch.context() as guard:
        guard.setattr(ControlledTrainer, "step", forbidden)
        guard.setattr(ControlledTrainer, "initialize_exact", forbidden)
        guard.setattr(Reference, "__init__", forbidden)
        for window in windows(data, Deadline(120)):
            profiles, panel = evaluate_window(
                window, data.config, "f" * 64, Deadline(120)
            )
            matches, error = fixed_targets(window, profiles, data, Deadline(120))
            results.append((window, profiles, panel, matches, error))
    return data, results


@pytest.mark.slow
def test_all_512_toy_profiles_preserve_inputs_learned_rows_and_full_realizations(
    toy_interventions: tuple[Any, ...],
) -> None:
    _, results = toy_interventions
    assert len(results) == 128
    assert sum(len(p) for _, p, _, _, _ in results) == 512
    assert sum(w.source.case["traversal"] == "full" for w, _, _, _, _ in results) == 32
    for window, profiles, panel, _, _ in results:
        assert panel["maximum_error_chips"] <= 1e-9
        assert profiles[0].metadata["source_window_policy_sha256"] == array_sha(
            window.policy
        )
        for profile in profiles:
            positive = window.mass.sum(axis=1) > 0
            assert (
                profile.policy[positive].tobytes() == window.policy[positive].tobytes()
            )
            assert not profile.policy.flags.writeable
        if window.source.case["traversal"] == "full":
            assert panel["full_control_error_chips"] <= 1e-9
            assert panel["maximum_realization_change"] <= 1e-12


@pytest.mark.slow
def test_all_2048_toy_fixed_targets_keep_roots_and_gain_ev_identities(
    toy_interventions: tuple[Any, ...],
) -> None:
    _, results = toy_interventions
    assert sum(len(m) for _, _, _, m, _ in results) == 2048
    for _, _, _, matches, error in results:
        assert error <= 1e-9
        assert {r["target"] for r in matches} == {0, 1}
        assert {r["fill_label"] for r in matches} == {"raw", "fill_both"}
        assert len({r["opponent_profile_id"] for r in matches}) == 4
        for row in matches:
            assert row["gain_difference_chips"] == pytest.approx(
                -row["ev_difference_chips"]
            )


@pytest.mark.slow
def test_altered_toy_raw_control_is_not_accepted(
    toy_interventions: tuple[Any, ...],
) -> None:
    data, results = toy_interventions
    window = results[0][0]
    row = copy.deepcopy(window.row)
    row["metrics"]["value_player_zero_chips"] += 0.25
    with pytest.raises(ArithmeticError, match="raw window control"):
        evaluate_window(replace(window, row=row), data.config, "f" * 64, Deadline(120))


@pytest.mark.slow
def test_missing_toy_opponent_mode_prevents_comparison(
    toy_interventions: tuple[Any, ...],
) -> None:
    data, results = toy_interventions
    window, profiles, _, _, _ = results[0]
    victim = next(
        p for p in data.history.base.policies if p.group == window.source.group
    )
    base = replace(
        data.history.base,
        policies=tuple(
            p for p in data.history.base.policies if p.identifier != victim.identifier
        ),
    )
    changed = replace(data, history=replace(data.history, base=base))
    with pytest.raises(ArithmeticError, match="source grid incomplete"):
        fixed_targets(window, profiles, changed, Deadline(120))
