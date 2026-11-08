"""Complete artificial grids reject favorable subsets and false crossed identities."""

import copy
import itertools
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.evaluation import controlled_reply_compute as compute
from poker_ai.evaluation.controlled_reply_inputs import (
    Inputs,
    SourcePolicy,
    config_inputs,
    modes,
)
from poker_ai.finite import ArrayTree
from poker_ai.postflop.controlled_checkpoints import pack_policy
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.river_study import Deadline

ROOT = Path(__file__).resolve().parents[1]


def asymmetric() -> ArrayTree:
    children = np.zeros((7, 2), dtype=np.int64)
    children[0], children[1], children[4] = (1, 4), (2, 3), (5, 6)
    valid = np.zeros((7, 2), dtype=np.bool_)
    valid[[0, 1, 4]] = True
    return ArrayTree(
        children,
        valid,
        np.array([0, 1, -2, -2, 1, -2, -2]),
        np.array([0, 1, -1, -1, 1, -1, -1]),
        ("player-zero", "player-one-hidden-action"),
        ((0, 1),) * 2,
        np.array([0, 1]),
        np.ones((2, 2)),
        np.zeros((7, 2)),
        np.ones(7),
        np.array([0, 0, 3, -1, 0, -2, 2], dtype=np.float64),
        (np.array([0]), np.array([1, 4])),
    )


def policy(p0: float, p1: float) -> np.ndarray[Any, np.dtype[np.float64]]:
    return np.array([[p0, 1 - p0], [p1, 1 - p1]])


@pytest.fixture
def synthetic_data(monkeypatch: pytest.MonkeyPatch) -> tuple[Any, ...]:
    tree = asymmetric()
    context = ScoringContext(
        tree, tree, np.arange(2), (np.zeros(2, dtype=np.bool_), np.array([False, True]))
    )
    config = config_inputs(ROOT)
    policies: list[SourcePolicy] = []
    probabilities = [(0.8, 0.3), (0.2, 0.9), (0.6, 0.7), (0.1, 0.4)]
    contexts = {}
    for game, name, traversal in itertools.product(
        config["spot_files"], config["representations"], config["traversals"]
    ):
        contexts[game, name] = context
        for seed in config["seeds"] if traversal == "external" else [None]:
            for mode, (p0, p1) in zip(modes(config), probabilities, strict=True):
                saved = policy(p0, p1)
                baseline = (
                    p0 * p1 * 3
                    - p0 * (1 - p1)
                    - 2 * (1 - p0) * p1
                    + 2 * (1 - p0) * (1 - p1)
                )
                values0 = (4 * p1 - 1, 2 - 4 * p1)
                values1 = (2 - 5 * p0, 3 * p0 - 2)
                roots = [max(values0), max(values1)]
                replies = []
                for target, values in enumerate((values0, values1)):
                    reply = saved.copy()
                    reply[target] = 0
                    reply[target, int(np.argmax(values))] = 1
                    replies.append(dict(restricted=sha(pack_policy(tree, reply))))
                responses = [
                    dict(
                        baseline_value_chips=sign * baseline,
                        restricted_reply_value_chips=roots[t],
                        within_partition_gain_chips=roots[t] - sign * baseline,
                    )
                    for t, sign in enumerate((1, -1))
                ]
                case = dict(
                    spot_file=game,
                    representation=name,
                    traversal=traversal,
                    seed=seed,
                    regret_rule=mode[0],
                    average_weight=mode[1],
                    regret_weight="linear",
                    bridge="common",
                )
                row = dict(
                    id=f"EXPLICIT_SYNTHETIC_PROFILE_{len(policies)}",
                    iteration=10,
                    total_work=140,
                    receipt=dict(policy_sha256=sha(pack_policy(tree, saved))),
                    responses=responses,
                    reply_sha256=replies,
                    metrics=dict(
                        value_player_zero_chips=baseline,
                        within_partition_gain_chips=sum(
                            r["within_partition_gain_chips"] for r in responses
                        )
                        / 2,
                    ),
                )
                policies.append(SourcePolicy(case, row, saved))
    data = Inputs(
        config, {}, contexts, tuple(sorted(policies, key=lambda p: p.identifier))
    )
    monkeypatch.setattr(compute, "public_streets", lambda ctx: ("TURN", "RIVER"))
    records: list[dict[str, Any]] = []
    output: dict[str, Any] = dict(self_profiles=[], crosses=[])
    compute.compute(data, Deadline(10), records.append, output, lambda: None)
    return data, output, records


def test_complete_grid_retains_all_targets_opponents_and_zero_sum(
    synthetic_data: tuple[Any, ...],
) -> None:
    data, saved, records = synthetic_data
    summary = compute.validate(saved, data)
    assert summary["source_profiles"] == 64
    assert summary["self_target_traces"] == len(records) == 128
    assert summary["crossed_profiles"] == 256
    assert summary["crossed_target_conditions"] == 512
    assert summary["maximum_identity_error_chips"] < 1e-12
    assert all(
        sum(r["baseline_value_chips"] for r in c["responses"]) == 0
        for c in saved["crosses"]
    )


@pytest.mark.parametrize(
    "mode",
    [
        "missing_self",
        "duplicate_self",
        "missing_cross",
        "duplicate_cross",
        "opponent",
        "root",
        "gain",
        "ev",
        "mode",
        "street",
        "target",
        "diagonal",
    ],
)
def test_false_or_incomplete_crosses_cannot_be_published(
    synthetic_data: tuple[Any, ...], mode: str
) -> None:
    data, original, _ = synthetic_data
    saved = copy.deepcopy(original)
    first = saved["self_profiles"][0]
    cross = saved["crosses"][0]
    if mode == "missing_self":
        saved["self_profiles"].pop()
    elif mode == "duplicate_self":
        saved["self_profiles"][-1] = copy.deepcopy(first)
    elif mode == "missing_cross":
        saved["crosses"].pop()
    elif mode == "duplicate_cross":
        saved["crosses"][-1] = copy.deepcopy(cross)
    elif mode == "opponent":
        cross["responses"][0]["opponent_profile_id"] = "foreign"
    elif mode == "root":
        cross["responses"][0]["restricted_reply_value_chips"] += 1
    elif mode == "gain":
        cross["responses"][0]["gain_chips"] += 1
    elif mode == "ev":
        cross["value_player_zero_chips"] += 1
    elif mode == "mode":
        cross["first_mode"].reverse()
    elif mode == "street":
        first["street_losses_chips"]["TURN"] += 1
    elif mode == "target":
        cross["responses"][0]["target"] = False
    else:
        first["within_partition_gain_chips"] += 1
    with pytest.raises(ArithmeticError):
        compute.validate(saved, data)


@pytest.fixture
def synthetic_archive(
    synthetic_data: tuple[Any, ...], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[Any, ...]:
    import gzip

    from poker_ai.evaluation import controlled_reply_io as io
    from poker_ai.evaluation.controlled_reply_inputs import TRACE_FORMAT
    from poker_ai.evaluation.controlled_reply_traces import COLUMNS
    from poker_ai.postflop.learning_artifacts import canonical
    from poker_ai.postflop.river_study import digest

    data, original, records = synthetic_data
    monkeypatch.setattr(io, "public_streets", lambda context: ("TURN", "RIVER"))
    header = dict(format=TRACE_FORMAT, records=128, columns=list(COLUMNS))
    blob = b"\n".join(canonical(r) for r in [header, *records]) + b"\n"
    archive = tmp_path / "explicit-synthetic-traces.jsonl.gz"
    archive.write_bytes(gzip.compress(blob, mtime=0))
    saved = {
        **original,
        "details_file": archive.name,
        "details_sha256": digest(archive),
    }
    return data, saved, records, archive, tmp_path / "own.json", header


def test_streamed_archive_checks_every_bound_row_and_target(
    synthetic_archive: tuple[Any, ...],
) -> None:
    from poker_ai.evaluation.controlled_reply_io import trace_records

    data, saved, records, _, path, _ = synthetic_archive
    assert list(trace_records(path, saved, data)) == records


@pytest.mark.parametrize(
    "mode", ["hash", "header", "truncated", "extra", "order", "summary", "menu"]
)
def test_serialized_trace_corruption_is_rejected(
    synthetic_archive: tuple[Any, ...], mode: str
) -> None:
    import gzip

    from poker_ai.evaluation.controlled_reply_io import trace_records
    from poker_ai.postflop.learning_artifacts import canonical
    from poker_ai.postflop.river_study import digest

    data, saved, original, archive, path, original_header = synthetic_archive
    records, header = copy.deepcopy(original), copy.deepcopy(original_header)
    if mode == "hash":
        saved["details_sha256"] = "0" * 64
    else:
        if mode == "header":
            header["records"] = True
        elif mode == "truncated":
            records.pop()
        elif mode == "extra":
            records.append(records[0])
        elif mode == "order":
            records[0], records[1] = records[1], records[0]
        elif mode == "summary":
            records[0]["summary"]["street_losses_chips"]["TURN"] += 1
        else:
            records[0]["summary"]["partition_sha256"] = "0" * 64
        archive.write_bytes(
            gzip.compress(
                b"\n".join(canonical(r) for r in [header, *records]) + b"\n", mtime=0
            )
        )
        saved["details_sha256"] = digest(archive)
    with pytest.raises(ArithmeticError):
        list(trace_records(path, saved, data))


def test_partial_receipt_and_trace_survive_failure_without_budget_reset(
    synthetic_data: tuple[Any, ...],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import json

    from poker_ai.evaluation import controlled_reply_io as io

    data, _, _ = synthetic_data
    source_path = tmp_path / data.config["source_report"]
    source_path.parent.mkdir(parents=True)
    source_path.write_text('{"EXPLICIT_SOFTWARE_FIXTURE":true}')
    monkeypatch.setattr(io, "config_inputs", lambda root: data.config)
    monkeypatch.setattr(io, "load", lambda root: data)
    monkeypatch.setattr(io, "source", lambda root: dict(dirty=False, sha256={}))

    def fail(*args: Any) -> None:
        args[2](dict(EXPLICIT_SYNTHETIC_PARTIAL=True))
        args[3]["self_profiles"].append(dict(EXPLICIT_SYNTHETIC_PARTIAL=True))
        raise TimeoutError("deliberate software fixture")

    monkeypatch.setattr(compute, "compute", fail)
    output = tmp_path / "diagnosis.json"
    with pytest.raises(TimeoutError):
        io.run(tmp_path, output)
    saved = json.loads(output.read_text())
    assert saved["status"] == "incomplete"
    assert saved["failure"]["type"] == "TimeoutError"
    assert saved["self_profiles"][0]["EXPLICIT_SYNTHETIC_PARTIAL"]
    assert (tmp_path / "diagnosis-traces.jsonl.tmp").exists()
    with pytest.raises(FileExistsError):
        io.run(tmp_path, output)


def test_all_numerical_tables_rebuild_identically_without_optional_runtime(
    synthetic_data: tuple[Any, ...],
    tmp_path: Path,
) -> None:
    from poker_ai.evaluation.controlled_reply_report import write_report

    data, saved, _ = synthetic_data
    pot = dict.fromkeys(data.config["spot_files"], 10.0)
    first, second = tmp_path / "first", tmp_path / "second"
    summary = write_report(
        data,
        saved,
        first,
        plots=False,
        pot=pot,
        scope="EXPLICIT SYNTHETIC SOFTWARE FIXTURE",
    )
    assert summary["source_profiles"] == 64
    assert summary["target_traces"] == 128
    assert summary["crossed_target_conditions"] == 512
    write_report(
        data,
        saved,
        second,
        plots=False,
        pot=pot,
        scope="EXPLICIT SYNTHETIC SOFTWARE FIXTURE",
    )
    for path in first.iterdir():
        assert path.read_bytes() == (second / path.name).read_bytes()


@pytest.mark.slow
def test_four_synthetic_figures_are_marked_and_readable(
    synthetic_data: tuple[Any, ...], tmp_path: Path
) -> None:
    pytest.importorskip("matplotlib")
    from poker_ai.evaluation.controlled_reply_report import FIGURES, write_report

    data, saved, _ = synthetic_data
    summary = write_report(
        data,
        saved,
        tmp_path,
        pot=dict.fromkeys(data.config["spot_files"], 10.0),
        scope="EXPLICIT SYNTHETIC SOFTWARE FIXTURE — NOT RESEARCH RESULTS",
    )
    assert summary["figures"] == list(FIGURES)
    assert all((tmp_path / name).stat().st_size > 1000 for name in FIGURES)


def fictional_native(saved: dict[str, Any], data: Any, path: Path) -> dict[str, Any]:
    """Scalar-copy schema fixture, explicitly NOT independent solver evidence."""
    from poker_ai.postflop.river_study import digest
    from poker_ai.solver_validation.controlled_replies import FORMAT

    path.write_text('{"EXPLICIT_SYNTHETIC_SOFTWARE_FIXTURE":true}')
    comparisons = []
    for index, row in enumerate(saved["crosses"]):
        responses = [
            {
                k: r[k]
                for k in (
                    "target",
                    "restricted_reply_value_chips",
                    "achieved_reply_value_chips",
                    "gain_chips",
                )
            }
            for r in row["responses"]
        ]
        comparisons.append(
            dict(
                index=index,
                first_id=row["first_id"],
                second_id=row["second_id"],
                value_player_zero_chips=row["value_player_zero_chips"],
                responses=responses,
                maximum_error_chips=0.0,
            )
        )
    saved["details_sha256"] = "f" * 64
    return dict(
        format=FORMAT,
        status="completed",
        failure=None,
        config=data.config,
        own_sha256=digest(path),
        details_sha256=saved["details_sha256"],
        reference_output_used_in_training=False,
        seconds=1.0,
        license=dict(sha256=data.config["native_reference"]["license_sha256"]),
        own_replay=dict(
            status="all_controlled_reply_rows_replayed",
            target_traces=128,
            maximum_error_chips=0.0,
            seconds=0.5,
        ),
        comparisons=comparisons,
    )


def test_fictional_native_schema_requires_every_crossed_scalar(
    synthetic_data: tuple[Any, ...], tmp_path: Path
) -> None:
    from poker_ai.solver_validation.controlled_replies import validate

    data, saved, _ = synthetic_data
    path = tmp_path / "fixture.json"
    native = fictional_native(saved, data, path)
    assert validate(native, saved, path, data)["target_conditions"] == 512
    for key, value in (
        ("status", "incomplete"),
        ("target_traces", 128.0),
        ("maximum_error_chips", 1.1e-9),
        ("seconds", float("nan")),
        ("seconds", 2.0),
    ):
        changed = copy.deepcopy(native)
        changed["own_replay"][key] = value
        with pytest.raises(ArithmeticError):
            validate(changed, saved, path, data)
    for mode in ("missing", "index", "target", "root", "achieved", "gain", "binding"):
        changed = copy.deepcopy(native)
        if mode == "missing":
            changed["comparisons"].pop()
        elif mode == "index":
            changed["comparisons"][0]["index"] = False
        elif mode == "target":
            changed["comparisons"][0]["responses"][0]["target"] = False
        elif mode == "binding":
            changed["own_sha256"] = "0" * 64
        else:
            key = {
                "root": "restricted_reply_value_chips",
                "achieved": "achieved_reply_value_chips",
                "gain": "gain_chips",
            }[mode]
            changed["comparisons"][0]["responses"][0][key] += 1
        with pytest.raises(ArithmeticError):
            validate(changed, saved, path, data)


def test_native_precomparison_failure_is_retained(
    synthetic_data: tuple[Any, ...], tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import json

    from poker_ai.evaluation import controlled_reply_io as io
    from poker_ai.solver_validation import controlled_replies as native

    data, _, _ = synthetic_data
    path = tmp_path / "own.json"
    path.write_text(
        json.dumps(
            dict(details_sha256="f" * 64, EXPLICIT_SYNTHETIC_SOFTWARE_FIXTURE=True)
        )
    )
    monkeypatch.setattr(native, "config_inputs", lambda root: data.config)
    monkeypatch.setattr(io, "source", lambda root: dict(dirty=False, sha256={}))

    def fail(*args: Any) -> Any:
        raise TimeoutError("deliberate native input-replay timeout")

    monkeypatch.setattr(io, "replay", fail)
    output = tmp_path / "native.json"
    with pytest.raises(TimeoutError):
        native.run(tmp_path, path, output)
    saved = json.loads(output.read_text())
    assert saved["status"] == "incomplete"
    assert saved["comparisons"] == []
    assert saved["failure"]["type"] == "TimeoutError"
    with pytest.raises(FileExistsError):
        native.run(tmp_path, path, output)
