"""Frozen river switches, observable probes and complete receipt/native checks."""

import copy
import itertools
import json
import shutil
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.cards import parse_card
from poker_ai.finite import ArrayTree
from poker_ai.postflop import made_admission as admission
from poker_ai.postflop import reply_diagnosis as replies
from poker_ai.postflop import river_distinction_report as reporting
from poker_ai.postflop import river_distinctions as diagnosis
from poker_ai.postflop.game import SpotState, load_spot
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation import river_distinctions as native

ROOT = Path(__file__).resolve().parents[1]


def cards(text: str) -> tuple[int, ...]:
    return tuple(parse_card(v) for v in text.split())


def seven_nodes(hidden: bool) -> ArrayTree:
    children = np.zeros((7, 2), dtype=np.int64)
    children[0], children[1], children[4] = (1, 4), (2, 3), (5, 6)
    valid = np.zeros((7, 2), dtype=np.bool_)
    valid[[0, 1, 4]] = True
    edges = np.zeros((7, 2))
    if hidden:
        edges[0] = (0.25, 0.75)
    return ArrayTree(
        children,
        valid,
        np.array([-1 if hidden else 0, 0, -2, -2, 0, -2, -2]),
        np.array(
            [
                -1 if hidden else 0,
                0 if hidden else 1,
                -1,
                -1,
                0 if hidden else 2,
                -1,
                -1,
            ]
        ),
        ("hidden",) if hidden else ("turn", "left", "right"),
        ((0, 1),) * (1 if hidden else 3),
        np.zeros(1 if hidden else 3, dtype=np.int64),
        np.ones((1 if hidden else 3, 2)),
        edges,
        np.array([1, 0.25, 0.25, 0.25, 0.75, 0.75, 0.75]) if hidden else np.ones(7),
        np.array(
            [0, 0, 4, 0, 0, 0, 2] if hidden else [0, 0, 0, 4, 0, 3, 2], dtype=np.float64
        ),
        (np.array([0]), np.array([1, 4])),
    )


@pytest.mark.parametrize("target", [0, 1])
def test_river_switches_hold_prefix_and_sum_signed_hidden_values(target: int) -> None:
    tree = seven_nodes(False)
    if target == 1:
        tree = replace(
            tree,
            player=np.where(tree.player == 0, 1, tree.player),
            owners=np.ones(3, dtype=np.int64),
            terminal_values=-tree.terminal_values,
        )
    b = np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]])
    c = np.array([[0.0, 1.0], [1.0, 0.0], [1.0, 0.0]])
    panels = diagnosis.river_switches(
        tree, b, c, target, np.array([False, True, True]), tolerance=1e-9
    )
    a, z = panels.values()
    assert (a.before_value, a.after_value) == (3, 3)
    assert (z.before_value, z.after_value) == (0, 4)
    assert a.losses.sum() == 0 and z.losses.sum() == 4
    np.testing.assert_array_equal(a.after[0], c[0])
    np.testing.assert_array_equal(z.before[0], b[0])
    assert z.after_value - a.before_value == 1  # Not the sum of the two river gains.
    assert a.error == z.error == 0


def test_hidden_deals_do_not_allow_clairvoyant_actions_and_zero_reach_is_zero() -> None:
    tree = seven_nodes(True)
    panels = diagnosis.river_switches(
        tree,
        np.array([[0.0, 1.0]]),
        np.array([[1.0, 0.0]]),
        0,
        np.array([True]),
        tolerance=1e-9,
    )
    for p in panels.values():
        assert p.before_value == 1 and p.after_value == 1.5  # Not hidden-world max 2.5.
        assert p.losses.sum() == 0.5 and p.mass.sum() == 1
    # Left future is never reached under the restricted turn prefix.
    seq = seven_nodes(False)
    p = diagnosis.river_switches(
        seq,
        np.array([[1.0, 0.0], [0.0, 1.0], [1.0, 0.0]]),
        np.array([[0.0, 1.0], [1.0, 0.0], [1.0, 0.0]]),
        0,
        np.array([False, True, True]),
        tolerance=1e-9,
    )["restricted_prefix"]
    assert p.mass[1] == p.losses[1] == 0


def test_ties_are_not_strict_conflicts_and_probe_counts_use_original_rows() -> None:
    def row(best: list[int], rank: int) -> dict[str, Any]:
        return {
            "near_optimal_columns": best,
            "features": {
                "own_rank": (rank,),
                "range_compatibility": (True,),
                "range_relations": (rank,),
            },
        }

    assert not diagnosis.conflicting([row([0, 1], 1), row([1], 2)])
    rows = [row([0], 1), row([1], 2)]
    assert diagnosis.conflicting(rows)
    assert not diagnosis.conflicting(rows, "own_rank")
    assert diagnosis.conflicting(rows, "range_compatibility")
    assert not diagnosis.conflicting(rows, "range_relations")


def test_switch_guards_reject_changed_opponent_mask_and_nan_tolerance() -> None:
    tree = seven_nodes(True)
    with pytest.raises(ValueError):
        diagnosis.river_switches(
            tree,
            np.array([[1.0, 0.0]]),
            np.array([[1.0, 0.0]]),
            0,
            np.array([1]),
            tolerance=1e-9,
        )
    with pytest.raises(ValueError):
        diagnosis.river_switches(
            tree,
            np.array([[1.0, 0.0]]),
            np.array([[1.0, 0.0]]),
            0,
            np.array([True]),
            tolerance=float("nan"),
        )
    other = replace(
        tree, player=np.where(tree.player == 0, 1, tree.player), owners=np.array([1])
    )
    with pytest.raises(ArithmeticError, match="opponent"):
        diagnosis.river_switches(
            other,
            np.array([[1.0, 0.0]]),
            np.array([[0.0, 1.0]]),
            0,
            np.array([False]),
            tolerance=1e-9,
        )


def test_same_full_house_rank_but_different_declared_range_blockers() -> None:
    known = (cards("As Js"), cards("Tc Td"))
    a = diagnosis.river_features(cards("9c 9d"), cards("Ts 9s 4d 2h Th"), known)
    b = diagnosis.river_features(cards("9c 9d"), cards("Ts 9s 4d 2h Td"), known)
    assert a["own_rank"] == b["own_rank"] == (6, 9, 10)
    assert a["range_compatibility"] == (True, True) and b["range_compatibility"] == (
        True,
        False,
    )
    assert a["range_relations"] == (1, -1) and b["range_relations"] == (1, None)


def test_relative_strength_can_differ_with_same_own_rank_and_compatibility() -> None:
    a = diagnosis.river_features(
        cards("9c 9d"), cards("Ts 9s 4d 2h 3s"), (cards("As Js"),)
    )
    b = diagnosis.river_features(
        cards("9c 9d"), cards("Ts 9s 4d 2h 3d"), (cards("As Js"),)
    )
    assert a["own_rank"] == b["own_rank"]
    assert a["range_compatibility"] == b["range_compatibility"]
    assert a["range_relations"] == (-1,) and b["range_relations"] == (1,)


def test_probe_symmetry_and_hidden_deal_invariance() -> None:
    hole, board, known = (
        cards("9c 9d"),
        cards("Ts 9s 4d 2h Th"),
        (cards("As Js"), cards("Tc Td")),
    )
    expected = diagnosis.river_features(hole, board, known)
    for suits in itertools.permutations(range(4)):

        def rename(
            xs: tuple[int, ...], mapping: tuple[int, ...] = suits
        ) -> tuple[int, ...]:
            return tuple(4 * (c // 4) + mapping[c % 4] for c in xs)

        assert (
            diagnosis.river_features(
                rename(hole), rename(board), tuple(rename(h) for h in known)
            )
            == expected
        )
    assert (
        diagnosis.river_features(
            hole[::-1], tuple(reversed(board[:3])) + board[3:], known
        )
        == expected
    )
    spot = load_spot(ROOT / "configs/learning-spots/dev_low_oop.json")
    states = [SpotState(spot).child(0).child(j) for j in (0, 1)]
    river = sorted(set(states[0].actions) & set(states[1].actions))[0]
    observations = []
    for s in states:
        s = s.child(river).child(1).child(1)
        assert s.dealer is not None
        observations.append(s.dealer.observe(0))
    whole_range = tuple(h.cards for h in spot.ranges[1])
    assert (
        len(
            {
                json.dumps(diagnosis.river_features(o.hole_cards, o.board, whole_range))
                for o in observations
            }
        )
        == 1
    )


@pytest.mark.parametrize(
    "hole,board,known",
    [
        ((), cards("Ts 9s 4d 2h Th"), (cards("As Js"),)),
        (cards("9c 9c"), cards("Ts 9s 4d 2h Th"), (cards("As Js"),)),
        (cards("9c 9d"), cards("Ts 9s 4d 2h"), (cards("As Js"),)),
        (cards("9c 9d"), cards("Ts 9s 4d 2h Th"), ()),
    ],
)
def test_invalid_probe_inputs(
    hole: tuple[int, ...], board: tuple[int, ...], known: tuple[tuple[int, ...], ...]
) -> None:
    with pytest.raises((ValueError, TypeError)):
        diagnosis.river_features(hole, board, known)


def fixture_source(*a: Any, **k: Any) -> dict[str, Any]:
    return {"dirty": False, "sha256": {}, "git_commit": "tiny-software-fixture"}


@pytest.fixture(scope="module")
def tiny_diagnosis(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, Path, dict[str, Any]]:
    d = tmp_path_factory.mktemp("river-distinction-fixture")
    c = json.loads((ROOT / "configs/made-category-admission.json").read_text())
    c.update(
        spot_files=c["spot_files"][:1],
        full_tree_checkpoints=[1],
        full_tree_backend="numpy",
    )
    cfg = d / "admission.json"
    cfg.write_text(json.dumps(c))
    with pytest.MonkeyPatch.context() as patch:
        # Tiny fixtures alone stub clean source metadata; no real outcome does.
        patch.setattr(admission, "source_provenance", fixture_source)
        original = d / "study.json"
        result = admission.run_admission(ROOT, cfg, original)
        assert result["status"] == "completed"
        c = json.loads((ROOT / "configs/candidate-best-response.json").read_text())
        c.update(
            input_report=str(original),
            input_report_sha256=digest(original),
            input_policy_sha256=result["own_policies_sha256"],
            iteration=1,
        )
        cfg = d / "reply-config.json"
        cfg.write_text(json.dumps(c))
        patch.setattr(replies, "source_provenance", fixture_source)
        path = d / "replies.json"
        result = replies.diagnose(ROOT, cfg, path)
        c = json.loads((ROOT / "configs/river-distinction-diagnosis.json").read_text())
        c.update(
            input_report=str(path),
            input_report_sha256=digest(path),
            input_details_sha256=result["details_sha256"],
        )
        cfg = d / "river-config.json"
        cfg.write_text(json.dumps(c))
        patch.setattr(diagnosis, "source_provenance", fixture_source)
        path = d / "diagnosis.json"
        result = diagnosis.diagnose(ROOT, cfg, path)
    return cfg, path, result


def test_complete_fixture_replay_reach_posterior_and_probe_bounds(
    tiny_diagnosis: tuple[Path, Path, dict[str, Any]],
) -> None:
    _, path, _ = tiny_diagnosis
    r, details, error = diagnosis.replay(ROOT, path)
    assert error == 0 and len(r["cases"]) == len(details) == 4
    for case, detail in zip(r["cases"], details, strict=True):
        for response, full in zip(case["responses"], detail["responses"], strict=True):
            assert response["exact_information_value_chips"] == pytest.approx(
                response["river_gain_restricted_prefix_chips"]
                + response["prefix_readjustment_chips"],
                abs=1e-9,
            )
            for panel in response["panels"]:
                assert panel["loss_sum_chips"] == pytest.approx(
                    panel["river_gain_chips"], abs=1e-9
                )
                assert all(
                    0 <= v <= panel["conflicting_rows"]
                    for v in panel["unresolved_after_probe"].values()
                )
                assert (
                    panel["unresolved_after_probe"]["range_relations"]
                    <= panel["unresolved_after_probe"]["range_compatibility"]
                )
            for row in full["river_infos"]:
                assert len(row["board"]) == 5 and "opponent_cards" not in row
                posterior = np.array(row["conditional_opponent_range"])
                assert posterior.sum() == pytest.approx(
                    1 if row["counterfactual_mass"] > 0 else 0
                )
                assert not posterior[
                    np.logical_not(row["features"]["range_compatibility"])
                ].any()


@pytest.mark.parametrize("change", ["missing", "duplicate", "number", "details"])
def test_changed_receipts_rejected(
    tiny_diagnosis: tuple[Path, Path, dict[str, Any]], tmp_path: Path, change: str
) -> None:
    _, original, raw = tiny_diagnosis
    r = copy.deepcopy(raw)
    shutil.copyfile(original.parent / r["details_file"], tmp_path / r["details_file"])
    if change == "missing":
        r["cases"].pop()
    elif change == "duplicate":
        r["cases"].append(r["cases"][-1])
    elif change == "number":
        r["cases"][0]["responses"][0]["panels"][0]["river_gain_chips"] += 1
    else:
        (tmp_path / r["details_file"]).write_bytes(b"changed")
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(r))
    with pytest.raises((ValueError, ArithmeticError)):
        diagnosis.replay(ROOT, path)


def test_overwrite_dirty_and_input_guards(
    tiny_diagnosis: tuple[Path, Path, dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    cfg, path, _ = tiny_diagnosis
    with pytest.raises(FileExistsError):
        diagnosis.diagnose(ROOT, cfg, path)
    monkeypatch.setattr(diagnosis, "source_provenance", lambda *a, **k: {"dirty": True})
    with pytest.raises(ValueError, match="publish"):
        diagnosis.diagnose(ROOT, cfg, tmp_path / "new.json")
    config = json.loads(cfg.read_text())
    config["input_report_sha256"] = "changed"
    with pytest.raises(ArithmeticError, match="input"):
        diagnosis.inputs(ROOT, config)


def test_native_values_report_and_changed_root_guard(
    tiny_diagnosis: tuple[Path, Path, dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("pyspiel")
    pytest.importorskip("matplotlib")
    cfg, path, _ = tiny_diagnosis
    monkeypatch.setattr(native, "source_provenance", fixture_source)
    audit = tmp_path / "audit.json"
    r = native.audit(ROOT, cfg, path, audit)
    assert r["status"] == "passed" and r["native_profiles_checked"] == 32
    report = reporting.render(ROOT, path, audit, tmp_path / "report")
    assert report["maximum_native_error_chips"] < 1e-9
    for name in (
        "river-gains.png",
        "probe-conflicts.png",
        "gains.csv",
        "conflicts.csv",
        "tables.md",
    ):
        assert (tmp_path / "report" / name).stat().st_size > 50
    r["rows"][0]["after_native_chips"] += 1
    audit.write_text(json.dumps(r))
    with pytest.raises(ArithmeticError, match="agreement"):
        reporting.render(ROOT, path, audit, tmp_path / "bad")


def test_offline_inspector_and_rank_guard(
    tiny_diagnosis: tuple[Path, Path, dict[str, Any]],
) -> None:
    _, path, _ = tiny_diagnosis
    command = [
        sys.executable,
        str(ROOT / "scripts/inspect_river_distinction.py"),
        "--report",
        str(path),
        "--game",
        "dev_low_oop",
    ]
    good = subprocess.run(command, text=True, capture_output=True)
    assert good.returncode == 0 and "River-only gain" in good.stdout
    bad = subprocess.run(command + ["--rank", "0"], capture_output=True)
    assert bad.returncode == 2
