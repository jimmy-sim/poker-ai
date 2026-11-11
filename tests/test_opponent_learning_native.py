"""Native checks of ALREADY PUBLISHED analytic fixtures, not new trained data.

The source05a analytic own0/.5 controls precede these comparisons on GitHub.
Auditing the new trained software dataset still requires its own publication.
"""

import importlib.util
import json
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.averaging_history_math import fixed_match
from poker_ai.evaluation.opponent_learning_contexts import software_context
from poker_ai.evaluation.opponent_learning_design import TOY
from poker_ai.evaluation.opponent_learning_sources import contract, frozen_opponent
from poker_ai.postflop.controlled_checkpoints import pack_policy
from poker_ai.postflop.learning_training import score_data
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.solver_validation import opponent_learning as native
from poker_ai.solver_validation.controlled_pipeline import license_record
from poker_ai.solver_validation.matched_array_reference import ScalarReference, compare

ROOT = Path(__file__).resolve().parents[1]
pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("pyspiel") is None, reason="optional OpenSpiel"
)


@pytest.mark.parametrize("game", [0, 1])
@pytest.mark.parametrize("kind", ["coarse", "mixed0", "mixed1", "fine"])
def test_native_profile_adapter_on_published_analytic_unsafe_control(
    game: int, kind: str
) -> None:
    published = json.loads(
        (
            ROOT / "results/opponent-information/software-views/correctness311.json"
        ).read_text()
    )
    check_source(ROOT, published["source"])
    assert published["toy"][game]["fine_unsafe_exploitability"] == 0.5
    license_record(contract(ROOT))
    contexts = software_context(game)
    context = contexts.scoring[kind]
    fine_policy = np.array([[0.0, 1.0]] * 2 + [[0.5, 0.5]] * 2)
    policy = np.zeros_like(context.partition.legal)
    for i, group in enumerate(context.exact_to_partition):
        policy[group] = fine_policy[i]
    own = context.score(policy)
    peer = dict(
        id="PUBLISHED_ANALYTIC_UNSAFE_" + kind,
        coordinate=3 * game,
        scope=TOY,
        receipt=dict(policy_sha256=array_sha(policy)),
        **score_data(context, own),
    )
    detail = dict(
        policy=pack_policy(context.partition, policy),
        metrics=own.metrics,
        responses=own.responses,
        replies=[
            {k: pack_policy(context.exact, p) for k, p in row.items()}
            for row in own.replies
        ],
    )
    fine = ScalarReference(context.exact)
    limited = fine if kind == "fine" else ScalarReference(context.partition)
    result = dict(
        id=peer["id"],
        coordinate=peer["coordinate"],
        scope=TOY,
        policy_sha256=peer["receipt"]["policy_sha256"],
        own_reply_sha256=peer["reply_sha256"],
        **compare(context, (fine, limited), detail),
    )
    assert native.self_error(result, peer) <= 1e-9
    assert result["native_metrics"]["exact_exploitability_chips"] == 0.5


@pytest.mark.parametrize("game", [0, 1])
def test_native_fixed_adapter_on_published_analytic_probability_tables(
    game: int,
) -> None:
    license_record(contract(ROOT))
    c = software_context(game)
    uniform = c.fine.normalize(c.fine.legal)
    opponent = frozen_opponent(
        c, "PUBLISHED_ANALYTIC_UNIFORM", game, uniform, array_sha(uniform)
    )
    candidate = np.array([[0.0, 1.0]] * 2 + [[0.5, 0.5]] * 2)
    reference = ScalarReference(c.fine)
    cache: dict[Any, Any] = {}
    for target in (0, 1):
        own = fixed_match(c.fine, candidate, opponent.policy, opponent.replies[target])
        peer = dict(
            id="PUBLISHED_ANALYTIC_UNSAFE",
            condition_id=f"analytic-{game}-{target}",
            coordinate=game * 3,
            target=target,
            opponent_id=opponent.identifier,
            source_sha256="a" * 64,
            candidate_policy_sha256=array_sha(candidate),
            opponent_policy_sha256=opponent.fine_policy_sha256,
            opponent_source_policy_sha256=opponent.source_policy_sha256,
            own_reply_sha256=array_sha(
                opponent.replies[target].apply(c.fine, opponent.policy)
            ),
            scope=TOY,
            readout="analytic_not_learned",
            arm="analytic_not_learned",
            work_label=0,
            target_ev_chips=own["baseline_value_chips"],
            fine_reply_value_chips=own["restricted_reply_value_chips"],
            achieved_own_reply_value_chips=own["achieved_reply_value_chips"],
            fine_reply_gain_chips=own["gain_chips"],
        )
        result = native.fixed(peer, candidate, opponent, reference, cache)
        assert native.fixed_error(result, peer) <= 1e-9
        repeated = native.fixed(peer, candidate, opponent, reference, cache)
        assert result == repeated
    assert len(cache) == 2
