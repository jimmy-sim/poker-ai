"""Saved diagnosis fixtures, complete identities, additive means and native roots."""

import copy
import gzip
import json
import statistics
import subprocess
import sys
from functools import lru_cache
from pathlib import Path
from typing import Any

import pytest

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop import range_reply as diagnosis
from poker_ai.postflop import range_reply_report as reporting
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.range_protocol import CONTROLS, build_representation_control
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.solver_validation import range_reply as native

ROOT = Path(__file__).resolve().parents[1]
REAL_LOAD = diagnosis.load_inputs


def source_fixture(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return {"dirty": False, "sha256": {}, "git_commit": "software-fixture-not-research"}


@lru_cache(maxsize=1)
def uniform_inputs() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    path = "configs/learning-spots/dev_low_oop.json"
    source = SpotTree.build(load_spot(ROOT / path))
    model = CardAbstraction.load(ROOT / "results/card-models/potential-8.json")
    records = []
    for name in CONTROLS:
        tree = build_representation_control(source, name, model)
        policy = tree.exact_policy(tree.normalize(tree.legal))
        exact = MatrixTree.build(source)
        from poker_ai.toy.analysis import evaluate

        metrics = evaluate(exact, exact.dense_exact(policy))
        for training, seed in (("full", None), ("sampled", 13)):
            records.append(
                {
                    "spot_file": path,
                    "representation": name,
                    "training": training,
                    "seed": seed,
                    "range_context_sha256": "software-context"
                    if name == "texture_range_q8_b8"
                    else None,
                    "policy": policy,
                    "exploitability_chips": metrics.exploitability,
                }
            )
    return {"config": {"model": "results/card-models/potential-8.json"}}, records


def load_fixture(
    root: Path, config: dict[str, Any]
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    if config["sampled_seeds"] == [13]:
        return uniform_inputs()
    return REAL_LOAD(root, config)


@pytest.fixture(autouse=True)
def fixtures(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(diagnosis, "load_inputs", load_fixture)
    monkeypatch.setattr(native, "load_inputs", load_fixture)


@pytest.fixture(scope="module")
def tiny(tmp_path_factory: pytest.TempPathFactory) -> tuple[Path, dict[str, Any]]:
    directory = tmp_path_factory.mktemp("range-reply-software")
    config = json.loads((ROOT / "configs/range-mass-reply-diagnosis.json").read_text())
    config.update(
        spot_files=config["spot_files"][:1],
        sampled_seeds=[13],
        top_groups=2,
        examples_per_group=2,
    )
    cfg = directory / "config.json"
    cfg.write_text(json.dumps(config))
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(diagnosis, "source_provenance", source_fixture)
        patch.setattr(diagnosis, "load_inputs", load_fixture)
        report = diagnosis.diagnose(ROOT, cfg, directory / "diagnosis.json")
    assert report["status"] == "completed"
    return directory / "diagnosis.json", report


def test_real_input_grid_keeps_all_final_seeds_and_full_controls() -> None:
    config = json.loads((ROOT / "configs/range-mass-reply-diagnosis.json").read_text())
    _, records = REAL_LOAD(ROOT, config)
    assert len(records) == 40
    assert {
        tuple(r[k] for k in diagnosis.IDENTITY) for r in records
    } == diagnosis.expected_grid(config)


def test_complete_fixture_replays_and_sums(tiny: tuple[Path, dict[str, Any]]) -> None:
    path, _ = tiny
    report, details, error = diagnosis.replay(ROOT, path)
    assert len(details) == 10 and error <= 1e-9
    assert (
        report["training_performed"] is False
        and report["fresh_global_admission"] is False
    )
    for case in report["cases"]:
        assert case["exact_exploitability_chips"] == pytest.approx(
            case["restricted_exploitability_chips"] + case["extra_information_chips"],
            abs=1e-9,
        )
        for response in case["responses"]:
            assert response["loss_sum_chips"] == pytest.approx(
                response["exact_gain_chips"], abs=1e-9
            )
            assert response["within_partition_gain_chips"] >= -1e-9
            assert response["extra_information_value_chips"] >= -1e-9
    with pytest.raises(FileExistsError):
        diagnosis.diagnose(ROOT, path.parent / "config.json", path)


def test_arithmetic_means_preserve_sum_but_component_medians_do_not() -> None:
    rows: list[dict[str, Any]] = [
        {
            "spot_file": "fixture",
            "representation": "fixture",
            "training": "sampled",
            "seed": i,
            "exact_percent_pot": a + b,
            "within_percent_pot": a,
            "extra_percent_pot": b,
        }
        for i, (a, b) in enumerate(((0, 10), (9, 9), (10, 0)))
    ]
    result = reporting.aggregate(rows)[0]
    assert result["mean_exact_percent_pot"] == pytest.approx(
        result["mean_within_percent_pot"] + result["mean_extra_percent_pot"]
    )
    assert result["median_exact_percent_pot"] == 10
    assert (
        statistics.median(r["within_percent_pot"] for r in rows)
        + statistics.median(r["extra_percent_pot"] for r in rows)
        == 18
    )


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "context",
        "seed",
        "global",
        "training",
        "source",
        "status",
        "numeric",
        "example",
        "nan",
        "full_seed",
    ],
)
def test_changed_summary_rejected(
    tiny: tuple[Path, dict[str, Any]], tmp_path: Path, change: str
) -> None:
    original, raw = tiny
    report = copy.deepcopy(raw)
    (tmp_path / raw["details_file"]).write_bytes(
        (original.parent / raw["details_file"]).read_bytes()
    )
    if change == "missing":
        report["cases"].pop()
    elif change == "duplicate":
        report["cases"].append(report["cases"][-1])
    elif change == "context":
        report["cases"][-1]["range_context_sha256"] = "wrong"
    elif change == "seed":
        report["cases"][-1]["seed"] = True
    elif change == "full_seed":
        report["cases"][0]["seed"] = 13
    elif change == "global":
        report["fresh_global_admission"] = True
    elif change == "training":
        report["training_performed"] = True
    elif change == "source":
        report["source"]["sha256"]["uv.lock"] = "wrong"
    elif change == "status":
        report["status"] = "incomplete"
    elif change == "example":
        report["cases"][0]["responses"][0]["top_groups"][0]["examples"][0][
            "saved_probabilities"
        ][0] += 0.25
    elif change == "numeric":
        report["cases"][0]["restricted_exploitability_chips"] += 1
    else:
        report["cases"][0]["exact_exploitability_chips"] = float("nan")
    path = tmp_path / "diagnosis.json"
    path.write_text(json.dumps(report))
    with pytest.raises((ArithmeticError, ValueError)):
        diagnosis.replay(ROOT, path)


@pytest.mark.parametrize(
    "change",
    ["hash", "missing", "duplicate", "loss", "profile", "example", "index_type"],
)
def test_changed_details_rejected(
    tiny: tuple[Path, dict[str, Any]], tmp_path: Path, change: str
) -> None:
    original, raw = tiny
    report = copy.deepcopy(raw)
    payload = json.loads(
        gzip.decompress((original.parent / raw["details_file"]).read_bytes())
    )
    if change == "missing":
        payload["cases"].pop()
    elif change == "duplicate":
        payload["cases"].append(payload["cases"][-1])
    elif change == "loss":
        payload["cases"][0]["responses"][0]["infos"][0]["loss_chips"] += 1
    elif change == "profile":
        payload["cases"][0]["responses"][0]["exact_reply_profile"][0] = [1.0]
    elif change == "index_type":
        payload["cases"][0]["responses"][0]["infos"][0]["exact_info"] = False
    else:
        payload["cases"][0]["responses"][0]["infos"][0]["loss_chips"] += 1
    sidecar = tmp_path / report["details_file"]
    sidecar.write_bytes(gzip.compress(json.dumps(payload).encode(), mtime=0))
    if change != "hash":
        report["details_sha256"] = digest(sidecar)
    path = tmp_path / "diagnosis.json"
    path.write_text(json.dumps(report))
    with pytest.raises((ArithmeticError, ValueError)):
        diagnosis.replay(ROOT, path)


def test_nested_comparison_rejects_types_and_nonfinite() -> None:
    for a, b in (
        (0, False),
        ("a", "b"),
        ([1], [1, 2]),
        ({"x": 1}, {"y": 1}),
        (1.0, float("nan")),
    ):
        with pytest.raises(ArithmeticError):
            diagnosis.compare(a, b)
    assert diagnosis.compare([1.0, {"a": 2.0}], [1.0 + 1e-12, {"a": 2.0}]) < 2e-12


def test_deadline_cannot_accept_partial(
    tiny: tuple[Path, dict[str, Any]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(diagnosis, "source_provenance", source_fixture)

    def expired(*args: Any) -> None:
        raise TimeoutError("software fixture")

    monkeypatch.setattr(Deadline, "check", expired)
    with pytest.raises(TimeoutError):
        diagnosis.diagnose(
            ROOT, tiny[0].parent / "config.json", tmp_path / "partial.json"
        )
    assert not (tmp_path / "partial.json").exists()


def test_inspector_selects_one_seed_or_full(tiny: tuple[Path, dict[str, Any]]) -> None:
    for training in ("sampled", "full"):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/inspect_range_reply.py"),
                "--report",
                str(tiny[0]),
                "--game",
                "dev_low_oop",
                "--training",
                training,
                "--seed",
                "13",
            ],
            text=True,
            capture_output=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        assert "Fixed saved opponent" in result.stdout and training in result.stdout


def test_native_roots_achieved_values_and_report(
    tiny: tuple[Path, dict[str, Any]], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("pyspiel")
    path, report = tiny
    monkeypatch.setattr(native, "source_provenance", source_fixture)
    audit_path = tmp_path / "audit.json"
    result = native.audit(ROOT, path.parent / "config.json", path, audit_path)
    assert result["status"] == "passed" and len(result["rows"]) == 20
    assert reporting.checked_audit(path, report, result) <= 1e-9
    for change in (
        "missing",
        "duplicate",
        "context",
        "root",
        "achieved",
        "error",
        "target",
        "input",
    ):
        bad = copy.deepcopy(result)
        row = bad["rows"][-1]
        if change == "missing":
            bad["rows"].pop()
        elif change == "duplicate":
            bad["rows"].append(row)
        elif change == "context":
            row["range_context_sha256"] = "wrong"
        elif change == "root":
            row["exact_native_value_chips"] += 1
        elif change == "achieved":
            row["exact_achieved_value_chips"] += 1
        elif change == "error":
            row["exact_root_error_chips"] = -1
        elif change == "target":
            row["target"] = True
        else:
            bad["input_sha256"] = "wrong"
        with pytest.raises(ArithmeticError):
            reporting.checked_audit(path, report, bad)
    monkeypatch.setattr(reporting, "plots", lambda *a: None)
    summary = reporting.render(ROOT, path, audit_path, tmp_path / "report")
    assert (
        summary["native_roots_checked"] == 40
        and summary["own_reply_values_checked"] == 40
    )
    assert summary["training_performed"] is False


def test_plot_smoke(tiny: tuple[Path, dict[str, Any]], tmp_path: Path) -> None:
    pytest.importorskip("matplotlib")
    rows = reporting.summary_rows(tiny[1]["cases"])
    reporting.plots(rows, reporting.aggregate(rows), tiny[1]["config"], tmp_path)
    assert {p.name for p in tmp_path.glob("*.png")} == {
        "candidate-profiles.png",
        "sampled-means.png",
    }


def test_config_requires_all_six_input_bindings() -> None:
    config = json.loads((ROOT / "configs/range-mass-reply-diagnosis.json").read_text())
    for name in list(config["inputs_sha256"]):
        bad = copy.deepcopy(config)
        del bad["inputs_sha256"][name]
        with pytest.raises(ValueError):
            diagnosis.validate_config(bad)
