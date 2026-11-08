"""Toy replay/IO integration; no new Hold'em learning or reference strategies."""

import itertools
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.evaluation.averaging_history_artifacts import array_sha, decode_mass
from poker_ai.evaluation.averaging_history_math import coverage, window_mass
from poker_ai.evaluation.averaging_history_training import train_one
from poker_ai.postflop.controlled_scoring import ScoringContext
from poker_ai.postflop.learning_artifacts import decode
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.node_profile import trainer
from poker_ai.postflop.river_study import Deadline
from poker_ai.postflop.row_profile import fingerprint
from poker_ai.postflop.training_isolation import sentinel_tree

CASES = list(
    itertools.product(
        ("full", "external"), ("signed", "clipped"), ("uniform", "linear")
    )
)


def software_fixture(traversal: str, regret: str, average: str) -> tuple[Any, ...]:
    tree = sentinel_tree()
    zeros = np.zeros(len(tree.keys), dtype=np.bool_)
    context = ScoringContext(
        tree, tree, np.arange(len(tree.keys), dtype=np.int64), (zeros, zeros)
    )
    case = dict(
        spot_file="EXPLICIT_SOFTWARE_FIXTURE_NOT_POKER_RESULTS",
        representation="toy_exact",
        traversal=traversal,
        regret_rule=regret,
        regret_weight="linear",
        average_weight=average,
        bridge="common",
        seed=7 if traversal == "external" else None,
    )
    solver = trainer(tree, case, "nodes" if traversal == "external" else "parent")
    solver.initialize_exact()
    labels = [solver.nodes_visited + k for k in (1000, 2000, 3000, 4000, 5000)]
    config = dict(
        source_target=labels[-1],
        current_work_labels=labels,
        cumulative_mass_work_labels=labels[2:],
        suffix_windows=[[labels[2], labels[4]], [labels[3], labels[4]]],
        tolerance_chips=1e-9,
    )
    original = {}
    for threshold in (labels[0], labels[2], labels[4]):
        previous = solver.nodes_visited
        while solver.nodes_visited < threshold:
            previous = solver.nodes_visited
            solver.step()
        original[threshold] = dict(
            id=f"toy-original-work-{threshold}",
            index=0,
            iteration=solver.iteration,
            previous_work=previous,
            total_work=solver.nodes_visited,
            last_iteration_visits=solver.nodes_visited - previous,
            state_sha256=fingerprint(solver),
            initialization_visits=solver.initialization_visits,
            receipt=dict(policy_sha256=array_sha(solver.average_policy)),
            **score_data(context, context.score(solver.average_policy)),
        )
    return context, case, config, original


@pytest.mark.parametrize("traversal,regret,average", CASES)
def test_complete_case_preserves_original_prefixes_and_reconstructs_windows(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    traversal: str,
    regret: str,
    average: str,
) -> None:
    from poker_ai.solver_validation.reference import Reference

    def forbidden(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("reference constructor forbidden during own toy replay")

    monkeypatch.setattr(Reference, "__init__", forbidden)
    context, case, config, original = software_fixture(traversal, regret, average)
    events: list[dict[str, Any]] = []
    train_one(
        context,
        case,
        "explicit-toy-source",
        0,
        original,
        config,
        tmp_path,
        "f" * 64,
        Deadline(10),
        events.append,
    )
    prefixes = [e for e in events if e["phase"] == "prefix"]
    profiles = [e["row"] for e in events if e["phase"] == "profile"]
    masses = [e["row"] for e in events if e["phase"] == "mass"]
    assert len(prefixes) == 3 and len(profiles) == 8 and len(masses) == 3
    assert events[-1]["phase"] == "trained"
    assert events[-1]["work"] == original[config["source_target"]]["total_work"]
    boundaries = {
        r["work_label"]: decode_mass(
            (tmp_path / r["file"]).read_bytes(), context.partition, r
        )
        for r in masses
    }
    for row in profiles:
        detail = decode((tmp_path / row["file"]).read_bytes(), context, row)
        if row["kind"] == "suffix":
            window = row["window"]
            increment = window_mass(
                context.partition,
                boundaries[window["left_label"]],
                boundaries[window["right_label"]],
            )
            actual = context.partition.normalize(increment)
            assert array_sha(increment) == window["increment_mass_sha256"]
            assert (
                coverage(
                    context.partition,
                    increment,
                    np.zeros(len(context.partition.keys), dtype=np.bool_),
                )
                == row["coverage"]
            )
        elif row["kind"] == "whole_average":
            actual = context.partition.normalize(boundaries[config["source_target"]])
            assert (
                array_sha(actual)
                == original[config["source_target"]]["receipt"]["policy_sha256"]
            )
        else:
            assert row["coverage"] is None
            continue
        from poker_ai.postflop.controlled_checkpoints import unpack_policy

        assert (
            actual.tobytes()
            == unpack_policy(context.partition, detail["policy"]).tobytes()
        )


@pytest.mark.parametrize(
    "field", ["state_sha256", "total_work", "iteration", "policy_sha256"]
)
def test_changed_original_prefix_stops_and_retains_partial_files(
    tmp_path: Path, field: str
) -> None:
    context, case, config, original = software_fixture("external", "clipped", "linear")
    final = original[config["source_target"]]
    if field == "policy_sha256":
        final["receipt"][field] = "0" * 64
    elif field == "state_sha256":
        final[field] = "0" * 64
    else:
        final[field] += 1
    events: list[dict[str, Any]] = []
    with pytest.raises(
        ArithmeticError, match="original trajectory/average prefix changed"
    ):
        train_one(
            context,
            case,
            "explicit-toy-source",
            0,
            original,
            config,
            tmp_path,
            "f" * 64,
            Deadline(10),
            events.append,
        )
    assert list(tmp_path.rglob("*.json.gz"))
    assert sum(e["phase"] == "profile" for e in events) == 4
    assert not any(e["phase"] == "trained" for e in events)
