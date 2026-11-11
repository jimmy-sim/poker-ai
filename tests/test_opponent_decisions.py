"""Read-only diagnosis tests; synthetic fixtures never admit poker learning."""

import copy
import itertools
import json
import time
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np
import pytest

from poker_ai.evaluation import opponent_decision_run as runner
from poker_ai.evaluation.opponent_decision_inputs import (
    CONFIG,
    CONFIG_SHA,
    contract,
    panel,
)
from poker_ai.evaluation.opponent_decision_math import (
    cross_policies,
    validate_cross,
    verify_trace,
)
from poker_ai.evaluation.opponent_learning_contexts import Contexts, software_context
from poker_ai.evaluation.opponent_learning_design import REAL, WORK, Design
from poker_ai.finite import FloatArray
from poker_ai.postflop.controlled_checkpoints import pack_policy
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.reply_trace import trace_losses
from poker_ai.postflop.river_study import digest

ROOT = Path(__file__).resolve().parents[1]
ARMS = ("coarse_self", "coarse_pair", "mixed_pair", "fine_self")


def source(
    context: Contexts, policy: FloatArray, identifier: str = "UNIT_ONLY"
) -> dict[str, Any]:
    return dict(
        id=identifier,
        **score_data(
            context.scoring["coarse"], context.scoring["coarse"].score(policy)
        ),
    )


def trace_fixture() -> tuple[Contexts, dict[str, Any], dict[str, Any], dict[str, Any]]:
    context = software_context(0)
    policy = np.array([[0.0, 1.0], [0.5, 0.5]])
    previous = source(context, policy)
    score = context.scoring["coarse"].score(policy)
    expanded = context.scoring["coarse"].expand(policy)
    responses, details = [], []
    for target in (0, 1):
        trace = trace_losses(context.fine, expanded, target, tolerance=1e-9)
        old = previous["responses"][target]
        infos = [int(i) for i in np.flatnonzero(context.fine.owners == target)]
        groups = sorted({int(context.mapping[i]) for i in infos})
        responses.append(
            dict(
                target=target,
                baseline_value_chips=old["baseline_value_chips"],
                exact_reply_value_chips=old["exact_reply_value_chips"],
                restricted_reply_value_chips=old["restricted_reply_value_chips"],
                within_partition_gain_chips=old["within_partition_gain_chips"],
                extra_information_value_chips=old["extra_information_gap_chips"],
                exact_gain_chips=trace.gain,
                loss_sum_chips=float(trace.losses.sum()),
                accounting_error_chips=trace.accounting_error,
                street_losses_chips={"RIVER": float(trace.losses.sum())},
                top_groups=[
                    dict(
                        abstract_info=g,
                        loss_contribution_chips=sum(
                            float(trace.losses[i])
                            for i in infos
                            if context.mapping[i] == g
                        ),
                    )
                    for g in groups
                ],
            )
        )
        details.append(
            dict(
                target=target,
                exact_reply_profile=pack_policy(context.fine, trace.profile),
                restricted_reply_profile=pack_policy(
                    context.fine, score.replies[target]["restricted"]
                ),
                infos=[
                    dict(
                        exact_info=i,
                        abstract_info=int(context.mapping[i]),
                        loss_chips=float(trace.losses[i]),
                        counterfactual_mass=float(trace.counterfactual_mass[i]),
                        saved_reach_mass=float(trace.saved_reach_mass[i]),
                        conditional_values_chips=trace.conditional_values[
                            i, :2
                        ].tolist(),
                    )
                    for i in infos
                ],
            )
        )
    summary = dict(
        exact_exploitability_chips=score.metrics["exact_exploitability_chips"],
        restricted_exploitability_chips=score.metrics["within_partition_gain_chips"],
        extra_information_chips=score.metrics["extra_information_gap_chips"],
        saved_value_player_zero_chips=score.metrics["value_player_zero_chips"],
        responses=responses,
    )
    return context, summary, dict(responses=details), previous


def verify(
    context: Contexts,
    summary: dict[str, Any],
    detail: dict[str, Any],
    previous: dict[str, Any],
) -> float:
    return verify_trace(
        summary,
        detail,
        previous,
        [int(x) for x in context.fine.owners],
        [2] * 4,
        context.mapping.tolist(),
        ["RIVER"] * 4,
        1e-9,
    )


def test_full_trace_matches_analytic_gap_and_accounts_all_rows() -> None:
    context, summary, detail, previous = trace_fixture()
    assert summary["exact_exploitability_chips"] == 0.5
    assert summary["restricted_exploitability_chips"] == 0.0
    assert verify(context, summary, detail, previous) == 0.0


@pytest.mark.parametrize(
    "change",
    [
        "missing",
        "duplicate",
        "loss",
        "street",
        "reply",
        "source",
        "negative_reach",
        "menu",
        "bool_info",
        "nan",
    ],
)
def test_trace_rejects_incomplete_or_inconsistent_details(change: str) -> None:
    context, summary, detail, previous = trace_fixture()
    rows = detail["responses"][0]["infos"]
    if change == "missing":
        rows.pop()
    elif change == "duplicate":
        rows.append(copy.deepcopy(rows[0]))
    elif change == "loss":
        rows[0]["loss_chips"] += 0.1
    elif change == "street":
        summary["responses"][0]["street_losses_chips"]["RIVER"] += 1
    elif change == "reply":
        detail["responses"][0]["exact_reply_profile"][0] = [0.5, 0.5]
    elif change == "source":
        previous["metrics"]["value_player_zero_chips"] += 1
    elif change == "negative_reach":
        rows[0]["saved_reach_mass"] = -1
    elif change == "menu":
        rows[0]["conditional_values_chips"].pop()
    elif change == "bool_info":
        rows[0]["exact_info"] = False
    else:
        rows[0]["loss_chips"] = float("nan")
    with pytest.raises((ArithmeticError, ValueError)):
        verify(context, summary, detail, previous)


def cross_fixture() -> list[dict[str, Any]]:
    context = software_context(0)
    policies = [np.array([[0.0, 1.0], [0.5, 0.5]]), np.array([[1.0, 0.0], [0.5, 0.5]])]
    own = {a: source(context, policies[i % 2], a) for i, a in enumerate(ARMS)}
    fine = {
        a: context.scoring["coarse"].expand(policies[i % 2]) for i, a in enumerate(ARMS)
    }
    return cross_policies(
        context.fine, fine, own, dict(coordinate=0, game="UNIT_ONLY", seed=1), 1e-9
    )


def test_common_opponent_crosses_preserve_nonzero_diagonal_and_zero_sum() -> None:
    rows = cross_fixture()
    assert len(rows) == 32
    lookup = {(r["candidate"], r["opponent"], r["target"]): r for r in rows}
    # A strategy against its own other seat can be exploitable: not a zero-gap test.
    assert (
        sum(lookup[ARMS[0], ARMS[0], t]["unilateral_gain_chips"] for t in (0, 1)) / 2
        == 0.5
    )
    for a, b, target in itertools.product(ARMS, ARMS, (0, 1)):
        assert (
            lookup[a, b, target]["target_ev_chips"]
            == -lookup[b, a, 1 - target]["target_ev_chips"]
        )
        # Arms0/2 are identical targets; fix the SAME opponent when comparing EV.
        assert (
            lookup[ARMS[0], b, target]["target_ev_chips"]
            == lookup[ARMS[2], b, target]["target_ev_chips"]
        )


@pytest.mark.parametrize(
    "change", ["missing", "duplicate", "ev", "gain", "reply", "bool_target", "nan"]
)
def test_cross_schema_and_accounting_fail_closed(change: str) -> None:
    rows = cross_fixture()
    if change == "missing":
        rows.pop()
    elif change == "duplicate":
        rows[-1] = copy.deepcopy(rows[0])
    elif change == "ev":
        rows[0]["target_ev_chips"] += 1
    elif change == "gain":
        rows[0]["unilateral_gain_chips"] += 1
    elif change == "reply":
        rows[0]["best_reply_value_chips"] += 1
    elif change == "bool_target":
        rows[0]["target"] = False
    else:
        rows[0]["target_ev_chips"] = float("nan")
    with pytest.raises((ArithmeticError, ValueError)):
        validate_cross(rows, ARMS, 1e-9)


def test_panel_uses_all_games_seeds_arms_and_rejects_source_inventory_changes() -> None:
    config = contract(ROOT)
    manifest = Design(REAL, WORK).manifest()
    own = dict(arms=manifest["arms"], rows=manifest["profiles"])
    result = panel(config, own)
    assert len(result) == 24
    assert {(x["game"], x["seed"], x["arm"]) for x in result} == set(
        itertools.product(config["games"], config["seeds"], config["arms"])
    )
    own["rows"].pop()
    with pytest.raises(ArithmeticError):
        panel(config, own)


def test_frozen_contract_cannot_be_silently_changed(tmp_path: Path) -> None:
    path = tmp_path / CONFIG
    path.parent.mkdir(parents=True)
    data = json.loads((ROOT / CONFIG).read_text())
    data["seeds"].pop()
    path.write_text(json.dumps(data))
    with pytest.raises(ArithmeticError, match="frozen"):
        contract(tmp_path)


def test_existing_output_is_preserved_before_loading_any_input(tmp_path: Path) -> None:
    output = tmp_path / "keep"
    output.mkdir()
    (output / "raw.txt").write_text("retained")
    with patch.object(runner, "contract", side_effect=AssertionError("must not load")):
        with pytest.raises(FileExistsError):
            runner.run(tmp_path, output, time.perf_counter())
    assert (output / "raw.txt").read_text() == "retained"


@pytest.mark.parametrize(
    "factory",
    [
        "poker_ai.postflop.batch_reduction.ReducedDispatchBatchTrainer",
        "poker_ai.solver_validation.reference.Reference",
    ],
)
def test_source_preflight_cannot_construct_learner_or_reference(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, factory: str
) -> None:
    import importlib

    monkeypatch.setattr(runner, "contract", lambda r: dict(maximum_seconds=900))
    monkeypatch.setattr(
        runner,
        "source_provenance",
        lambda *a, **k: dict(dirty=False, sha256={"UNIT": "a" * 64}),
    )

    def construct(*args: Any) -> Any:
        module, name = factory.rsplit(".", 1)
        kind: Any = getattr(importlib.import_module(module), name)
        return kind("UNIT_ONLY_NOT_A_GAME")

    monkeypatch.setattr(runner, "checked", construct)
    output = tmp_path / "blocked"
    with pytest.raises(AssertionError, match="learner/reference"):
        runner.run(tmp_path, output, time.perf_counter())
    failure = json.loads((output / "failure.json").read_text())
    assert failure["completed_profiles"] == 0
    assert failure["training_performed"] is failure["reference_constructed"] is False


def test_interruption_retains_completed_profile_before_advancing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from poker_ai.evaluation.averaging_history_artifacts import array_sha
    from poker_ai.evaluation.opponent_decision_inputs import Profile
    from poker_ai.evaluation.opponent_learning_sources import build_game
    from poker_ai.postflop.reply_diagnosis import analyse as actual

    # Real own finite-game math on a uniform UNIT fixture, not a learner run.
    context = build_game(ROOT, 0)
    policy = context.coarse.normalize(context.coarse.legal)
    old = source(context, policy, "UNIT_ONLY_UNIFORM_POLICY")
    old["receipt"] = dict(policy_sha256=array_sha(policy))
    old["origin"] = "UNIT_ONLY_COMPOSED_PROFILE"
    fine = context.scoring["coarse"].expand(policy)
    first = Profile(0, "dev_low_oop", 20261301, ARMS[0], old, context, policy, fine)
    second = Profile(0, "dev_low_oop", 20261301, ARMS[1], old, context, policy, fine)
    monkeypatch.setattr(runner, "contract", lambda r: contract(ROOT))
    monkeypatch.setattr(
        runner,
        "source_provenance",
        lambda *a, **k: dict(dirty=False, sha256={"UNIT": "a" * 64}),
    )
    monkeypatch.setattr(runner, "checked", lambda *a: {"unit_only": True})
    monkeypatch.setattr(runner, "profiles", lambda *a: [first, second])
    calls = 0

    def interrupted(*args: Any, **kwargs: Any) -> Any:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise KeyboardInterrupt("unit interruption after first complete trace")
        return actual(*args, **kwargs)

    monkeypatch.setattr(runner, "analyse", interrupted)
    output = tmp_path / "partial"
    with pytest.raises(KeyboardInterrupt):
        runner.run(ROOT, output, time.perf_counter())
    saved = json.loads((output / "partial.json").read_text())
    assert len(saved["profiles"]) == 1
    assert saved["profiles"][0]["source_id"] == "UNIT_ONLY_UNIFORM_POLICY"
    assert (output / "details/00-coarse_self.json.gz").is_file()
    assert not (output / "details/00-coarse_pair.json.gz").exists()
    assert json.loads((output / "failure.json").read_text())["completed_profiles"] == 1


def cached_fixture(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    from poker_ai.evaluation import opponent_decision_view as view

    # IO/schema test only: source/publication inputs are explicitly mocked.
    # These synthetic records are never scientific evidence or a compute permit.
    config = copy.deepcopy(contract(ROOT))
    for name in ("own", "native"):
        config[name] = f"unit/{name}.json"
        path = tmp_path / config[name]
        path.parent.mkdir(exist_ok=True)
        path.write_text("UNIT_ONLY_NOT_A_STUDY")
        config[name + "_sha256"] = digest(path)
    monkeypatch.setattr(view, "contract", lambda r: config)
    monkeypatch.setattr(view, "check_source", lambda *a: None)
    monkeypatch.setattr(view, "input_pins", lambda *a: {})
    output = tmp_path / "cache"
    output.mkdir()
    summaries, crosses = [], []
    original = cross_fixture()
    for coordinate, (game, seed) in enumerate(
        itertools.product(config["games"], config["seeds"])
    ):
        for arm in ARMS:
            summaries.append(
                dict(
                    game=game,
                    seed=seed,
                    arm=arm,
                    responses=[dict(target=t, top_groups=[]) for t in (0, 1)],
                )
            )
            path = output / f"details/{coordinate:02d}-{arm}.json.gz"
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(b"UNIT_ONLY_DETAIL")
        for row in original:
            crosses.append(dict(row, coordinate=coordinate, game=game, seed=seed))
    (output / "summary.json").write_text(json.dumps(dict(profiles=summaries)))
    (output / "cross.json").write_text(json.dumps(dict(conditions=crosses)))
    for name in ("cross.csv", "partial.json", "partial-cross.json"):
        (output / name).write_text("UNIT_ONLY")
    source_map = {"UNIT_ONLY": "a" * 64}
    manifest = dict(
        status="complete_own_opponent_decisions",
        config_sha256=CONFIG_SHA,
        profiles=24,
        responses=48,
        cross_conditions=192,
        constructors_blocked=True,
        training_performed=False,
        reference_constructed=False,
        independent_new_cross_audit=False,
        new_agent_default=False,
        fresh_global_admission=False,
        source=dict(sha256=source_map),
        source_sha256=sha(source_map),
        own_sha256=config["own_sha256"],
        native_sha256=config["native_sha256"],
        outputs={
            str(p.relative_to(output)): digest(p)
            for p in output.rglob("*")
            if p.is_file()
        },
    )
    (output / "manifest.json").write_text(json.dumps(manifest))
    return output


def test_cached_reader_checks_complete_panel_without_math_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from poker_ai.evaluation import opponent_decision_view as view
    from poker_ai.evaluation import opponent_learning_cli

    output = cached_fixture(tmp_path, monkeypatch)
    monkeypatch.setattr(
        opponent_learning_cli,
        "read",
        lambda *a: pytest.fail("cache invoked full replay"),
    )
    profiles, crosses = view.load(tmp_path, output)
    assert len(profiles) == 24 and len(crosses) == 192


@pytest.mark.parametrize(
    "change",
    [
        "bytes",
        "input",
        "missing_hash",
        "duplicate_profile",
        "missing_cross",
        "failure",
        "temporary",
    ],
)
def test_cached_reader_rejects_tamper_or_partial_inventory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, change: str
) -> None:
    from poker_ai.evaluation import opponent_decision_view as view

    output = cached_fixture(tmp_path, monkeypatch)
    manifest_path = output / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    if change == "bytes":
        (output / "summary.json").write_text("edited")
    elif change == "input":
        (tmp_path / "unit/own.json").write_text("edited")
    elif change == "missing_hash":
        del manifest["outputs"]["summary.json"]
        manifest_path.write_text(json.dumps(manifest))
    elif change == "failure":
        (output / "failure.json").write_text("interrupted after final manifest")
    elif change == "temporary":
        (output / "raw.tmp").write_text("partial bytes")
    else:
        name = "summary.json" if change == "duplicate_profile" else "cross.json"
        data = json.loads((output / name).read_text())
        if change == "duplicate_profile":
            data["profiles"][-1] = copy.deepcopy(data["profiles"][0])
        else:
            data["conditions"].pop()
        (output / name).write_text(json.dumps(data))
        manifest["outputs"][name] = digest(output / name)
        manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ArithmeticError):
        view.load(tmp_path, output)


def test_interactive_browser_cycles_cached_dimensions_and_quits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import sys

    from poker_ai.evaluation import opponent_decision_view as view

    output = cached_fixture(tmp_path, monkeypatch)
    profiles, crosses = view.load(tmp_path, output)
    monkeypatch.setattr(view, "load", lambda *a: (profiles, crosses))
    shown: list[tuple[str, int, str, int, int]] = []

    def record(profile: dict[str, Any], pairs: Any, seat: int, rank: int) -> None:
        shown.append((profile["game"], profile["seed"], profile["arm"], seat, rank))

    monkeypatch.setattr(view, "show", record)
    commands = iter(("n", "p", "s", "o", "g", "t", "q"))
    monkeypatch.setattr("builtins.input", lambda prompt: next(commands))
    monkeypatch.setattr(sys, "argv", ["inspect", "--interactive"])
    assert view.main(tmp_path) == 0
    assert shown[0] == ("dev_medium_oop", 20261302, "mixed_pair", 0, 1)
    assert shown[-1] == ("dev_low_oop", 20261303, "fine_self", 1, 1)
    assert len(shown) == 7


def test_invalid_rank_is_rejected_even_for_an_empty_display() -> None:
    from poker_ai.evaluation import opponent_decision_view as view

    profile: dict[str, Any] = dict(responses=[dict(top_groups=[]), dict(top_groups=[])])
    with pytest.raises(ValueError, match="positive group rank"):
        view.show(profile, [], 0, 0)
