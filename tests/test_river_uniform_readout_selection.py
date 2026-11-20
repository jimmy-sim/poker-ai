"""The published panel selects only structural inputs and cannot replace them."""

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from poker_ai.cards import parse_card

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from river_uniform_readout import selection  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def _repo(tmp_path: Path) -> Path:
    root = tmp_path / "cohort"
    root.mkdir(parents=True)
    config = json.loads((ROOT / selection.CONFIG).read_bytes())
    names = [str(selection.CONFIG), *config["input_sha256"]]
    for directory in config["known_spot_directories"]:
        names.extend(
            subprocess.check_output(
                ["git", "-C", str(ROOT), "ls-files", "--", directory], text=True
            ).splitlines()
        )
    for name in set(names):
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


def test_fixed_panel_is_deterministic_novel_and_nonreplaceable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(selection, "SELECTION_SOURCES", ())
    first = _repo(tmp_path / "one")
    second = _repo(tmp_path / "two")
    a = selection.select(first)
    b = selection.select(second)
    assert a["spot_sha256"] == b["spot_sha256"]
    assert a["selection"] == b["selection"]
    assert len(a["selection"]) == 4
    known = {
        selection.rank_signature(
            [
                parse_card(card)
                for card in json.loads((first / name).read_bytes())["board"]
            ]
        )
        for name in a["known_spot_sha256"]
    }
    selected: set[tuple[tuple[int, ...], int]] = set()
    for row in a["selection"]:
        spot = json.loads((first / row["spot_file"]).read_bytes())
        board = [parse_card(card) for card in spot["board"]]
        signature = selection.rank_signature(board)
        assert signature not in known and signature not in selected
        assert selection.texture_matches(board, spot["texture"])
        selected.add(signature)
        assert row["selection_attempts"] <= 10_000
    saved = (first / a["selection"][0]["spot_file"]).read_bytes()
    with pytest.raises(RuntimeError, match="clean published source"):
        selection.select(first)
    assert (first / a["selection"][0]["spot_file"]).read_bytes() == saved


def test_pinned_input_and_dirty_checkout_fail_closed(tmp_path: Path) -> None:
    root = _repo(tmp_path)
    config = json.loads((root / selection.CONFIG).read_bytes())
    pinned = root / next(iter(config["input_sha256"]))
    pinned.write_bytes(pinned.read_bytes() + b"\n")
    with pytest.raises(RuntimeError, match="clean published source"):
        selection.select(root)
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
            "tampered",
        ],
        check=True,
    )
    with pytest.raises(ArithmeticError, match="pinned selection input"):
        selection.select(root)
