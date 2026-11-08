"""Old OWN policies exercise new adapters; no new Hold'em training in these tests."""

from pathlib import Path
from typing import Any

import pytest

from poker_ai.evaluation.controlled_reply_inputs import load
from poker_ai.evaluation.controlled_reply_math import cross
from poker_ai.evaluation.controlled_reply_traces import make_record, public_streets
from poker_ai.postflop.controlled_training import ControlledTrainer

ROOT = Path(__file__).resolve().parents[1]


def forbidden(*args: Any, **kwargs: Any) -> None:
    raise AssertionError(
        "new learning/reference strategy export forbidden in adapter checks"
    )


@pytest.mark.slow
def test_selected_old_profiles_need_no_native_runtime_or_training(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poker_ai.solver_validation.reference import Reference

    monkeypatch.setattr(ControlledTrainer, "step", forbidden)
    monkeypatch.setattr(ControlledTrainer, "initialize_exact", forbidden)
    monkeypatch.setattr(Reference, "__init__", forbidden)
    data = load(ROOT)
    assert len(data.policies) == 64
    assert len({p.group for p in data.policies}) == 16
    assert all(not p.policy.flags.writeable for p in data.policies)


@pytest.mark.slow
def test_real_old_crossed_profile_matches_native_without_reference_strategy_export(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    pytest.importorskip("pyspiel")
    from poker_ai.solver_validation.controlled_replies import compare_cross, references
    from poker_ai.solver_validation.reference import Reference

    monkeypatch.setattr(ControlledTrainer, "step", forbidden)
    monkeypatch.setattr(ControlledTrainer, "initialize_exact", forbidden)
    monkeypatch.setattr(Reference, "policy", forbidden)
    monkeypatch.setattr(Reference, "train_to", forbidden)
    data = load(ROOT)
    first = data.policies[0]
    second = next(
        p
        for p in data.policies
        if p.group == first.group and p.identifier != first.identifier
    )
    context = data.context(first.case)
    replies = {}
    for p in (first, second):
        for target in (0, 1):
            _, _, reply = make_record(p, context, target, public_streets(context), 1e-9)
            replies[p.identifier, target] = reply
    record = dict(
        first_id=first.identifier,
        second_id=second.identifier,
        **cross(
            context.partition,
            first.policy,
            second.policy,
            replies[second.identifier, 0],
            replies[first.identifier, 1],
            tolerance=1e-9,
        ),
    )
    key = first.case["spot_file"], first.case["representation"]
    result = compare_cross(
        data,
        record,
        {p.identifier: p for p in (first, second)},
        replies,
        references(data)[key],
    )
    assert result["maximum_error_chips"] <= 1e-9


@pytest.mark.slow
def test_inspector_decodes_an_old_own_row_without_training_or_reference_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from poker_ai.evaluation import controlled_reply_inspect as inspector
    from poker_ai.solver_validation.reference import Reference

    monkeypatch.setattr(ControlledTrainer, "step", forbidden)
    monkeypatch.setattr(ControlledTrainer, "initialize_exact", forbidden)
    monkeypatch.setattr(Reference, "__init__", forbidden)
    data = load(ROOT)
    source = data.policies[0]
    _, record, _ = make_record(
        source,
        data.context(source.case),
        0,
        public_streets(data.context(source.case)),
        1e-9,
    )
    monkeypatch.setattr(inspector, "read_saved", lambda root, path: ({}, data))
    monkeypatch.setattr(
        inspector, "trace_records", lambda path, saved, loaded: iter([record])
    )
    result = inspector.inspect(
        ROOT,
        tmp_path / "own.json",
        game=Path(source.case["spot_file"]).stem,
        representation=source.case["representation"],
        traversal=source.case["traversal"],
        seed=source.case["seed"],
        clip=source.case["regret_rule"],
        average=source.case["average_weight"],
        target=0,
        rank=1,
    )
    assert len(result["hole"]) == 2
    assert len(result["board"]) in (4, 5)
    assert (
        len(result["actions"])
        == len(result["saved_probabilities"])
        == len(result["conditional_values_chips"])
    )
    assert result["loss_chips"] == max(r[1] for r in record["rows"])
    assert "absent" in result["audit_status"]
