"""Small deterministic software fixtures; no fixture is a research strength claim."""

import copy
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from poker_ai.postflop import range_sampled as study
from poker_ai.postflop import range_sampled_report as reporting
from poker_ai.postflop.range_protocol import assess_full_metrics, check_inputs
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.solver_validation import range_sampled as native

ROOT = Path(__file__).resolve().parents[1]
REAL_PREREQUISITE = study.prerequisite


def source_fixture(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {"dirty": False, "sha256": {}, "git_commit": "software-fixture-not-research"}


def prerequisite_fixture(root: Path, config: dict[str, Any]) -> dict[str, Any]:
    if config["later_sampled"]["seeds"] != [13]:
        return REAL_PREREQUISITE(root, config)
    full = assess_full_metrics(
        [], [], [], config, check_inputs(root, config), elapsed_seconds=0
    )
    full["eligible_for_sampled_comparison"] = True
    return {
        "study_sha256": digest(root / study.FULL_STUDY),
        "audit_sha256": digest(root / study.FULL_AUDIT),
        "assessment": full,
        "fixture": "software-only prerequisite, not measured admission",
    }


@pytest.fixture(autouse=True)
def use_software_prerequisite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(study, "prerequisite", prerequisite_fixture)


@pytest.fixture(scope="module")
def tiny(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    directory = tmp_path_factory.mktemp("range-sampled-fixture")
    config = json.loads((ROOT / "configs/range-mass-protocol.json").read_text())
    config["spot_files"] = config["spot_files"][:1]
    config["spot_sha256"] = {p: config["spot_sha256"][p] for p in config["spot_files"]}
    config["later_sampled"].update(
        seeds=[13],
        node_work_checkpoints=[7000, 12000],
        profile_iterations=2,
        profile_repetitions=2,
    )
    cfg = directory / "config.json"
    cfg.write_text(json.dumps(config))
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(study, "source_provenance", source_fixture)
        patch.setattr(study, "prerequisite", prerequisite_fixture)
        result = study.run_study(ROOT, cfg, directory / "study.json")
    assert result["status"] == "completed", result["failure"]
    return directory / "study.json", result


def test_real_full_prerequisite_replays() -> None:
    config = json.loads((ROOT / "configs/range-mass-protocol.json").read_text())
    result = REAL_PREREQUISITE(ROOT, config)
    assert result["assessment"]["eligible_for_sampled_comparison"]
    assert result["maximum_own_replay_error_chips"] == 0
    assert result["maximum_native_error_chips"] <= 1e-9


def test_complete_fixture_replays_without_advancing(
    tiny: tuple[Path, dict[str, Any]],
) -> None:
    path, _ = tiny
    report, policies, error = study.replay(ROOT, path)
    assert len(policies) == 10 and error == 0
    assert report["assessment"]["own_grid_complete"]
    assert not report["assessment"]["complete"]
    assert report["fresh_global_admission"] is False
    assert report["assessment"]["independent_audit"] == "pending"
    for row in report["rows"]:
        assert (
            0
            < row["initialization_node_work"]
            <= row["previous_node_work"]
            < row["node_work_checkpoint"]
            <= row["total_node_work"]
        )
        assert (
            row["last_iteration_node_work"]
            == row["total_node_work"] - row["previous_node_work"]
        )
    with pytest.raises(FileExistsError):
        study.run_study(ROOT, path.parent / "config.json", path)


def clone(
    tiny: tuple[Path, dict[str, Any]], directory: Path
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    original, raw = tiny
    report = copy.deepcopy(raw)
    payload = json.loads(
        gzip.decompress((original.parent / raw["own_receipts_file"]).read_bytes())
    )
    return directory / "study.json", report, payload


def write_clone(
    path: Path, report: dict[str, Any], payload: dict[str, Any], *, rehash: bool = True
) -> None:
    bundle = path.parent / report["own_receipts_file"]
    bundle.write_bytes(gzip.compress(json.dumps(payload).encode(), mtime=0))
    if rehash:
        report["own_receipts_sha256"] = digest(bundle)
    report["assessment"] = study.assessment(report)
    path.write_text(json.dumps(report))


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "global",
        "partial",
        "context",
        "row_context",
        "diagnostic",
        "profile",
        "profile_seed",
        "zero_init",
        "work",
        "warm",
        "last",
        "source",
        "prerequisite",
        "value",
        "method",
        "sampling",
        "initial_flag",
        "recall",
        "nan",
    ],
)
def test_changed_receipts_rejected(
    tiny: tuple[Path, dict[str, Any]], tmp_path: Path, change: str
) -> None:
    path, report, payload = clone(tiny, tmp_path)
    row = report["rows"][-1]
    if change == "missing":
        report["rows"].pop()
    elif change == "duplicate":
        report["rows"].append(row)
    elif change == "global":
        report["fresh_global_admission"] = True
    elif change == "partial":
        report["status"] = "incomplete"
    elif change == "context":
        report["range_contexts"][row["spot_file"]] = "wrong"
    elif change == "row_context":
        row["range_context_sha256"] = "wrong"
    elif change == "diagnostic":
        report["diagnostics"][-1]["key_utf8_bytes"] += 1
    elif change == "profile":
        report["diagnostics"][-1]["profiles"].pop()
    elif change == "profile_seed":
        report["diagnostics"][-1]["profiles"][0]["seed"] += 1
    elif change == "zero_init":
        row["initialization_node_work"] = 0
    elif change == "work":
        row["recursive_node_visits"] += 1
    elif change == "warm":
        row["initialization_node_work"] += 1
    elif change == "last":
        row["last_iteration_node_work"] += 1
    elif change == "source":
        report["source"]["sha256"]["uv.lock"] = "wrong"
    elif change == "prerequisite":
        report["full_prerequisite"]["study_sha256"] = "wrong"
    elif change == "value":
        row["value_player_zero_chips"] += 1
    elif change == "method":
        row["weighting"] = "uniform"
    elif change == "sampling":
        row["sampling"] = "other"
    elif change == "initial_flag":
        row["initial_exact_expectation"] = False
    elif change == "recall":
        row["recall_violations"] = 1
    else:
        row["value_player_zero_chips"] = float("nan")
    write_clone(path, report, payload)
    with pytest.raises((ArithmeticError, ValueError)):
        study.replay(ROOT, path)


@pytest.mark.parametrize(
    "change",
    [
        "hash",
        "missing",
        "duplicate",
        "context",
        "identity",
        "active",
        "sampled",
        "policy",
        "counter",
        "accumulator",
        "visit_weight",
        "visit_hash",
        "config",
    ],
)
def test_changed_checkpoint_bundle_rejected(
    tiny: tuple[Path, dict[str, Any]], tmp_path: Path, change: str
) -> None:
    path, report, payload = clone(tiny, tmp_path)
    snapshot = payload["policies"][-1]
    if change == "missing":
        payload["policies"].pop()
    elif change == "duplicate":
        payload["policies"].append(snapshot)
    elif change == "context":
        snapshot["range_context_sha256"] = "wrong"
    elif change == "identity":
        snapshot["seed"] = True
    elif change == "active":
        snapshot["average_active"][0] = 2
    elif change == "sampled":
        snapshot["sampled"][0] = 2
    elif change == "policy":
        snapshot["policy"][0] = [1.0]
    elif change in ("counter", "accumulator", "config"):
        core = json.loads(snapshot["checkpoint_json"])
        if change == "counter":
            core["nodes_visited"] += 1
        elif change == "accumulator":
            core["rows"][0]["strategy_sum"][0] += 100
        else:
            core["config"]["range_context_sha256"] = "wrong"
        snapshot["checkpoint_json"] = json.dumps(core)
        sha = hashlib.sha256(snapshot["checkpoint_json"].encode()).hexdigest()
        report["rows"][-1]["checkpoint_sha256"] = sha
        visits = json.loads(snapshot["visits_json"])
        visits["core_sha256"] = sha
        snapshot["visits_json"] = json.dumps(visits)
        report["rows"][-1]["visits_sha256"] = hashlib.sha256(
            snapshot["visits_json"].encode()
        ).hexdigest()
    else:
        visits = json.loads(snapshot["visits_json"])
        visits["weighting"] = "uniform" if change != "visit_hash" else "linear"
        if change == "visit_hash":
            visits["core_sha256"] = "wrong"
        snapshot["visits_json"] = json.dumps(visits)
        report["rows"][-1]["visits_sha256"] = hashlib.sha256(
            snapshot["visits_json"].encode()
        ).hexdigest()
    write_clone(path, report, payload, rehash=change != "hash")
    with pytest.raises((ArithmeticError, ValueError)):
        study.replay(ROOT, path)


def test_deadline_retains_partial(
    tiny: tuple[Path, dict[str, Any]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(study, "source_provenance", source_fixture)

    def expired(*args: Any) -> None:
        raise TimeoutError("software fixture")

    monkeypatch.setattr(Deadline, "check", expired)
    report = study.run_study(
        ROOT, tiny[0].parent / "config.json", tmp_path / "partial.json"
    )
    assert report["status"] == "incomplete" and not report["rows"]
    assert report["failure"]["type"] == "TimeoutError"
    with pytest.raises(ArithmeticError):
        study.replay(ROOT, tmp_path / "partial.json")


def test_native_audit_and_offline_report(
    tiny: tuple[Path, dict[str, Any]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("pyspiel")
    path, report = tiny
    monkeypatch.setattr(native, "source_provenance", source_fixture)
    audit_path = tmp_path / "audit.json"
    result = native.audit(ROOT, path.parent / "config.json", path, audit_path)
    assert result["status"] == "passed" and len(result["comparisons"]) == 10
    for change in ("duplicate", "context", "value", "error", "input"):
        bad = copy.deepcopy(result)
        if change == "duplicate":
            bad["comparisons"].append(bad["comparisons"][-1])
        elif change == "context":
            bad["comparisons"][-1]["range_context_sha256"] = "wrong"
        elif change == "value":
            bad["comparisons"][-1]["native_value_chips"] += 1
        elif change == "error":
            bad["comparisons"][-1]["value_error_chips"] = -1
        else:
            bad["input_sha256"] = "wrong"
        with pytest.raises(ArithmeticError):
            reporting.checked_audit(path, report, bad)
    monkeypatch.setattr(reporting, "plots", lambda *a: None)
    summary = reporting.render(ROOT, path, audit_path, tmp_path / "report")
    assert summary["assessment"]["complete"]
    assert summary["fresh_global_admission"] is False
    assert summary["checkpoint_visit_pairs_replayed"] == 10


def test_plot_smoke(tiny: tuple[Path, dict[str, Any]], tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    reporting.plots(tiny[1], reporting.learning_summary(tiny[1]), tmp_path)
    assert {p.name for p in tmp_path.glob("*.png")} == {
        "learning-work.png",
        "final-seeds.png",
    }
