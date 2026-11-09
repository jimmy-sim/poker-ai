"""Pure replay guards and an explicit three-process toy archive integration."""

import copy
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.averaging_history_correctness import software_roundtrip
from poker_ai.evaluation.averaging_history_inputs import inputs
from poker_ai.evaluation.averaging_history_replay import (
    archive_path,
    compare_coverage,
    replay_archives,
)
from poker_ai.evaluation.averaging_history_software import software_inputs
from poker_ai.postflop.learning_artifacts import (
    canonical,
    read_archive,
    sha,
    write_archive,
)
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize(
    "name", ["../outside.gz", "/tmp/outside.gz", "", ".", "..", True]
)
def test_archive_names_cannot_escape_bound_directory(name: Any) -> None:
    with pytest.raises(ArithmeticError):
        archive_path(Path("/tmp/example/own.json"), name)


def test_coverage_uses_strict_counts_and_its_separate_unitless_tolerance() -> None:
    import copy

    expected: dict[str, Any] = dict(
        all=dict(rows=4, positive_rows=2, row_fraction=0.5, uniform_reach_fraction=0.4),
        river=dict(
            rows=0, positive_rows=0, row_fraction=None, uniform_reach_fraction=None
        ),
    )
    assert compare_coverage(expected, expected, 1e-12) == 0
    for key, value in (
        ("rows", 4.0),
        ("positive_rows", True),
        ("uniform_reach_fraction", 0.4 + 2e-11),
    ):
        changed = copy.deepcopy(expected)
        changed["all"][key] = value
        with pytest.raises(ArithmeticError):
            compare_coverage(expected, changed, 1e-12)


@pytest.fixture(scope="module")
def toy_archives(tmp_path_factory: pytest.TempPathFactory) -> tuple[Any, ...]:
    folder = tmp_path_factory.mktemp("history-replay") / "EXPLICIT_SOFTWARE_FIXTURE"
    config = inputs(ROOT)
    result = software_roundtrip(config, folder, "f" * 64, Deadline(120))
    saved = json.loads((folder / "own.json").read_text())
    data = software_inputs(config, Deadline(120))
    return folder, result, saved, data


@pytest.mark.slow
def test_three_process_toy_archive_replays_every_profile_mass_and_match(
    toy_archives: tuple[Any, ...],
) -> None:
    _, result, _, _ = toy_archives
    assert result["status"] == "passed_software_roundtrip_no_new_poker_training"
    assert result["new_postflop_training_performed"] is False
    assert result["original_prefix_checks"] == 192
    assert result["fixed_opponent_targets"] == 2048
    proof = result["replay"]
    assert proof["profiles"] == 512
    assert proof["cumulative_boundaries"] == 192
    assert proof["suffix_reconstructions"] == 128
    assert proof["whole_reconstructions"] == 64
    assert proof["identical_current_pairs"] == 160
    assert proof["maximum_error_chips"] == 0
    assert proof["maximum_error_unitless"] == 0
    assert proof["maximum_fixed_identity_error_chips"] <= 1e-9


@pytest.mark.slow
@pytest.mark.parametrize("change", ["score", "coverage", "window", "mass"])
def test_rehashed_toy_corruptions_fail_semantic_replay(
    toy_archives: tuple[Any, ...],
    tmp_path: Path,
    change: str,
) -> None:
    """Update every envelope hash: semantic checks must still find the corruption."""
    import shutil

    folder, _, original, data = toy_archives
    saved = copy.deepcopy(original)
    mass = change == "mass"
    rows_key = "masses" if mass else "rows"
    name_key = "mass_details_file" if mass else "details_file"
    hash_key = "mass_details_sha256" if mass else "details_sha256"
    scratch = tmp_path / "scratch"
    scratch.mkdir()
    for i, (row, blob) in enumerate(
        read_archive(folder / original[name_key], original[hash_key], saved[rows_key])
    ):
        # First case: whole average (5), first suffix (6), or first raw boundary.
        selected = i == (0 if mass else 6 if change == "window" else 5)
        if selected:
            payload = json.loads(gzip.decompress(blob))
            if change == "score":
                row["metrics"]["value_player_zero_chips"] += 0.25
            elif change == "coverage":
                row["coverage"]["all"]["uniform_reach_fraction"] -= 0.01
            elif change == "window":
                row["window"]["left_iteration"] += 1
            else:
                import numpy as np

                from poker_ai.evaluation.averaging_history_artifacts import (
                    array_sha,
                    unpack_mass,
                )

                payload["mass"][0][0] += 1.0
                tree = data.base.context(data.base.policies[0].case).partition
                row["receipt"]["mass_sha256"] = array_sha(
                    unpack_mass(tree, payload["mass"])
                )
                assert np.isfinite(payload["mass"][0][0])
            payload["metadata"] = {
                k: v
                for k, v in row.items()
                if k
                not in {"receipt", "metadata_sha256", "file", "seconds", "cpu_seconds"}
            }
            row["metadata_sha256"] = sha(payload["metadata"])
            blob = gzip.compress(canonical(payload), mtime=0)
            row["receipt"].update(
                bytes=len(blob), sha256=hashlib.sha256(blob).hexdigest()
            )
        target = scratch / row["file"]
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(blob)
    other = "details_file" if mass else "mass_details_file"
    shutil.copyfile(folder / original[other], tmp_path / original[other])
    saved[hash_key] = write_archive(
        tmp_path / saved[name_key], scratch, saved[rows_key]
    )
    expected = {
        "score": "own score/reply",
        "coverage": "coverage changed",
        "window": "suffix boundary",
        "mass": "suffix boundary",
    }[change]
    with pytest.raises(ArithmeticError, match=expected):
        replay_archives(folder, tmp_path / "own.json", saved, data, Deadline(120))


def test_failed_software_attempt_is_retained_and_not_overwritten(
    tmp_path: Path,
) -> None:
    import json

    folder = tmp_path / "incomplete-explicit-software"
    with pytest.raises(TimeoutError):
        software_roundtrip(inputs(ROOT), folder, "f" * 64, Deadline(1e-9))
    path = folder / "software.json"
    before = path.read_bytes()
    result = json.loads(before)
    assert result["status"] == "incomplete"
    assert result["failure"]["type"] == "TimeoutError"
    assert result["new_postflop_training_performed"] is False
    with pytest.raises(FileExistsError):
        software_roundtrip(inputs(ROOT), folder, "f" * 64, Deadline(120))
    assert path.read_bytes() == before
