"""Optional OpenSpiel alignment and solver comparisons; no training imports this."""

import importlib
from typing import Any

import numpy as np

from poker_ai.toy.cfr import Variant
from poker_ai.toy.tree import FloatArray, Tree


class OpenSpielReference:
    def __init__(self, tree: Tree, variant: Variant) -> None:
        pyspiel = importlib.import_module("pyspiel")
        name = "kuhn_poker" if tree.states[0].game == "kuhn" else "leduc_poker"
        self.game: Any = pyspiel.load_game(name)
        self.tree = tree
        self.states: list[Any] = [None] * len(tree.keys)
        self.actions: list[tuple[int, ...]] = [()] * len(tree.keys)
        aligned: dict[int, Any] = {0: self.game.new_initial_state()}
        for node, state in enumerate(tree.states):
            other = aligned.pop(node)
            mapped = tuple(
                action
                if state.chance or name == "leduc_poker"
                else int(
                    action == 2
                    or (action == 1 and state.paid[state.actor] < max(state.paid))
                )
                for action in state.actions
            )
            if not state.chance and not state.terminal:
                info = tree.information[node]
                self.states[info] = other
                self.actions[info] = mapped
            for slot, action in enumerate(mapped):
                aligned[int(tree.children[node, slot])] = other.child(action)
        module = importlib.import_module("open_spiel.python.algorithms.cfr")
        discounted = importlib.import_module(
            "open_spiel.python.algorithms.discounted_cfr"
        )
        factory = {
            "cfr": module.CFRSolver,
            "cfr_plus": module.CFRPlusSolver,
            "linear": discounted.LCFRSolver,
            "discounted": discounted.DCFRSolver,
        }
        self.solver: Any = factory[variant](self.game)
        self.exploit_module: Any = importlib.import_module(
            "open_spiel.python.algorithms.exploitability"
        )
        self.policy_module: Any = importlib.import_module("open_spiel.python.policy")

    def step(self) -> None:
        self.solver.evaluate_and_update_policy()

    def average_policy(self) -> FloatArray:
        policy = self.solver.average_policy()
        result = np.zeros_like(self.tree.legal)
        for info, (state, actions) in enumerate(
            zip(self.states, self.actions, strict=True)
        ):
            probabilities = policy.action_probabilities(state)
            for slot, action in enumerate(actions):
                result[info, slot] = probabilities[action]
        return result

    def value(self) -> float:
        scoring = importlib.import_module(
            "open_spiel.python.algorithms.expected_game_score"
        )
        return float(
            scoring.policy_value(
                self.game.new_initial_state(), [self.solver.average_policy()] * 2
            )[0]
        )

    def exploitability(self, policy: FloatArray | None = None) -> float:
        """Use OpenSpiel's independent BR on its own or the mapped own policy."""
        if policy is None:
            reference_policy = self.solver.average_policy()
        else:
            self.tree.validate_policy(policy)
            reference_policy = self.policy_module.TabularPolicy(self.game)
            for info, (state, actions) in enumerate(
                zip(self.states, self.actions, strict=True)
            ):
                row = reference_policy.policy_for_key(state.information_state_string())
                row[:] = 0
                for slot, action in enumerate(actions):
                    row[action] = policy[info, slot]
        return float(self.exploit_module.exploitability(self.game, reference_policy))
