"""Synthetic report schema and historical measurement-source pin checks."""

from pathlib import Path

import pytest
from known_mixture_residual_map import report as module
from known_mixture_residual_map.gate import REPORT_SOURCE
from known_mixture_residual_map.report import MEASUREMENT_SOURCE, negative_mixture


def test_nested_published_classification_is_required() -> None:
    assert negative_mixture({"classification": {"classification": "negative"}})
    assert not negative_mixture({"classification": "negative"})
    assert not negative_mixture({"classification": {"classification": "positive"}})


def test_historical_measurement_source_is_explicit() -> None:
    assert MEASUREMENT_SOURCE == (
        "4eba834da858694d40ac1ce87fddb68bd47efb43f5dabcb4db6f29b223d9f57c"
    )


def test_report_requires_new_receipt_before_old_measurement_archives(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    fingerprint = "new-report-source"
    seen: list[tuple[Path, str, str]] = []

    def reject_missing_receipt(
        root: Path, path: Path, status: str, source: str
    ) -> None:
        seen.append((path, status, source))
        raise FileNotFoundError("new report receipt absent")

    monkeypatch.setattr(module, "contract", lambda root: {})
    monkeypatch.setattr(module, "clean_head", lambda root: "clean-head")
    monkeypatch.setattr(module, "source_fingerprint", lambda root: fingerprint)
    monkeypatch.setattr(module, "require_archive", reject_missing_receipt)
    with pytest.raises(FileNotFoundError, match="new report receipt absent"):
        module.report(tmp_path, tmp_path / "output")
    assert seen == [(tmp_path / REPORT_SOURCE, "source_qualified", fingerprint)]
