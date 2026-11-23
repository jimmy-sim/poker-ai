"""Independent toy checks for the fixed saved-policy turn diagnosis."""

import json
import math
import sys
from pathlib import Path

import numpy as np
import pytest

from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.postflop.reply_trace import trace_losses

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from river_full_broader.gate import source_fingerprint as parent_fingerprint  # noqa: E402
from river_turn_loss.analysis import collision_sizes, fingerprint, rank, run  # noqa: E402


def test_candidate_ranking_keeps_zero_rows_and_exact_tie_order() -> None:
    values = np.array([0.0, 0.2, 0.2, 0.0, 0.4])
    streets = np.array(["TURN", "TURN", "TURN", "TURN", "RIVER"])
    assert rank(values, streets, "TURN", 4) == [1, 2, 0, 3]
    assert rank(values, streets, "RIVER", 5) == [4]
    with pytest.raises(ValueError):
        rank(values, streets[:-1], "TURN", 3)


def test_collision_count_uses_exact_to_abstract_group_size() -> None:
    mapping = np.array([0, 1, 1, 2, 2, 2], dtype=np.int64)
    assert collision_sizes(mapping, 3).tolist() == [1, 2, 2, 3, 3, 3]
    with pytest.raises(ValueError):
        collision_sizes(np.array([0, 3]), 3)


def test_fictional_additive_reply_reconciles_independent_own_score() -> None:
    scoring = software_context(0).scoring["coarse"]
    policy = scoring.partition.normalize(scoring.partition.legal.copy())
    expanded = scoring.expand(policy)
    traces = [trace_losses(scoring.exact, expanded, seat) for seat in (0, 1)]
    chips = math.fsum(trace.gain for trace in traces) / 2
    assert (
        abs(chips - scoring.score(policy).metrics["exact_exploitability_chips"]) < 1e-9
    )
    assert all(trace.accounting_error < 1e-9 for trace in traces)
    sizes = collision_sizes(scoring.exact_to_partition, len(scoring.partition.keys))
    assert len(sizes) == len(scoring.exact.keys)


def test_prospective_grid_and_source_are_isolated() -> None:
    plan = json.loads((ROOT / "configs/river-turn-loss-diagnosis.json").read_text())
    assert plan["charged_work_labels"] == [100000, 1000000, 10000000]
    assert plan["controls"]["seeds"] == [20261511, 20261512, 20261513]
    assert plan["saved_policies"] == 12
    assert plan["responding_seat_traces"] == 24
    assert plan["whole_process_cap_seconds"] == 900
    assert len(fingerprint(ROOT)) == 64
    assert parent_fingerprint(ROOT) == (
        "5aafb939fdc4ac75b06480dbd8203efddbd0e1f1b02170ab086ff8bf61668ac6"
    )


def test_existing_output_refuses_duplicate_diagnostic(tmp_path: Path) -> None:
    output = tmp_path / "existing"
    output.mkdir()
    with pytest.raises(ValueError, match="duplicate diagnostic"):
        run(ROOT, output, "proof")
