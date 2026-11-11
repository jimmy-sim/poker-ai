"""Frozen input, complete cache and failure-retention controls; UNIT only."""

import copy
import gzip
import importlib
import itertools
import json
import sys
import time
from pathlib import Path
from typing import Any, cast

import pytest

from poker_ai.evaluation import turn_continuation_io as io
from poker_ai.evaluation import turn_continuation_run as runner
from poker_ai.evaluation import turn_continuation_view as view
from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.opponent_decision_inputs import Profile
from poker_ai.evaluation.opponent_learning_sources import build_game
from poker_ai.evaluation.turn_continuation_math import PANELS
from poker_ai.postflop.learning_artifacts import canonical, sha
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.reply_diagnosis import analyse
from poker_ai.postflop.river_study import digest

ROOT = Path(__file__).resolve().parents[1]


def response() -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Explicit software schema fixture, never measured poker evidence."""
    rows = [
        dict(
            exact_info=0,
            abstract_info=0,
            hole=["UNIT", "ONLY"],
            board=[],
            street="TURN",
            hand_category="UNIT",
            pot=0,
            history=[],
            actions=["fold", "call"],
            saved_probabilities=[0.5, 0.5],
            support=1.0,
            saved_reach_mass=1.0,
            prior_loss_chips=1.0,
            conditional_action_values_chips=dict(
                zip(
                    PANELS,
                    ([0.0, 0.5], [0.0, 1.0], [0.0, 4.0], [0.0, 4.0]),
                    strict=True,
                )
            ),
        )
    ]
    summary = dict(
        target=0,
        root_values_chips=dict(zip(PANELS, (0.25, 0.5, 2.0, 4.0), strict=True)),
        root_increments_chips=[0.25, 1.5, 2.0],
        source_unilateral_gain_chips=3.75,
        turn_info_ids=[0],
        supported_turn_rows=1,
        top_turn_groups=[dict(abstract_info=0, infos=[0], prior_loss_chips=1.0)],
    )
    return summary, rows


def test_canonical_round_trip_keeps_panel_meaning_despite_sorted_keys() -> None:
    s, rows = response()
    a, b = json.loads(canonical([s, rows]))
    io.validate_response(a, b)
    assert list(a["root_values_chips"]) != list(PANELS)


@pytest.mark.parametrize(
    "change",
    [
        "missing_row",
        "duplicate_row",
        "root",
        "stage",
        "missing_panel",
        "support",
        "menu",
        "zero_support",
        "nan",
        "bool_target",
        "bool_info",
        "group",
    ],
)
def test_response_rejects_bad_accounting_inventory_or_support(change: str) -> None:
    s, rows = response()
    if change == "missing_row":
        rows.clear()
    elif change == "duplicate_row":
        rows.append(copy.deepcopy(rows[0]))
    elif change == "root":
        s["root_values_chips"]["fine_river"] += 1
    elif change == "stage":
        s["root_increments_chips"][0] = -1
    elif change == "missing_panel":
        del rows[0]["conditional_action_values_chips"]["saved"]
    elif change == "support":
        rows[0]["support"] = -1
    elif change == "menu":
        rows[0]["conditional_action_values_chips"]["saved"].pop()
    elif change == "zero_support":
        rows[0]["support"] = 0
    elif change == "nan":
        rows[0]["conditional_action_values_chips"]["saved"][0] = float("nan")
    elif change == "bool_target":
        s["target"] = False
    elif change == "bool_info":
        rows[0]["exact_info"] = False
    else:
        s["top_turn_groups"][0]["infos"] = [99]
    with pytest.raises((ArithmeticError, ValueError)):
        io.validate_response(s, rows)


def test_frozen_protocol_rejects_even_an_unregistered_display_change(
    tmp_path: Path,
) -> None:
    assert io.contract(ROOT)["expected_root_values"] == 192
    p = tmp_path / io.CONFIG
    p.parent.mkdir(parents=True)
    config = io.contract(ROOT)
    config["top_turn_groups"] = 9
    p.write_text(json.dumps(config))
    with pytest.raises(ArithmeticError, match="frozen"):
        io.contract(tmp_path)


def test_actual_published_prior_cache_is_bound_without_new_training() -> None:
    result = io.prior(ROOT, io.contract(ROOT))
    assert len(result) == 24
    assert sum(len(p["responses"]) for p in result) == 48


@pytest.mark.parametrize(
    "pin",
    ["decision_manifest_sha256", "decision_summary_sha256", "decision_config_sha256"],
)
def test_prior_reader_rejects_changed_input_pin(pin: str) -> None:
    config = io.contract(ROOT)
    config[pin] = "0" * 64
    with pytest.raises(ArithmeticError, match="bound prior"):
        io.prior(ROOT, config)


def cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    # Mocked source/publication inputs for IO only, NOT a scientific receipt.
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
                s, rows = response()
                s["target"] = target
                responses.append(s)
                details.append(dict(target=target, turn_rows=rows))
            name = f"details/{coordinate:02d}-{arm}.json.gz"
            (folder / name).write_bytes(
                gzip.compress(canonical(dict(**identity, responses=details)), mtime=0)
            )
            profiles.append(dict(**identity, responses=responses, details_file=name))
    (folder / "summary.json").write_bytes(canonical(dict(profiles=profiles)))
    (folder / "partial.json").write_text("UNIT_ONLY")
    source = dict(UNIT_ONLY="a" * 64)
    manifest = dict(
        status="complete_fixed_turn_continuations",
        config_sha256=io.CONFIG_SHA,
        source=dict(sha256=source),
        source_sha256=sha(source),
        profiles=24,
        responses=48,
        root_values=192,
        turn_rows=48,
        constructors_blocked=True,
        maximum_seconds=900,
        seconds=1,
        training_performed=False,
        reference_constructed=False,
        new_independent_audit=False,
        new_agent_default=False,
        fresh_global_admission=False,
        decision_manifest_sha256=config["decision_manifest_sha256"],
        outputs={
            str(p.relative_to(folder)): digest(p)
            for p in folder.rglob("*")
            if p.is_file()
        },
    )
    (folder / "manifest.json").write_bytes(canonical(manifest))
    return folder


def test_cached_reader_checks_all_profiles_without_mathematical_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = cache(tmp_path, monkeypatch)
    monkeypatch.setattr(
        runner, "checked", lambda *a: pytest.fail("cache reran source math")
    )
    result = io.load(tmp_path, folder)
    assert len(result) == 24
    assert sum(len(p["responses"]) for p in result) == 48
    assert all(
        r["turn_rows"][0]["support"] == 1 for p in result for r in p["responses"]
    )


@pytest.mark.parametrize(
    "change",
    [
        "bytes",
        "missing_hash",
        "failure",
        "tmp",
        "clock",
        "turn_total",
        "duplicate_profile",
        "missing_response",
        "coordinate",
        "detail_seat",
        "detail_identity",
    ],
)
def test_cached_reader_rejects_tampering_and_incomplete_panels(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    folder = cache(tmp_path, monkeypatch)
    mpath = folder / "manifest.json"
    m = json.loads(mpath.read_text())
    if change == "bytes":
        (folder / "summary.json").write_text("edited")
    elif change == "missing_hash":
        del m["outputs"]["partial.json"]
    elif change == "failure":
        (folder / "failure.json").write_text("interrupted")
    elif change == "tmp":
        (folder / "left.tmp").write_text("unfinished")
    elif change == "clock":
        m["seconds"] = 901
    elif change == "turn_total":
        m["turn_rows"] = 47
    elif change.startswith("detail"):
        name = "details/00-coarse_self.json.gz"
        data = json.loads(gzip.decompress((folder / name).read_bytes()))
        if change == "detail_seat":
            data["responses"][1]["target"] = 0
        else:
            data["source_id"] = "WRONG_UNIT_ID"
        (folder / name).write_bytes(gzip.compress(canonical(data), mtime=0))
        m["outputs"][name] = digest(folder / name)
    else:
        p = folder / "summary.json"
        data = json.loads(p.read_text())
        if change == "duplicate_profile":
            data["profiles"][-1] = copy.deepcopy(data["profiles"][0])
        elif change == "missing_response":
            data["profiles"][0]["responses"].pop()
        else:
            data["profiles"][0]["coordinate"] = True
        p.write_bytes(canonical(data))
        m["outputs"]["summary.json"] = digest(p)
    mpath.write_bytes(canonical(m))
    with pytest.raises(ArithmeticError):
        io.load(tmp_path, folder)


def test_browser_navigation_and_rank_guard(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = cache(tmp_path, monkeypatch)
    profiles = io.load(tmp_path, folder)
    monkeypatch.setattr(view, "load", lambda *a: profiles)
    shown = []
    monkeypatch.setattr(
        view,
        "show",
        lambda p, s, r: shown.append((p["game"], p["seed"], p["arm"], s, r)),
    )
    keys = iter(("n", "p", "s", "o", "g", "t", "bad", "q"))
    monkeypatch.setattr("builtins.input", lambda prompt: next(keys))
    monkeypatch.setattr(sys, "argv", ["inspect", "--interactive"])
    assert view.main(tmp_path) == 0
    assert shown[0] == ("dev_medium_oop", 20261302, "mixed_pair", 1, 1)
    assert shown[-1] == ("dev_low_oop", 20261303, "fine_self", 0, 1)


def test_real_view_explains_four_panels_and_rejects_bad_rank(
    capsys: pytest.CaptureFixture[str],
) -> None:
    s, rows = response()
    s["turn_rows"] = rows
    p = dict(game="UNIT_ONLY", seed=1, arm="UNIT_ONLY", responses=[s])
    view.show(p, 0, 1)
    output = capsys.readouterr().out
    assert all(name in output for name in PANELS)
    assert "not additive losses" in output and "no new native audit" in output
    with pytest.raises(ValueError, match="positive"):
        view.show(p, 0, 0)


@pytest.mark.parametrize(
    "factory",
    [
        "poker_ai.postflop.controlled_training.ControlledTrainer",
        "poker_ai.solver_validation.reference.Reference",
    ],
)
def test_preflight_blocks_training_and_reference_construction(
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
    failure = json.loads((folder / "failure.json").read_text())
    assert failure["completed_profiles"] == 0 and failure["training_performed"] is False


def test_existing_destination_is_preserved_before_preflight(tmp_path: Path) -> None:
    (tmp_path / "sentinel").write_text("keep")
    with pytest.raises(FileExistsError):
        runner.run(ROOT, tmp_path, time.perf_counter())
    assert (tmp_path / "sentinel").read_text() == "keep"


@pytest.fixture(scope="module")
def uniform_case() -> tuple[Profile, dict[str, Any], dict[str, Any]]:
    # Genuine own low-SPR mechanics with an analytic uniform UNIT policy.
    # There is no trainer, imported reference policy or scientific study here.
    context = build_game(ROOT, 0)
    policy = context.coarse.normalize(context.coarse.legal)
    row = dict(
        id="UNIT_ONLY_UNIFORM",
        **score_data(
            context.scoring["coarse"], context.scoring["coarse"].score(policy)
        ),
        origin="UNIT_ONLY_COMPOSED_PROFILE",
        receipt=dict(policy_sha256=array_sha(policy)),
    )
    fine = context.scoring["coarse"].expand(policy)
    profile = Profile(
        0, "dev_low_oop", 20261301, "coarse_self", row, context, policy, fine
    )
    summary, detail = analyse(
        cast(MatrixTree, context.fine),
        cast(MatrixTree, context.coarse),
        fine,
        top=10,
        examples=4,
        tolerance=1e-9,
    )
    return profile, json.loads(canonical(summary)), json.loads(canonical(detail))


def test_genuine_uniform_own_trace_validates_every_turn_menu(
    uniform_case: tuple[Profile, dict[str, Any], dict[str, Any]],
) -> None:
    p, s, d = uniform_case
    result, detail = runner.analyse_profile(p, s, d, io.contract(ROOT))
    for response, full in zip(result["responses"], detail["responses"], strict=True):
        io.validate_response(response, full["turn_rows"])
        assert (
            response["turn_info_ids"]
            and response["maximum_source_accounting_error_chips"] < 1e-9
        )


@pytest.mark.parametrize("change", ["root", "reply", "turn_value", "missing_row"])
def test_genuine_trace_rejects_changed_source(
    uniform_case: tuple[Profile, dict[str, Any], dict[str, Any]], change: str
) -> None:
    p, old_s, old_d = uniform_case
    s, d = copy.deepcopy(old_s), copy.deepcopy(old_d)
    if change == "root":
        s["responses"][0]["baseline_value_chips"] += 1
    elif change == "reply":
        d["responses"][0]["exact_reply_profile"][0].reverse()
    elif change == "turn_value":
        d["responses"][0]["infos"][0]["conditional_values_chips"][0] += 1
    else:
        d["responses"][0]["infos"].pop()
    with pytest.raises((ArithmeticError, ValueError)):
        runner.analyse_profile(p, s, d, io.contract(ROOT))


def test_interruption_retains_first_completed_genuine_profile(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    uniform_case: tuple[Profile, dict[str, Any], dict[str, Any]],
) -> None:
    p, s, d = uniform_case
    config = io.contract(ROOT)
    old_file = tmp_path / "unit-old-detail.json.gz"
    old_file.write_bytes(gzip.compress(canonical(d), mtime=0))
    previous = dict(s, source_id=p.row["id"], details_file=str(old_file))
    monkeypatch.setattr(runner, "contract", lambda r: config)
    monkeypatch.setattr(
        runner,
        "source_provenance",
        lambda *a, **k: dict(dirty=False, sha256={"UNIT_ONLY": "a" * 64}),
    )
    monkeypatch.setattr(runner, "prior", lambda *a: [previous])
    monkeypatch.setattr(runner, "checked", lambda *a: {"unit_only": True})
    monkeypatch.setattr(runner, "profiles", lambda *a: [p, p])
    actual = runner.analyse_profile
    calls = 0

    def interrupted(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise KeyboardInterrupt("UNIT interruption after first complete profile")
        return actual(*args, **kwargs)

    monkeypatch.setattr(runner, "analyse_profile", interrupted)
    folder = tmp_path / "partial"
    with pytest.raises(KeyboardInterrupt):
        runner.run(ROOT, folder, time.perf_counter())
    assert len(json.loads((folder / "partial.json").read_text())["profiles"]) == 1
    assert (folder / "details/00-coarse_self.json.gz").is_file()
    assert json.loads((folder / "failure.json").read_text())["completed_profiles"] == 1
