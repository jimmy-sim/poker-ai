"""Complete toy artifacts and deliberate rehashed semantic corruptions."""

import copy
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.window_fallback_replay import replay_archives
from poker_ai.evaluation.window_fallback_software import software_roundtrip
from poker_ai.evaluation.window_fallback_validation import grid, validate_replay
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.learning_artifacts import canonical, sha, write_archive
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def toy_archive(tmp_path_factory: pytest.TempPathFactory) -> tuple[Any, ...]:
    folder = tmp_path_factory.mktemp("fallback-archive") / "EXPLICIT_SOFTWARE_FIXTURE"
    data, saved, scratch = software_roundtrip(ROOT, folder, Deadline(120))
    return folder, data, saved, scratch


@pytest.mark.slow
def test_complete_toy_archive_reconstructs_all_profiles_controls_and_matches(
    toy_archive: tuple[Any, ...],
) -> None:
    _, data, saved, _ = toy_archive
    proof = saved["own_replay"]
    validate_replay(proof, data.config)
    assert proof["profiles"] == 512
    assert proof["raw_window_controls"] == 128
    assert proof["full_windows"] == 32
    assert proof["additivity_panels"] == 128
    assert proof["fixed_target_conditions"] == 2048
    assert proof["maximum_error_chips"] <= 1e-9
    assert proof["maximum_error_unitless"] == 0
    assert proof["maximum_full_realization_change"] <= 1e-12


@pytest.mark.slow
@pytest.mark.parametrize("change", ["score", "mask", "support", "policy"])
def test_rehashed_corruptions_fail_meaning_not_only_byte_hashes(
    toy_archive: tuple[Any, ...],
    tmp_path: Path,
    change: str,
) -> None:
    _, data, original, source_scratch = toy_archive
    saved = copy.deepcopy(original)
    scratch = tmp_path / "scratch"
    for i, row in enumerate(saved["rows"]):
        blob = (source_scratch / row["file"]).read_bytes()
        if i == (1 if change == "policy" else 0):
            payload = json.loads(gzip.decompress(blob))
            if change == "score":
                row["metrics"]["value_player_zero_chips"] += 0.25
            elif change == "mask":
                row["eligible_sha256"] = "0" * 64
            elif change == "support":
                key = "eligible_uniform_reach_fraction"
                value = row["support"][0][key]
                row["support"][0][key] += 2e-11 if value < 0.5 else -2e-11
            else:
                payload["policy"][0] = (
                    [1.0, 0.0] if payload["policy"][0] != [1.0, 0.0] else [0.0, 1.0]
                )
                tree = data.history.base.context(row["case"]).partition
                row["receipt"]["policy_sha256"] = array_sha(
                    unpack_policy(tree, payload["policy"])
                )
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
        path = scratch / row["file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(blob)
    saved["details_sha256"] = write_archive(
        tmp_path / saved["details_file"], scratch, saved["rows"]
    )
    with pytest.raises(ArithmeticError):
        replay_archives(data, tmp_path / "own.json", saved, Deadline(120))


@pytest.mark.slow
@pytest.mark.parametrize(
    "mode",
    [
        "missing_row",
        "duplicate",
        "bool_index",
        "mask_order",
        "changed_case",
        "missing_panel",
        "false_full_gate",
        "panel_ev",
        "fixed_missing",
        "fixed_duplicate",
        "fixed_bool_target",
        "fixed_reply",
        "fixed_delta",
    ],
)
def test_complete_grid_and_replay_reject_changed_fictional_toy_ledgers(
    toy_archive: tuple[Any, ...],
    mode: str,
) -> None:
    folder, data, original, _ = toy_archive
    saved = copy.deepcopy(original)
    if mode == "missing_row":
        saved["rows"].pop()
    elif mode == "duplicate":
        saved["rows"][1] = copy.deepcopy(saved["rows"][0])
    elif mode == "bool_index":
        saved["rows"][0]["index"] = False
    elif mode == "mask_order":
        saved["rows"][3]["fill_targets"] = [1, 0]
    elif mode == "changed_case":
        saved["rows"][0]["case"]["seed"] = 123
    elif mode == "missing_panel":
        saved["panels"].pop()
    elif mode == "false_full_gate":
        row = next(r for r in saved["rows"] if r["case"]["traversal"] == "full")
        row["maximum_realization_change"] = 2e-11
    elif mode == "panel_ev":
        saved["panels"][0]["baseline_ev_interaction_chips"] += 0.25
    elif mode == "fixed_missing":
        saved["fixed_matches"].pop()
    elif mode == "fixed_duplicate":
        saved["fixed_matches"][1] = copy.deepcopy(saved["fixed_matches"][0])
    elif mode == "fixed_bool_target":
        saved["fixed_matches"][0]["target"] = False
    elif mode == "fixed_reply":
        saved["fixed_matches"][0]["reply_sha256"] = "0" * 64
    else:
        saved["fixed_matches"][0]["gain_difference_chips"] += 0.1
    with pytest.raises(ArithmeticError):
        if mode == "panel_ev":
            replay_archives(data, folder / "software.json", saved, Deadline(120))
        else:
            grid(saved, data)


def test_timeout_software_fixture_retained_and_not_replaced(tmp_path: Path) -> None:
    folder = tmp_path / "EXPLICIT_FAILED_SOFTWARE_FIXTURE"
    with pytest.raises(TimeoutError):
        software_roundtrip(ROOT, folder, Deadline(1e-9))
    before = (folder / "software.json").read_bytes()
    saved = json.loads(before)
    assert saved["status"] == "incomplete"
    assert saved["failure"]["type"] == "TimeoutError"
    assert saved["new_postflop_training_performed"] is False
    with pytest.raises(FileExistsError):
        software_roundtrip(ROOT, folder, Deadline(120))
    assert (folder / "software.json").read_bytes() == before
