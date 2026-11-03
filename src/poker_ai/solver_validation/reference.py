"""Own spot tree exported to OpenSpiel's native EFG parser and CFR+ solver.

The solver/BR implementation is independent; spot mechanics/export originate in
this project and are validated separately. Reference policies remain comparison
artifacts and never enter own training, checkpoints or agent lookup inputs.
"""

import importlib
import math
from dataclasses import dataclass
from typing import Any

from poker_ai.solver_validation.spots import Spot, SpotState

Policy = tuple[tuple[float, ...], ...]


@dataclass(frozen=True)
class SpotTree:
    spot: Spot
    states: tuple[SpotState, ...]
    children: tuple[tuple[int, ...], ...]
    information: tuple[int, ...]
    representatives: tuple[int, ...]
    keys: tuple[str, ...]
    owners: tuple[int, ...]
    menus: tuple[tuple[int, ...], ...]
    chance_probabilities: tuple[tuple[float, ...], ...]
    payoffs: tuple[float, ...]

    @classmethod
    def build(cls, spot: Spot) -> "SpotTree":
        states: list[SpotState] = []
        children: list[tuple[int, ...]] = []
        information: list[int] = []
        representatives: list[int] = []
        keys: list[str] = []
        owners: list[int] = []
        menus: list[tuple[int, ...]] = []
        probabilities: list[tuple[float, ...]] = []
        payoffs: list[float] = []
        lookup: dict[str, int] = {}

        def visit(state: SpotState) -> int:
            if len(states) >= spot.max_tree_nodes:
                raise ValueError("spot tree exceeded its declared node budget")
            index = len(states)
            states.append(state)
            children.append(())
            info = -1
            if not state.chance and not state.terminal:
                key = state.information
                if key not in lookup:
                    lookup[key] = len(keys)
                    keys.append(key)
                    owners.append(state.actor)
                    menus.append(state.actions)
                    representatives.append(index)
                info = lookup[key]
                assert menus[info] == state.actions and owners[info] == state.actor
            information.append(info)
            probabilities.append(state.chance_probabilities if state.chance else ())
            payoffs.append(state.payoff if state.terminal else 0.0)
            children[index] = tuple(visit(state.child(a)) for a in state.actions)
            return index

        visit(SpotState(spot))
        return cls(
            spot,
            tuple(states),
            tuple(children),
            tuple(information),
            tuple(representatives),
            tuple(keys),
            tuple(owners),
            tuple(menus),
            tuple(probabilities),
            tuple(payoffs),
        )

    def validate_policy(self, policy: Policy) -> None:
        if len(policy) != len(self.keys):
            raise ValueError("wrong policy information sets")
        for row, menu in zip(policy, self.menus, strict=True):
            if (
                len(row) != len(menu)
                or any(not math.isfinite(p) or p < 0 for p in row)
                or abs(sum(row) - 1) > 1e-12
            ):
                raise ValueError("invalid spot policy")

    def uniform(self) -> Policy:
        return tuple((1 / len(menu),) * len(menu) for menu in self.menus)

    def values(self, policy: Policy) -> tuple[float, ...]:
        self.validate_policy(policy)
        values = list(self.payoffs)
        for node in reversed(range(len(self.states))):
            if self.states[node].terminal:
                continue
            probabilities = (
                self.chance_probabilities[node]
                if self.states[node].chance
                else policy[self.information[node]]
            )
            values[node] = math.fsum(
                p * values[child]
                for p, child in zip(probabilities, self.children[node], strict=True)
            )
        return tuple(values)

    def reaches(self, policy: Policy) -> tuple[float, ...]:
        self.validate_policy(policy)
        reach = [0.0] * len(self.states)
        reach[0] = 1.0
        for node, state in enumerate(self.states):
            if state.terminal:
                continue
            probabilities = (
                self.chance_probabilities[node]
                if state.chance
                else policy[self.information[node]]
            )
            for p, child in zip(probabilities, self.children[node], strict=True):
                reach[child] = reach[node] * p
        return tuple(reach)

    def cross(self, first: Policy, second: Policy) -> Policy:
        """Player-zero rows from first, player-one rows from second."""
        self.validate_policy(first)
        self.validate_policy(second)
        return tuple(
            a if owner == 0 else b
            for owner, a, b in zip(self.owners, first, second, strict=True)
        )

    def chance_label(self, node: int, action: int) -> str:
        state = self.states[node]
        prefix = "h" if state.first is None else "v" if state.second is None else "r"
        return f"{prefix}{action}"

    def efg(self) -> str:
        numbers = []
        counts = [0, 0]
        for owner in self.owners:
            counts[owner] += 1
            numbers.append(counts[owner])
        lines = [f'EFG 2 R "{self.spot.name}" {{ "P0" "P1" }}']
        chance = terminal = 0
        for node, state in enumerate(self.states):
            if state.terminal:
                terminal += 1
                value = self.payoffs[node]
                lines.append(f't "" {terminal} "" {{ {value:.17g} {-value:.17g} }}')
            elif state.chance:
                chance += 1
                outcomes = " ".join(
                    f'"{self.chance_label(node, a)}" {p:.17g}'
                    for a, p in zip(
                        state.actions, self.chance_probabilities[node], strict=True
                    )
                )
                lines.append(f'c "" {chance} "" {{ {outcomes} }} 0')
            else:
                info = self.information[node]
                number = numbers[info]
                labels = " ".join(f'"a{a}"' for a in state.actions)
                lines.append(
                    f'p "" {state.actor + 1} {number} "i{number}" {{ {labels} }} 0'
                )
        return "\n".join(lines) + "\n"


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
