"""Exhaustive independent rule checks; optional OpenSpiel stays at this boundary."""

import importlib
from typing import Any

from poker_ai.toy.games import GameName, ToyState


def validate_game_rules(game: GameName) -> dict[str, int]:
    """Check chance, actions, actor, payoff, and a bijection of information sets."""
    pyspiel = importlib.import_module("pyspiel")
    reference = pyspiel.load_game("kuhn_poker" if game == "kuhn" else "leduc_poker")
    forward: dict[str, str] = {}
    backward: dict[str, str] = {}
    counts = {"nodes": 0, "terminals": 0, "chance_nodes": 0}

    def visit(own: ToyState, other: Any) -> None:
        counts["nodes"] += 1
        assert own.terminal == other.is_terminal(), "terminal disagreement"
        assert own.chance == other.is_chance_node(), "chance disagreement"
        if own.terminal:
            assert abs(own.payoff - other.returns()[0]) < 1e-12
            assert abs(sum(other.returns())) < 1e-12
            counts["terminals"] += 1
            return
        if own.chance:
            counts["chance_nodes"] += 1
            outcomes = dict(other.chance_outcomes())
            assert own.actions == tuple(outcomes)
            assert all(abs(p - 1 / len(own.actions)) < 1e-12 for p in outcomes.values())
        else:
            assert own.actor == other.current_player()
            key, ref_key = own.information, other.information_state_string()
            assert forward.setdefault(key, ref_key) == ref_key
            assert backward.setdefault(ref_key, key) == key
        mapped = tuple(
            action
            if own.chance or game == "leduc"
            else int(
                action == 2 or (action == 1 and own.paid[own.actor] < max(own.paid))
            )
            for action in own.actions
        )
        assert mapped == tuple(other.legal_actions()), "legal-action disagreement"
        for action, reference_action in zip(own.actions, mapped, strict=True):
            visit(own.child(action), other.child(reference_action))

    visit(ToyState(game), reference.new_initial_state())
    return counts | {"information_sets": len(forward)}
