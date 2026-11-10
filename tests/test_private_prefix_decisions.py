"""Fictional panel/accounting checks, separate from the saved poker diagnosis."""

import copy
import importlib.util
import json
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "decision_cli", ROOT / "scripts/trace_private_prefix_decisions.py"
)
assert SPEC is not None and SPEC.loader is not None
CLI = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CLI)


def panel_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    config = json.loads((ROOT / CLI.CONFIG).read_text())
    own: dict[str, Any] = dict(rows=[], baseline_rows=[], self_pairs=[])
    for seed in config["seeds"]:
        row = dict(
            id=f"FICTIONAL-new-{seed}",
            case=dict(
                spot_file="configs/learning-spots/dev_medium_oop.json",
                representation="texture_range_q8_b8",
                regret_rule="signed",
                seed=seed,
            ),
            batch_size=4,
            work_label=10000000,
            readout="linear_average",
        )
        own["rows"].append(row)
        for kind in ("B1", "IID"):
            peer = dict(row, id=f"FICTIONAL-{kind}-{seed}")
            own["baseline_rows"].append(peer)
            own["self_pairs"].append(
                dict(candidate_id=row["id"], baseline_kind=kind, baseline_id=peer["id"])
            )
    return config, own


def test_fixed_panel_keeps_every_seed_and_both_controls() -> None:
    cfg, own = panel_fixture()
    result = CLI.panel(cfg, own)
    assert [(r["seed"], r["role"]) for r in result] == [
        (seed, role)
        for seed in (20261301, 20261302, 20261303)
        for role in ("B1", "IID", "stratified")
    ]
    assert len({r["row"]["id"] for r in result}) == 9


@pytest.mark.parametrize(
    "bad", ["missing", "duplicate", "typed_seed", "baseline", "pair"]
)
def test_reject_incomplete_or_ambiguous_panel(bad: str) -> None:
    cfg, own = panel_fixture()
    if bad == "missing":
        own["rows"].pop()
    elif bad == "duplicate":
        own["rows"].append(copy.deepcopy(own["rows"][0]))
    elif bad == "typed_seed":
        own["rows"][0]["case"]["seed"] = float(cfg["seeds"][0])
    elif bad == "baseline":
        own["baseline_rows"].append(copy.deepcopy(own["baseline_rows"][0]))
    else:
        own["self_pairs"].append(copy.deepcopy(own["self_pairs"][0]))
    with pytest.raises(ArithmeticError):
        CLI.panel(cfg, own)


def roots_fixture() -> tuple[dict[str, Any], dict[str, Any]]:
    responses, previous = [], []
    for seat, baseline in ((0, 2.0), (1, -2.0)):
        responses.append(
            dict(
                target=seat,
                baseline_value_chips=baseline,
                exact_reply_value_chips=baseline + 3.0,
                restricted_reply_value_chips=baseline + 1.0,
                within_partition_gain_chips=1.0,
                extra_information_value_chips=2.0,
                exact_gain_chips=3.0,
                loss_sum_chips=3.0,
                street_losses_chips=dict(TURN=1.0, RIVER=2.0),
                accounting_error_chips=0.0,
            )
        )
        previous.append(
            dict(
                target=seat,
                baseline_value_chips=baseline,
                exact_reply_value_chips=baseline + 3.0,
                restricted_reply_value_chips=baseline + 1.0,
                within_partition_gain_chips=1.0,
                extra_information_gap_chips=2.0,
            )
        )
    return (
        dict(
            exact_exploitability_chips=3.0,
            restricted_exploitability_chips=1.0,
            extra_information_chips=2.0,
            saved_value_player_zero_chips=2.0,
            responses=responses,
        ),
        dict(
            metrics=dict(
                exact_exploitability_chips=3.0,
                within_partition_gain_chips=1.0,
                extra_information_gap_chips=2.0,
                value_player_zero_chips=2.0,
                river_only_gain_exact_prefix_chips=10.0,
            ),
            responses=previous,
        ),
    )


def test_total_accounting_and_target_signs_keep_river_switch_separate() -> None:
    summary, source = roots_fixture()
    CLI.verify(summary, source, 1e-9)
    assert sum(r["exact_gain_chips"] for r in summary["responses"]) / 2 == 3.0
    assert source["metrics"]["river_only_gain_exact_prefix_chips"] == 10.0


@pytest.mark.parametrize(
    "bad", ["root", "street", "nonfinite", "order", "negative", "row"]
)
def test_reject_changed_roots_or_accounting(bad: str) -> None:
    summary, source = roots_fixture()
    if bad == "root":
        summary["extra_information_chips"] = 2.5
    elif bad == "street":
        summary["responses"][0]["street_losses_chips"]["RIVER"] = 2.5
    elif bad == "nonfinite":
        summary["responses"][0]["exact_gain_chips"] = float("nan")
    elif bad == "order":
        summary["responses"].reverse()
    elif bad == "negative":
        summary["responses"][0]["street_losses_chips"] = dict(TURN=-1.0, RIVER=4.0)
    else:
        summary["responses"][1]["loss_sum_chips"] = 3.1
    with pytest.raises((ArithmeticError, ValueError)):
        CLI.verify(summary, source, 1e-9)


def test_existing_output_is_preserved_before_any_reader(tmp_path: Path) -> None:
    output = tmp_path / "partial"
    output.mkdir()
    marker = output / "notice"
    marker.write_text("keep")
    with patch.object(CLI, "read", side_effect=AssertionError("reader called")):
        with pytest.raises(FileExistsError):
            CLI.run(ROOT, output)
    assert marker.read_text() == "keep"


VIEW_SPEC = importlib.util.spec_from_file_location(
    "decision_view", ROOT / "scripts/inspect_private_prefix_decisions.py"
)
assert VIEW_SPEC is not None and VIEW_SPEC.loader is not None
VIEW = importlib.util.module_from_spec(VIEW_SPEC)
VIEW_SPEC.loader.exec_module(VIEW)


def cached_fixture(tmp_path: Path) -> Path:
    root = tmp_path
    (root / "configs").mkdir()
    cfg, _ = panel_fixture()
    (root / CLI.CONFIG).write_text(json.dumps(cfg))
    for key in ("own", "native"):
        path = root / cfg[key]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("FICTIONAL ONLY")
    output = root / "report"
    output.mkdir()
    profile = dict(
        exact_exploitability_chips=3.0,
        responses=[
            dict(
                target=seat,
                exact_gain_chips=3.0,
                top_groups=[
                    dict(abstract_info=i, loss_contribution_chips=float(i), examples=[])
                    for i in (1, 2)
                ],
            )
            for seat in (0, 1)
        ],
    )
    profiles = [
        dict(profile, seed=seed, role=role)
        for seed in cfg["seeds"]
        for role in cfg["roles"]
    ]
    (output / "summary.json").write_text(json.dumps(dict(profiles=profiles)))
    manifest = dict(
        status="complete_saved_decision_diagnosis",
        config_sha256=VIEW.digest(root / CLI.CONFIG),
        source={},
        profiles=9,
        responses=18,
        constructors_blocked=True,
        training_performed=False,
        reference_constructed=False,
        new_agent_default=False,
        fresh_global_admission=False,
        outputs={"summary.json": VIEW.digest(output / "summary.json")},
        own_sha256=VIEW.digest(root / cfg["own"]),
        native_sha256=VIEW.digest(root / cfg["native"]),
    )
    (output / "manifest.json").write_text(json.dumps(manifest))
    return output


def test_cached_browser_rejects_changed_report_or_input(tmp_path: Path) -> None:
    output = cached_fixture(tmp_path)
    with patch.object(VIEW, "check_source") as check:
        assert len(VIEW.load(tmp_path, output)) == 9
        check.assert_called_once()
        original = (output / "summary.json").read_bytes()
        (output / "summary.json").write_text("{}")
        with pytest.raises(ArithmeticError, match="bytes changed"):
            VIEW.load(tmp_path, output)
        (output / "summary.json").write_bytes(original)
        cfg = json.loads((tmp_path / CLI.CONFIG).read_text())
        (tmp_path / cfg["own"]).write_text("CHANGED")
        with pytest.raises(ArithmeticError, match="input bytes changed"):
            VIEW.load(tmp_path, output)


def test_browser_controls_switch_rows_seeds_methods_and_seats(
    tmp_path: Path,
    capsys: Any,
) -> None:
    output = cached_fixture(tmp_path)
    with patch.object(VIEW, "check_source"):
        profiles = VIEW.load(tmp_path, output)
    with (
        patch.object(VIEW, "load", return_value=profiles),
        patch("sys.argv", ["viewer", "--interactive"]),
        patch("builtins.input", side_effect=["n", "p", "s", "o", "t", "q"]),
    ):
        assert VIEW.main() == 0
    text = capsys.readouterr().out
    assert "Group 2/2" in text and "Group 1/2" in text
    assert "20261303 / stratified / responding seat 0" in text
    assert "20261303 / B1 / responding seat 1" in text
    assert "TOTAL unilateral gain" in text
    assert "not an extra-information-only or retraining benefit" in text
