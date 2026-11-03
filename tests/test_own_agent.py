"""Own-policy inference uses only observations and explicit fallback diagnostics."""

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

import pytest
from numpy.random import PCG64, Generator

from poker_ai.abstraction.model import CardAbstraction, Kind
from poker_ai.abstraction.shadow import legal_actions
from poker_ai.agents.no_limit import ENCODER_FILES, OwnNoLimitAgent, PolicyRow
from poker_ai.engine import Action, ActionKind, Observation
from poker_ai.training.checkpoint import save_checkpoint
from poker_ai.training.mccfr import MCCFR
from poker_ai.training.no_limit import NoLimitRules, NoLimitState, sample_no_limit


def observation(state: NoLimitState) -> Observation:
    assert state.dealer.actor is not None
    return state.dealer.observe(state.dealer.actor)


def test_loaded_own_checkpoint_matches_known_on_grid_row(
    tmp_path: Path, card_model_factory: Callable[[Kind], CardAbstraction]
) -> None:
    model = card_model_factory("potential")
    model_path = tmp_path / "own-model.json"
    model.save(model_path, provenance={})
    rules = NoLimitRules()

    def factory(rng: Generator) -> NoLimitState:
        return sample_no_limit(rules, rng, information_builder=model.information)

    solver = MCCFR(factory, Generator(PCG64(52)))
    first = factory(Generator(PCG64(52)))
    solver.train(1)
    from poker_ai import __file__ as package_file

    assert package_file is not None
    root = Path(package_file).parent
    source = {
        "sha256": {
            f"src/poker_ai/{name}": hashlib.sha256(
                (root / name).read_bytes()
            ).hexdigest()
            for name in ENCODER_FILES
        }
    }
    config = {
        "training": {
            "game": "no_limit",
            "rules": {
                "stacks": [200, 200],
                "button": 1,
                "fractions": [[1, 2], [1, 1], [2, 1]],
                "include_minimum": True,
                "include_all_in": True,
            },
        },
        "model_sha256": hashlib.sha256(model_path.read_bytes()).hexdigest(),
    }
    checkpoint = tmp_path / "own-policy.json"
    save_checkpoint(solver, checkpoint, config=config, provenance=source)
    agent = OwnNoLimitAgent.load(checkpoint, model_path)
    decision = agent.distribution(observation(first), episode_seed=99)
    assert decision.status == "matched"
    expected = solver.policy(first.information, first.actions, average=True)
    assert decision.probabilities == pytest.approx(tuple(expected))
    for action, p in zip(decision.actions, decision.probabilities, strict=True):
        if p:
            first.dealer.apply(action)  # All supported output actions are legal.
    payload = json.loads(checkpoint.read_text())
    payload["source"]["sha256"]["src/poker_ai/cards.py"] = "0" * 64
    checkpoint.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match="encoder fingerprint"):
        OwnNoLimitAgent.load(checkpoint, model_path)


def test_fallback_statuses_are_explicit_and_always_legal(
    card_model_factory: Callable[[Kind], CardAbstraction],
) -> None:
    model = card_model_factory("strength")
    rules = NoLimitRules()
    state = sample_no_limit(rules, Generator(PCG64(8)))
    agent = OwnNoLimitAgent(model, rules, {})
    decision = agent.distribution(observation(state), episode_seed=1)
    assert decision.status == "unseen" and sum(decision.probabilities) == pytest.approx(
        1
    )
    ids, actions = legal_actions(observation(state), rules)
    assert decision.actions == actions
    key = model.information(observation(state))
    unaveraged = OwnNoLimitAgent(model, rules, {key: PolicyRow(ids, None)})
    assert (
        unaveraged.distribution(observation(state), episode_seed=1).status
        == "unaveraged"
    )
    off_grid = state.dealer.apply(Action(ActionKind.RAISE_TO, 150)).apply(
        Action(ActionKind.CALL)
    )
    assert off_grid.actor is not None
    fallback = OwnNoLimitAgent(model, rules, {}, scheme="nearest").distribution(
        off_grid.observe(off_grid.actor), episode_seed=1
    )
    assert fallback.status == "shadow_failure"
    for action, p in zip(fallback.actions, fallback.probabilities, strict=True):
        if p:
            off_grid.apply(action)


def test_encoding_bug_is_not_hidden_as_uniform_fallback(
    card_model_factory: Callable[[Kind], CardAbstraction],
) -> None:
    model = card_model_factory("strength")
    rules = NoLimitRules()
    state = sample_no_limit(rules, Generator(PCG64(8)))
    key = model.information(observation(state))
    agent = OwnNoLimitAgent(model, rules, {key: PolicyRow((1,), (1.0,))})
    with pytest.raises(ValueError, match="encoding"):
        agent.distribution(observation(state), episode_seed=1)


def test_reference_strategy_json_is_not_an_own_agent(tmp_path: Path) -> None:
    path = tmp_path / "reference-strategy.json"
    path.write_text('{"strategy":{"root":[0.2,0.8]}}')
    with pytest.raises(ValueError, match="own MCCFR"):
        OwnNoLimitAgent.load(path, tmp_path / "unused.json")
