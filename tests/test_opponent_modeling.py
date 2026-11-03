"""Mathematical checks independent of posterior implementation arithmetic."""

import itertools
from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from numpy.random import PCG64, Generator

from poker_ai.opponent_modeling.bayes import Evidence, Posterior, TranscriptModel
from poker_ai.opponent_modeling.policies import (
    guarded_response,
    profile_value,
    response_policy,
    root_mixture,
    scripted_policy,
    security,
)
from poker_ai.toy.analysis import best_response
from poker_ai.toy.games import GameName, ToyState
from poker_ai.toy.tree import Tree


def test_hidden_card_censored_manual_fold_likelihood() -> None:
    tree = Tree.build("kuhn")
    hypotheses = tuple(
        scripted_policy(tree, n) for n in ("calling_station", "aggressive")
    )
    model = TranscriptModel(tree, hypotheses, 0)
    terminal = ToyState("kuhn", cards=(2, 0))
    for action in (1, 2, 0):
        terminal = terminal.child(action)
    e = Evidence.from_terminal(terminal, 0)
    assert e == Evidence.from_terminal(replace(terminal, cards=(2, 1)), 0)
    assert not hasattr(e, "opponent_card") and not hasattr(e, "payoff")
    # Each compatible deal has chance 1/6. Opponent bet probabilities .05/.95.
    np.testing.assert_allclose(model.likelihood(e), [2 * 0.05 / 6, 2 * 0.95 / 6])
    posterior = Posterior(np.array([0.5, 0.5]))
    posterior.update(model.likelihood(e))
    np.testing.assert_allclose(posterior.weights, [0.05, 0.95])


@pytest.mark.parametrize("game", ["kuhn", "leduc"])
@pytest.mark.parametrize("seat", [0, 1])
def test_likelihood_against_independent_recursive_enumeration(
    game: GameName,
    seat: int,
) -> None:
    tree = Tree.build(game)
    policy = scripted_policy(tree, "value")
    model = TranscriptModel(tree, (policy,), seat)
    rows = dict(zip(tree.keys, policy, strict=True))
    totals: dict[Evidence, float] = {}

    def walk(state: ToyState, probability: float) -> None:
        if state.terminal:
            evidence = Evidence.from_terminal(state, seat)
            totals[evidence] = totals.get(evidence, 0) + probability
            return
        for column, action in enumerate(state.actions):
            factor = (
                1 / len(state.actions)
                if state.chance
                else float(rows[state.information][column])
                if state.actor != seat
                else 1
            )
            walk(state.child(action), probability * factor)

    walk(ToyState(game), 1)
    for evidence, expected in totals.items():
        assert model.likelihood(evidence)[0] == pytest.approx(expected, abs=1e-14)


@pytest.mark.parametrize("game", ["kuhn", "leduc"])
@pytest.mark.parametrize("seat", [0, 1])
def test_predictive_root_mixture_exact_distribution(game: GameName, seat: int) -> None:
    tree = Tree.build(game)
    policies = tuple(scripted_policy(tree, n) for n in ("value", "aggressive"))
    model = TranscriptModel(tree, policies, seat)
    weights = np.array([0.37, 0.63])
    logging = tree.normalize(tree.legal)
    behavioral = root_mixture(tree, policies, weights, 1 - seat)
    np.testing.assert_allclose(
        model.predictive_distribution(weights, logging),
        model.transcript_distribution(logging, behavioral),
        atol=1e-14,
    )
    prediction = model.predictive_distribution(np.array([1.0, 0.0]), logging)
    assert prediction.sum() == pytest.approx(1)
    assert np.isfinite(model.conditional_log_loss(weights, logging, policies[0]))


def test_posterior_stability_order_and_support_errors() -> None:
    first, second = Posterior(np.array([0.2, 0.8])), Posterior(np.array([0.2, 0.8]))
    for _ in range(10000):
        first.update(np.array([0.001, 0.002]))
    assert first.weights[1] == 1
    observations = (np.array([0.1, 0.2]), np.array([0.8, 0.3]))
    a, b = Posterior(np.array([0.2, 0.8])), second
    for obs in observations:
        a.update(obs)
    for obs in reversed(observations):
        b.update(obs)
    np.testing.assert_allclose(a.weights, b.weights)
    previous = a.weights.copy()
    with pytest.raises(ValueError, match="impossible"):
        a.update(np.array([0.0, 0.0]))
    np.testing.assert_array_equal(a.weights, previous)
    for bad in (np.array([-0.1, 1.1]), np.array([np.nan, 1.0]), np.array([1.0])):
        with pytest.raises(ValueError):
            a.update(bad)
    with pytest.raises(ValueError):
        Posterior(np.array([0.0, 0.0]))


def test_root_mixture_differs_from_naive_local_interpolation() -> None:
    tree = Tree.build("kuhn")
    a = scripted_policy(tree, "uniform")
    b = a.copy()
    for info, key in enumerate(tree.keys):
        if tree.owners[info] != 0:
            continue
        history = key.rsplit(":", 1)[1]
        a[info] = b[info] = 0
        if history == "":
            a[info, tree.actions[info].index(1)] = 1  # Type A checks.
            b[info, tree.actions[info].index(2)] = 1  # Type B bets.
        else:
            a[info, tree.actions[info].index(0)] = 1  # A folds after checking.
            b[info, tree.actions[info].index(1)] = 1  # B never gets here.
    mix = root_mixture(tree, (a, b), np.array([0.5, 0.5]), 0)
    opponent = scripted_policy(tree, "aggressive")
    expected = 0.5 * (
        profile_value(tree, a, opponent, 0) + profile_value(tree, b, opponent, 0)
    )
    assert profile_value(tree, mix, opponent, 0) == pytest.approx(expected)
    assert abs(profile_value(tree, (a + b) / 2, opponent, 0) - expected) > 0.01
    for info, key in enumerate(tree.keys):
        if tree.owners[info] == 0 and key.endswith(":12"):
            assert mix[info, tree.actions[info].index(0)] == 1


@pytest.mark.parametrize("seat", [0, 1])
def test_response_policy_against_exhaustive_pure_strategy_enumeration(
    seat: int,
) -> None:
    tree = Tree.build("kuhn")
    rng = Generator(PCG64(731 + seat))
    opponent = tree.normalize(rng.random(tree.legal.shape) * tree.legal)
    response = response_policy(tree, opponent, seat)
    infos = np.flatnonzero(tree.owners == seat)
    values = []
    for choices in itertools.product(*(range(len(tree.actions[i])) for i in infos)):
        candidate = opponent.copy()
        for info, action in zip(infos, choices, strict=True):
            candidate[info] = 0
            candidate[info, action] = 1
        values.append(profile_value(tree, candidate, opponent, seat))
    value = profile_value(tree, response, opponent, seat)
    assert value == pytest.approx(max(values), abs=1e-12)
    assert value == pytest.approx(best_response(tree, opponent, seat), abs=1e-12)


@pytest.mark.parametrize("game", ["kuhn", "leduc"])
@pytest.mark.parametrize("seat", [0, 1])
def test_guarded_security_bound_and_ev_linearity(game: GameName, seat: int) -> None:
    tree = Tree.build(game)
    blueprint = tree.normalize(tree.legal)
    opponent = scripted_policy(tree, "calling_station")
    for budget in (0.0, 0.1, 100.0):
        result = guarded_response(tree, blueprint, opponent, seat, budget)
        assert (
            result.actual_security >= security(tree, blueprint, seat) - budget - 1e-10
        )
        assert result.actual_security >= result.certified_lower_bound - 1e-10
        mixed_ev = (1 - result.fraction) * profile_value(
            tree, blueprint, opponent, seat
        ) + result.fraction * profile_value(tree, result.unrestricted, opponent, seat)
        assert profile_value(tree, result.policy, opponent, seat) == pytest.approx(
            mixed_ev
        )
        assert 0 <= result.fraction <= 1
    with pytest.raises(ValueError):
        guarded_response(tree, blueprint, opponent, seat, -0.1)


def test_likelihood_rejects_incompatible_evidence() -> None:
    tree = Tree.build("kuhn")
    model = TranscriptModel(tree, (scripted_policy(tree, "uniform"),), 0)
    with pytest.raises(ValueError):
        model.likelihood(Evidence(0, 999, None, ((1, 1),)))
    with pytest.raises(ValueError):
        Evidence.from_terminal(ToyState("kuhn"), 0)


def test_experiment_config_and_tiny_integration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import gzip
    import json

    from poker_ai.opponent_modeling import experiment

    root = Path(__file__).resolve().parents[1]
    config = json.loads((root / "configs/opponent-modeling.json").read_text())
    config.update(
        {
            "seeds": [11],
            "checkpoints": [0, 1, 2, 4],
            "blueprint_iterations": {"kuhn": 2, "leduc": 2},
        }
    )
    config["switching"]["after_hand"] = 2
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config))
    monkeypatch.setattr(
        experiment, "source_provenance", lambda *args, **kwargs: {"test": True}
    )
    report = experiment.run_experiment(root, path, tmp_path / "report.json")
    assert report["status"] == "completed" and len(report["rows"]) == 96
    transcripts = json.loads(
        gzip.decompress((tmp_path / "public-transcripts.json.gz").read_bytes())
    )
    assert len(transcripts["histories"]) == 24
    assert all(len(row["evidence_indices"]) == 4 for row in transcripts["histories"])
    assert all(
        row["policies"]["guarded"]["security_ante_chips"]
        >= row["policies"]["blueprint"]["security_ante_chips"] - 0.1 - 1e-10
        for row in report["rows"]
    )
    for mutation in (
        {"seeds": [11, 11]},
        {"checkpoints": [1, 2]},
        {"prior": [0, 0, 0, 0]},
        {"security_tolerance": 0.1},
    ):
        path.write_text(json.dumps({**config, **mutation}))
        with pytest.raises(ValueError):
            experiment.load_config(path)


def test_extension_learning_has_no_reference_or_benchmark_imports() -> None:
    import ast

    root = Path(__file__).resolve().parents[1] / "src/poker_ai"
    for package in ("opponent_modeling", "risk"):
        for path in (root / package).glob("*.py"):
            for node in ast.walk(ast.parse(path.read_text())):
                names = (
                    [node.module or ""]
                    if isinstance(node, ast.ImportFrom)
                    else [a.name for a in node.names]
                    if isinstance(node, ast.Import)
                    else []
                )
                assert all(
                    not any(
                        forbidden in name
                        for forbidden in (
                            "open_spiel",
                            "pyspiel",
                            "solver_validation",
                            "evaluation",
                            "slumbot",
                        )
                    )
                    for name in names
                ), path
