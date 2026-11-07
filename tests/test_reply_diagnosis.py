"""Hidden-state-safe replies, additive identity, frozen inputs and native roots."""

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

from poker_ai.finite import ArrayTree
from poker_ai.postflop import made_admission as admission
from poker_ai.postflop import reply_diagnosis as diagnosis
from poker_ai.postflop import reply_report as reporting
from poker_ai.postflop.reply_trace import response_profile, trace_losses
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation import reply_diagnosis as native
from poker_ai.toy.games import GameName
from poker_ai.toy.tree import Tree

ROOT = Path(__file__).resolve().parents[1]


def hidden_tree() -> ArrayTree:
    children = np.zeros((7, 2), dtype=np.int64)
    children[0], children[1], children[4] = (1, 4), (2, 3), (5, 6)
    valid = np.zeros((7, 2), dtype=np.bool_)
    valid[[0, 1, 4]] = True
    edges = np.zeros((7, 2))
    edges[0] = (0.25, 0.75)
    return ArrayTree(
        children,
        valid,
        np.array([-1, 0, -2, -2, 0, -2, -2]),
        np.array([-1, 0, -1, -1, 0, -1, -1]),
        ("hidden",),
        ((0, 1),),
        np.array([0]),
        np.ones((1, 2)),
        edges,
        np.array([1, 0.25, 0.25, 0.25, 0.75, 0.75, 0.75]),
        np.array([0, 0, 4, 0, 0, 0, 2], dtype=np.float64),
        (np.array([0]), np.array([1, 4])),
    )


@pytest.mark.parametrize("target", [0, 1])
def test_hidden_average_before_max_and_signs(target: int) -> None:
    tree = hidden_tree()
    if target == 1:
        tree = replace(
            tree,
            player=np.where(tree.player == 0, 1, tree.player),
            owners=np.array([1]),
        )
    trace = trace_losses(tree, np.array([[0.5, 0.5]]), target)
    assert trace.value == (1.5 if target == 0 else -1)
    assert trace.gain == pytest.approx(0.25)
    assert trace.losses.sum() == pytest.approx(0.25)
    np.testing.assert_array_equal(trace.profile, [[0, 1]] if target == 0 else [[1, 0]])
    # Seeing the hidden world would illegally give 2.5 (or 0 for player one).
    assert trace.value != (2.5 if target == 0 else 0)


def test_extra_information_value_and_zero_optimal_profile() -> None:
    limited = hidden_tree()
    revealed = replace(
        limited,
        information=np.array([-1, 0, -1, -1, 1, -1, -1]),
        keys=("left", "right"),
        actions=((0, 1),) * 2,
        owners=np.array([0, 0]),
        legal=np.ones((2, 2)),
    )
    a = trace_losses(limited, np.array([[0.5, 0.5]]), 0)
    b = trace_losses(revealed, np.array([[0.5, 0.5], [0.5, 0.5]]), 0)
    assert b.value - a.value == 1
    assert b.gain == a.gain + 1
    optimal = trace_losses(limited, np.array([[0.0, 1.0]]), 0)
    assert optimal.gain == 0 and np.count_nonzero(optimal.losses) == 0


def test_first_legal_ties_zero_support_and_zero_baseline_reach() -> None:
    tree = hidden_tree()
    tied = replace(
        tree, terminal_values=np.array([0, 0, 2, 2, 0, 3, 3], dtype=np.float64)
    )
    np.testing.assert_array_equal(
        response_profile(tied, np.array([[0.5, 0.5]]), 0), [[1, 0]]
    )
    blocked = replace(
        tree,
        player=np.array([1, 0, -2, -2, 0, -2, -2]),
        information=np.array([0, 1, -1, -1, 2, -1, -1]),
        keys=("opponent", "left", "right"),
        actions=((0, 1),) * 3,
        owners=np.array([1, 0, 0]),
        legal=np.ones((3, 2)),
        chance_edges=np.zeros((7, 2)),
        chance_reach=np.ones(7),
    )
    trace = trace_losses(blocked, np.array([[1.0, 0.0], [0.5, 0.5], [0.5, 0.5]]), 0)
    assert (
        trace.counterfactual_mass[2]
        == trace.saved_reach_mass[2]
        == trace.losses[2]
        == 0
    )
    np.testing.assert_array_equal(trace.profile[2], [1, 0])
    kuhn = Tree.build("kuhn")
    policy = np.zeros_like(kuhn.legal)
    for i, actions in enumerate(kuhn.actions):
        policy[i, len(actions) - 1] = 1
    trace = trace_losses(kuhn, policy, 0)
    unreachable = (
        (trace.counterfactual_mass > 0)
        & (trace.saved_reach_mass == 0)
        & (kuhn.owners == 0)
    )
    assert unreachable.any()
    np.testing.assert_array_equal(trace.losses[unreachable], 0)


@pytest.mark.parametrize("game", ["kuhn", "leduc"])
@pytest.mark.parametrize("seed", [1, 7, 23])
def test_random_sequential_identity_and_opponent_preservation(
    game: GameName, seed: int
) -> None:
    tree = Tree.build(game)
    rng = np.random.default_rng(seed)
    policy = tree.normalize(rng.random(tree.legal.shape) * tree.legal)
    for target in (0, 1):
        trace = trace_losses(tree, policy, target)
        np.testing.assert_array_equal(
            trace.profile[tree.owners != target], policy[tree.owners != target]
        )
        assert trace.losses.sum() == pytest.approx(trace.gain, abs=1e-10)
        assert trace.losses.min() >= -1e-10
        assert trace.accounting_error < 1e-10
        if game == "kuhn":
            infos = np.flatnonzero(tree.owners == target)
            values = []
            for choices in itertools.product((0, 1), repeat=len(infos)):
                brute = policy.copy()
                brute[infos] = 0
                brute[infos, list(choices)] = 1
                values.append(
                    (1 if target == 0 else -1) * tree.values(tree.edges(brute))[0]
                )
            assert trace.value == pytest.approx(max(values), abs=1e-12)


def test_known_kuhn_equilibrium_has_zero_loss_and_minus_one_eighteenth_value() -> None:
    tree = Tree.build("kuhn")
    policy = np.zeros_like(tree.legal)
    seen = set()
    for node, state in enumerate(tree.states):
        if tree.player[node] < 0:
            continue
        info = int(tree.information[node])
        if info in seen:
            continue
        seen.add(info)
        rank, history = state.cards[state.actor], state.histories[0]
        if state.actor == 0 and not history:
            probability = (1 / 3, 0, 1)[rank]  # Opening bet.
        elif state.actor == 0:
            assert history == (1, 2)
            probability = (0, 2 / 3, 1)[rank]  # Call after check/bet.
        elif history == (1,):
            probability = (1 / 3, 0, 1)[rank]  # Bet after check.
        else:
            assert history == (2,)
            probability = (0, 1 / 3, 1)[rank]  # Call an opening bet.
        policy[info, :2] = (1 - probability, probability)
    assert tree.values(tree.edges(policy))[0] == pytest.approx(-1 / 18)
    for target in (0, 1):
        trace = trace_losses(tree, policy, target)
        assert abs(trace.gain) < 1e-12
        assert np.abs(trace.losses).max() < 1e-12


def test_imperfect_recall_invalid_player_and_tolerance_are_rejected() -> None:
    tree = hidden_tree()
    forgotten = replace(
        tree,
        player=np.array([0, 0, -2, -2, 0, -2, -2]),
        information=np.array([0, 1, -1, -1, 1, -1, -1]),
        keys=("first", "forgotten"),
        actions=((0, 1),) * 2,
        owners=np.array([0, 0]),
        legal=np.ones((2, 2)),
    )
    with pytest.raises(ValueError, match="recall"):
        response_profile(forgotten, np.full((2, 2), 0.5), 0)
    with pytest.raises(ValueError, match="target"):
        response_profile(tree, np.array([[0.5, 0.5]]), 2)
    with pytest.raises(ValueError, match="tolerance"):
        trace_losses(tree, np.array([[0.5, 0.5]]), 0, tolerance=float("nan"))


def fixture_source(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {"dirty": False, "sha256": {}, "git_commit": "tiny-software-fixture"}


@pytest.fixture(scope="module")
def tiny_diagnosis(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, Path, dict[str, Any]]:
    directory = tmp_path_factory.mktemp("reply-fixture")
    cfg = json.loads((ROOT / "configs/made-category-admission.json").read_text())
    cfg.update(
        spot_files=cfg["spot_files"][:1],
        full_tree_checkpoints=[1],
        full_tree_backend="numpy",
    )
    config = directory / "admission-config.json"
    config.write_text(json.dumps(cfg))
    with pytest.MonkeyPatch.context() as patch:
        # Only small software fixtures bypass clean source metadata, never evidence.
        patch.setattr(admission, "source_provenance", fixture_source)
        original = directory / "study.json"
        report = admission.run_admission(ROOT, config, original)
        assert report["status"] == "completed"
        cfg = json.loads((ROOT / "configs/candidate-best-response.json").read_text())
        cfg.update(
            input_report=str(original),
            input_report_sha256=digest(original),
            input_policy_sha256=report["own_policies_sha256"],
            iteration=1,
        )
        config = directory / "reply-config.json"
        config.write_text(json.dumps(cfg))
        patch.setattr(diagnosis, "source_provenance", fixture_source)
        path = directory / "diagnosis.json"
        result = diagnosis.diagnose(ROOT, config, path)
    return config, path, result


def test_tiny_complete_grid_replays_and_losses_sum(
    tiny_diagnosis: tuple[Path, Path, dict[str, Any]],
) -> None:
    _, path, _ = tiny_diagnosis
    report, details, error = diagnosis.replay(ROOT, path)
    assert len(report["cases"]) == len(details) == 4 and error == 0
    for case in report["cases"]:
        assert case["exact_exploitability_chips"] == pytest.approx(
            case["restricted_exploitability_chips"] + case["extra_information_chips"]
        )
        for response in case["responses"]:
            assert sum(response["street_losses_chips"].values()) == pytest.approx(
                response["exact_gain_chips"]
            )
            assert (
                sum(g["loss_contribution_chips"] for g in response["top_groups"])
                <= response["exact_gain_chips"] + 1e-9
            )
            for group in response["top_groups"]:
                for row in group["examples"]:
                    assert "opponent_cards" not in row and "future" not in row
                    assert len(row["hole"]) == 2


@pytest.mark.parametrize("change", ["missing", "duplicate", "number", "nan", "sidecar"])
def test_mutated_receipts_rejected(
    tiny_diagnosis: tuple[Path, Path, dict[str, Any]], tmp_path: Path, change: str
) -> None:
    _, original, raw = tiny_diagnosis
    report = copy.deepcopy(raw)
    sidecar = original.parent / report["details_file"]
    shutil.copyfile(sidecar, tmp_path / sidecar.name)
    if change == "missing":
        report["cases"].pop()
    elif change == "duplicate":
        report["cases"].append(report["cases"][-1])
    elif change == "sidecar":
        (tmp_path / sidecar.name).write_bytes(b"changed")
    else:
        report["cases"][0]["exact_exploitability_chips"] += (
            0.1 if change == "number" else float("nan")
        )
    path = tmp_path / "changed.json"
    path.write_text(json.dumps(report))
    with pytest.raises((ValueError, ArithmeticError)):
        diagnosis.replay(ROOT, path)


def test_overwrite_input_and_dirty_source_guards(
    tiny_diagnosis: tuple[Path, Path, dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config, path, _ = tiny_diagnosis
    with pytest.raises(FileExistsError):
        diagnosis.diagnose(ROOT, config, path)
    cfg = json.loads(config.read_text())
    cfg["input_report_sha256"] = "changed"
    other = tmp_path / "config.json"
    other.write_text(json.dumps(cfg))
    with pytest.raises(ArithmeticError, match="report"):
        diagnosis.diagnose(ROOT, other, tmp_path / "diagnosis.json")
    monkeypatch.setattr(diagnosis, "source_provenance", lambda *a, **k: {"dirty": True})
    with pytest.raises(ValueError, match="clean"):
        diagnosis.diagnose(ROOT, config, tmp_path / "diagnosis.json")


def test_native_roots_and_offline_report(
    tiny_diagnosis: tuple[Path, Path, dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("pyspiel")
    pytest.importorskip("matplotlib")
    config, path, _ = tiny_diagnosis
    audit_path = tmp_path / "independent.json"
    monkeypatch.setattr(native, "source_provenance", fixture_source)
    result = native.audit(ROOT, config, path, audit_path)
    assert result["status"] == "passed" and len(result["rows"]) == 8
    assert result["maximum_native_error_chips"] < 1e-9
    rendered = reporting.render(ROOT, path, audit_path, tmp_path / "report")
    assert rendered["native_roots_checked"] == 16
    for name in (
        "response-values.png",
        "candidate-streets.png",
        "tables.md",
        "summary.csv",
        "street-losses.csv",
    ):
        assert (tmp_path / "report" / name).stat().st_size > 50
    result["rows"].pop()
    audit_path.write_text(json.dumps(result))
    with pytest.raises(ArithmeticError, match="audit"):
        reporting.render(ROOT, path, audit_path, tmp_path / "changed")


def test_terminal_viewer_and_invalid_rank(
    tiny_diagnosis: tuple[Path, Path, dict[str, Any]],
) -> None:
    _, path, _ = tiny_diagnosis
    command = [
        sys.executable,
        str(ROOT / "scripts/inspect_saved_reply.py"),
        "--report",
        str(path),
        "--game",
        "dev_low_oop",
    ]
    good = subprocess.run(command, text=True, capture_output=True)
    assert (
        good.returncode == 0
        and "additive loss" in good.stdout
        and "saved probability" in good.stdout
    )
    bad = subprocess.run(command + ["--rank", "0"], capture_output=True)
    assert bad.returncode == 2
