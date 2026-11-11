"""Tiny-game complete captures and role composition, never real poker learning."""

import copy
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.random import PCG64, Generator, SeedSequence

from poker_ai.evaluation.averaging_history_artifacts import array_sha, write_mass
from poker_ai.evaluation.frozen_batch_replay import warm_mass
from poker_ai.evaluation.opponent_learning_capture import collect, trainer
from poker_ai.evaluation.opponent_learning_contexts import Contexts, software_context
from poker_ai.evaluation.opponent_learning_design import TOY, TOY_WORK, Design
from poker_ai.evaluation.opponent_learning_replay import (
    compose_profiles,
    member,
    metadata,
    profile_replay,
    raw_replay,
)
from poker_ai.postflop.controlled_checkpoints import read_snapshot, write_snapshot
from poker_ai.postflop.frozen_batches import guard
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import Deadline

BINDING = "a" * 64


@pytest.fixture(scope="module")
def captured(tmp_path_factory: pytest.TempPathFactory) -> dict[str, Any]:
    folder = tmp_path_factory.mktemp("opponent-capture")
    design = Design(TOY, TOY_WORK)
    contexts = [software_context(0), software_context(1)]
    events: list[dict[str, Any]] = []
    results = [
        collect(
            contexts[design.path(i)["coordinate"] // 3].tree(
                design.path(i)["tree_kind"]
            ),
            design,
            i,
            folder,
            BINDING,
            events.append,
            Deadline(180),
        )
        for i in range(30)
    ]
    captures = [r for result in results for r in result["captures"]]
    masses = [r for result in results for r in result["masses"]]
    warms = [r["warm"] for r in results]

    def context_for(i: int) -> Contexts:
        return contexts[i // 3]

    policies = raw_replay(
        folder, design, captures, masses, warms, context_for, BINDING, Deadline(180)
    )
    return dict(
        folder=folder,
        design=design,
        contexts=contexts,
        events=events,
        results=results,
        captures=captures,
        masses=masses,
        warms=warms,
        policies=policies,
    )


def test_full_raw_grid_reconstructs_every_average_from_its_mass(
    captured: dict[str, Any],
) -> None:
    assert len(captured["captures"]) == 324
    assert len(captured["masses"]) == 216
    assert len(captured["warms"]) == 30
    assert len(captured["policies"]) == 324
    assert len(captured["events"]) == 570
    assert all(not p.flags.writeable for p in captured["policies"].values())
    assert all(r["initialization_visits"] == 22 for r in captured["captures"])


def test_added_half_observations_preserve_every_final_state_bit(
    captured: dict[str, Any],
) -> None:
    design = captured["design"]
    for index in range(30):
        p = design.path(index)
        tree = captured["contexts"][p["coordinate"] // 3].tree(p["tree_kind"])
        plain = trainer(tree, design, index)
        plain.initialize_exact()
        while plain.nodes_visited < design.boundaries(index)[-1]:
            plain.step()
        endpoint = [r for r in captured["captures"] if r["path_index"] == index][-1]
        assert guard(plain) == endpoint["guard_sha256"]
        assert array_sha(plain.current_policy) == endpoint["current_sha256"]
        assert plain.nodes_visited == captured["results"][index]["final_total_work"]


def test_role_one_uses_declared_seed_sequence_not_scalar_or_role_zero() -> None:
    d = Design(TOY, TOY_WORK)
    c = software_context(0)
    seed = d.path(0)["seed"]
    for i in (0, 2, 4):
        actual = trainer(c.tree(d.path(i)["tree_kind"]), d, i).rng.random(12)
        np.testing.assert_array_equal(actual, Generator(PCG64(seed)).random(12))
    for i in (1, 3):
        actual = trainer(c.tree(d.path(i)["tree_kind"]), d, i).rng.random(12)
        np.testing.assert_array_equal(
            actual, Generator(PCG64(SeedSequence([seed, 1]))).random(12)
        )
        assert not np.array_equal(actual, Generator(PCG64(seed)).random(12))


def test_all_compositions_use_only_correct_own_seat_sources(
    captured: dict[str, Any], tmp_path: Path
) -> None:
    design = captured["design"]
    policies = dict(captured["policies"])
    contexts = captured["contexts"]
    profiles, arms = compose_profiles(
        tmp_path,
        design,
        captured["captures"],
        policies,
        lambda i: contexts[i // 3],
        BINDING,
        Deadline(180),
    )
    assert len(profiles) == len(policies) == 432
    assert len(arms) == 216
    assert sum(p["origin"] == "own_seat_composition" for p in profiles) == 108
    replayed = profile_replay(
        tmp_path,
        design,
        captured["captures"],
        profiles,
        arms,
        captured["policies"],
        lambda i: contexts[i // 3],
        BINDING,
        Deadline(180),
    )
    assert all(replayed[k].tobytes() == p.tobytes() for k, p in policies.items())
    for row in profiles:
        if row["origin"] != "own_seat_composition":
            continue
        c = contexts[row["coordinate"] // 3]
        policy = read_snapshot(
            tmp_path / row["file"], c.coarse, row["receipt"], metadata(row)
        )
        for target, identifier in enumerate(row["components"]):
            own = c.coarse.owners == target
            source = policies[identifier]
            if row["arm"] == "mixed_pair":
                source = source[c.views[target].coarse_own_to_view[own]]
            else:
                source = source[own]
            np.testing.assert_array_equal(policy[own], source)
        assert row["charged_work"]["component_count"] == 2
        assert row["charged_work"]["initialization_visits"] == 44
        assert (
            row["charged_work"]["overshoot"]
            < row["charged_work"]["overshoot_bound_exclusive"]
        )

    for change in ("receipts", "work", "alias", "bits"):
        bad_profiles, bad_arms = copy.deepcopy(profiles), copy.deepcopy(arms)
        bad = bad_profiles[-1]
        if change == "receipts":
            bad["component_receipts"].reverse()
            bad["metadata_sha256"] = sha(
                {
                    k: v
                    for k, v in bad.items()
                    if k not in {"file", "receipt", "metadata_sha256"}
                }
            )
        elif change == "work":
            arm_row = next(r for r in bad_arms if r["id"] == bad["id"])
            assert arm_row["charged_work"]["initialization_visits"] == 44
            arm_row["charged_work"]["initialization_visits"] = 22
        elif change == "alias":
            bad_profiles[0]["file"] = "wrong-alias"
        else:
            c = contexts[bad["coordinate"] // 3]
            values = policies[bad["id"]].copy()
            values[0] = 0
            values[0, (int(np.argmax(policies[bad["id"]][0])) + 1) % 2] = 1
            bad["file"] = "forged-composition.json.gz"
            bad["receipt"] = write_snapshot(
                tmp_path / bad["file"], c.coarse, values, metadata(bad)
            )
        with pytest.raises(ArithmeticError):
            profile_replay(
                tmp_path,
                design,
                captured["captures"],
                bad_profiles,
                bad_arms,
                captured["policies"],
                lambda i: contexts[i // 3],
                BINDING,
                Deadline(180),
            )


@pytest.mark.parametrize(
    "field,value",
    [
        ("source_sha256", "b" * 64),
        ("tree_sha256", "b" * 64),
        ("initialization_visits", 0),
        ("sampled_traversals", 1),
        ("overshoot", True),
        ("guard_sha256", "invalid"),
    ],
)
def test_raw_replay_rejects_bad_endpoint_bindings(
    captured: dict[str, Any], field: str, value: Any
) -> None:
    rows = copy.deepcopy(captured["captures"])
    rows[0][field] = value
    rows[0]["metadata_sha256"] = sha(
        {
            k: v
            for k, v in rows[0].items()
            if k not in {"file", "receipt", "metadata_sha256"}
        }
    )
    with pytest.raises(ArithmeticError):
        raw_replay(
            captured["folder"],
            captured["design"],
            rows,
            captured["masses"],
            captured["warms"],
            lambda i: captured["contexts"][i // 3],
            BINDING,
            Deadline(180),
        )


def test_missing_book_warm_or_wrong_context_is_rejected(
    captured: dict[str, Any],
) -> None:
    for books, warms, wrong in [
        (captured["masses"][:-1], captured["warms"], False),
        (captured["masses"], captured["warms"][:-1], False),
        (captured["masses"], captured["warms"], True),
    ]:

        def select_context(i: int, wrong: bool = wrong) -> Contexts:
            return captured["contexts"][1 if wrong else i // 3]  # type: ignore[no-any-return]

        with pytest.raises(ArithmeticError):
            raw_replay(
                captured["folder"],
                captured["design"],
                captured["captures"],
                books,
                warms,
                select_context,
                BINDING,
                Deadline(180),
            )


def test_interruption_retains_warm_and_reached_partial_member(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen = []

    def stop(event: dict[str, Any]) -> None:
        seen.append(event)
        if event["phase"] == "capture":
            raise KeyboardInterrupt("fixture interruption")

    with pytest.raises(KeyboardInterrupt):
        collect(
            software_context(0).coarse,
            Design(TOY, TOY_WORK),
            0,
            tmp_path,
            BINDING,
            stop,
            Deadline(180),
        )
    assert [e["phase"] for e in seen] == ["warm", "mass", "mass", "capture"]
    assert all((tmp_path / e["row"]["file"]).exists() for e in seen)

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("overwrite attempt constructed a learner")

    monkeypatch.setattr(
        "poker_ai.evaluation.opponent_learning_capture.trainer", forbidden
    )
    with pytest.raises(FileExistsError):
        collect(
            software_context(0).coarse,
            Design(TOY, TOY_WORK),
            0,
            tmp_path,
            BINDING,
            lambda e: None,
            Deadline(180),
        )


def test_unsafe_paths_and_changed_metadata_are_rejected(tmp_path: Path) -> None:
    for name in ("../escape", "/tmp/escape", 4):
        with pytest.raises(ArithmeticError):
            member(tmp_path, name)
    (tmp_path / "escape").symlink_to(tmp_path.parent)
    with pytest.raises(ArithmeticError):
        member(tmp_path, "escape/file")
    with pytest.raises(ArithmeticError):
        metadata(dict(metadata_sha256="invalid", source_sha256=BINDING))


def test_unknown_tree_and_unpaired_composition_are_rejected() -> None:
    c: Contexts = software_context(0)
    with pytest.raises(ValueError):
        c.tree("unknown")
    with pytest.raises(ValueError):
        c.combine("fine_self", c.coarse.legal, c.coarse.legal)


def test_consistently_repacked_average_still_must_equal_its_book(
    captured: dict[str, Any], tmp_path: Path
) -> None:
    rows = copy.deepcopy(captured["captures"])
    row = next(r for r in rows if r["readout"] == "uniform_average")
    tree = captured["contexts"][0].coarse
    values = captured["policies"][row["id"]].copy()
    values[0] = 0
    values[0, (int(np.argmax(captured["policies"][row["id"]][0])) + 1) % 2] = 1
    row["file"] = f"forged-average-{tmp_path.name}.json.gz"
    row["receipt"] = write_snapshot(
        captured["folder"] / row["file"], tree, values, metadata(row)
    )
    with pytest.raises(ArithmeticError, match="average no longer matches"):
        raw_replay(
            captured["folder"],
            captured["design"],
            rows,
            captured["masses"],
            captured["warms"],
            lambda i: captured["contexts"][i // 3],
            BINDING,
            Deadline(180),
        )


def test_consistently_repacked_warm_still_must_equal_exact_expectation(
    captured: dict[str, Any], tmp_path: Path
) -> None:
    rows = copy.deepcopy(captured["warms"])
    row = rows[0]
    tree = captured["contexts"][0].coarse
    row["file"] = f"forged-warm-{tmp_path.name}.json.gz"
    row["receipt"] = write_mass(
        captured["folder"] / row["file"], tree, 2 * warm_mass(tree), metadata(row)
    )
    with pytest.raises(ArithmeticError, match="exact uniform expectation"):
        raw_replay(
            captured["folder"],
            captured["design"],
            captured["captures"],
            captured["masses"],
            rows,
            lambda i: captured["contexts"][i // 3],
            BINDING,
            Deadline(180),
        )
