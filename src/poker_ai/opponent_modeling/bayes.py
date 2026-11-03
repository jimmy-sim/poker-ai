"""Finite-type Bayesian inference from censored public toy-game transcripts."""

from dataclasses import dataclass
from typing import cast

import numpy as np
from numpy.random import Generator

from poker_ai.toy.games import ToyState
from poker_ai.toy.tree import FloatArray, Tree


@dataclass(frozen=True, slots=True)
class Evidence:
    """No opponent card, terminal payoff, hidden node index or latent type."""

    seat: int
    own_card: int
    board: int | None
    histories: tuple[tuple[int, ...], ...]

    @classmethod
    def from_terminal(cls, state: ToyState, seat: int) -> "Evidence":
        if not state.terminal or seat not in (0, 1):
            raise ValueError("requires terminal state and valid observer")
        return cls(seat, state.cards[seat], state.board, state.histories)


class Posterior:
    """Stable categorical weights; all-zero observation likelihood is an error."""

    def __init__(self, prior: FloatArray) -> None:
        if (
            prior.ndim != 1
            or not len(prior)
            or np.any(prior < 0)
            or not np.all(np.isfinite(prior))
            or not np.isclose(prior.sum(), 1, atol=1e-12, rtol=0)
        ):
            raise ValueError("invalid categorical prior")
        self.log_weights = np.full(prior.shape, -np.inf)
        positive = prior > 0
        self.log_weights[positive] = np.log(prior[positive])
        self.observations = 0

    @property
    def weights(self) -> FloatArray:
        values = np.exp(self.log_weights - self.log_weights.max())
        return cast(FloatArray, values / values.sum())

    def update(self, likelihood: FloatArray) -> None:
        if (
            likelihood.shape != self.log_weights.shape
            or not np.all(np.isfinite(likelihood))
            or np.any(likelihood < 0)
        ):
            raise ValueError("invalid likelihood")
        updated = np.full(likelihood.shape, -np.inf)
        positive = likelihood > 0
        updated[positive] = self.log_weights[positive] + np.log(likelihood[positive])
        if not np.any(np.isfinite(updated)):
            raise ValueError("observation impossible under all supported hypotheses")
        self.log_weights = updated - np.max(updated)
        self.observations += 1


class TranscriptModel:
    """Pre-enumerated hidden-card marginal likelihoods for finite own toy trees.

    L[e,h] = sum_{terminal z matching evidence e} chance(z)*opp_own_reach_h(z).
    Observer's own action reach and P(own_card) are common factors across types
    and cancel in posterior odds, even for adaptive collection between hands.
    Opponent private cards are integrated, including folds; no deal is selected
    from the simulator's hidden state. Full-support hypotheses avoid zero support.
    """

    def __init__(self, tree: Tree, policies: tuple[FloatArray, ...], seat: int) -> None:
        if seat not in (0, 1) or not policies:
            raise ValueError("requires observer and hypotheses")
        self.tree, self.seat, self.policies = tree, seat, policies
        self.terminals = np.flatnonzero(tree.player == -2)
        self.lookup: dict[Evidence, int] = {}
        groups: list[int] = []
        representatives: list[int] = []
        for node in self.terminals:
            evidence = Evidence.from_terminal(tree.states[node], seat)
            if evidence not in self.lookup:
                self.lookup[evidence] = len(self.lookup)
                representatives.append(int(node))
            groups.append(self.lookup[evidence])
        self.groups = np.array(groups, dtype=np.int64)
        self.representatives = np.array(representatives, dtype=np.int64)
        self.likelihoods = np.zeros((len(self.lookup), len(policies)))
        for h, policy in enumerate(policies):
            opp = tree.reaches(tree.edges(policy))[:, 1 - seat]
            np.add.at(
                self.likelihoods[:, h],
                self.groups,
                tree.chance_reach[self.terminals] * opp[self.terminals],
            )

    def likelihood(self, evidence: Evidence) -> FloatArray:
        if evidence.seat != self.seat or evidence not in self.lookup:
            raise ValueError("impossible public transcript")
        return cast(FloatArray, self.likelihoods[self.lookup[evidence]].copy())

    def predictive_distribution(
        self, weights: FloatArray, own: FloatArray
    ) -> FloatArray:
        """Joint law of own card + public transcript under a fixed logging policy."""
        if (
            weights.shape != (len(self.policies),)
            or np.any(weights < 0)
            or not np.all(np.isfinite(weights))
            or not np.isclose(weights.sum(), 1, atol=1e-12, rtol=0)
        ):
            raise ValueError("invalid hypothesis weights")
        reach = self.tree.reaches(self.tree.edges(own))[:, self.seat]
        result = (self.likelihoods @ weights) * reach[self.representatives]
        if not np.isclose(result.sum(), 1, atol=1e-12, rtol=0):
            raise ArithmeticError("predictive transcript probabilities not normalized")
        return result

    def transcript_distribution(
        self, own: FloatArray, opponent: FloatArray
    ) -> FloatArray:
        profile = opponent.copy()
        profile[self.tree.owners == self.seat] = own[self.tree.owners == self.seat]
        reaches = self.tree.reaches(self.tree.edges(profile))
        terminal_mass = self.tree.chance_reach[self.terminals] * reaches[
            self.terminals
        ].prod(axis=1)
        probabilities = np.zeros(len(self.lookup))
        np.add.at(probabilities, self.groups, terminal_mass)
        if not np.isclose(probabilities.sum(), 1, atol=1e-12, rtol=0):
            raise ArithmeticError("true transcript probabilities not normalized")
        return probabilities

    def conditional_log_loss(
        self, weights: FloatArray, logging: FloatArray, true_opponent: FloatArray
    ) -> float:
        """Exact next-transcript expected NLL given own card, natural-log units.

        Score distribution is fixed blueprint logging, not the changing collector.
        Conditioning divides joint law by own-card probability (uniform deck).
        Own actions are included for a properly normalized score; they are common
        across type hypotheses and cancel from learning. Fold evidence is kept.
        """
        prediction = self.predictive_distribution(weights, logging)
        truth = self.transcript_distribution(logging, true_opponent)
        support = truth > 0
        if np.any(prediction[support] <= 0):
            return float("inf")
        deck_size = 3 if self.tree.states[0].game == "kuhn" else 6
        return float(-np.dot(truth[support], np.log(prediction[support] * deck_size)))


def sample_terminal(tree: Tree, policy: FloatArray, rng: Generator) -> ToyState:
    """Simulator returns full state; caller must censor it before learner access."""
    tree.validate_policy(policy)
    node = 0
    while tree.player[node] != -2:
        state = tree.states[node]
        probabilities = (
            state.chance_probabilities
            if state.chance
            else policy[tree.information[node], : len(state.actions)]
        )
        column = int(rng.choice(len(state.actions), p=probabilities))
        node = int(tree.children[node, column])
    return tree.states[node]
