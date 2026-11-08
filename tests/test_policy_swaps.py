"""Frozen-policy math/receipts with labeled software fixtures, not research results."""

import copy
import gzip
import json
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop import policy_swap_report as reporting
from poker_ai.postflop import policy_swaps as study
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.range_protocol import CONTROLS, build_representation_control
from poker_ai.postflop.reply_diagnosis import analyse
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.solver_validation import policy_swaps as native

ROOT = Path(__file__).resolve().parents[1]
REAL_LOAD = study.load_previous


def source_fixture(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {"dirty": False, "sha256": {}, "git_commit": "software-fixture-not-research"}


@lru_cache(maxsize=1)
def fixture_inputs() -> tuple[
    dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]
]:
    path = "configs/learning-spots/dev_low_oop.json"
    source = SpotTree.build(load_spot(ROOT / path))
    exact = MatrixTree.build(source)
    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    records, cases = [], []
    for name in CONTROLS:
        abstract = build_representation_control(source, name, model)
        for training, seed in (("full", None), ("sampled", 13)):
            weights = abstract.legal.copy()
            if seed is not None:
                weights[:, 0] *= 3
            policy = exact.dense_exact(
                abstract.exact_policy(abstract.normalize(weights))
            )
            case, _ = analyse(
                exact, abstract, policy, top=1, examples=2, tolerance=1e-9
            )
            key = {
                "spot_file": path,
                "representation": name,
                "training": training,
                "seed": seed,
                "range_context_sha256": "software-context"
                if name == "texture_range_q8_b8"
                else None,
            }
            records.append(
                {
                    **key,
                    "policy": exact.exact_policy(policy),
                    "exploitability_chips": case["exact_exploitability_chips"],
                }
            )
            cases.append({**key, **case})
    return {"config": {"model": "results/card-models/potential-8.json"}}, records, cases


def load_fixture(
    root: Path, config: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    if config["seeds"] == [13]:
        return fixture_inputs()
    return REAL_LOAD(root, config)


@pytest.fixture(autouse=True)
def fake_inputs(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(study, "load_previous", load_fixture)


@pytest.fixture(scope="module")
def tiny(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    directory = tmp_path_factory.mktemp("policy-swap-software")
    config = json.loads((ROOT / "configs/range-mass-policy-swaps.json").read_text())
    config.update(spot_files=config["spot_files"][:1], seeds=[13])
    cfg = directory / "config.json"
    cfg.write_text(json.dumps(config))
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(study, "source_provenance", source_fixture)
        patch.setattr(study, "load_previous", load_fixture)
        report = study.run(ROOT, cfg, directory / "study.json")
    assert report["status"] == "completed"
    return directory / "study.json", report


def test_real_prior_40_profiles_and_native_binding() -> None:
    config = json.loads((ROOT / "configs/range-mass-policy-swaps.json").read_text())
    _, records, cases = REAL_LOAD(ROOT, config)
    assert len(records) == len(cases) == 40


def test_signed_order_averaged_effects() -> None:
    r = study.effects({"FF": 1.0, "SF": 4.0, "FS": 2.0, "SS": 8.0})
    assert r == {
        "gap_change_chips": 7.0,
        "turn_effect_chips": 4.5,
        "river_effect_chips": 2.5,
        "interaction_chips": 3.0,
    }
    r = study.effects({"FF": 4.0, "SF": 2.0, "FS": 10.0, "SS": 8.0})
    assert r["turn_effect_chips"] == -2 and r["river_effect_chips"] == 6


def test_swaps_preserve_street_and_partition_and_fixed_opponent_roots() -> None:
    original, records, _ = fixture_inputs()
    source = SpotTree.build(load_spot(ROOT / records[0]["spot_file"]))
    exact = MatrixTree.build(source)
    model = CardAbstraction.load(ROOT / original["config"]["model"])
    abstract = build_representation_control(source, "texture_range_q8_b8", model)
    selected = [r for r in records if r["representation"] == "texture_range_q8_b8"]
    a, b = (
        exact.dense_exact(tuple(tuple(row) for row in r["policy"])) for r in selected
    )
    turn = study.street_mask(exact, abstract)
    sf = study.hybrid_policy(exact, abstract, a, b, "SF")
    np.testing.assert_array_equal(sf[turn], b[turn])
    np.testing.assert_array_equal(sf[~turn], a[~turn])
    fs = study.hybrid_policy(exact, abstract, a, b, "FS")
    np.testing.assert_array_equal(fs[turn], a[turn])
    np.testing.assert_array_equal(fs[~turn], b[~turn])
    for target in (0, 1):
        base, _ = study.response_roots(exact, abstract, a, 1e-9)
        changed = (
            study.seat_policy(exact, b, a)
            if target == 0
            else study.seat_policy(exact, a, b)
        )
        other, _ = study.response_roots(exact, abstract, changed, 1e-9)
        for field in (
            "exact_reply_value_chips",
            "restricted_reply_value_chips",
            "extra_information_chips",
        ):
            assert base[target][field] == pytest.approx(other[target][field], abs=1e-9)
        assert other[target]["within_partition_gain_chips"] - base[target][
            "within_partition_gain_chips"
        ] == pytest.approx(
            base[target]["baseline_value_chips"]
            - other[target]["baseline_value_chips"],
            abs=1e-9,
        )
    with pytest.raises(ValueError):
        study.hybrid_policy(exact, abstract, a, b, "bad")


def test_complete_grids_diagonals_and_balance(
    tiny: tuple[Path, dict[str, Any]],
) -> None:
    report, details, error = study.replay(ROOT, tiny[0])
    assert error == 0 and len(details) == 20 and len(report["crossplay"]) == 20
    assert len(report["cross_targets"]) == 40 and len(report["effects"]) == 10
    lookup = {tuple(r[k] for k in study.CROSS): r for r in report["crossplay"]}
    for key, row in lookup.items():
        assert (
            row["seat_balanced_first_chips"]
            == -lookup[(*key[:2], key[3], key[2])]["seat_balanced_first_chips"]
        )
        if key[2] == key[3]:
            assert row["seat_balanced_first_chips"] == 0
    assert (
        report["training_performed"] is False
        and report["fresh_global_admission"] is False
    )
    with pytest.raises(FileExistsError):
        study.run(ROOT, tiny[0].parent / "config.json", tiny[0])


@pytest.mark.parametrize(
    "change",
    [
        "missing_cross",
        "duplicate_cross",
        "missing_hybrid",
        "duplicate_hybrid",
        "missing_target",
        "missing_effect",
        "context",
        "value",
        "balanced",
        "root",
        "effect",
        "seed",
        "training",
        "global",
        "source",
        "nan",
    ],
)
def test_changed_raw_receipts_rejected(
    tiny: tuple[Path, dict[str, Any]], tmp_path: Path, change: str
) -> None:
    original, raw = tiny
    report = copy.deepcopy(raw)
    (tmp_path / raw["profiles_file"]).write_bytes(
        (original.parent / raw["profiles_file"]).read_bytes()
    )
    if change == "missing_cross":
        report["crossplay"].pop()
    elif change == "duplicate_cross":
        report["crossplay"].append(report["crossplay"][-1])
    elif change == "missing_hybrid":
        report["hybrids"].pop()
    elif change == "duplicate_hybrid":
        report["hybrids"].append(report["hybrids"][-1])
    elif change == "missing_target":
        report["cross_targets"].pop()
    elif change == "missing_effect":
        report["effects"].pop()
    elif change == "context":
        report["hybrids"][0]["range_context_sha256"] = "wrong"
    elif change == "value":
        report["crossplay"][0]["value_player_zero_chips"] += 1
    elif change == "balanced":
        report["crossplay"][0]["seat_balanced_first_chips"] += 1
    elif change == "root":
        report["hybrids"][0]["responses"][0]["exact_reply_value_chips"] += 1
    elif change == "effect":
        report["effects"][0]["turn_effect_chips"] += 1
    elif change == "seed":
        report["hybrids"][0]["seed"] = True
    elif change == "training":
        report["training_performed"] = True
    elif change == "global":
        report["fresh_global_admission"] = True
    elif change == "source":
        report["source"]["sha256"]["uv.lock"] = "wrong"
    else:
        report["crossplay"][0]["value_player_zero_chips"] = float("nan")
    path = tmp_path / "study.json"
    path.write_text(json.dumps(report))
    with pytest.raises((ArithmeticError, ValueError)):
        study.replay(ROOT, path)


@pytest.mark.parametrize(
    "change", ["hash", "missing", "duplicate", "baseline", "response", "context"]
)
def test_changed_profile_receipts_rejected(
    tiny: tuple[Path, dict[str, Any]], tmp_path: Path, change: str
) -> None:
    original, raw = tiny
    report = copy.deepcopy(raw)
    payload = json.loads(
        gzip.decompress((original.parent / raw["profiles_file"]).read_bytes())
    )
    if change == "missing":
        payload["hybrids"].pop()
    elif change == "duplicate":
        payload["hybrids"].append(payload["hybrids"][-1])
    elif change == "baseline":
        payload["hybrids"][0]["baseline_policy"][0] = [1.0]
    elif change == "response":
        payload["hybrids"][0]["responses"][0]["exact_reply_profile"][0] = [1.0]
    elif change == "context":
        payload["hybrids"][0]["range_context_sha256"] = "wrong"
    else:
        payload["hybrids"][0]["baseline_policy"][0] = [1.0]
    sidecar = tmp_path / report["profiles_file"]
    sidecar.write_bytes(gzip.compress(json.dumps(payload).encode(), mtime=0))
    if change != "hash":
        report["profiles_sha256"] = digest(sidecar)
    path = tmp_path / "study.json"
    path.write_text(json.dumps(report))
    with pytest.raises((ArithmeticError, ValueError)):
        study.replay(ROOT, path)


def test_deadline_rejects_partial(
    tiny: tuple[Path, dict[str, Any]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(study, "source_provenance", source_fixture)

    def expired(*args: Any) -> None:
        raise TimeoutError("software fixture")

    monkeypatch.setattr(Deadline, "check", expired)
    with pytest.raises(TimeoutError):
        study.run(ROOT, tiny[0].parent / "config.json", tmp_path / "partial.json")
    assert not (tmp_path / "partial.json").exists()


def test_inspector_selects_seed(tiny: tuple[Path, dict[str, Any]]) -> None:
    r = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts/inspect_policy_swap.py"),
            "--report",
            str(tiny[0]),
            "--game",
            "dev_low_oop",
            "--seed",
            "13",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 0, r.stderr
    assert "No retraining" in r.stdout and "FF:" in r.stdout


def test_native_and_report(
    tiny: tuple[Path, dict[str, Any]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("pyspiel")
    monkeypatch.setattr(native, "source_provenance", source_fixture)
    path, report = tiny
    audit_path = tmp_path / "audit.json"
    r = native.audit(ROOT, path.parent / "config.json", path, audit_path)
    assert (
        r["status"] == "passed"
        and len(r["crossplay"]) == 20
        and len(r["responses"]) == 40
    )
    assert reporting.checked_audit(path, report, r) <= 1e-9
    for change in (
        "missing",
        "duplicate",
        "cross_value",
        "root",
        "achieved",
        "baseline",
        "error",
        "context",
        "target",
        "input",
    ):
        bad = copy.deepcopy(r)
        row = bad["responses"][0]
        if change == "missing":
            bad["responses"].pop()
        elif change == "duplicate":
            bad["responses"].append(row)
        elif change == "cross_value":
            bad["crossplay"][0]["native_value_player_zero_chips"] += 1
        elif change == "root":
            row["exact_native_value_chips"] += 1
        elif change == "achieved":
            row["exact_achieved_value_chips"] += 1
        elif change == "baseline":
            row["native_baseline_value_chips"] += 1
        elif change == "error":
            row["baseline_error_chips"] = -1
        elif change == "context":
            row["range_context_sha256"] = "wrong"
        elif change == "target":
            row["target"] = True
        else:
            bad["input_sha256"] = "wrong"
        with pytest.raises(ArithmeticError):
            reporting.checked_audit(path, report, bad)
    monkeypatch.setattr(reporting, "plots", lambda *a: None)
    summary = reporting.render(ROOT, path, audit_path, tmp_path / "report")
    assert (
        summary["native_roots_checked"] == 80
        and summary["own_achieved_values_checked"] == 80
    )
    assert summary["training_performed"] is False


def test_plots(tiny: tuple[Path, dict[str, Any]], tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    hybrid, _, _ = reporting.tables(tiny[1])
    reporting.plots(tiny[1], hybrid, tmp_path)
    assert {p.name for p in tmp_path.glob("*.png")} == {
        "crossed-payoffs.png",
        "street-gaps.png",
    }
