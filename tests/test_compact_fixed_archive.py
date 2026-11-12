"""Mocked tiny sources exercise complete own IO; not source-bound proof/admission."""

import copy
import gzip
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest

from poker_ai.evaluation import compact_fixed_inputs as inputs
from poker_ai.evaluation import compact_fixed_run as runner
from poker_ai.evaluation import compact_sampled_inputs as old_inputs
from poker_ai.evaluation.compact_fixed_software import coarse_context
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
from poker_ai.postflop.compact_fixed import detail
from poker_ai.postflop.compact_full_context import Context
from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.postflop.river_study import digest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def archive(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, Any]]:
    fixture = coarse_context()
    originals = []
    for case in old_inputs.cases(ROOT, "software"):
        c = Context(
            case["spot_file"],
            case["representation"],
            "f" * 64,
            fixture.scoring,
            2.0,
            {},
        )
        s = np.array([[0.5, 0.5]])
        f = np.array([[0.0, 1.0]])
        sm = dict(
            value_player_zero_chips=1.25,
            exploitability_chips=0.625,
            best_response_zero_chips=2.5,
            best_response_one_chips=-1.25,
        )
        fm = dict(
            value_player_zero_chips=1.5,
            exploitability_chips=0.5,
            best_response_zero_chips=2.5,
            best_response_one_chips=-1.5,
        )
        originals.append(inputs.Pair(c, case["seed"], s, f, dict(fixture=True), sm, fm))
    monkeypatch.setattr(inputs, "pairs", lambda *a, **k: originals)
    monkeypatch.setattr(
        inputs, "replay_sources", lambda *a, **k: dict(mocked_tiny_parents=True)
    )
    monkeypatch.setattr(inputs, "checks", lambda *a, **k: dict(mocked_unit_checks=True))
    monkeypatch.setattr(inputs, "source", lambda *a, **k: dict(fingerprint="f" * 64))
    monkeypatch.setattr(inputs, "check_source", lambda *a, **k: None)
    monkeypatch.setattr(runner, "runtime", lambda: dict(mocked_unit_runtime=True))
    monkeypatch.setattr(runner, "check_runtime", lambda *a, **k: None)
    # Test harness imports optional modules; the actual fresh CLI keeps its guard.
    monkeypatch.setattr(runner, "old_own_guard", lambda: None)
    output = tmp_path / "own.json"
    with patch.object(
        ReducedDispatchBatchTrainer,
        "__init__",
        side_effect=AssertionError("no learner"),
    ):
        saved = runner.run(
            ROOT, output, True, tmp_path / "mocked-checks.json", time.perf_counter()
        )
    assert saved["status"] == "completed", saved["failure"]
    return output, saved


def test_complete_mocked_144_details_and_288_targets(
    archive: tuple[Path, dict[str, Any]],
) -> None:
    path, saved = archive
    assert len(saved["rows"]) == 144 and len(saved["fixed_opponent_conditions"]) == 144
    assert sum(len(r["responses"]) for r in saved["rows"]) == 288
    assert saved["new_training"] is False and saved["native_constructed"] is False
    result = runner.replay(ROOT, path)
    assert result["logical_profiles"] == 144 and result["target_conditions"] == 288
    assert result["maximum_identity_error_chips"] == 0


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "origin",
        "receipt",
        "metric",
        "identity",
        "flag",
        "scope",
        "resigned_policy",
        "truncated",
    ],
)
def test_archive_corruption_never_replays(
    archive: tuple[Path, dict[str, Any]], mutation: str
) -> None:
    path, original = archive
    saved = copy.deepcopy(original)
    if mutation == "missing":
        saved["rows"].pop()
    elif mutation == "duplicate":
        saved["rows"][-1] = copy.deepcopy(saved["rows"][0])
    elif mutation == "origin":
        saved["rows"][0]["origins"]["fixture"] = False
    elif mutation == "receipt":
        saved["rows"][0]["receipt"] = copy.deepcopy(saved["rows"][1]["receipt"])
    elif mutation == "metric":
        saved["rows"][0]["metrics"]["exact_exploitability_chips"] += 1
    elif mutation == "identity":
        saved["fixed_opponent_conditions"][0]["own_S_to_F_gain_chips"] += 1
    elif mutation == "flag":
        saved["new_training"] = True
    elif mutation == "scope":
        saved["scope"] = "unknown"
    else:
        row = saved["rows"][0]
        p = path.parent / "details" / row["receipt"]["file"]
        raw = files.load_snapshot(path.parent / "details", row["receipt"])
        raw["policy"][0] = [0.25, 0.75]
        data = gzip.compress(canonical(raw), mtime=0)
        p.write_bytes(data[:20] if mutation == "truncated" else data)
        row["receipt"].update(sha256=digest(p), bytes=p.stat().st_size)
    files.atomic(path, saved)
    with pytest.raises((ArithmeticError, ValueError, EOFError, OSError)):
        runner.replay(ROOT, path)


def test_failed_prefix_is_retained_and_never_complete(
    archive: tuple[Path, dict[str, Any]],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    old = detail
    calls = 0

    def fail(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 3:
            raise TimeoutError("unit interruption after two confirmed details")
        return old(*args, **kwargs)

    monkeypatch.setattr(runner, "detail", fail)
    out = tmp_path / "second" / "own.json"
    saved = runner.run(ROOT, out, True, tmp_path / "mocked.json", time.perf_counter())
    assert saved["status"] == "incomplete" and len(saved["rows"]) == 2
    assert len(list((out.parent / "details").glob("*.json.gz"))) == 2
    assert saved["actual_admission"] is False
    with pytest.raises(ArithmeticError):
        runner.replay(ROOT, out)


def native_receipt(own: dict[str, Any]) -> dict[str, Any]:
    reference = inputs.config(ROOT)["native_reference"]
    rows = []
    for row in own["rows"]:
        roots = [
            dict(
                target=t,
                exact_root_chips=r["exact_reply_value_chips"],
                restricted_root_chips=r["restricted_reply_value_chips"],
                achieved_exact_chips=r["exact_reply_value_chips"],
                achieved_restricted_chips=r["restricted_reply_value_chips"],
                achieved_river_before_chips=r["river_before_value_chips"],
            )
            for t, r in enumerate(row["responses"])
        ]
        rows.append(
            dict(
                **{k: row[k] for k in inputs.FIELDS},
                detail_sha256=row["receipt"]["sha256"],
                native_metrics=row["metrics"].copy(),
                responses=roots,
                maximum_error_chips=0.0,
            )
        )
    return dict(
        format=runner.NATIVE,
        status="completed",
        failure=None,
        own_sha256="a" * 64,
        scope=own["scope"],
        source=own["source"],
        reference=reference,
        installed_license=dict(
            sha256=reference["license_sha256"],
            previously_read_record="docs/solver_validation.md",
        ),
        reference_output_used_in_training=False,
        new_training=False,
        actual_admission=False,
        fresh_global_admission=False,
        comparisons=rows,
    )


def test_mocked_native_self_check_zero(archive: tuple[Path, dict[str, Any]]) -> None:
    _, own = archive
    n = native_receipt(own)
    runner.validate_native(own, n, "a" * 64, inputs.config(ROOT)["native_reference"])


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "source",
        "input",
        "scope",
        "license",
        "training",
        "detail",
        "fake_error",
        "root",
    ],
)
def test_native_receipt_failure_cases(
    archive: tuple[Path, dict[str, Any]], mutation: str
) -> None:
    _, own = archive
    n = native_receipt(own)
    if mutation == "missing":
        n["comparisons"].pop()
    elif mutation == "duplicate":
        n["comparisons"][-1] = copy.deepcopy(n["comparisons"][0])
    elif mutation == "source":
        n["source"] = dict(fingerprint="e" * 64)
    elif mutation == "input":
        n["own_sha256"] = "b" * 64
    elif mutation == "scope":
        n["scope"] = "real"
    elif mutation == "license":
        n["installed_license"]["sha256"] = "b" * 64
    elif mutation == "training":
        n["reference_output_used_in_training"] = True
    elif mutation == "detail":
        n["comparisons"][0]["detail_sha256"] = "b" * 64
    elif mutation == "fake_error":
        n["comparisons"][0]["maximum_error_chips"] = 0.1
    else:
        n["comparisons"][0]["responses"][0]["exact_root_chips"] += 1
    with pytest.raises(ArithmeticError):
        runner.validate_native(
            own, n, "a" * 64, inputs.config(ROOT)["native_reference"]
        )


def test_published_tiny_source_adapter_with_constructors_blocked() -> None:
    """Original archive replay only; never new real or crossed diagnostic outcomes."""
    import importlib.util
    import platform

    if (
        platform.python_version() != "3.11.17"
        or np.__version__ != "2.4.6"
        or importlib.util.find_spec("numba") is None
    ):
        pytest.skip(
            "published source replay requires its recorded optional3.11/NumPy runtime"
        )
    from poker_ai.solver_validation.matched_array_reference import ScalarReference

    with (
        patch.object(
            ReducedDispatchBatchTrainer,
            "__init__",
            side_effect=AssertionError("no sampled learner"),
        ),
        patch(
            "poker_ai.postflop.compact_full_run.solver",
            side_effect=AssertionError("no full learner"),
        ),
        patch.object(
            ScalarReference,
            "__init__",
            side_effect=AssertionError("no reference construction"),
        ),
    ):
        result = inputs.replay_sources(ROOT, True)
        pairs = inputs.pairs(ROOT, True)
    assert result["sampled_readouts"] == 324 and result["full_profiles"] == 72
    assert len(pairs) == 36 and result["new_training"] is False
    assert all(
        not pair.sampled.flags.writeable and not pair.full.flags.writeable
        for pair in pairs
    )
