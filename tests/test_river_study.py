"""Work budgets, missing-grid failures, frozen-error arithmetic and retention."""

import gzip
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.postflop import river_study as study
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning import root_factory
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.sampling import PostflopMCCFR, exact_initial_expectation
from poker_ai.postflop.tree import SpotTree

ROOT = Path(__file__).resolve().parents[1]


def tiny_config() -> dict[str, Any]:
    config: dict[str, Any] = json.loads(
        (ROOT / "configs/river-integration-study.json").read_text()
    )
    config.update(
        spot_files=config["spot_files"][:1],
        training_seeds=[17],
        total_node_thresholds=[6000, 6200],
        full_tree_checkpoints=[256],
        full_tree_backend="numpy",
    )
    config["frozen_panel"].update(seeds=[18], passes_per_seed_target_policy_variant=2)
    return config


@pytest.fixture(scope="module")
def tree() -> MatrixTree:
    return MatrixTree.build(
        SpotTree.build(load_spot(ROOT / "configs/learning-spots/dev_low_oop.json"))
    )


def test_zero_and_sparse_error_include_unvisited_rows() -> None:
    expected = np.array([[2.0, 3.0], [4.0, 0.0]])
    lookup = {"a": 0, "b": 1}
    mask = np.array([True, True])
    assert study.squared_error({}, expected, lookup, mask) == 29
    assert (
        study.squared_error(
            {"a": np.array([2.0, 3.0]), "b": np.array([4.0])}, expected, lookup, mask
        )
        == 0
    )
    assert (
        study.squared_error({"a": np.array([1.0, 1.0])}, expected, lookup, mask) == 21
    )
    assert study.squared_error({}, expected, lookup, np.array([False, True])) == 16


def test_work_budget_charges_warm_start_and_whole_iterations(tree: MatrixTree) -> None:
    solver = PostflopMCCFR(root_factory(tree), Generator(PCG64(7)), "linear")
    exact_initial_expectation(solver, tree)
    warm = 2 * len(tree.player)
    study.advance_to_work(solver, warm, study.Deadline(10))
    assert solver.iteration == 1 and solver.nodes_visited == 0
    study.advance_to_work(solver, warm + 1, study.Deadline(10))
    assert solver.iteration == 2
    assert 1 <= solver.nodes_visited < 2 * len(tree.player)


def test_frozen_expectation_agrees_with_initial_expected_iteration(
    tree: MatrixTree,
) -> None:
    policy = tree.normalize(tree.legal)
    r0, a1 = study.expected_updates(tree, policy, 0)
    r1, a0 = study.expected_updates(tree, policy, 1)
    solver = PostflopMCCFR(root_factory(tree), Generator(PCG64(9)))
    exact_initial_expectation(solver, tree)
    for i, key in enumerate(tree.keys):
        n = len(tree.actions[i])
        np.testing.assert_allclose(
            solver.rows[key].regrets, (r0 + r1)[i, :n], atol=1e-12
        )
        np.testing.assert_allclose(
            solver.rows[key].strategy_sum, (a0 + a1)[i, :n], atol=1e-12
        )


@pytest.fixture(scope="module")
def tiny_report(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, dict[str, Any]]:
    directory = tmp_path_factory.mktemp("river-study")
    path = directory / "config.json"
    path.write_text(json.dumps(tiny_config()))
    # Configs inside the repository are required by provenance; test injection
    # keeps this temporary fixture from making an experimental source claim.
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(
            study, "source_provenance", lambda *args, **kwargs: {"test": True}
        )
        output = directory / "study.json"
        report = study.run_study(ROOT, path, output)
    return output, report


def test_tiny_study_complete_grid_policies_and_cost(
    tiny_report: tuple[Path, dict[str, Any]],
) -> None:
    path, report = tiny_report
    assert report["status"] == "completed", report["failure"]
    assert report["acceptance"]["complete"]
    assert len(report["rows"]) == 5 and len(report["frozen_panel"]) == 8
    policies = json.loads(
        gzip.decompress(path.with_name(report["own_policies_file"]).read_bytes())
    )
    assert len(policies["policies"]) == 5
    for row in report["rows"]:
        if row["method"] == "full_cfr_plus":
            continue
        assert (
            row["total_node_work"]
            == row["recursive_visits"] + row["warm_node_equivalent"]
        )
        assert (
            row["node_threshold"]
            <= row["total_node_work"]
            < row["node_threshold"] + 5998
        )
        assert (
            row["subsequently_sampled_information_sets"]
            + row["initial_only_information_sets"]
            == row["exact_information_sets"]
        )
        assert row["uniform_reach_average_row_coverage"] == pytest.approx(1)
    with pytest.raises(FileExistsError):
        study.run_study(ROOT, path.parent / "config.json", path)


def test_missing_intermediate_or_duplicate_cannot_pass_grid(
    tiny_report: tuple[Path, dict[str, Any]],
) -> None:
    _, report = tiny_report
    rows, config = report["rows"], report["config"]
    for bad in (rows[:-1], rows + [rows[-1]], rows[:1] + rows[2:]):
        assert not study.acceptance(bad, config)["complete"]
        assert not study.acceptance(bad, config)["candidate_passed"]


def test_timeout_retains_failed_report(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config = tmp_path / "config.json"
    config.write_text(json.dumps(tiny_config()))
    monkeypatch.setattr(
        study, "source_provenance", lambda *args, **kwargs: {"test": True}
    )

    def timeout(self: study.Deadline) -> None:
        raise TimeoutError("test cap")

    monkeypatch.setattr(study.Deadline, "check", timeout)
    path = tmp_path / "study.json"
    report = study.run_study(ROOT, config, path)
    assert (
        report["status"] == "incomplete" and report["failure"]["reason"] == "test cap"
    )
    assert not report["acceptance"]["complete"]
    assert json.loads(path.read_text()) == report
    assert path.with_name(report["own_policies_file"]).exists()


@pytest.mark.parametrize(
    "change",
    [
        {"training_seeds": [1, 1]},
        {"total_node_thresholds": [10, 1]},
        {"maximum_seconds_total": float("nan")},
        {"variants": ["river_integrated"]},
        {"initial_exact_expectation": False},
        {"spot_files": []},
    ],
)
def test_invalid_design_rejected_before_work(change: dict[str, Any]) -> None:
    config = tiny_config()
    config.update(change)
    with pytest.raises(ValueError):
        study.validate_config(config)


def test_artifacts_and_summaries_require_every_panel_cell(
    tiny_report: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    from poker_ai.postflop.river_artifacts import checked_artifacts
    from poker_ai.postflop.river_report import learning_summary, panel_summary

    path, report = tiny_report
    checked, policies = checked_artifacts(path)
    assert checked == report and len(policies) == 5
    assert len(learning_summary(report)) == 4
    assert len(panel_summary(report)) == 4
    bad = json.loads(path.read_text())
    bad["frozen_panel"].pop()
    bad_path = path.with_name("missing-panel.json")
    bad_path.write_text(json.dumps(bad))
    with pytest.raises(ArithmeticError, match="panel"):
        checked_artifacts(bad_path)
    bad["frozen_panel"] = report["frozen_panel"] + [report["frozen_panel"][0]]
    bad_path.write_text(json.dumps(bad))
    with pytest.raises(ArithmeticError, match="panel"):
        checked_artifacts(bad_path)
    broken = tmp_path / "study.json"
    broken.write_text(path.read_text())
    (tmp_path / report["own_policies_file"]).write_bytes(b"changed")
    with pytest.raises(ArithmeticError, match="hash"):
        checked_artifacts(broken)


def test_ratio_of_pooled_batch_means_and_zero_denominator() -> None:
    from poker_ai.postflop.river_report import panel_summary

    rows = []
    for method, pairs in (
        ("external", [(2.0, 10.0), (6.0, 20.0)]),
        ("river_integrated", [(1.0, 20.0), (3.0, 40.0)]),
    ):
        for error, cost in pairs:
            rows.append(
                {
                    "spot": "example",
                    "policy": "uniform",
                    "target": 0,
                    "variant": method,
                    "regret_mse_all": error,
                    "regret_mse_turn": error,
                    "average_mse_all": 0.0,
                    "mean_node_visits": cost,
                }
            )
    result = panel_summary(
        {"frozen_panel": rows, "config": {"variants": ["external", "river_integrated"]}}
    )[0]
    assert result["regret_mse_all_ratio"] == 0.5
    assert result["visit_ratio"] == 2
    assert result["regret_mse_all_cost_ratio"] == 1
    assert result["average_mse_all_cost_ratio"] is None


def test_native_audit_rejects_missing_or_corrupt_comparison(
    tiny_report: tuple[Path, dict[str, Any]], tmp_path: Path
) -> None:
    pytest.importorskip("pyspiel")
    from poker_ai.postflop.river_report import checked_audit
    from poker_ai.solver_validation.river import validate_study

    path, report = tiny_report
    output = tmp_path / "native.json"
    native = validate_study(ROOT, path, output)
    assert native["status"] == "passed" and len(native["comparisons"]) == 5
    checked_audit(path, output, report)
    native["comparisons"][-1]["native_exploitability_chips"] += 1.0
    output.write_text(json.dumps(native))
    with pytest.raises(ArithmeticError, match="tolerance"):
        checked_audit(path, output, report)
    native["comparisons"].pop()
    output.write_text(json.dumps(native))
    with pytest.raises(ArithmeticError, match="audit"):
        checked_audit(path, output, report)
