"""New compact adapters: no real learning study or reference construction."""

import copy
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.evaluation.compact_opponent_boundaries import (
    boundaries,
    load_contexts,
    readout_fingerprint,
    select_points,
)
from poker_ai.evaluation.compact_opponent_contexts import build_game, refinement
from poker_ai.evaluation.compact_opponent_contract import (
    contract,
    cost_contract,
    input_pins,
)
from poker_ai.evaluation.compact_opponent_projection import (
    lift_book_and_average,
    lift_mass,
    lift_policy,
)
from poker_ai.evaluation.frozen_batch_replay import warm_mass
from poker_ai.evaluation.opponent_learning_capture import trainer
from poker_ai.evaluation.opponent_learning_contexts import Contexts, software_context
from poker_ai.evaluation.opponent_learning_design import TOY, TOY_WORK, Design
from poker_ai.evaluation.opponent_learning_sources import build_game as old_game
from poker_ai.postflop.compact_sampled_state import policies
from poker_ai.postflop.opponent_views import tree_digest

ROOT = Path(__file__).resolve().parents[1]


def test_registered_caps_controls_and_pins_remain_prospective() -> None:
    c = contract(ROOT)
    assert len(input_pins(ROOT)) == len(c["input_sha256"])
    assert c["maximum_own_seconds"] == 7200
    assert c["maximum_native_seconds"] == 900
    assert c["maximum_software_seconds"] == 180
    assert c["long_run_admitted"] is False
    assert c["coarse_representation"] == "texture_range_q8_own_q8_b8"
    assert len(c["frozen_controls"]) == 16
    # Frozen scoring controls intentionally keep their historical encoding.
    assert {p["case"]["representation"] for p in c["frozen_controls"]} == {
        "exact",
        "texture_range_q8_b8",
    }
    assert cost_contract(ROOT)["new_training_nodes"] == 0


@pytest.fixture(scope="module", params=[0, 1])
def real_contexts(request: pytest.FixtureRequest) -> tuple[Contexts, Contexts]:
    game = int(request.param)
    return old_game(ROOT, game), build_game(ROOT, game)


def test_new_real_factory_refines_original_and_preserves_game(
    real_contexts: tuple[Contexts, Contexts],
) -> None:
    old, new = real_contexts
    mapping = refinement(old, new)
    assert np.array_equal(mapping[new.mapping], old.mapping)
    assert mapping.flags.writeable is False
    assert len(new.coarse.keys) > len(old.coarse.keys)
    assert tree_digest(old.fine) == tree_digest(new.fine)
    for target in (0, 1):
        view = new.views[target]
        assert view.fine_sha256 == tree_digest(new.fine)
        assert view.coarse_sha256 == tree_digest(new.coarse)
        assert len(new.coarse.keys) <= len(view.tree.keys) <= len(new.fine.keys)
        assert view.coarse_seat == target
    for index in (True, False, -1, 2, 0.0):
        with pytest.raises(ValueError):
            build_game(ROOT, index)  # type: ignore[arg-type]


def test_refinement_rejects_different_payoffs_and_crossed_groups() -> None:
    old = software_context(0)
    new = software_context(1)
    with pytest.raises(ArithmeticError, match="fine game"):
        refinement(old, new)
    # Supply an independently valid coarser grouping as the proposed refinement.
    fine_context = Contexts.build(
        old.fine,
        old.fine,
        np.arange(len(old.fine.keys)),
        (old.fine.owners == 0, old.fine.owners == 1),
    )
    with pytest.raises(ArithmeticError, match="crosses"):
        refinement(fine_context, old)


def test_exact_warm_origin_and_monotone_density_lifts(
    real_contexts: tuple[Contexts, Contexts],
) -> None:
    old, new = real_contexts
    mapping = refinement(old, new)
    before, after = warm_mass(old.coarse), warm_mass(new.coarse)
    lifted, receipt = lift_mass(old, new, mapping, before)
    assert np.array_equal(lifted, after)
    assert receipt["learned_compact_book"] is False
    assert receipt["new_training_nodes"] == 0
    previous = lifted
    # Unequal action densities test policy preservation, not just uniform scaling.
    delta = before * np.arange(1, before.shape[1] + 1)[None, :]
    for scale in (1, 3, 7):
        values = before + scale * delta
        current, _ = lift_mass(old, new, mapping, values)
        assert np.all(current >= previous)
        assert np.allclose(
            new.coarse.normalize(current),
            old.coarse.normalize(values)[mapping],
            atol=1e-12,
            rtol=0,
        )
        assert current.flags.writeable is False
        previous = current
    p = old.coarse.normalize(before + delta)
    q = lift_policy(old, new, mapping, p)
    assert np.array_equal(q[new.mapping], p[old.mapping])
    assert q.flags.writeable is False


def test_book_before_warm_and_nonfinite_book_are_rejected(
    real_contexts: tuple[Contexts, Contexts],
) -> None:
    old, new = real_contexts
    mapping = refinement(old, new)
    with pytest.raises(ArithmeticError, match="predates"):
        lift_mass(old, new, mapping, warm_mass(old.coarse) * 0.5)
    values = warm_mass(old.coarse)
    values.flat[0] = np.nan
    with pytest.raises(ValueError):
        lift_mass(old, new, mapping, values)


def test_cost_average_is_bit_exact_with_its_lifted_book(
    real_contexts: tuple[Contexts, Contexts],
) -> None:
    old, new = real_contexts
    mapping = refinement(old, new)
    coefficients = np.resize(
        np.array(
            [
                0.123456789,
                0.987654321,
                0.333333333,
                0.777777777,
                0.314159265,
                0.271828182,
                0.161803399,
            ]
        ),
        old.coarse.legal.shape[1],
    )
    book = warm_mass(old.coarse) + old.coarse.legal * coefficients
    average = old.coarse.normalize(book)
    lifted, policy, receipt = lift_book_and_average(old, new, mapping, book, average)
    assert np.array_equal(new.coarse.normalize(lifted), policy)
    assert policy.flags.writeable is False
    assert receipt["average_origin"] == "exact_normalization_of_lifted_cost_book"
    assert receipt["maximum_old_probability_difference"] <= 1e-12
    assert np.allclose(policy, average[mapping], atol=1e-12, rtol=0)
    with pytest.raises(ArithmeticError, match="original cost average"):
        lift_book_and_average(
            old, new, mapping, book, old.coarse.normalize(old.coarse.legal)
        )


def original() -> dict[str, Any]:
    saved: dict[str, Any] = json.loads(
        (ROOT / "results/compact-sampled/real/own.json").read_text()
    )
    return saved


def test_all36_original_new_compact_and_exact_selectors() -> None:
    rows = select_points(original())
    assert len(rows) == 36
    assert len({(i, r["work_checkpoint"]) for i, r in rows}) == 36
    assert {i % 5 for i, _ in rows} == {0, 4}
    assert {r["representation"] for _, r in rows} == {
        "exact",
        "texture_range_q8_own_q8_b8",
    }


@pytest.mark.parametrize("change", ["missing", "duplicate", "seed_bool", "work_bool"])
def test_boundary_selectors_reject_missing_duplicate_or_boolean_identity(
    change: str,
) -> None:
    saved = original()
    _, selected = select_points(saved)[0]
    if change == "missing":
        saved["points"].remove(selected)
    elif change == "duplicate":
        saved["points"].append(copy.deepcopy(selected))
    else:
        selected["seed" if change == "seed_bool" else "work_checkpoint"] = True
    with pytest.raises(ArithmeticError, match="per boundary"):
        select_points(saved)


def test_all36_raw_snapshots_decode_without_learner() -> None:
    saved = original()
    peers = boundaries(
        ROOT / "results/compact-sampled/real", saved, load_contexts(ROOT)
    )
    assert len(peers) == 36
    assert all(
        set(p["readouts"]) == set(p["mass_sha256"]) == {"uniform", "linear"}
        for p in peers
    )
    assert all(p["current_sha256"] == p["current_policy_sha256"] for p in peers)


@pytest.mark.parametrize("weight", ["uniform", "linear"])
def test_decoded_readout_fingerprint_matches_literal_old_observer(weight: str) -> None:
    # Fictional signal-game updates, not new poker trajectories or admission.
    tree = software_context(0).coarse
    solver = trainer(tree, Design(TOY, TOY_WORK), 0)
    solver.initialize_exact()
    for _ in range(4):
        solver.step()
    arrays = dict(
        regrets=solver.regrets,
        uniform_sum=solver.uniform_sum,
        linear_sum=solver.strategy_sum,
    )
    raw = dict(
        rng_state=solver.rng.bit_generator.state,
        sampled_rows=[int(k in solver.sampled_keys) for k in tree.keys],
    )
    probs = policies(
        tree, arrays["regrets"], arrays["uniform_sum"], arrays["linear_sum"]
    )
    assert readout_fingerprint(
        tree, raw, arrays, probs, weight
    ) == solver.readout_fingerprint(weight)  # type: ignore[arg-type]
    assert readout_fingerprint(tree, raw, arrays, probs, weight) != readout_fingerprint(
        tree, raw, {**arrays, "regrets": arrays["regrets"] + tree.legal}, probs, weight
    )
