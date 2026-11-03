"""Independent OpenSpiel parser/CFR/BR; outputs are comparison-only."""

import importlib
from typing import Any

from poker_ai.postflop.tree import Policy as Policy
from poker_ai.postflop.tree import SpotTree as SpotTree


class Reference:
    """Independent native EFG parser, solver and best-response calculator."""

    def __init__(self, tree: SpotTree) -> None:
        self.pyspiel: Any = importlib.import_module("pyspiel")
        self.tree = tree
        self.game: Any = self.pyspiel.load_efg_game(tree.efg())
        self.keys = [""] * len(tree.keys)
        self.actions: list[tuple[int, ...]] = [()] * len(tree.keys)
        aligned: dict[int, Any] = {0: self.game.new_initial_state()}
        reverse: dict[str, int] = {}
        for node, state in enumerate(tree.states):
            other = aligned.pop(node)
            assert (
                state.terminal == other.is_terminal()
                and state.chance == other.is_chance_node()
            )
            if state.terminal:
                assert abs(other.returns()[0] - tree.payoffs[node]) < 1e-12
                assert abs(sum(other.returns())) < 1e-12
                continue
            label_to_action = {
                other.action_to_string(a): a for a in other.legal_actions()
            }
            labels = tuple(
                tree.chance_label(node, a) if state.chance else f"a{a}"
                for a in state.actions
            )
            assert set(labels) == set(label_to_action)
            native_actions = tuple(label_to_action[label] for label in labels)
            if state.chance:
                native_probs = dict(other.chance_outcomes())
                assert all(
                    abs(native_probs[a] - p) < 1e-12
                    for a, p in zip(
                        native_actions, tree.chance_probabilities[node], strict=True
                    )
                )
            else:
                assert state.actor == other.current_player()
                info = tree.information[node]
                key = other.information_state_string()
                assert not self.keys[info] or self.keys[info] == key
                assert reverse.setdefault(key, info) == info
                self.keys[info] = key
                self.actions[info] = native_actions
            for action, child in zip(native_actions, tree.children[node], strict=True):
                aligned[child] = other.child(action)
        assert all(self.keys) and len(reverse) == len(tree.keys)
        self.solver: Any = self.pyspiel.CFRPlusSolver(self.game)
        self.iteration = 0

    def train_to(self, iteration: int) -> None:
        if type(iteration) is not int or iteration < self.iteration:
            raise ValueError("reference iterations must increase")
        while self.iteration < iteration:
            self.solver.evaluate_and_update_policy()
            self.iteration += 1

    def policy(self) -> Policy:
        table = self.solver.tabular_average_policy().policy_table()
        return tuple(
            tuple(float(dict(table[key])[a]) for a in actions)
            for key, actions in zip(self.keys, self.actions, strict=True)
        )

    def native_policy(self, policy: Policy) -> Any:
        self.tree.validate_policy(policy)
        return self.pyspiel.TabularPolicy(
            {
                key: list(zip(actions, row, strict=True))
                for key, actions, row in zip(
                    self.keys, self.actions, policy, strict=True
                )
            }
        )

    def exploitability(self, policy: Policy) -> float:
        return float(self.pyspiel.exploitability(self.game, self.native_policy(policy)))

    def value(self, policy: Policy) -> float:
        return float(
            self.pyspiel.expected_returns(
                self.game.new_initial_state(), self.native_policy(policy), -1, True
            )[0]
        )
