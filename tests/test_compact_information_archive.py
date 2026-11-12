"""Mocked full trace IO/failure tests; this is not a source-bound proof count."""

import copy
import gzip
import time
from contextlib import nullcontext
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import compact_information_inputs as inputs
from poker_ai.evaluation import compact_information_run as run
from poker_ai.evaluation import compact_sampled_inputs as old
from poker_ai.evaluation import diagnostic_receipts as receipts
from poker_ai.evaluation.compact_fixed_software import coarse_context
from poker_ai.evaluation.compact_information_software import mocked_source as source
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.compact_full_context import Context
from poker_ai.postflop.compact_information import panel as math_panel
from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.postflop.river_study import digest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, request: pytest.FixtureRequest
) -> tuple[Path, dict[str, Any]]:
    software = getattr(request, "param", "software") == "software"
    original = coarse_context()
    sources: list[inputs.Input] = []
    for case in old.cases(ROOT, "software" if software else "real"):
        c = Context(
            case["spot_file"],
            case["representation"],
            "f" * 64,
            original.scoring,
            2.0,
            {},
        )
        sources.extend(source(c, m, case["seed"]) for m in ("SS", "SF", "FS", "FF"))
    monkeypatch.setattr(
        inputs, "load", lambda *a, **k: (dict(rows=[r.row for r in sources]), sources)
    )
    monkeypatch.setattr(
        receipts, "source", lambda *a, **k: dict(fingerprint="mocked-unit-source")
    )
    monkeypatch.setattr(receipts, "check_source", lambda *a, **k: None)
    monkeypatch.setattr(
        receipts,
        "checks",
        lambda *a, **k: dict(file="mocked-unit-checks.json", sha256="a" * 64),
    )
    monkeypatch.setattr(run, "checked", lambda *a, **k: tmp_path / "mocked-checks.json")
    monkeypatch.setattr(run, "runtime", lambda: dict(mocked_unit_runtime=True))
    monkeypatch.setattr(run, "check_runtime", lambda *a, **k: None)
    # Optional fixture modules can already be loaded by pytest; the CLI uses its
    # fresh-process constructor/import blocker, tested separately.
    monkeypatch.setattr(run, "own_only", nullcontext)
    monkeypatch.setattr(run, "software_proof", lambda *a: dict(mocked_unit_proof=True))
    out = tmp_path / "own.json"
    saved = run.run(
        ROOT, out, software, tmp_path / "mocked-checks.json", time.perf_counter()
    )
    assert saved["status"] == "completed", saved["failure"]
    return out, saved


def test_complete_mocked_144_panels_288_aliases(
    archive: tuple[Path, dict[str, Any]],
) -> None:
    path, saved = archive
    assert len(saved["panels"]) == 144
    assert sum(len(r["source_aliases"]) for r in saved["panels"]) == 288
    result = run.verify(ROOT, path, saved)
    assert result["panels"] == 144 and result["response_aliases"] == 288
    assert result["maximum_error_chips"] == 0 and result["new_training"] is False


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "scope",
        "flag",
        "parent",
        "count",
        "check",
        "alias",
        "root",
        "receipt",
        "resigned_values",
        "resigned_group",
        "truncated",
    ],
)
def test_corrupted_trace_or_provenance_never_replays(
    archive: tuple[Path, dict[str, Any]], mutation: str
) -> None:
    path, original = archive
    saved = copy.deepcopy(original)
    if mutation == "missing":
        saved["panels"].pop()
    elif mutation == "duplicate":
        saved["panels"][-1] = copy.deepcopy(saved["panels"][0])
    elif mutation == "scope":
        saved["scope"] = "other"
    elif mutation == "flag":
        saved["independent_new_row_value_audit"] = True
    elif mutation == "parent":
        saved["parent_inputs"][0]["sha256"] = "e" * 64
    elif mutation == "count":
        saved["parent_inventory"]["response_aliases"] = 287
    elif mutation == "check":
        saved["checks"]["sha256"] = "d" * 64
    elif mutation == "alias":
        saved["panels"][0]["source_aliases"].pop()
    elif mutation == "root":
        saved["panels"][0]["exact_root_chips"] += 1
    elif mutation == "receipt":
        saved["panels"][0]["receipt"] = saved["panels"][1]["receipt"].copy()
    else:
        row = next(r for r in saved["panels"] if r["owned_rows"])
        packet = files.load_snapshot(path.parent / "details", row["receipt"])
        p = path.parent / "details" / row["receipt"]["file"]
        if mutation == "resigned_values":
            packet["rows"][0]["reply_continuation_values_chips"][0] += 1
        elif mutation == "resigned_group":
            packet["groups"][0]["strict_conflict"] = not packet["groups"][0][
                "strict_conflict"
            ]
        data = gzip.compress(canonical(packet), mtime=0)
        p.write_bytes(data[:15] if mutation == "truncated" else data)
        row["receipt"].update(sha256=digest(p), bytes=p.stat().st_size)
    with pytest.raises((ArithmeticError, ValueError, EOFError, OSError, KeyError)):
        run.verify(ROOT, path, saved)


def test_failed_prefix_is_retained_without_completion(
    archive: tuple[Path, dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    function = math_panel
    calls = 0

    def fail(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise TimeoutError("unit interruption after two confirmed writes")
        return function(*args, **kwargs)

    monkeypatch.setattr(run, "panel", fail)
    path = tmp_path / "second/own.json"
    result = run.run(ROOT, path, True, tmp_path / "checks", time.perf_counter())
    assert result["status"] == "incomplete" and len(result["panels"]) == 2
    assert len(list((path.parent / "details").glob("*.gz"))) == 2
    assert result["actual_admission"] is False
    with pytest.raises(ArithmeticError):
        run.replay(ROOT, path)


def test_original_tiny_parent_replay_requires_no_new_reference_or_learning() -> None:
    import importlib.util
    import platform
    from unittest.mock import patch

    import numpy as np

    if (
        platform.python_version() != "3.11.17"
        or np.__version__ != "2.4.6"
        or importlib.util.find_spec("numba") is None
    ):
        pytest.skip("sealed parent archive needs its recorded optional runtime")
    from poker_ai.solver_validation.matched_array_reference import ScalarReference

    with (
        patch(
            "poker_ai.postflop.compact_full_run.solver",
            side_effect=AssertionError("no learner"),
        ),
        patch(
            "poker_ai.postflop.batch_reduction.ReducedDispatchBatchTrainer.__init__",
            side_effect=AssertionError("no sampled learner"),
        ),
        patch.object(
            ScalarReference, "__init__", side_effect=AssertionError("no reference")
        ),
    ):
        original, sources = inputs.load(ROOT, True)
    assert len(original["rows"]) == len(sources) == 144
    assert sum(len(s.packet["responses"]) for s in sources) == 288
    assert original["new_training"] is False


def cache_mocks(monkeypatch: pytest.MonkeyPatch) -> None:
    from poker_ai.evaluation import compact_information_view as view

    monkeypatch.setattr(receipts, "historical", lambda *a, **k: None)
    monkeypatch.setattr(view, "measurement", lambda *a, **k: None)
    monkeypatch.setattr(files, "published", lambda *a, **k: "mocked-unit-publication")
    monkeypatch.setattr(
        view,
        "replay",
        lambda *a, **k: dict(panels=144, response_aliases=288, mocked_unit_replay=True),
    )
    monkeypatch.setattr(
        receipts, "bound", lambda root, p: dict(file=str(p), sha256=digest(p))
    )


def test_complete_mocked_cache_and_software_report_is_rejected(
    archive: tuple[Path, dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poker_ai.evaluation import compact_information_view as view

    path, saved = archive
    cache_mocks(monkeypatch)
    assert len(view.cached(ROOT, path)["panels"]) == 144
    result = view.report(
        ROOT, path, tmp_path / "software-report/result.json", time.perf_counter()
    )
    assert result["status"] == "incomplete" and result["actual_admission"] is False
    assert "tiny aliases" in result["failure"]["reason"]


@pytest.mark.parametrize(
    "mutation", ["flag", "missing", "detail_hash", "manifest_scalar"]
)
def test_mocked_cache_fails_closed(
    archive: tuple[Path, dict[str, Any]], mutation: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    from poker_ai.evaluation import compact_information_view as view

    path, original = archive
    saved = copy.deepcopy(original)
    cache_mocks(monkeypatch)
    if mutation == "flag":
        saved["new_training"] = True
    elif mutation == "missing":
        saved["panels"].pop()
    elif mutation == "detail_hash":
        saved["panels"][0]["receipt"]["sha256"] = "e" * 64
    else:
        saved["panels"][0]["information_gain_chips"] += 1
    files.atomic(path, saved)
    with pytest.raises(ArithmeticError):
        view.cached(ROOT, path)


@pytest.mark.parametrize("archive", ["real"], indirect=True)
def test_mocked_real_report_keeps_all_panels_and_artifacts(
    archive: tuple[Path, dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import csv

    from poker_ai.evaluation import compact_information_view as view

    path, _ = archive
    cache_mocks(monkeypatch)
    out = tmp_path / "report/result.json"
    result = view.report(ROOT, path, out, time.perf_counter())
    assert result["status"] == "completed", result["failure"]
    assert result["panels"] == 144 and result["response_aliases"] == 288
    assert len(list(csv.DictReader((out.parent / "panels.csv").open()))) == 144
    assert len(result["artifacts"]) == 3
    assert all(digest(Path(r["file"])) == r["sha256"] for r in result["artifacts"])
    assert result["independent_new_row_value_audit"] is False
    with pytest.raises(FileExistsError):
        view.report(ROOT, path, out, time.perf_counter())


@pytest.mark.parametrize("archive", ["real"], indirect=True)
def test_mocked_report_timeout_retains_written_prefix(
    archive: tuple[Path, dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poker_ai.evaluation import compact_information_view as view

    path, _ = archive
    cache_mocks(monkeypatch)
    out = tmp_path / "report/result.json"
    result = view.report(ROOT, path, out, time.perf_counter() - 901)
    assert result["status"] == "incomplete" and result["actual_admission"] is False
    assert result["failure"]["type"] == "TimeoutError"
    assert (out.parent / "panels.csv").exists() and (out.parent / "tables.md").exists()


@pytest.mark.parametrize("archive", ["real"], indirect=True)
def test_mocked_terminal_navigation_and_bad_selection(
    archive: tuple[Path, dict[str, Any]],
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    import sys

    from poker_ai.evaluation import compact_information_view as view

    path, _ = archive
    cache_mocks(monkeypatch)
    monkeypatch.setattr(
        sys, "argv", ["viewer", "--own", str(path), "--target", "0", "--interactive"]
    )
    answers = iter(["n", "p", "j", "k", "q"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))
    view.main(ROOT)
    text = capsys.readouterr().out
    assert "Restricted-best-reply prefix" in text and "Strict conflict: True" in text
    assert "finer-reply suffix value" in text
    monkeypatch.setattr(
        sys, "argv", ["viewer", "--own", str(path), "--seed", "20261399"]
    )
    with pytest.raises(ValueError):
        view.main(ROOT)
