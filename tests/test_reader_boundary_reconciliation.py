"""Data-only checks; no reader, training or reference solver is executed."""

import copy
import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
tool = importlib.import_module("reconcile_reader_boundaries")


def inputs() -> dict[str, Any]:
    return tool.load_inputs(ROOT)[1]  # type: ignore[no-any-return]


def test_saved_evidence_without_processes(monkeypatch: pytest.MonkeyPatch) -> None:
    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("data audit must not execute a process or clock snapshot")

    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(
        importlib.import_module("card_clock_support"), "snapshot", forbidden
    )
    saved = tool.report(ROOT)
    assert saved == tool.report(ROOT)
    assert saved["boundary_count"] == 8
    assert saved["recorded_real_summaries_compared"] == 6
    assert saved["current_source_files_checked"] == 398
    assert saved["recorded_real_summaries_equal"] is True
    assert saved["cause_identified"] is False
    assert saved["mathematical_archive_replay_performed"] is False
    assert saved["poker_training_performed"] is False
    assert saved["long_run_admitted"] is False
    assert [r["label"] for r in saved["rows"]] == [
        "uncached/tiny",
        "uncached/initial",
        "uncached/final",
        "cached/tiny",
        "cached/initial",
        "cached/final",
        "standalone/control",
        "standalone/observed",
    ]
    first = saved["rows"][1]
    assert first["reaped_child_user_seconds"] == pytest.approx(21.461343)
    assert saved["rows"][-1]["reaped_child_user_seconds"] == pytest.approx(0.239208)


@pytest.mark.parametrize("field", ["pid", "platform", "rss_unit"])
def test_changed_boundary_identity(field: str) -> None:
    raw = inputs()[f"{tool.OLD}/uncached/parent-resource-reads.json"]
    row = raw["reads"][1]["observation"]
    row["after"][field] = 1 if field == "pid" else "changed"
    with pytest.raises(ArithmeticError):
        tool.boundary(row, row["before"]["pid"], "fixture")


def test_unrelated_parent_is_rejected() -> None:
    raw = inputs()[f"{tool.OLD}/uncached/parent-resource-reads.json"]
    row = raw["reads"][1]["observation"]
    with pytest.raises(ArithmeticError, match="parent"):
        tool.boundary(row, row["before"]["pid"] + 1, "fixture")


def test_changed_saved_subtraction_is_rejected() -> None:
    raw = inputs()[f"{tool.OLD}/uncached/parent-resource-reads.json"]
    row = raw["reads"][1]["observation"]
    row["interval"]["resources"]["reaped_child_usage"]["delta"]["ru_utime"] = 0
    with pytest.raises(ArithmeticError, match="interval"):
        tool.boundary(row, row["before"]["pid"], "fixture")


@pytest.mark.parametrize("kind", ["missing", "scope", "status", "before", "order"])
def test_incomplete_historical_read_is_rejected(kind: str) -> None:
    data = inputs()
    rows = data[f"{tool.OLD}/uncached/parent-resource-reads.json"]["reads"]
    if kind == "missing":
        rows.pop()
    elif kind == "before":
        rows[1]["before"] = copy.deepcopy(rows[1]["before"])
        rows[1]["before"]["pid"] += 1
    elif kind == "order":
        rows.reverse()
    else:
        rows[1][kind] = "changed"
    with pytest.raises(ArithmeticError):
        tool.reconcile(ROOT, data)


@pytest.mark.parametrize("kind", ["mode", "status", "scope", "pid", "before"])
def test_incomplete_standalone_read_is_rejected(kind: str) -> None:
    data = inputs()
    row = data[f"{tool.NEW}/observed/child.json"]
    if kind == "scope":
        row["witness"]["reader_scope"] = tool.TINY
    elif kind == "pid":
        row["pid"] += 1
    elif kind == "before":
        row["target_before"] = copy.deepcopy(row["target_before"])
        row["target_before"]["pid"] += 1
    else:
        row[kind] = "changed"
    with pytest.raises(ArithmeticError):
        tool.reconcile(ROOT, data)


@pytest.mark.parametrize("kind", ["old", "new", "own", "computed"])
def test_changed_recorded_identities_are_rejected(kind: str) -> None:
    data = inputs()
    if kind == "old":
        data[f"{tool.OLD}/cached/child.json"]["source"]["sha256"].popitem()
    elif kind == "new":
        data[f"{tool.NEW}/observed/child.json"]["source"]["sha256"].popitem()
    elif kind == "own":
        data[f"{tool.NEW}/observed/child.json"]["witness"]["own_sha256"] = "0" * 64
    else:
        data[f"{tool.OLD}/uncached/child.json"]["identity"]["computed_replays"][1][
            "computed"
        ]["maximum_error"] = 1.0
    with pytest.raises(ArithmeticError):
        tool.reconcile(ROOT, data)


def test_changed_current_source_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    original = tool.digest

    def changed(path: Path) -> str:
        return "0" * 64 if path.name == "engine.py" else str(original(path))

    monkeypatch.setattr(tool, "digest", changed)
    with pytest.raises(ArithmeticError, match="source bytes"):
        tool.reconcile(ROOT, inputs())


def contract_root(tmp_path: Path) -> Path:
    (tmp_path / "configs").mkdir()
    (tmp_path / tool.CONFIG).write_bytes((ROOT / tool.CONFIG).read_bytes())
    return tmp_path


@pytest.mark.parametrize("kind", ["format", "scope", "inputs"])
def test_changed_contract_rejected(tmp_path: Path, kind: str) -> None:
    root = contract_root(tmp_path)
    config = json.loads((root / tool.CONFIG).read_text())
    config[kind] = False if kind == "format" else "changed" if kind == "scope" else {}
    (root / tool.CONFIG).write_text(json.dumps(config))
    with pytest.raises(ArithmeticError, match="contract"):
        tool.load_inputs(root)


def test_changed_pinned_input_rejected(tmp_path: Path) -> None:
    root = contract_root(tmp_path)
    name = next(iter(json.loads((root / tool.CONFIG).read_text())["inputs"]))
    path = root / name
    path.parent.mkdir(parents=True)
    path.write_text("{}")
    with pytest.raises(ArithmeticError, match="input changed"):
        tool.load_inputs(root)


@pytest.mark.parametrize("name", ["../outside", "/tmp/outside"])
def test_paths_cannot_escape(tmp_path: Path, name: str) -> None:
    with pytest.raises(ArithmeticError, match="within"):
        tool.local_path(tmp_path, name)


def test_cli_never_overwrites(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    output = tmp_path / "existing.json"
    output.write_text("retain")
    monkeypatch.setattr(
        sys, "argv", ["reconcile_reader_boundaries.py", "--output", str(output)]
    )
    with pytest.raises(FileExistsError):
        tool.main()
    assert output.read_text() == "retain"
