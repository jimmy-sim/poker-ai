"""Software evidence refusal/retention; these fixtures admit no learning run."""

import importlib.util
import json
from pathlib import Path
from typing import Any

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "opponent_view_command", ROOT / "scripts/check_opponent_views.py"
)
assert SPEC is not None and SPEC.loader is not None
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)


def test_exact_software_contract_retains_all_scientific_caps() -> None:
    assert CLI.digest(ROOT / CLI.CONFIG) == CLI.CONFIG_SHA
    cfg = json.loads((ROOT / CLI.CONFIG).read_text())
    assert cfg["long_run_admitted"] is False
    assert cfg["future_own_seconds"] == 7200
    assert cfg["future_native_seconds"] == 900
    assert cfg["coarse_seats"] == [0, 1]


def test_existing_receipt_is_not_overwritten_before_reading_inputs(
    tmp_path: Path,
) -> None:
    path = tmp_path / "old.json"
    path.write_text("prior evidence")
    with pytest.raises(FileExistsError):
        CLI.run(tmp_path, path)
    assert path.read_text() == "prior evidence"


@pytest.mark.parametrize("failure", ["interrupted", "incomplete"])
def test_partial_failure_has_no_training_admission(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure: str
) -> None:
    cfg = json.loads((ROOT / CLI.CONFIG).read_text())
    dest = tmp_path / CLI.CONFIG
    dest.parent.mkdir(parents=True)
    dest.write_bytes((ROOT / CLI.CONFIG).read_bytes())
    for name in (cfg["model"], *cfg["spot_files"]):
        p = tmp_path / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes((ROOT / name).read_bytes())
    parent = tmp_path / cfg["historical_own"]
    parent.parent.mkdir(parents=True, exist_ok=True)
    parent.write_text(
        json.dumps(dict(source={}, source_sha256=cfg["historical_source_sha256"]))
    )
    original_digest = CLI.digest
    monkeypatch.setattr(
        CLI,
        "digest",
        lambda p: cfg["historical_own_sha256"] if p == parent else original_digest(p),
    )
    monkeypatch.setattr(
        CLI, "source_provenance", lambda *a, **k: dict(dirty=False, sha256={})
    )
    monkeypatch.setattr(CLI, "check_source", lambda *a: None)

    def stop(*a: Any) -> list[dict[str, Any]]:
        if failure == "interrupted":
            raise RuntimeError("fixture interruption")
        return []

    monkeypatch.setattr(CLI, "structural", stop)
    output = tmp_path / "software.json"
    with pytest.raises((RuntimeError, ArithmeticError)):
        CLI.run(tmp_path, output)
    saved = json.loads(output.read_text())
    assert saved["status"] == "failed_software_only"
    assert len(saved["toy"]) == 2
    assert saved["long_run_admitted"] is False
    assert saved["poker_training_performed"] is False
    assert saved["reference_constructed"] is False
    assert saved["failure"] is not None
