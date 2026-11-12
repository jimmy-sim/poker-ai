"""Optional real OpenSpiel arithmetic on tiny OWN B4 readouts only."""

from pathlib import Path

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.evaluation import compact_sampled_inputs as inputs
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.batch_reduction import ReducedDispatchBatchTrainer
from poker_ai.postflop.compact_sampled_capture import payload
from poker_ai.postflop.compact_sampled_native_checks import compare
from poker_ai.postflop.compact_sampled_state import decode, scores
from poker_ai.postflop.controlled_training import Rules
from poker_ai.solver_validation.matched_array_reference import ScalarReference

pytest.importorskip("pyspiel")
ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("case_index", [0, 3, 18, 21])
def test_native_agrees_on_all_three_readouts_and_both_roots(case_index: int) -> None:
    case = inputs.cases(ROOT, "software")[case_index]
    context = inputs.game_contexts(ROOT, "software")[
        case["spot_file"], case["representation"]
    ]
    solver = ReducedDispatchBatchTrainer(
        context.scoring.partition,
        Generator(PCG64(case["seed"])),
        batch_size=4,
        rules=Rules("signed", "linear", "linear"),
    )
    solver.initialize_exact()
    warm = payload(context, case, case_index, "software", "f" * 64, solver, None, None)
    # A warm fixture alone still exercises reversed maps and both payoff signs.
    arrays, policies = decode(context, warm, None, "f" * 64, "software")
    reference = ScalarReference(context.scoring.exact)
    for row in scores(context, warm, arrays, policies):
        policy = context.scoring.expand(policies[row["readout"]])
        before = policy.copy()
        result = compare(
            dict(
                row, **case, work_checkpoint=1000, context_sha256=context.context_sha256
            ),
            dict(
                value_player_zero_chips=reference.value(policy),
                best_response_zero_chips=reference.response_value(policy, 0),
                best_response_one_chips=reference.response_value(policy, 1),
            ),
        )
        np.testing.assert_array_equal(policy, before)
        assert files.array_sha(policy) == files.array_sha(before)
        assert result["maximum_error_chips"] < 1e-12
