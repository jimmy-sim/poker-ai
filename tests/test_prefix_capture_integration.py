"""Actual tiny IO/replay and retained corrupt/partial output; never poker evidence."""

import copy
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from poker_ai.evaluation import prefix_capture_software as software
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.tree import SpotTree
from poker_ai.solver_validation.reference import Reference

pytestmark = pytest.mark.slow
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def clean_root(tmp_path_factory: pytest.TempPathFactory) -> Path:
    root = tmp_path_factory.mktemp("EXPLICIT_clean_software_source")
    shutil.copytree(
        ROOT / "src", root / "src", ignore=shutil.ignore_patterns("__pycache__")
    )
    for name in (
        software.CONFIG,
        "configs/matched-update-batches.json",
        "scripts/check_prefix_capture.py",
        "pyproject.toml",
        "uv.lock",
        ".gitignore",
    ):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    for command in (
        ["init", "-q"],
        ["add", "."],
        [
            "-c",
            "user.name=Software fixture",
            "-c",
            "user.email=fixture@example.invalid",
            "-c",
            "commit.gpgsign=false",
            "commit",
            "-qm",
            "Explicit temporary software source",
        ],
    ):
        subprocess.run(
            ["git", "-C", str(root), *command], check=True, capture_output=True
        )
    return root


@pytest.fixture(scope="module")
def complete(
    tmp_path_factory: pytest.TempPathFactory, clean_root: Path
) -> tuple[Path, dict[str, Any]]:
    path = tmp_path_factory.mktemp("EXPLICIT_tiny_prefix") / "own.json"
    with (
        patch.object(Reference, "__init__", side_effect=AssertionError("no reference")),
        patch.object(SpotTree, "build", side_effect=AssertionError("no poker tree")),
    ):
        saved = software.run(clean_root, path)
        assert software.read(clean_root, path) == saved["replay"]
    return path, saved


def test_complete144policy96mass384step_grid_is_explicit_software(
    complete: tuple[Path, dict[str, Any]],
) -> None:
    _, saved = complete
    assert saved["scope"] == software.SCOPE
    assert saved["completed_profiles"] == 144
    assert saved["completed_raw_ledgers"] == 96
    assert saved["completed_step_checks"] == 384
    assert saved["replay"]["maximum_error_fixture_chips"] < 1e-12
    assert saved["software_training_performed"] is True
    assert saved["poker_training_performed"] is False
    assert saved["reference_constructed"] is False
    assert saved["long_run_admitted"] is False
    # Repeated logical cases deliberately share a tiny path: not24independent games.
    policies = {
        (r["fixture_case"], r["iteration"], r["readout"]): r for r in saved["profiles"]
    }
    assert (
        policies[0, 4, "current"]["receipt"]["policy_sha256"]
        == policies[6, 4, "current"]["receipt"]["policy_sha256"]
    )


@pytest.mark.parametrize(
    "kind",
    [
        "profile_missing",
        "profile_duplicate",
        "mass_missing",
        "step_missing",
        "bool_case",
        "wrong_guard",
        "work_crossing",
    ],
)
def test_inventory_and_source_step_corruption_rejected(
    complete: tuple[Path, dict[str, Any]],
    kind: str,
) -> None:
    _, original = complete
    saved = copy.deepcopy(original)
    if kind == "profile_missing":
        saved["profiles"].pop()
    elif kind == "profile_duplicate":
        saved["profiles"][-1] = saved["profiles"][0]
    elif kind == "mass_missing":
        saved["masses"].pop()
    elif kind == "step_missing":
        saved["checks"].pop()
    elif kind == "bool_case":
        saved["profiles"][0]["fixture_case"] = False
    elif kind == "wrong_guard":
        saved["profiles"][0]["guard_sha256"] = "b" * 64
    else:
        saved["checks"][1]["work_labels"] = [1]
    with pytest.raises(ArithmeticError):
        software.inventory(saved)


def test_archive_corruption_is_detected_without_modifying_source(
    complete: tuple[Path, dict[str, Any]],
    tmp_path: Path,
    clean_root: Path,
) -> None:
    source, saved = complete
    for name in ("own.json", saved["policies_file"], saved["masses_file"]):
        shutil.copyfile(source.with_name(name), tmp_path / name)
    path = tmp_path / saved["policies_file"]
    path.write_bytes(path.read_bytes() + b"CORRUPT")
    with pytest.raises(ArithmeticError, match="hash changed"):
        software.read(clean_root, tmp_path / "own.json")


def test_pre_input_failure_is_retained_without_training_attempt(
    tmp_path: Path, clean_root: Path
) -> None:
    output = tmp_path / "own.json"
    with patch.object(
        software, "config_inputs", side_effect=RuntimeError("input failed")
    ):
        with pytest.raises(RuntimeError, match="input failed"):
            software.run(clean_root, output)
    saved = json.loads(output.read_text())
    assert (
        saved["status"] == "incomplete" and saved["failure"]["type"] == "RuntimeError"
    )
    assert saved["software_training_attempted"] is False
    assert saved["completed_profiles"] == 0
    with pytest.raises(ArithmeticError, match="incomplete"):
        software.read(clean_root, output)
    before = output.read_bytes()
    with pytest.raises(FileExistsError):
        software.run(clean_root, output)
    assert output.read_bytes() == before


def test_partial_capture_keeps_raw_files_and_actual_counts(
    tmp_path: Path, clean_root: Path
) -> None:
    output = tmp_path / "own.json"
    actual = software.collect

    def stop(index: int, *args: Any, **kwargs: Any) -> None:
        if index == 1:
            raise RuntimeError("stop after first tiny case")
        actual(index, *args, **kwargs)

    with patch.object(software, "collect", side_effect=stop):
        with pytest.raises(RuntimeError, match="first tiny case"):
            software.run(clean_root, output)
    saved = json.loads(output.read_text())
    assert saved["status"] == "incomplete"
    assert saved["completed_profiles"] == 6
    assert saved["completed_raw_ledgers"] == 4
    assert saved["completed_step_checks"] == 16
    assert saved["software_training_performed"] is True
    assert saved["long_run_admitted"] is False
    assert all(
        (Path(saved["scratch"]) / r["file"]).is_file() for r in saved["profiles"]
    )


def test_timeout_is_retained_and_cannot_mark_complete(
    tmp_path: Path, clean_root: Path
) -> None:
    output = tmp_path / "own.json"
    with patch.object(Deadline, "check", side_effect=TimeoutError("fixed cap")):
        with pytest.raises(TimeoutError):
            software.run(clean_root, output)
    saved = json.loads(output.read_text())
    assert (
        saved["status"] == "incomplete" and saved["failure"]["type"] == "TimeoutError"
    )
    assert saved["completed_profiles"] == 0
    assert saved["poker_training_performed"] is False


def test_archive_failure_retains_complete_raw_capture_without_claiming_completion(
    tmp_path: Path,
    clean_root: Path,
) -> None:
    output = tmp_path / "own.json"
    with patch.object(software, "write_archive", side_effect=OSError("archive failed")):
        with pytest.raises(OSError):
            software.run(clean_root, output)
    saved = json.loads(output.read_text())
    assert saved["status"] == "incomplete"
    assert saved["completed_profiles"] == 144 and saved["completed_raw_ledgers"] == 96
    assert saved["failure"]["type"] == "OSError"
