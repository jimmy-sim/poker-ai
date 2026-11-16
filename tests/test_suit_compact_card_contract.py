"""Fictional-source card-only fixtures; never a formal published software proof."""

import json
import shutil
from pathlib import Path
from typing import Any

import grouped_depth_support as fields
import pytest
import suit_candidates_support as kernel
from compact_suit import card_contract as t

from poker_ai.abstraction import potential
from poker_ai.postflop.river_study import Deadline, digest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = "UNIT_CARD_CONTRACT_NOT_SOURCE_QUALIFICATION_OR_ADMISSION"


@pytest.fixture(scope="module")
def captured(tmp_path_factory: pytest.TempPathFactory) -> Path:
    folder = tmp_path_factory.mktemp("fictional-card-contract") / "capture"
    meta = t.collect(ROOT, folder, FIXTURE, Deadline(180))
    assert meta["source_sha256"] == FIXTURE
    assert potential.canonical_cards is kernel.BASE
    return folder


def test_full_card_only_fixture_and_data_only_parser(
    captured: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("saved card verifier evaluated a kernel or builder")

    for name in ["BASE", "ALL", "reduced_cards"]:
        monkeypatch.setattr(kernel, name, forbidden)
    monkeypatch.setattr(fields, "build", forbidden)
    saved = t.verify(ROOT, captured, FIXTURE)
    assert saved["normalization"]["requests"] == 12296
    assert saved["normalization"]["restored"] is True
    assert saved["valid_completed"] == dict(original=5724, reduced=5724)


@pytest.mark.parametrize(
    "damage",
    [
        "pid_float",
        "live",
        "disabled",
        "counter_bool",
        "geometry_flag",
        "geometry_bool",
        "extra_raw",
        "changed_cards",
        "fixed_restoration",
        "missing_fixed",
    ],
)
def test_rebound_corruptions_are_rejected(
    captured: Path, tmp_path: Path, damage: str
) -> None:
    folder = tmp_path / "modified"
    shutil.copytree(captured, folder)
    path = folder / "contract.json"
    saved = json.loads(path.read_text())
    if damage == "pid_float":
        saved["pid"] = float(saved["pid"])
    elif damage == "live":
        saved["normalization"].update(active=True, status="running", restored=False)
    elif damage == "disabled":
        saved["normalization"]["enabled"] = False
    elif damage == "counter_bool":
        saved["normalization"]["fallbacks"] = False
    elif damage == "geometry_flag":
        saved["geometry_check_completed"] = 1
    elif damage == "geometry_bool":
        saved["geometry_inventory"]["table_entries"] = True
    elif damage == "extra_raw":
        extra = folder / "extra.json"
        extra.write_text("{}")
        saved["raw_sha256"]["extra.json"] = digest(extra)
    elif damage == "changed_cards":
        cards = folder / "reduced-cards.jsonl"
        cards.write_bytes(
            cards.read_bytes().replace(
                b'"inputs_unchanged": true', b'"inputs_unchanged": 1', 1
            )
        )
        saved["raw_sha256"]["reduced-cards.jsonl"] = digest(cards)
    elif damage == "fixed_restoration":
        fixed = folder / "fixed/valid_lists.json"
        row = json.loads(fixed.read_text())
        row["restored"] = 1
        t.write(fixed, row)
        saved["raw_sha256"]["fixed/valid_lists.json"] = digest(fixed)
    elif damage == "missing_fixed":
        name = "fixed/valid_lists.json"
        (folder / name).unlink()
        saved["raw_sha256"].pop(name)
    t.write(path, saved)
    with pytest.raises((ArithmeticError, FileNotFoundError)):
        t.verify(ROOT, folder, FIXTURE)


def test_source_mismatch_and_existing_partial_refuse(captured: Path) -> None:
    with pytest.raises(ArithmeticError):
        t.verify(ROOT, captured, "another fixture")
    before = (captured / "contract.json").read_bytes()
    with pytest.raises(FileExistsError):
        t.collect(ROOT, captured, FIXTURE, Deadline(180))
    assert (captured / "contract.json").read_bytes() == before


def test_secondary_save_failure_preserves_primary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = t.write
    calls = 0

    def save(path: Path, value: Any) -> None:
        nonlocal calls
        calls += 1
        if calls > 1:
            raise OSError("secondary save")
        original(path, value)

    def fail(*args: Any, **kwargs: Any) -> None:
        raise LookupError("primary geometry")

    monkeypatch.setattr(t, "write", save)
    monkeypatch.setattr(kernel, "check_geometry", fail)
    with pytest.raises(LookupError, match="primary geometry"):
        t.collect(ROOT, tmp_path / "partial", FIXTURE, Deadline(180))
    assert (tmp_path / "partial/contract.json").exists()
