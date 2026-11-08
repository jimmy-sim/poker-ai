"""Saved-policy math/IO and native integration; no training or benchmark claims."""

import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.postflop import pipeline_cost as own
from poker_ai.postflop.controlled_checkpoints import pack_policy
from poker_ai.postflop.controlled_training import ControlledTrainer
from poker_ai.postflop.pipeline_render import SCOPE, planned_rows

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def old_profiles() -> tuple[Any, ...]:
    config = json.loads((ROOT / own.CONFIG).read_text())
    cases, protocol, training = own.inputs(ROOT, config)
    contexts = own.contexts(ROOT, protocol["future_comparison"])
    details = []
    for index, case in enumerate(cases):
        context = contexts[case["spot_file"], case["representation"]]
        policy = own.source_policy(context, case)
        score = context.score(policy)
        details.append(
            dict(
                case={k: case[k] for k in own.CASE},
                policy=pack_policy(context.partition, policy),
                metrics=score.metrics,
                responses=score.responses,
                replies=[
                    {k: pack_policy(context.exact, v) for k, v in row.items()}
                    for row in score.replies
                ],
                maximum_accounting_error=score.maximum_accounting_error,
                index=index,
            )
        )
    return config, cases, protocol, training, contexts, details


@pytest.mark.slow
def test_all_sixteen_profiles_match_existing_published_own_metrics(
    old_profiles: tuple[Any, ...],
) -> None:
    _, cases, _, _, _, details = old_profiles
    assert len(cases) == len(details) == 16
    for case, detail in zip(cases, details, strict=True):
        assert (
            max(
                abs(detail["metrics"][k] - v) for k, v in case["source_metrics"].items()
            )
            <= 1e-9
        )
        assert detail["maximum_accounting_error"] <= 1e-9
        if case["representation"] == "exact":
            assert detail["metrics"]["extra_information_gap_chips"] == 0
            assert detail["metrics"]["river_only_gain_exact_prefix_chips"] == 0


@pytest.mark.slow
def test_own_job_roundtrips_real_old_profiles_without_any_training(
    old_profiles: tuple[Any, ...], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    config, cases, protocol, _, _, _ = old_profiles

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("calibration must not train")

    monkeypatch.setattr(ControlledTrainer, "step", forbidden)
    monkeypatch.setattr(ControlledTrainer, "initialize_exact", forbidden)
    events: list[dict[str, Any]] = []
    result = own.own_job(
        0,
        [0, 15],
        dict(
            root=str(ROOT),
            config=config,
            cases=cases,
            comparison=protocol["future_comparison"],
            remaining_seconds=30,
            scratch=str(tmp_path),
            repeat=0,
        ),
        events.append,
    )
    assert result == dict(cells=2)
    assert [e["kind"] for e in events] == ["prepared", "cell", "cell"]
    assert [e["index"] for e in events[1:]] == [0, 15]
    for event in events[1:]:
        assert event["row"]["seconds"] > 0
        assert event["row"]["receipt"]["bytes"] > 0
        assert "detail" in event


@pytest.mark.slow
def test_synthetic_reporting_fixture_labels_every_duplicate(
    old_profiles: tuple[Any, ...],
) -> None:
    _, _, protocol, _, _, details = old_profiles
    rows, profiles = planned_rows(protocol, details)
    assert len(rows) == len(profiles) == 840
    assert all(r["scope"] == SCOPE for r in [*rows, *profiles])
    assert len({r["planned_cell"] for r in rows}) == 140
    assert len({r["source_case"] for r in rows}) == 16
    assert {r["axis"] for r in rows} == {"work", "iteration"}
    assert all(
        len({r["target"] for r in rows if r["axis"] == a}) == 3
        for a in ("work", "iteration")
    )


@pytest.mark.slow
def test_native_checks_all_old_profiles_without_reference_strategy_export(
    old_profiles: tuple[Any, ...], monkeypatch: pytest.MonkeyPatch
) -> None:
    pytest.importorskip("pyspiel")
    from poker_ai.solver_validation import controlled_pipeline as native
    from poker_ai.solver_validation.reference import Reference

    config, _, _, _, contexts, details = old_profiles

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("reference actions/policies/training forbidden")

    monkeypatch.setattr(Reference, "train_to", forbidden)
    monkeypatch.setattr(Reference, "policy", forbidden)
    assert (
        native.license_record(config)["sha256"]
        == config["native_reference"]["license_sha256"]
    )
    references = native.references(contexts)
    for detail in details:
        key = detail["case"]["spot_file"], detail["case"]["representation"]
        result = native.compare_one(contexts[key], references[key], detail)
        assert result["maximum_error_chips"] <= 1e-9
        assert set(result) == {"native_metrics", "responses", "maximum_error_chips"}
        assert set(result["native_metrics"]) == set(own.METRICS)


@pytest.mark.slow
def test_context_projection_refuses_another_range_id(
    old_profiles: tuple[Any, ...],
) -> None:
    _, cases, _, _, contexts, _ = old_profiles
    case = {**cases[-1], "range_context_sha256": "0" * 64}
    with pytest.raises(ArithmeticError, match="range context"):
        own.source_policy(contexts[case["spot_file"], case["representation"]], case)


@pytest.mark.slow
def test_diagnostics_timing_fixture_cannot_modify_source_policy(
    old_profiles: tuple[Any, ...],
) -> None:
    _, cases, _, _, contexts, _ = old_profiles
    case = cases[-1]
    context = contexts[case["spot_file"], case["representation"]]
    policy = own.source_policy(context, case)
    before = policy.tobytes()
    own.observation_cost_fixture(context, policy)
    assert policy.tobytes() == before
    np.testing.assert_allclose(policy.sum(axis=1), 1, atol=1e-12)


@pytest.fixture(scope="module")
def fictional_receipts() -> tuple[Any, ...]:
    """EXPLICIT FICTIONAL timings/labels for schema tests, never run evidence."""
    import gzip
    import hashlib

    from poker_ai.postflop.cell_process import THREAD_ENV, partition
    from poker_ai.postflop.controlled_scoring import ScoringContext
    from poker_ai.toy.tree import Tree

    tree = Tree.build("kuhn")
    context = ScoringContext(
        tree,
        tree,
        np.arange(len(tree.keys)),
        (np.zeros(len(tree.keys), dtype=np.bool_),) * 2,
    )
    policy = tree.normalize(tree.legal)
    scored = context.score(policy)
    config = json.loads((ROOT / own.CONFIG).read_text())
    protocol = json.loads((ROOT / "configs/training-isolation.json").read_text())
    comparison = protocol["future_comparison"]
    cases: list[dict[str, Any]] = []
    profiles: list[dict[str, Any]] = []
    for game in sorted(comparison["spot_files"]):
        for name in sorted(comparison["representations"]):
            for seed in [None, *comparison["seeds"]]:
                case = dict(
                    spot_file=game,
                    representation=name,
                    training="full" if seed is None else "sampled",
                    seed=seed,
                    range_context_sha256=None if name == "exact" else "0" * 64,
                    policy=pack_policy(context.partition, policy),
                    source_metrics={
                        k: v
                        for k, v in scored.metrics.items()
                        if k != "river_only_gain_exact_prefix_chips"
                    },
                )
                cases.append(case)
                profiles.append(
                    dict(
                        case={k: case[k] for k in own.CASE},
                        metrics=scored.metrics,
                        responses=scored.responses,
                        replies=[
                            {k: pack_policy(context.exact, v) for k, v in row.items()}
                            for row in scored.replies
                        ],
                        maximum_accounting_error=scored.maximum_accounting_error,
                        policy=pack_policy(context.partition, policy),
                        index=len(profiles),
                    )
                )
    batches: list[dict[str, Any]] = []
    native_batches: list[dict[str, Any]] = []
    for repeat in range(3):
        for is_native, destination in ((False, batches), (True, native_batches)):
            workers: list[dict[str, Any]] = []
            for slot, indices in enumerate(partition(16, 3)):
                messages: list[dict[str, Any]] = [
                    dict(
                        kind="started", pid=1000 + slot, thread_environment=THREAD_ENV
                    ),
                    dict(kind="prepared", seconds=1.0),
                ]
                for index in indices:
                    detail = profiles[index]
                    metadata = {
                        k: detail[k]
                        for k in (
                            "case",
                            "metrics",
                            "responses",
                            "replies",
                            "maximum_accounting_error",
                        )
                    }
                    if is_native:
                        responses = [
                            dict(
                                target=t,
                                exact_root_chips=r["exact_reply_value_chips"],
                                restricted_root_chips=r["restricted_reply_value_chips"],
                                achieved_exact_chips=r["exact_reply_value_chips"],
                                achieved_restricted_chips=r[
                                    "restricted_reply_value_chips"
                                ],
                                achieved_river_before_chips=r[
                                    "river_before_value_chips"
                                ],
                            )
                            for t, r in enumerate(detail["responses"])
                        ]
                        row = dict(
                            index=index,
                            case=detail["case"],
                            native_metrics=detail["metrics"],
                            responses=responses,
                            maximum_error_chips=0.0,
                            seconds=0.1,
                            cpu_seconds=0.05,
                        )
                    else:
                        envelope = dict(
                            format="poker-ai-controlled-own-policy-snapshot-v1",
                            dtype="<f8",
                            shape=list(policy.shape),
                            actions=[list(a) for a in tree.actions],
                            metadata=metadata,
                            policy=pack_policy(context.partition, policy),
                        )
                        blob = gzip.compress(
                            json.dumps(
                                envelope,
                                sort_keys=True,
                                separators=(",", ":"),
                                allow_nan=False,
                            ).encode(),
                            mtime=0,
                        )
                        receipt = dict(
                            sha256=hashlib.sha256(blob).hexdigest(),
                            policy_sha256=hashlib.sha256(
                                policy.astype("<f8").tobytes()
                            ).hexdigest(),
                            bytes=len(blob),
                        )
                        row = dict(
                            index=index,
                            case=detail["case"],
                            metrics=detail["metrics"],
                            responses=detail["responses"],
                            accounting_error=detail["maximum_accounting_error"],
                            receipt=receipt,
                            metadata_sha256=hashlib.sha256(
                                json.dumps(
                                    metadata,
                                    sort_keys=True,
                                    separators=(",", ":"),
                                    allow_nan=False,
                                ).encode()
                            ).hexdigest(),
                            seconds=0.2,
                            cpu_seconds=0.1,
                        )
                    messages.append(dict(kind="cell", index=index, row=row))
                messages.append(
                    dict(
                        kind="done",
                        summary=dict(cells=len(indices)),
                        seconds=1.5 + len(indices) * (0.1 if is_native else 0.2),
                        cpu_seconds=1.0,
                    )
                )
                workers.append(
                    dict(slot=slot, pid=1000 + slot, exitcode=0, messages=messages)
                )
            destination.append(
                dict(
                    repeat=repeat,
                    worker_count=3,
                    assignments=partition(16, 3),
                    workers=workers,
                    status="completed",
                    failure=None,
                    seconds=max(w["messages"][-1]["seconds"] for w in workers) + 0.25,
                    parent_cpu_seconds=0.02,
                    reaped_children_cpu_seconds=2.2,
                )
            )
    fixtures = [
        dict(
            scope=SCOPE,
            rows=840,
            unique_source_profiles=16,
            figures=8,
            seconds=2.0,
            cpu_seconds=0.5,
            artifacts={str(i): dict(bytes=10, sha256="a" * 64) for i in range(11)},
        )
        for _ in range(3)
    ]
    saved = dict(
        config=config,
        batches=batches,
        fixtures=fixtures,
        seconds=sum(b["seconds"] for b in batches) + 10.0,
        parent_cpu_seconds=2.0,
        reaped_children_cpu_seconds=7.0,
    )
    native = dict(
        batches=native_batches,
        seconds=sum(b["seconds"] for b in native_batches) + 4.0,
        parent_cpu_seconds=1.0,
        reaped_children_cpu_seconds=7.0,
    )
    training = dict(
        forecasts={
            "3": dict(
                worker_training_seconds=[100.0, 110.0, 120.0],
                maximum_worker_nontraining_seconds=2.0,
                maximum_launch_collection_seconds=3.0,
            )
        }
    )
    return saved, native, cases, profiles, protocol, training, context, policy


def test_fictional_receipt_shapes_and_independent_cost_arithmetic(
    fictional_receipts: tuple[Any, ...],
) -> None:
    from poker_ai.postflop.pipeline_native_checks import validate_native
    from poker_ai.postflop.pipeline_report import native_forecast, own_forecast

    saved, native, cases, profiles, protocol, training, _, _ = fictional_receipts
    own.validate_batches(saved, cases)
    validate_native(native, saved, profiles, cases)
    estimate = own_forecast(saved, protocol, training)
    # 47/47/46 cells, six snapshots twice at .2s; training100/110/120.
    # Max230.4 + training overhead5 + worker1.5 + launch.25 + parent4 + IO2.
    assert estimate["worker_training_scoring_replay_seconds"] == pytest.approx(
        [212.8, 222.8, 230.4]
    )
    assert estimate["guarded_seconds"] == pytest.approx(486.3)
    native_estimate = native_forecast(saved, native, protocol)
    # Max native28.2 + SERIAL old-input replay168 + worker1.5+launch.25+parent4.
    assert native_estimate["serial_own_input_replay_seconds"] == pytest.approx(168)
    assert native_estimate["guarded_seconds"] == pytest.approx(403.9)
    assert estimate["training_admitted"] is False


@pytest.mark.parametrize(
    "change",
    ["repeat", "partition", "pid", "event", "index", "metric", "hash", "timer"],
)
def test_own_schema_rejects_changed_fictional_receipts(
    fictional_receipts: tuple[Any, ...], change: str
) -> None:
    import copy

    saved, _, cases, _, _, _, _, _ = fictional_receipts
    altered = copy.deepcopy(saved)
    batch = altered["batches"][0]
    worker = batch["workers"][0]
    event = worker["messages"][2]
    if change == "repeat":
        batch["repeat"] = False
    elif change == "partition":
        batch["assignments"][0][0] = 1
    elif change == "pid":
        worker["exitcode"] = -15
    elif change == "event":
        worker["messages"].pop()
    elif change == "index":
        event["index"] = True
    elif change == "metric":
        event["row"]["metrics"]["exact_exploitability_chips"] += 1
    elif change == "hash":
        event["row"]["metadata_sha256"] = "0" * 64
    else:
        event["row"]["seconds"] = -1
    with pytest.raises(ArithmeticError):
        own.validate_batches(altered, cases)


@pytest.mark.parametrize(
    "change",
    [
        "repeat",
        "partition",
        "pid",
        "event",
        "index",
        "metric",
        "root",
        "achieved",
        "error",
        "cpu",
    ],
)
def test_native_schema_rejects_changed_fictional_receipts(
    fictional_receipts: tuple[Any, ...], change: str
) -> None:
    import copy

    from poker_ai.postflop.pipeline_native_checks import validate_native

    saved, native, cases, profiles, _, _, _, _ = fictional_receipts
    altered = copy.deepcopy(native)
    batch = altered["batches"][0]
    worker = batch["workers"][0]
    event = worker["messages"][2]
    if change == "repeat":
        batch["repeat"] = False
    elif change == "partition":
        batch["assignments"][0][0] = 1
    elif change == "pid":
        worker["pid"] = 0
    elif change == "event":
        worker["messages"].pop()
    elif change == "index":
        event["row"]["index"] = True
    elif change == "metric":
        event["row"]["native_metrics"]["extra_information_gap_chips"] += 1
    elif change == "root":
        event["row"]["responses"][0]["exact_root_chips"] += 1
    elif change == "achieved":
        event["row"]["responses"][0]["achieved_river_before_chips"] += 1
    elif change == "error":
        event["row"]["maximum_error_chips"] = 1
    else:
        batch["reaped_children_cpu_seconds"] = float("nan")
    with pytest.raises(ArithmeticError):
        validate_native(altered, saved, profiles, cases)


def test_full_fictional_replay_binds_owned_values_and_rejects_forged_river_gap(
    fictional_receipts: tuple[Any, ...], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Fictional timings test file/schema replay; never a benchmark receipt."""
    import copy
    import gzip

    from poker_ai.postflop import pipeline_report as report
    from poker_ai.postflop.river_study import digest
    from poker_ai.validation.five_card import source_provenance

    saved0, native0, cases, profiles, protocol, training, context, policy = (
        fictional_receipts
    )
    saved, native = copy.deepcopy(saved0), copy.deepcopy(native0)
    source = source_provenance(ROOT, ROOT / own.CONFIG, entrypoints=own.ENTRIES)
    source["dirty"] = False  # EXPLICIT fictional schema fixture, never published.
    bundle = tmp_path / "synthetic-own-profiles.json.gz"
    bundle.write_bytes(
        gzip.compress(
            json.dumps(dict(format=own.DETAIL_FORMAT, profiles=profiles)).encode(),
            mtime=0,
        )
    )
    saved.update(
        format=own.FORMAT,
        status="completed",
        failure=None,
        source=source,
        training_performed=False,
        strength_comparison_performed=False,
        details_file=bundle.name,
        details_sha256=digest(bundle),
    )
    own_path = tmp_path / "synthetic-own.json"
    own_path.write_text(json.dumps(saved))
    native.update(
        format="poker-ai-saved-own-pipeline-native-cost-v1",
        status="completed",
        failure=None,
        input_sha256=digest(own_path),
        details_sha256=digest(bundle),
        reference=saved["config"]["native_reference"],
        source=source,
        training_performed=False,
        reference_actions_exported=False,
    )
    native_path = tmp_path / "synthetic-native.json"
    native_path.write_text(json.dumps(native))
    monkeypatch.setattr(own, "inputs", lambda root, config: (cases, protocol, training))
    monkeypatch.setattr(
        own,
        "contexts",
        lambda root, comparison: {
            (c["spot_file"], c["representation"]): context for c in cases
        },
    )
    monkeypatch.setattr(own, "source_policy", lambda ctx, case: policy.copy())
    result = report.summary(ROOT, own_path, native_path)
    assert result["training_admitted"] is False
    assert (
        result["decision"] == "forecasts_fit_requires_separate_checked_learning_runner"
    )
    assert result["own_forecast"]["guarded_seconds"] == pytest.approx(486.3)
    assert "No new learning" in report.tables(result)
    # A positive invented river number can pass simple sign checks; full replay
    # must still recompute the owned profiles and reject it.
    for event in own.cell_events(saved):
        event["row"]["metrics"]["river_only_gain_exact_prefix_chips"] += 0.25
    own_path.write_text(json.dumps(saved))
    with pytest.raises(ArithmeticError):
        report.replay_own(ROOT, own_path)


@pytest.mark.slow
def test_full_size_synthetic_render_is_labeled_and_round_trips(
    old_profiles: tuple[Any, ...], tmp_path: Path
) -> None:
    pytest.importorskip("matplotlib")
    import gzip

    from poker_ai.postflop.pipeline_render import fixture

    _, _, protocol, _, _, profiles = old_profiles
    output = tmp_path / "synthetic"
    result = fixture(ROOT, protocol, profiles, output)
    assert result["scope"] == SCOPE
    assert result["rows"] == 840 and result["figures"] == 8
    assert len(result["artifacts"]) == 11
    assert len(list(output.glob("*.png"))) == 8
    with gzip.open(output / "synthetic-840-profiles.jsonl.gz", "rt") as stream:
        header = json.loads(next(stream))
        assert header["scope"] == SCOPE and header["rows"] == 840
        assert sum(json.loads(line)["scope"] == SCOPE for line in stream) == 840
    assert "not new learning outcomes" in (output / "README.md").read_text()
