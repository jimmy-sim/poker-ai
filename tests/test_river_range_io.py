"""Local-panel/cache corruption and command controls; synthetic UNIT receipts."""

import copy
import gzip
import importlib
import itertools
import json
import sys
import time
from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation import river_range_io as io
from poker_ai.evaluation import river_range_run as runner
from poker_ai.evaluation import river_range_view as view
from poker_ai.postflop.learning_artifacts import canonical, sha
from poker_ai.postflop.river_study import digest

ROOT = Path(__file__).resolve().parents[1]


def suffix(target: int, label: str) -> tuple[dict[str, Any], dict[str, Any]]:
    """Known zero-sharing/self-mixture schema example, not a poker result."""
    row = dict(
        exact_info=target,
        abstract_info=target,
        hole=["As", "Js"],
        board=["Ts", "9s", "4d", "2h", "3h"],
        pot=72,
        actions=["fold", "call"],
        static_features=dict(
            own_rank=[0, 14, 13],
            range_compatibility=[True, True],
            range_relations=[1, 1],
        ),
        compatible=[True, True],
        actual_posterior=[0.5, 0.5],
        compatible_prior=[0.5, 0.5],
        combo_action_values_chips=[[1.0, 0.0], [3.0, 0.0]],
        actual_action_values_chips=[2.0, 0.0],
        prior_action_values_chips=[2.0, 0.0],
        counterfactual_support=1.0,
        uniform_decision_weight=1.0,
        saved_reach_mass=1.0,
        saved_probabilities=[1.0, 0.0],
        prior_fine_trace_loss_chips=0.0,
        history=[],
    )
    group = dict(
        group_id=str(target),
        abstract_info=target,
        infos=[target],
        supported_infos=[target],
        static_signature=None,
        maximum_posterior_total_variation=0.0,
        intervention_range_total_variation=0.0,
        local_cost=0.0,
        strict_conflict=False,
        supported_rows=1,
        weight=1.0,
    )
    static = dict(
        group, group_id=f"{target}:UNIT_STATIC", static_signature=row["static_features"]
    )
    metrics = dict(
        supported_uniform_decision_weight=1.0,
        local_sharing_cost_chips_per_weighted_decision=0.0,
        strict_conflicting_groups=0,
        total_groups=1,
        supported_groups=1,
        maximum_posterior_total_variation_within_group=0.0,
    )
    panels = [
        dict(
            range_weights=w,
            group_controls={c: copy.deepcopy(metrics) for c in io.GROUPS},
        )
        for w in io.WEIGHTS
    ]
    summary = dict(
        suffix=label,
        panels=panels,
        river_info_ids=[target],
        maximum_source_chip_error=0.0,
        maximum_unitless_error=0.0,
        top_groups=[group],
    )
    detail = dict(
        suffix=label,
        rows=[row],
        groups={
            w: {
                io.GROUPS[0]: [copy.deepcopy(group)],
                io.GROUPS[1]: [copy.deepcopy(static)],
            }
            for w in io.WEIGHTS
        },
    )
    return summary, detail


def cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Every source/publication assertion is mocked and labeled UNIT_ONLY.
    # This fixture is never a scientific receipt, training input or admission.
    config = io.contract(ROOT)
    monkeypatch.setattr(io, "contract", lambda r: config)
    monkeypatch.setattr(io, "prior", lambda *a: [])
    monkeypatch.setattr(io, "check_source", lambda *a: None)
    folder = tmp_path / "cache"
    (folder / "details").mkdir(parents=True)
    profiles = []
    for coordinate, (game, seed) in enumerate(
        itertools.product(config["games"], config["seeds"])
    ):
        for arm in config["arms"]:
            identity = dict(
                coordinate=coordinate,
                game=game,
                seed=seed,
                arm=arm,
                source_id=f"UNIT_ONLY/{coordinate}/{arm}",
            )
            responses, details = [], []
            for target in (0, 1):
                summaries, full = zip(
                    *(suffix(target, s) for s in io.SUFFIXES), strict=True
                )
                responses.append(dict(target=target, suffixes=list(summaries)))
                details.append(
                    dict(
                        target=target,
                        declared_opponent_range=[["Kh", "Qh"], ["9c", "9d"]],
                        suffixes=list(full),
                    )
                )
            name = f"details/{coordinate:02d}-{arm}.json.gz"
            (folder / name).write_bytes(
                gzip.compress(canonical(dict(**identity, responses=details)), mtime=0)
            )
            profiles.append(dict(**identity, responses=responses, details_file=name))
    (folder / "summary.json").write_bytes(canonical(dict(profiles=profiles)))
    for name in ("partial.json", "panels.csv"):
        (folder / name).write_text("UNIT_ONLY_NOT_A_STUDY")
    source = dict(UNIT_ONLY="a" * 64)
    m = dict(
        status="complete_local_river_range_reweighting",
        config_sha256=io.CONFIG_SHA,
        source=dict(sha256=source),
        source_sha256=sha(source),
        profiles=24,
        responses=48,
        suffix_conditions=96,
        local_panels=192,
        constructors_blocked=True,
        continuation_manifest_sha256=config["continuation_manifest_sha256"],
        maximum_seconds=900,
        seconds=1.0,
        training_performed=False,
        reference_constructed=False,
        new_independent_audit=False,
        feature_deployed=False,
        new_agent_default=False,
        fresh_global_admission=False,
        profile_river_rows=48,
        suffix_river_rows=96,
        group_control_csv_rows=384,
        maximum_source_chip_error=0.0,
        maximum_unitless_error=0.0,
        outputs={
            str(p.relative_to(folder)): digest(p)
            for p in folder.rglob("*")
            if p.is_file()
        },
    )
    (folder / "manifest.json").write_bytes(canonical(m))
    return folder


def test_canonical_schema_and_all_local_csv_identities(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = cache(tmp_path, monkeypatch)
    profiles = io.load(tmp_path, folder)
    assert len(profiles) == 24 and len(runner.csv_rows(profiles)) == 384
    d = io.load_detail(folder, profiles[0])
    assert len(d["responses"]) == 2
    for target in (0, 1):
        for s, full in zip(
            profiles[0]["responses"][target]["suffixes"],
            d["responses"][target]["suffixes"],
            strict=True,
        ):
            io.validate_suffix(s, full, 2)


@pytest.mark.parametrize(
    "change",
    [
        "missing_row",
        "duplicate_row",
        "weight",
        "posterior",
        "blocked",
        "q",
        "bool_q",
        "group",
        "group_cost",
        "display",
        "missing_panel",
        "nan",
    ],
)
def test_local_suffix_rejects_malformed_or_unaccounted_values(change: str) -> None:
    s, d = suffix(0, io.SUFFIXES[0])
    row = d["rows"][0]
    if change == "missing_row":
        d["rows"].clear()
    elif change == "duplicate_row":
        d["rows"].append(copy.deepcopy(row))
    elif change == "weight":
        row["uniform_decision_weight"] = 0.5
    elif change == "posterior":
        row["actual_posterior"] = [0.1, 0.1]
    elif change == "blocked":
        row["compatible"][0] = False
    elif change == "q":
        row["actual_action_values_chips"][0] = 3.0
    elif change == "bool_q":
        row["combo_action_values_chips"][0][0] = True
    elif change == "group":
        d["groups"][io.WEIGHTS[0]][io.GROUPS[0]][0]["infos"] = [99]
    elif change == "group_cost":
        d["groups"][io.WEIGHTS[1]][io.GROUPS[0]][0]["local_cost"] = 1.0
    elif change == "display":
        s["top_groups"] = []
    elif change == "missing_panel":
        s["panels"].pop()
    else:
        row["actual_action_values_chips"][0] = float("nan")
    with pytest.raises((ArithmeticError, ValueError, KeyError)):
        io.validate_suffix(s, d, 2)


@pytest.mark.parametrize(
    "change",
    [
        "bytes",
        "missing_hash",
        "duplicate_profile",
        "source_id",
        "missing_suffix",
        "bool_seat",
        "bool_coordinate",
        "row_total",
        "clock",
        "failure",
        "tmp",
    ],
)
def test_cached_inventory_rejects_tampering(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    folder = cache(tmp_path, monkeypatch)
    mpath = folder / "manifest.json"
    m = json.loads(mpath.read_text())
    if change == "bytes":
        (folder / "summary.json").write_text("edited")
    elif change == "missing_hash":
        del m["outputs"]["partial.json"]
    elif change == "row_total":
        m["suffix_river_rows"] = 95
    elif change == "clock":
        m["seconds"] = 901
    elif change == "failure":
        (folder / "failure.json").write_text("interrupted")
    elif change == "tmp":
        (folder / "left.tmp").write_text("partial")
    else:
        p = folder / "summary.json"
        data = json.loads(p.read_text())
        profiles = data["profiles"]
        if change == "duplicate_profile":
            profiles[-1] = copy.deepcopy(profiles[0])
        elif change == "source_id":
            profiles[-1]["source_id"] = profiles[0]["source_id"]
        elif change == "missing_suffix":
            profiles[0]["responses"][0]["suffixes"].pop()
        elif change == "bool_seat":
            profiles[0]["responses"][0]["target"] = False
        else:
            profiles[0]["coordinate"] = False
        p.write_bytes(canonical(data))
        m["outputs"]["summary.json"] = digest(p)
    mpath.write_bytes(canonical(m))
    with pytest.raises(ArithmeticError):
        io.load(tmp_path, folder)


def test_lazy_detail_rechecks_bytes_after_master_cache_load(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = cache(tmp_path, monkeypatch)
    p = io.load(tmp_path, folder)[0]
    (folder / p["details_file"]).write_bytes(b"edited after first hash pass")
    with pytest.raises(ArithmeticError, match="lazy"):
        io.load_detail(folder, p)


def test_actual_bound_prior_cache_and_wrong_pins(tmp_path: Path) -> None:
    c = io.contract(ROOT)
    assert len(io.prior(ROOT, c)) == 24
    for pin in (
        "continuation_manifest_sha256",
        "decision_config_sha256",
        "continuation_summary_sha256",
    ):
        changed = copy.deepcopy(c)
        changed[pin] = "0" * 64
        with pytest.raises(ArithmeticError):
            io.prior(ROOT, changed)
    p = tmp_path / io.CONFIG
    p.parent.mkdir()
    c["top_groups"] = 9
    p.write_text(json.dumps(c))
    with pytest.raises(ArithmeticError, match="frozen"):
        io.contract(tmp_path)


def test_view_prints_local_scope_and_navigates_both_suffixes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    folder = cache(tmp_path, monkeypatch)
    profiles = io.load(tmp_path, folder)
    d = io.load_detail(folder, profiles[0])
    view.show(profiles[0], d, 0, 0, 1)
    printed = capsys.readouterr().out
    assert "not a global strategy or root EV" in printed and "hypothetical" in printed
    with pytest.raises(ValueError, match="positive"):
        view.show(profiles[0], d, 0, 0, 0)
    monkeypatch.setattr(view, "load", lambda *a: profiles)
    monkeypatch.setattr(view, "load_detail", lambda f, p: io.load_detail(folder, p))
    shown = []
    monkeypatch.setattr(
        view,
        "show",
        lambda p, d, t, s, r: shown.append((p["game"], p["seed"], p["arm"], t, s, r)),
    )
    keys = iter(("n", "p", "s", "o", "g", "t", "r", "bad", "q"))
    monkeypatch.setattr("builtins.input", lambda prompt: next(keys))
    monkeypatch.setattr(sys, "argv", ["inspect", "--interactive"])
    assert view.main(tmp_path) == 0
    assert shown[0] == ("dev_medium_oop", 20261302, "mixed_pair", 1, 0, 1)
    assert shown[-1] == ("dev_low_oop", 20261303, "fine_self", 0, 1, 1)


@pytest.mark.parametrize(
    "factory",
    [
        "poker_ai.postflop.controlled_training.ControlledTrainer",
        "poker_ai.solver_validation.reference.Reference",
    ],
)
def test_preflight_blocks_learner_and_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, factory: str
) -> None:
    monkeypatch.setattr(runner, "contract", lambda r: dict(maximum_seconds=900))
    monkeypatch.setattr(
        runner,
        "source_provenance",
        lambda *a, **k: dict(dirty=False, sha256={"UNIT_ONLY": "a" * 64}),
    )

    def construct(*args: Any) -> Any:
        module, name = factory.rsplit(".", 1)
        return getattr(importlib.import_module(module), name)("UNIT_ONLY_NOT_A_GAME")

    monkeypatch.setattr(runner, "prior", construct)
    folder = tmp_path / "blocked"
    with pytest.raises(AssertionError, match="learner/reference"):
        runner.run(tmp_path, folder, time.perf_counter())
    f = json.loads((folder / "failure.json").read_text())
    assert f["completed_profiles"] == 0 and f["training_performed"] is False


def test_existing_output_preserved_before_any_preflight(tmp_path: Path) -> None:
    (tmp_path / "sentinel").write_text("keep")
    with pytest.raises(FileExistsError):
        runner.run(ROOT, tmp_path, time.perf_counter())
    assert (tmp_path / "sentinel").read_text() == "keep"
