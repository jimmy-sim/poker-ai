"""Independent tiny trajectories, failure barriers and immutable capture lineage."""

import copy
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from poker_ai.evaluation import matched_update_capture as capture
from poker_ai.evaluation import reduced_study_inputs as study
from poker_ai.evaluation.averaging_history_artifacts import array_sha, decode_mass
from poker_ai.evaluation.averaging_history_software import toy_context
from poker_ai.postflop.controlled_checkpoints import unpack_policy, write_snapshot
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.frozen_batches import guard
from poker_ai.postflop.learning_artifacts import decode
from poker_ai.postflop.river_study import Deadline

SCOPE = "EXPLICIT_TEST_FIXTURE_NOT_POKER"


def fixture(
    clipped: bool = False,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[int, Any]]:
    context = toy_context()
    path = dict(
        batch_size=1,
        spot_file="EXPLICIT_TOY",
        representation="EXPLICIT_TOY",
        regret_rule="clipped" if clipped else "signed",
        seed=20261301,
    )
    direct = study.trainer(context.partition, path)
    direct.initialize_exact()
    trace: dict[int, Any] = {}
    for iteration in range(1, 17):
        previous = 0 if iteration == 1 else trace[iteration - 1]["total_work"]
        current = direct.current_policy.copy()
        masses = {w: direct.ledger(w).copy() for w in study.WEIGHTS}
        trace[iteration] = dict(
            path_index=0,
            work_label=direct.nodes_visited - 1,
            iteration=iteration,
            previous_work=previous,
            total_work=direct.nodes_visited,
            last_iteration_visits=direct.nodes_visited - previous,
            initialization_visits=direct.initialization_visits,
            sampled_traversals=direct.sampled_traversals,
            guard_sha256=guard(direct),
            current_sha256=array_sha(current),
            readouts={
                w: dict(
                    source_id="EXPLICIT-" + w,
                    original_id="ORIGINAL-" + w,
                    policy_sha256=array_sha(context.partition.normalize(masses[w])),
                    state_sha256=direct.readout_fingerprint(w),
                    mass_sha256=array_sha(masses[w]),
                )
                for w in study.WEIGHTS
            },
            current=current,
            masses=masses,
        )
        if iteration < 16:
            direct.step()
    expected = [
        {k: v for k, v in trace[i].items() if k not in ("current", "masses")}
        for i in (2, 7, 16)
    ]
    targets = [
        dict(
            id="EXPLICIT-B" + str(b),
            baseline_path_index=0,
            target_iteration=t,
            comparison_batch_size=b,
        )
        for b, t in ((4, 4), (16, 8))
    ]
    return path, targets, expected, trace


def run(
    tmp_path: Path, *, clipped: bool = False, duplicate: bool = False
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[int, Any]]:
    path, targets, expected, trace = fixture(clipped)
    if duplicate:
        targets[1]["target_iteration"] = targets[0]["target_iteration"]
    events: list[dict[str, Any]] = []
    with patch.object(
        ScoringContext, "score", side_effect=AssertionError("capture may not score")
    ):
        counts = capture.collect(
            toy_context(),
            path,
            0,
            targets,
            expected,
            tmp_path,
            "a" * 64,
            SCOPE,
            events.append,
            Deadline(30),
        )
    assert counts["captures"] == 6
    assert counts["masses"] == 4
    assert counts["checkpoints"] == 3
    assert counts["capture_events"] == (1 if duplicate else 2)
    assert counts["iteration"] == 16
    return events, expected, trace


@pytest.mark.parametrize("clipped", [False, True])
@pytest.mark.parametrize("duplicate", [False, True])
def test_observation_and_archives_match_uninterrupted_path(
    tmp_path: Path, clipped: bool, duplicate: bool
) -> None:
    events, expected, trace = run(tmp_path, clipped=clipped, duplicate=duplicate)
    checks = [e["row"] for e in events if e["phase"] == "checkpoint"]
    capture.barrier(checks, expected)
    context = toy_context()
    for event in events:
        if event["phase"] not in ("capture", "mass"):
            continue
        row = event["row"]
        blob = (tmp_path / row["file"]).read_bytes()
        direct = trace[row["iteration"]]
        if event["phase"] == "mass":
            actual = decode_mass(blob, context.partition, row)
            assert array_sha(actual) == array_sha(direct["masses"][row["readout"]])
        else:
            actual = unpack_policy(
                context.partition, decode(blob, context, row)["policy"]
            )
            want = (
                direct["current"]
                if row["readout"] == "current"
                else context.partition.normalize(
                    direct["masses"][row["readout"].removesuffix("_average")]
                )
            )
            assert array_sha(actual) == array_sha(want)
            assert "metrics" not in row
    assert len({e["row"]["id"] for e in events if e["phase"] == "capture"}) == 6


@pytest.mark.parametrize(
    "field",
    [
        "iteration",
        "previous_work",
        "total_work",
        "last_iteration_visits",
        "initialization_visits",
        "sampled_traversals",
        "guard_sha256",
        "current_sha256",
        "linear_mass",
        "uniform_policy",
        "linear_state",
    ],
)
def test_changed_old_state_rejected_and_earlier_captures_retained(
    tmp_path: Path, field: str
) -> None:
    path, targets, expected, _ = fixture()
    bad = copy.deepcopy(expected)
    if field == "linear_mass":
        bad[-1]["readouts"]["linear"]["mass_sha256"] = "f" * 64
    elif field == "uniform_policy":
        bad[-1]["readouts"]["uniform"]["policy_sha256"] = "f" * 64
    elif field == "linear_state":
        bad[-1]["readouts"]["linear"]["state_sha256"] = "f" * 64
    elif isinstance(bad[-1][field], int):
        bad[-1][field] += 1
    else:
        bad[-1][field] = "f" * 64
    events: list[dict[str, Any]] = []
    with patch.object(ScoringContext, "score", side_effect=AssertionError("no scores")):
        with pytest.raises(ArithmeticError, match="mismatch"):
            capture.collect(
                toy_context(),
                path,
                0,
                targets,
                bad,
                tmp_path,
                "a" * 64,
                SCOPE,
                events.append,
                Deadline(30),
            )
    assert len([e for e in events if e["phase"] == "capture"]) == 6
    with pytest.raises(ArithmeticError, match="barrier"):
        capture.barrier(
            [e["row"] for e in events if e["phase"] == "checkpoint"], expected
        )
    assert len(list((tmp_path / "captures").glob("*.gz"))) == 6


@pytest.mark.parametrize(
    "kind", ["missing", "duplicate", "different_context", "bool_counter"]
)
def test_global_barrier_cannot_accept_partial_duplicate_or_changed_case(
    kind: str,
) -> None:
    _, _, expected, _ = fixture()
    checks = copy.deepcopy(expected)
    if kind == "missing":
        checks.pop()
    elif kind == "duplicate":
        checks[-1] = copy.deepcopy(checks[0])
    elif kind == "different_context":
        checks[-1]["path_index"] = 23
    else:
        checks[-1]["iteration"] = True
    with pytest.raises(ArithmeticError, match="barrier"):
        capture.barrier(checks, expected)


def test_partial_io_failure_keeps_prior_capture_without_scoring(tmp_path: Path) -> None:
    path, targets, expected, _ = fixture()
    events: list[dict[str, Any]] = []
    original = write_snapshot
    calls = 0

    def fail(*args: Any, **kwargs: Any) -> dict[str, Any]:
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("injected disk failure")
        return original(*args, **kwargs)

    with (
        patch.object(capture, "write_snapshot", fail),
        pytest.raises(OSError, match="disk failure"),
    ):
        capture.collect(
            toy_context(),
            path,
            0,
            targets,
            expected,
            tmp_path,
            "a" * 64,
            SCOPE,
            events.append,
            Deadline(30),
        )
    assert len([e for e in events if e["phase"] == "capture"]) == 1
    assert len(list((tmp_path / "captures").glob("*.gz"))) == 1
