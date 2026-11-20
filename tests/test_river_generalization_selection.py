"""Prospective selection uses structural novelty and never replaces a cohort."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from poker_ai.cards import parse_card

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from river_generalization import selection  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "cohort"
    root.mkdir(parents=True)
    names = [
        "configs/river-generalization-fixed-spots.json",
        *json.loads(
            (ROOT / "configs/river-generalization-fixed-spots.json").read_bytes()
        )["input_sha256"],
        "configs/spots/dry_low_oop.json",
    ]
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, path)
    subprocess.run(["git", "init", "-q", str(root)], check=True)
    subprocess.run(["git", "-C", str(root), "add", "."], check=True)
    subprocess.run(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "user.name=Test",
            "-c",
            "user.email=test@example.com",
            "commit",
            "-qm",
            "inputs",
        ],
        check=True,
    )
    return root


def test_rank_texture_rules_reject_known_signature_across_suits() -> None:
    wet = [parse_card(card) for card in ("4h", "2s", "3s", "7s")]
    recolored = [parse_card(card) for card in ("4c", "2d", "3d", "7h")]
    dry = [parse_card(card) for card in ("Jh", "8d", "2c", "3s")]
    assert selection.rank_signature(wet) == selection.rank_signature(recolored)
    assert selection.texture_matches(wet, "wet")
    assert selection.texture_matches(dry, "dry")
    assert not selection.texture_matches(wet, "dry")
    assert not selection.texture_matches(dry, "wet")


def test_tracked_inventory_ignores_unrelated_local_spot(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    extra = root / "configs/spots/untracked.json"
    extra.write_text((ROOT / "configs/spots/dry_low_oop.json").read_text())
    known = selection.tracked_known_spots(
        root, ["configs/learning-spots", "configs/fresh-spots", "configs/spots"]
    )
    assert extra not in known
    assert len(known) == 3


def test_selection_is_deterministic_novel_legal_and_refuses_replacement(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(selection, "SELECTION_SOURCES", ())
    first = _repo(tmp_path / "one")
    second = _repo(tmp_path / "two")
    a = selection.select(first)
    b = selection.select(second)
    assert a["spot_sha256"] == b["spot_sha256"]
    assert a["selection"] == b["selection"]
    known = {
        selection.rank_signature(
            [
                parse_card(card)
                for card in json.loads((first / name).read_bytes())["board"]
            ]
        )
        for name in a["known_spot_sha256"]
    }
    selected = set()
    for row in a["selection"]:
        spot = json.loads((first / row["spot_file"]).read_bytes())
        board = [parse_card(card) for card in spot["board"]]
        signature = selection.rank_signature(board)
        assert signature not in known and signature not in selected
        selected.add(signature)
        assert selection.texture_matches(board, spot["texture"])
        assert len(spot["ranges"]) == 2
        assert [len(group) for group in spot["ranges"]] == [2, 2]
        cards = board + [
            parse_card(card)
            for group in spot["ranges"]
            for entry in group
            for card in entry["cards"]
        ]
        assert len(set(cards)) == 12
        assert all(
            1 <= entry["weight"] <= 3 for group in spot["ranges"] for entry in group
        )
    saved = (first / a["selection"][0]["spot_file"]).read_bytes()
    with pytest.raises(RuntimeError, match="clean published source"):
        selection.select(first)
    assert (first / a["selection"][0]["spot_file"]).read_bytes() == saved
