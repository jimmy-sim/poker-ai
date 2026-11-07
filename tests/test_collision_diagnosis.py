"""Local sharing score math, hidden-state averaging and retained fixture inputs."""

import json
import subprocess
import sys
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.finite import ArrayTree
from poker_ai.postflop import collision_diagnosis as diagnosis
from poker_ai.postflop import public_study
from poker_ai.postflop.river_study import digest

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


def test_hidden_histories_are_averaged_before_actions_are_compared() -> None:
    tree = hidden_tree()
    q, support = diagnosis.conditional_actions(tree, np.array([[0.5, 0.5]]))
    np.testing.assert_array_equal(q, [[1, 1.5]])
    np.testing.assert_array_equal(support, [1])
    assert q.max() == 1.5  # A forbidden per-hidden-world maximization gives 2.5.
    other = replace(
        tree, player=np.array([-1, 1, -2, -2, 1, -2, -2]), owners=np.array([1])
    )
    negative, _ = diagnosis.conditional_actions(other, np.array([[0.5, 0.5]]))
    np.testing.assert_array_equal(negative, [[-1, -1.5]])
    np.testing.assert_array_equal(
        diagnosis.conditional_actions(tree, np.array([[1.0, 0.0]]))[0], q
    )


def test_sharing_score_zero_sanity_weighting_and_offsets() -> None:
    q = np.array([[3.0, 1.0], [0.0, 4.0]])
    weights = np.array([0.25, 0.75])
    assert diagnosis.sharing_cost(q, weights) == 0.5
    assert diagnosis.sharing_cost(q + np.array([[100.0], [-50.0]]), weights) == 0.5
    assert diagnosis.sharing_cost(q, 2 * weights) == 1
    assert diagnosis.sharing_cost(q[:1], weights[:1]) == 0
    assert diagnosis.sharing_cost(np.array([[3.0, 1.0], [4.0, 0.0]]), weights) == 0
    assert diagnosis.sharing_cost(q, np.zeros(2)) == 0


def test_opponent_reach_weights_hidden_values_and_zero_support_is_explicit() -> None:
    tree = hidden_tree()
    tree = replace(
        tree,
        player=np.array([1, 0, -2, -2, 0, -2, -2]),
        information=np.array([0, 1, -1, -1, 1, -1, -1]),
        keys=("opponent", "hidden"),
        actions=((0, 1), (0, 1)),
        owners=np.array([1, 0]),
        legal=np.ones((2, 2)),
        chance_edges=np.zeros((7, 2)),
        chance_reach=np.ones(7),
    )
    q, mass = diagnosis.conditional_actions(tree, np.array([[0.25, 0.75], [0.5, 0.5]]))
    np.testing.assert_array_equal(q[1], [1, 1.5])
    assert mass[1] == 1
    separate = replace(
        tree,
        information=np.array([0, 1, -1, -1, 2, -1, -1]),
        keys=("opponent", "left", "right"),
        actions=((0, 1),) * 3,
        owners=np.array([1, 0, 0]),
        legal=np.ones((3, 2)),
    )
    q, mass = diagnosis.conditional_actions(
        separate, np.array([[1.0, 0.0], [0.5, 0.5], [0.5, 0.5]])
    )
    assert mass[2] == 0
    np.testing.assert_array_equal(q[2], [0, 0])


@pytest.mark.parametrize(
    "q,weights",
    [
        (np.ones((2, 2)), np.array([1.0])),
        (np.ones((2, 2)), np.array([1.0, -1.0])),
        (np.array([[float("nan"), 0.0]]), np.ones(1)),
        (np.empty((0, 2)), np.empty(0)),
    ],
)
def test_invalid_sharing_values_are_rejected(
    q: np.ndarray[Any, Any], weights: np.ndarray[Any, Any]
) -> None:
    with pytest.raises(ValueError):
        diagnosis.sharing_cost(q, weights)


@pytest.fixture(scope="module")
def fixture_diagnosis(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, Path, dict[str, Any]]:
    directory = tmp_path_factory.mktemp("collision-fixture")
    raw = json.loads((ROOT / "configs/public-board-study.json").read_text())
    raw.update(
        development_spots=raw["development_spots"][:1],
        seeds=[17],
        sampled_node_checkpoints=[6000],
        full_tree_checkpoints=[1],
        full_tree_backend="numpy",
        profile_iterations=1,
        profile_repetitions=1,
    )
    config = directory / "study-config.json"
    config.write_text(json.dumps(raw))
    path = directory / "study.json"
    with pytest.MonkeyPatch.context() as patch:
        # Explicit tiny software fixture, never actual diagnosis/learning evidence.
        def fixture_source(*args: Any, **kwargs: Any) -> dict[str, Any]:
            return {"dirty": False, "sha256": {}, "git_commit": "test"}

        patch.setattr(public_study, "source_provenance", fixture_source)
        report = public_study.run_study(ROOT, config, path)
        assert report["status"] == "completed", report["failure"]
        raw = json.loads((ROOT / "configs/board-collision-diagnosis.json").read_text())
        raw.update(
            input_report=str(path),
            input_report_sha256=digest(path),
            input_policy_sha256=report["own_policies_sha256"],
        )
        config = directory / "diagnosis-config.json"
        config.write_text(json.dumps(raw))
        patch.setattr(diagnosis, "source_provenance", fixture_source)
        output = directory / "diagnosis.json"
        result = diagnosis.diagnose(ROOT, config, output)
    return config, output, result


def test_diagnostic_fixture_panels_support_and_visible_examples(
    fixture_diagnosis: tuple[Path, Path, dict[str, Any]],
) -> None:
    _, _, result = fixture_diagnosis
    assert len(result["cases"]) == 2
    assert [c["panel"] for c in result["cases"]] == ["own_exact_full", "uniform"]
    assert result["cases"][1]["supported_uniform_decision_weight"] == pytest.approx(1)
    for case in result["cases"]:
        scores = [
            r["local_sharing_cost_chips_per_decision"] for r in case["top_groups"]
        ]
        assert scores == sorted(scores, reverse=True)
        for group in case["top_groups"]:
            assert group["supported_exact_infos"] >= 2
            assert group["local_sharing_cost_chips_per_decision"] > 0
            for example in group["examples"]:
                assert len(example["hole"]) == 2 and len(example["board"]) in (4, 5)
                assert "opponent_cards" not in example and "future" not in example
                assert len(example["actions"]) == len(
                    example["conditional_action_values_chips"]
                )


def test_diagnosis_refuses_changed_inputs_and_existing_output(
    fixture_diagnosis: tuple[Path, Path, dict[str, Any]],
    tmp_path: Path,
) -> None:
    config, output, _ = fixture_diagnosis
    with pytest.raises(FileExistsError):
        diagnosis.diagnose(ROOT, config, output)
    raw = json.loads(config.read_text())
    raw["input_report_sha256"] = "changed"
    changed = tmp_path / "config.json"
    changed.write_text(json.dumps(raw))
    with pytest.raises(ArithmeticError, match="input report"):
        diagnosis.diagnose(ROOT, changed, tmp_path / "new.json")


def test_inspector_uses_only_saved_examples_and_rejects_missing_rank(
    fixture_diagnosis: tuple[Path, Path, dict[str, Any]],
    tmp_path: Path,
) -> None:
    _, _, result = fixture_diagnosis
    # A deterministic display fixture keeps CLI coverage independent of whether
    # the tiny uniform control has a nonzero local gap on a particular platform.
    payload = {
        "cases": [
            {
                "spot": "example",
                "panel": "uniform",
                "top_groups": [
                    {
                        "abstract_info": 7,
                        "local_sharing_cost_chips_per_decision": 0.5,
                        "examples": [
                            {
                                "seat": 0,
                                "hole": ["As", "Js"],
                                "board": ["Ts", "9s", "4d", "2h", "7c"],
                                "hand_category": "HIGH_CARD",
                                "pot": 36,
                                "preferred_actions": ["check"],
                                "actions": ["check", "raise_to 36"],
                                "conditional_action_values_chips": [1.0, 0.0],
                            }
                        ],
                    }
                ],
            }
        ]
    }
    path = tmp_path / "display-fixture.json"
    path.write_text(json.dumps(payload))
    command = [
        sys.executable,
        str(ROOT / "scripts/inspect_board_collision.py"),
        "--report",
        str(path),
        "--game",
        "example",
        "--panel",
        "uniform",
    ]
    good = subprocess.run(command, capture_output=True, text=True)
    assert (
        good.returncode == 0
        and "texture row 7" in good.stdout
        and "preferred: check" in good.stdout
    )
    bad = subprocess.run(command + ["--rank", "0"], capture_output=True)
    assert bad.returncode == 2
    assert result["format"] == "poker-ai-board-collision-diagnosis-v1"
