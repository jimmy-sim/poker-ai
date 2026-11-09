"""Actual complete tiny-game IO and failure paths; explicitly not poker results."""

import base64
import copy
import gzip
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import reduced_study_inputs as inputs
from poker_ai.evaluation import reduced_study_run as own
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs
from poker_ai.evaluation.frozen_batch_replay import raw_grid, replay_archives
from poker_ai.evaluation.frozen_batch_report import write_report
from poker_ai.evaluation.frozen_batch_validation import grid
from poker_ai.evaluation.reduced_study_fixture import SCOPE, roundtrip
from poker_ai.postflop.cached_nodes import CachedNodeTrainer
from poker_ai.postflop.learning_artifacts import (
    FORMAT_ARCHIVE,
    canonical,
    read_archive,
    sha,
)
from poker_ai.postflop.river_study import Deadline, digest

pytestmark = pytest.mark.slow
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def complete(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[dict[str, Any], HistoryInputs, Path]:
    config = inputs.config_inputs(ROOT)
    return roundtrip(
        tmp_path_factory.mktemp("frozen-batch-EXPLICIT-TOY") / "toy",
        config,
        "a" * 64,
        Deadline(120),
    )


def test_complete_three_worker_grid_replays_without_learner_or_reference(
    complete: tuple[dict[str, Any], HistoryInputs, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved, data, path = complete

    def forbidden(*a: Any, **kw: Any) -> Any:
        raise AssertionError("offline replay constructed a learner/reference")

    monkeypatch.setattr(CachedNodeTrainer, "step", forbidden)
    monkeypatch.setattr(inputs, "trainer", forbidden)
    proof = replay_archives(path, saved, data, Deadline(30))
    assert saved["scope"] == SCOPE
    assert proof["profiles"] == 480
    assert proof["mass_reconstructions"] == 432
    assert proof["current_observations"] == 216
    assert proof["maximum_error_chips"] == proof["maximum_error_unitless"] == 0
    assert len(saved["prefix_checks"]) == 144
    assert proof["new_postflop_training_performed"] is False


@pytest.mark.parametrize(
    "damage",
    ["missing", "duplicate", "source", "work", "policy", "origin", "order", "unsafe"],
)
def test_complete_grid_rejects_altered_profiles(
    complete: tuple[dict[str, Any], HistoryInputs, Path],
    damage: str,
) -> None:
    saved, data, _ = complete
    rows = copy.deepcopy(saved["rows"])
    if damage == "missing":
        rows.pop()
    elif damage == "duplicate":
        rows[-1] = copy.deepcopy(rows[0])
    elif damage == "source":
        rows[0]["source_sha256"] = "b" * 64
    elif damage == "work":
        rows[0]["initialization_visits"] = 0
    elif damage == "policy":
        rows[0]["receipt"]["policy_sha256"] = "b" * 64
    elif damage == "origin":
        rows[0]["origin"] = "stronger_agent"
    elif damage == "order":
        rows.reverse()
    elif damage == "unsafe":
        rows[0]["file"] = "../outside.json.gz"
    with pytest.raises(ArithmeticError):
        grid(rows, data, saved["config"], saved["source_sha256"])


@pytest.mark.parametrize(
    "damage",
    [
        "mass_missing",
        "mass_duplicate",
        "current_missing",
        "current_order",
        "guard",
        "binding",
    ],
)
def test_raw_observation_grid_is_required(
    complete: tuple[dict[str, Any], HistoryInputs, Path],
    damage: str,
) -> None:
    saved = copy.deepcopy(complete[0])
    if damage == "mass_missing":
        saved["masses"].pop()
    elif damage == "mass_duplicate":
        saved["masses"][-1] = copy.deepcopy(saved["masses"][0])
    elif damage == "current_missing":
        saved["currents"].pop()
    elif damage == "current_order":
        saved["currents"].reverse()
    elif damage == "guard":
        saved["currents"][0]["guard_sha256"] = "b" * 64
    elif damage == "binding":
        saved["masses"][0]["case"]["seed"] = 17
    with pytest.raises((ArithmeticError, KeyError)):
        raw_grid(saved)


def rewrite_archive(
    path: Path,
    saved: dict[str, Any],
    output: Path,
    key: str,
    rows_key: str,
    field: str,
    value: Any,
) -> dict[str, Any]:
    """Rehash bytes AND metadata so the scorer/reconstructor must catch corruption."""
    changed = copy.deepcopy(saved)
    target = changed[rows_key][0]
    blobs = []
    for row, blob in read_archive(
        path.with_name(saved[key + "_file"]), saved[key + "_sha256"], saved[rows_key]
    ):
        if row["id"] == target["id"]:
            envelope = json.loads(gzip.decompress(blob))
            if field == "mass":
                envelope["mass"][0][0] += 1
                from poker_ai.evaluation.averaging_history_artifacts import (
                    array_sha,
                    unpack_mass,
                )

                tree = (
                    __import__(
                        "poker_ai.evaluation.averaging_history_software",
                        fromlist=["toy_context"],
                    )
                    .toy_context()
                    .partition
                )
                target["receipt"]["mass_sha256"] = array_sha(
                    unpack_mass(tree, envelope["mass"])
                )
            else:
                target[field] = value
                envelope["metadata"][field] = value
            target["metadata_sha256"] = sha(envelope["metadata"])
            blob = gzip.compress(canonical(envelope), mtime=0)
            target["receipt"]["sha256"] = __import__("hashlib").sha256(blob).hexdigest()
            target["receipt"]["bytes"] = len(blob)
        blobs.append((row["id"], blob))
    raw = canonical(dict(format=FORMAT_ARCHIVE, snapshots=len(blobs))) + b"\n"
    raw += b"".join(
        canonical(dict(id=i, blob=base64.b64encode(b).decode())) + b"\n"
        for i, b in blobs
    )
    output.write_bytes(gzip.compress(raw, mtime=0))
    changed[key + "_file"] = output.name
    changed[key + "_sha256"] = digest(output)
    # All unchanged archives must be next to this test copy of own.json.
    for other in ("details", "mass_details", "current_details"):
        if other != key:
            (output.parent / saved[other + "_file"]).write_bytes(
                path.with_name(saved[other + "_file"]).read_bytes()
            )
    return changed


@pytest.mark.parametrize("kind", ["metric", "coverage", "mass"])
def test_rehashed_numerical_corruption_is_rejected(
    complete: tuple[dict[str, Any], HistoryInputs, Path],
    tmp_path: Path,
    kind: str,
) -> None:
    saved, data, path = complete
    if kind == "mass":
        changed = rewrite_archive(
            path,
            saved,
            tmp_path / "altered-mass.jsonl.gz",
            "mass_details",
            "masses",
            "mass",
            None,
        )
    else:
        field = "metrics" if kind == "metric" else "coverage"
        value = copy.deepcopy(saved["rows"][0][field])
        if kind == "metric":
            value["exact_exploitability_chips"] += 0.1
        else:
            value["post_warm"]["all"]["positive_rows"] -= 1
        changed = rewrite_archive(
            path,
            saved,
            tmp_path / "altered-profile.jsonl.gz",
            "details",
            "rows",
            field,
            value,
        )
    with pytest.raises(ArithmeticError):
        replay_archives(tmp_path / "own.json", changed, data, Deadline(30))


def test_baseline_prefix_barrier_stops_before_larger_batches_and_retains_failure(
    complete: tuple[dict[str, Any], HistoryInputs, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    saved, data, _ = complete
    config = saved["config"]
    monkeypatch.setattr(inputs, "config_inputs", lambda root: config)
    monkeypatch.setattr(inputs, "protocol", lambda root: {"scope": SCOPE})
    monkeypatch.setattr(
        inputs,
        "binding",
        lambda root: (
            {"dirty": False, "sha256": {"SOFTWARE_ONLY": "a" * 64}},
            "a" * 64,
        ),
    )
    monkeypatch.setattr(inputs, "prerequisites", lambda root: data)
    monkeypatch.setattr(own, "runtime_environment", lambda: config["prefix_runtime"])
    monkeypatch.setattr(
        own,
        "require_admission",
        lambda root, **kw: {"scope": SCOPE, "source_sha256": "a" * 64},
    )
    (tmp_path / "configs").mkdir()
    (tmp_path / "configs/training-isolation.json").write_text(
        json.dumps(dict(future_comparison={}))
    )
    calls = []

    def fake_batch(
        size: int,
        workers: int,
        job: Any,
        payload: Any,
        deadline: Any,
        record: dict[str, Any],
    ) -> None:
        calls.append(payload["selected"])
        record.update(copy.deepcopy(saved["batches"][0]))
        event = next(
            e for e in record["workers"][0]["messages"] if e.get("phase") == "prefix"
        )
        event["check"]["state_sha256"] = "b" * 64

    monkeypatch.setattr(own, "run_batch", fake_batch)
    output = tmp_path / "attempt/own.json"
    with pytest.raises(ArithmeticError, match="prefix barrier"):
        own.run(tmp_path, output)
    assert calls == [list(range(24))]
    partial = json.loads(output.read_text())
    assert partial["status"] == "incomplete"
    assert len(partial["batches"]) == 1
    assert len(partial["rows"]) == 144
    with pytest.raises(FileExistsError):
        own.run(tmp_path, output)


def test_complete_report_reproduces_every_numeric_file(
    complete: tuple[dict[str, Any], HistoryInputs, Path],
    tmp_path: Path,
) -> None:
    saved, _, path = complete
    a = write_report(path.parent, saved, tmp_path / "first", plots=False)
    b = write_report(path.parent, saved, tmp_path / "second", plots=False)
    assert a["numerical_sha256"] == b["numerical_sha256"]
    assert (
        a["profiles"] == 480 and a["mean_rows"] == 192 and a["paired_seed_rows"] == 288
    )
    assert a["figures"] == []
    assert "no selected" in a["scope"]


def test_complete_toy_figures_are_rendered_and_labeled_as_software(
    complete: tuple[dict[str, Any], HistoryInputs, Path],
    tmp_path: Path,
) -> None:
    pytest.importorskip("matplotlib")
    saved, _, path = complete
    report = write_report(path.parent, saved, tmp_path / "plots")
    assert len(report["figures"]) == 4
    assert all(
        (tmp_path / "plots" / f).stat().st_size > 1000 for f in report["figures"]
    )


def test_complete_explicit_backend_runner_and_offline_reader(
    complete: tuple[dict[str, Any], HistoryInputs, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("matplotlib")
    from unittest.mock import patch

    from poker_ai.evaluation import reduced_study_training
    from poker_ai.evaluation.reduced_study_fixture import job
    from poker_ai.postflop.controlled_training import ControlledTrainer
    from poker_ai.solver_validation.reference import Reference

    saved, data, path = complete
    root = path.parent
    config = saved["config"]
    marker = root / "EXPLICIT_SOFTWARE_SOURCE.py"
    marker.write_text("# explicit fixture, not observed source CI\n")
    source = dict(
        dirty=False, git_commit="d" * 40, sha256={marker.name: digest(marker)}
    )
    h = sha(source["sha256"])
    monkeypatch.setattr(inputs, "config_inputs", lambda root: config)
    monkeypatch.setattr(inputs, "protocol", lambda root: {"scope": SCOPE})
    monkeypatch.setattr(inputs, "source", lambda root: copy.deepcopy(source))
    monkeypatch.setattr(inputs, "binding", lambda root: (copy.deepcopy(source), h))
    monkeypatch.setattr(inputs, "prerequisites", lambda root: data)
    monkeypatch.setattr(own, "runtime_environment", lambda: config["prefix_runtime"])
    admission = dict(scope=SCOPE, source_sha256=h)
    monkeypatch.setattr(own, "require_admission", lambda root, **kw: admission)
    monkeypatch.setattr(reduced_study_training, "own_job", job)
    (root / "configs").mkdir(exist_ok=True)
    (root / "configs/training-isolation.json").write_text(
        json.dumps(dict(future_comparison={}))
    )
    output = root / "actual-runner/own.json"
    result = own.run(root, output)
    assert result["status"] == "completed_own_native_pending"
    assert (
        len(result["rows"]) == 480
        and len(result["masses"]) == 432
        and len(result["currents"]) == 216
    )
    with (
        patch.object(
            ControlledTrainer,
            "__init__",
            side_effect=AssertionError("reader training forbidden"),
        ),
        patch.object(
            Reference, "__init__", side_effect=AssertionError("reader native forbidden")
        ),
    ):
        replayed, _, proof = own.replay(root, output, Deadline(60))
    assert replayed == result and proof["maximum_error_chips"] == 0
