"""Independent tiny information accounting; no new poker diagnostic outcomes."""

import math
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import compact_information_inputs as inputs
from poker_ai.evaluation import compact_sampled_inputs as old
from poker_ai.evaluation.compact_fixed_software import coarse_context
from poker_ai.evaluation.compact_information_software import mocked_source as source
from poker_ai.postflop.compact_information import panel

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("target", [0, 1])
def test_positive_hidden_world_loss_matches_independent_path_sum(target: int) -> None:
    c = coarse_context(target)
    a, b = ("SS", "FS") if target == 0 else ("SS", "SF")
    value = panel(source(c, a), source(c, b), target)
    # Literal enumeration: probability .25 sees payoffs(4,0), .75 sees(0,2).
    # Restricted reply always chooses right: R=.25*0+.75*2=1.5.
    # Fine reply sees its legal own information: B=.25*4+.75*2=2.5.
    assert value["restricted_root_chips"] == 0.25 * 0 + 0.75 * 2
    assert value["exact_root_chips"] == 0.25 * 4 + 0.75 * 2
    assert value["information_gain_chips"] == 1
    assert [r["loss_contribution_chips"] for r in value["rows"]] == [1, 0]
    assert math.fsum(r["loss_contribution_chips"] for r in value["rows"]) == 1
    assert value["groups"][0]["strict_conflict"] is True
    assert value["groups"][0]["exact_members"] == 2
    assert value["maximum_error_chips"] == 0
    assert all(r["restricted_probabilities"] == [0, 1] for r in value["rows"])
    assert value["independent_new_row_value_audit"] is False


@pytest.mark.parametrize("target", [0, 1])
def test_one_to_one_kuhn_rows_have_zero_information_gap(target: int) -> None:
    c = next(iter(old.game_contexts(ROOT, "software").values()))
    a, b = ("SS", "FS") if target == 0 else ("SS", "SF")
    value = panel(source(c, a), source(c, b), target)
    assert abs(value["information_gain_chips"]) < 1e-12
    assert all(not g["strict_conflict"] for g in value["groups"])
    assert len(value["rows"]) == int((c.scoring.exact.owners == target).sum())
    assert value["maximum_error_chips"] < 1e-12


@pytest.mark.parametrize(
    "mutation",
    ["seed", "opponent", "reply", "root", "baseline", "target_type", "target_order"],
)
def test_incorrect_alias_or_audited_root_is_rejected(mutation: str) -> None:
    c = coarse_context()
    a = source(c, "SS")
    b = source(c, "FS")
    if mutation == "seed":
        b.row["seed"] += 1
    elif mutation == "opponent":
        b.row["mixture"] = "FF"
    elif mutation == "reply":
        b.packet["replies"][0]["exact"][0] = [0.5, 0.5]
    elif mutation == "root":
        a.native["responses"][0]["exact_root_chips"] += 1
    elif mutation == "baseline":
        a.native["responses"][0]["restricted_root_chips"] += 1
    elif mutation == "target_type":
        a.native["responses"][0]["target"] = False
    else:
        a.row["responses"][0]["target"] = 1
    with pytest.raises(ArithmeticError):
        panel(a, b, 0)


@pytest.mark.parametrize("bad", [False, True, 0.0, 1.0, -1, 2])
def test_integer_target_cannot_be_substituted(bad: Any) -> None:
    c = coarse_context()
    with pytest.raises(ValueError):
        panel(source(c, "SS"), source(c, "FS"), bad)


def test_parent_inputs_and_fixed_inventory_are_frozen() -> None:
    c = inputs.config(ROOT)
    assert len(inputs.expected(ROOT, True)) == len(inputs.expected(ROOT, False)) == 144
    assert c["response_aliases"] == 288 and c["source_profiles"] == 48
    assert c["maximum_own_seconds"] == c["maximum_report_seconds"] == 900
    assert (
        c["software_maximum_seconds"] == 180 and c["deadline_reserve_seconds"] == 3900
    )
    assert c["absolute_tolerance_chips"] == 1e-9


def test_overlapping_action_ties_are_not_a_strict_conflict() -> None:
    from dataclasses import replace

    from poker_ai.postflop.controlled_scoring import ScoringContext

    c = coarse_context()
    old_score = c.scoring
    values = old_score.exact.terminal_values.copy()
    values[3] = 4
    scoring = ScoringContext(
        replace(old_score.exact, terminal_values=values),
        replace(old_score.partition, terminal_values=values),
        old_score.exact_to_partition,
        old_score.river_masks,
    )
    c = replace(c, scoring=scoring)
    value = panel(source(c, "SS"), source(c, "FS"), 0)
    assert value["information_gain_chips"] == 0
    assert {r["reply_action"] for r in value["rows"]} == {"0", "1"}
    assert value["rows"][0]["near_optimal_columns"] == [0, 1]
    assert value["rows"][1]["near_optimal_columns"] == [1]
    assert value["groups"][0]["strict_conflict"] is False


def test_zero_support_rows_are_kept_with_zero_loss() -> None:
    c = next(iter(old.game_contexts(ROOT, "software").values()))
    value = panel(source(c, "SF"), source(c, "FF"), 0)
    zero = [r for r in value["rows"] if r["restricted_prefix_reach_mass"] == 0]
    assert zero and all(r["loss_contribution_chips"] == 0 for r in zero)
    assert len(value["rows"]) == int((c.scoring.exact.owners == 0).sum())


def test_corrupted_declared_context_cannot_relabel_a_trace() -> None:
    c = coarse_context()
    a, b = source(c, "SS"), source(c, "FS")
    b.packet["binding"] = dict(b.packet["binding"], exact_sha256="0" * 64)
    with pytest.raises(ArithmeticError):
        panel(a, b, 0)
