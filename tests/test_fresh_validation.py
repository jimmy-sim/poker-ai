"""Prospective selection, immutable inputs, admission ordering and retained grids."""

import copy
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest

from poker_ai.postflop import fresh_cohort as cohort
from poker_ai.postflop import fresh_learning as learning
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree

ROOT = Path(__file__).resolve().parents[1]


def config() -> dict[str, Any]:
    result: dict[str, Any] = json.loads(
        (ROOT / "configs/fresh-validation.json").read_text()
    )
    return result


def selection_root(root: Path) -> Path:
    raw = config()
    # Test-only cards/seed, never the actual reserved cohort or any outcomes.
    raw["selection_seed"] = 17
    inputs = set(cohort.ENTRYPOINTS) | {s["template"] for s in raw["strata"]}
    inputs |= {
        str(p.relative_to(ROOT))
        for d in raw["known_spot_directories"]
        for p in (ROOT / d).glob("*.json")
    }
    inputs |= {
        raw[k]
        for k in ("development_report", "development_audit", "development_policy")
    }
    inputs |= {"uv.lock", "pyproject.toml"}
    for name in inputs:
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    path = root / "configs/fresh-validation.json"
    path.write_text(json.dumps(raw))
    return path


def test_selection_is_reproducible_legal_and_never_calls_solver(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    first, second = tmp_path / "first", tmp_path / "second"

    def no_solver(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("selection must not construct a game tree or solve")

    monkeypatch.setattr(SpotTree, "build", no_solver)
    one = cohort.prepare_cohort(first, selection_root(first))
    two = cohort.prepare_cohort(second, selection_root(second))
    assert one == two and len(one["spot_sha256"]) == 4
    for filename in one["spot_sha256"]:
        assert (first / filename).read_bytes() == (second / filename).read_bytes()
        spot = load_spot(first / filename)
        assert len(spot.joint) == 4 and sum(
            p for _, _, p in spot.joint
        ) == pytest.approx(1)
        assert spot.hero == spot.actor and len(spot.board) == 4
        assert cohort.texture_matches(list(spot.board), spot.texture)
    with pytest.raises(FileExistsError, match="replacement"):
        cohort.prepare_cohort(first, first / "configs/fresh-validation.json")


@pytest.mark.parametrize("field", ["config", "source", "fresh", "known", "development"])
def test_freeze_rejects_changed_inputs(tmp_path: Path, field: str) -> None:
    path = selection_root(tmp_path)
    freeze = cohort.prepare_cohort(tmp_path, path)
    cohort.verify_freeze(tmp_path, path)
    files = {
        "config": "configs/fresh-validation.json",
        "source": cohort.ENTRYPOINTS[0],
        "fresh": next(iter(freeze["spot_sha256"])),
        "known": next(iter(freeze["known_spot_sha256"])),
        "development": next(iter(freeze["development_sha256"])),
    }
    changed = tmp_path / files[field]
    changed.write_bytes(changed.read_bytes() + b"\n")
    with pytest.raises(ArithmeticError, match="mismatch"):
        cohort.verify_freeze(tmp_path, path)


def test_attempt_cap_does_not_retry_until_favorable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = selection_root(tmp_path)
    monkeypatch.setattr(cohort, "texture_matches", lambda *args: False)
    raw = json.loads(path.read_text())
    raw["maximum_selection_attempts_per_spot"] = 2
    path.write_text(json.dumps(raw))
    with pytest.raises(ValueError, match="attempt cap"):
        cohort.prepare_cohort(tmp_path, path)
    assert not (tmp_path / raw["freeze_file"]).exists()


@pytest.fixture
def gate_context(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], Path]:
    raw = config()
    freeze = tmp_path / "freeze.json"
    freeze.write_text("{}")
    raw["freeze_file"] = str(freeze)
    path = tmp_path / "config.json"
    path.write_text(json.dumps(raw))
    monkeypatch.setattr(
        cohort, "verify_freeze", lambda *args: (raw, {"source_sha256": {}})
    )
    monkeypatch.setattr(cohort, "require_published_freeze", lambda *args: None)
    return raw, path


def test_actual_development_evidence_admits_unchanged_procedure(
    gate_context: tuple[dict[str, Any], Path],
) -> None:
    _, path = gate_context
    receipt = cohort.development_gate(ROOT, path)
    assert receipt["status"] == "passed" and receipt["replayed_final_policies"] == 16
    assert receipt["maximum_replay_error_chips"] <= 1e-9


@pytest.mark.parametrize(
    "change",
    [
        "seed_overlap",
        "limits",
        "weighting",
        "missing_seed",
        "native_hash",
        "implementation",
    ],
)
def test_development_gate_rejects_mismatch(
    gate_context: tuple[dict[str, Any], Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    raw, path = gate_context
    if change == "seed_overlap":
        raw["training_seeds"] = [20261208]
    elif change == "limits":
        raw["sampled_median_exploitability_pot_limit"] = 0.02
    elif change == "weighting":
        raw["sampling_weighting"] = "uniform"
    elif change == "implementation":
        original = digest
        monkeypatch.setattr(
            cohort,
            "digest",
            lambda p: (
                "changed" if str(p).endswith("postflop/sampling.py") else original(p)
            ),
        )
    elif change == "missing_seed":
        report = json.loads((ROOT / raw["development_report"]).read_text())
        report["rows"].pop()
        other = tmp_path / "study.json"
        other.write_text(json.dumps(report))
        raw["development_report"] = str(other)
    else:
        native = json.loads((ROOT / raw["development_audit"]).read_text())
        native["input_sha256"] = "changed"
        other = tmp_path / "native.json"
        other.write_text(json.dumps(native))
        raw["development_audit"] = str(other)
    with pytest.raises(ArithmeticError):
        cohort.development_gate(ROOT, path)


def tiny_config() -> dict[str, Any]:
    raw = config()
    raw.update(
        training_seeds=[17],
        total_node_thresholds=[6000, 6200],
        full_tree_checkpoints=[2],
        full_tree_backend="numpy",
    )
    raw["strata"] = [{"name": "fixture"}]
    return raw


def test_gate_failure_retained_before_fresh_input_access(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(tiny_config()))
    monkeypatch.setattr(
        learning, "source_provenance", lambda *args, **kwargs: {"test": True}
    )

    def block(*args: Any) -> Any:
        raise ArithmeticError("test admission failure")

    def forbidden(*args: Any) -> Any:
        raise AssertionError("fresh input accessed before admission")

    monkeypatch.setattr(learning, "development_gate", block)
    monkeypatch.setattr(learning, "load_spot", forbidden)
    report = learning.run_validation(ROOT, path, tmp_path / "study.json")
    assert report["status"] == "gate_failed" and report["rows"] == []
    assert report["failure"]["reason"] == "test admission failure"
    assert not report["acceptance"]["passed"]
    assert json.loads((tmp_path / "study.json").read_text()) == report


@pytest.fixture
def tiny_run(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Path, dict[str, Any]]:
    raw = tiny_config()
    path = tmp_path / "config.json"
    path.write_text(json.dumps(raw))
    spot = tmp_path / "configs/fresh-spots/fixture.json"
    spot.parent.mkdir(parents=True)
    # This is the OLD known low game, never a reserved-case outcome in tests.
    spot.write_bytes((ROOT / "configs/learning-spots/dev_low_oop.json").read_bytes())
    freeze_path = tmp_path / raw["freeze_file"]
    freeze_path.write_text("{}")
    freeze = {"spot_sha256": {"configs/fresh-spots/fixture.json": digest(spot)}}
    monkeypatch.setattr(
        learning, "source_provenance", lambda *args, **kwargs: {"test": True}
    )
    monkeypatch.setattr(
        learning, "development_gate", lambda *args: {"status": "passed", "test": True}
    )
    monkeypatch.setattr(learning, "verify_freeze", lambda *args: (raw, freeze))
    output = tmp_path / "study.json"
    report = learning.run_validation(tmp_path, path, output)
    return output, report


def test_tiny_run_retains_every_budget_and_checkpoint(
    tiny_run: tuple[Path, dict[str, Any]],
) -> None:
    path, report = tiny_run
    assert report["status"] == "completed", report["failure"]
    assert report["acceptance"]["complete"] and len(report["rows"]) == 3
    _, policies = learning.checked_artifacts(path)
    assert len(policies) == 3
    for r in report["rows"]:
        if r["method"] != "external":
            continue
        assert r["total_node_work"] == r["warm_node_equivalent"] + r["recursive_visits"]
        assert 0 <= r["overshoot"] < 5998
        assert digest(path.parent / r["checkpoint_file"]) == r["checkpoint_sha256"]
    with pytest.raises(FileExistsError):
        learning.run_validation(path.parent, path.parent / "config.json", path)


def test_missing_or_duplicate_budget_cannot_pass(
    tiny_run: tuple[Path, dict[str, Any]],
) -> None:
    _, report = tiny_run
    for rows in (report["rows"][:-1], report["rows"] + [report["rows"][-1]]):
        result = learning.acceptance(rows, report["config"])
        assert not result["complete"] and not result["passed"]


def test_failed_performance_is_a_complete_result(
    tiny_run: tuple[Path, dict[str, Any]],
) -> None:
    _, report = tiny_run
    rows = copy.deepcopy(report["rows"])
    rows[-1]["exploitability_pot_fraction"] = 1.0
    result = learning.acceptance(rows, report["config"])
    assert result["complete"] and not result["passed"]


@pytest.mark.parametrize(
    "change",
    [
        {"candidate": "river_integrated"},
        {"sampled_median_exploitability_pot_limit": 0.02},
        {"training_seeds": [1, 1]},
        {"maximum_seconds_total": float("nan")},
    ],
)
def test_unfrozen_design_rejected(change: dict[str, Any]) -> None:
    raw = config()
    raw.update(change)
    with pytest.raises(ValueError):
        cohort.validate_config(raw)


@pytest.mark.parametrize("published", [True, False])
def test_manifest_must_match_committed_bytes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, published: bool
) -> None:
    path = tmp_path / "freeze.json"
    path.write_bytes(b"published")
    monkeypatch.setattr(
        subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(
            args[0], 0, b"published" if published else b"different", b""
        ),
    )
    if published:
        cohort.require_published_freeze(tmp_path, {"freeze_file": "freeze.json"})
    else:
        with pytest.raises(ArithmeticError, match="committed"):
            cohort.require_published_freeze(tmp_path, {"freeze_file": "freeze.json"})


def test_policy_artifact_tampering_rejected(
    tiny_run: tuple[Path, dict[str, Any]],
) -> None:
    path, report = tiny_run
    policy = path.parent / report["own_policies_file"]
    policy.write_bytes(policy.read_bytes() + b"changed")
    with pytest.raises(ArithmeticError, match="hash"):
        learning.checked_artifacts(path)


def test_independent_audit_on_known_fixture(
    tiny_run: tuple[Path, dict[str, Any]], monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("pyspiel")
    from poker_ai.postflop.river_report import checked_audit
    from poker_ai.solver_validation import fresh

    path, report = tiny_run
    raw = report["config"]
    monkeypatch.setattr(
        fresh,
        "verify_freeze",
        lambda *args: (raw, {"spot_sha256": report["spot_sha256"]}),
    )
    monkeypatch.setattr(
        fresh, "source_provenance", lambda *args, **kwargs: {"test": True}
    )
    output = path.with_name("native.json")
    result = fresh.audit(path.parent, path.with_name("config.json"), path, output)
    assert result["status"] == "passed" and len(result["comparisons"]) == 3
    checked_audit(path, output, report)
    result["comparisons"][0]["native_value_chips"] += 1
    output.write_text(json.dumps(result))
    with pytest.raises(ArithmeticError, match="tolerance"):
        checked_audit(path, output, report)
