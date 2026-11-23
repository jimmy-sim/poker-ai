"""Use exact acting turn and river information without changing the old q8 tree."""

import numpy as np

from poker_ai.postflop.matrix import MatrixTree, recall_violations
from poker_ai.postflop.tree import SpotTree
from poker_ai.training.holdem import exact_information


def exact_turn_candidate(source: SpotTree, control: MatrixTree) -> MatrixTree:
    """Split q8 turn groups; keep exact game, river keys and action menus.

    `MatrixTree.build(source)` uses only the acting player's public history
    and private cards on both streets. The control is the historical
    q8-turn/exact-river partition. Returning the exact tree keeps the
    original game and chance arrays intact; each candidate information row
    is the exact acting observation, so no hidden opponent cards enter a key.
    """
    exact = MatrixTree.build(source)
    if exact.encoding != "exact" or control.source is not source:
        raise ValueError("candidate requires the same exact source tree")
    if len(exact.keys) != len(source.keys) or not np.array_equal(
        exact.exact_to_abstract, np.arange(len(source.keys))
    ):
        raise ArithmeticError("exact acting information changed")
    if len(control.keys) > len(exact.keys) or recall_violations(exact):
        raise ArithmeticError("invalid exact-turn refinement")
    if control.node_actions != exact.node_actions:
        raise ArithmeticError("concrete game action menu changed")
    for i, node in enumerate(source.representatives):
        state = source.states[node]
        if state.dealer is None:
            raise ArithmeticError("decision has no acting observation")
        observed = state.dealer.observe(state.actor)
        candidate_key = exact.keys[i]
        control_info = int(control.exact_to_abstract[i])
        if candidate_key != exact_information(observed):
            raise ArithmeticError("candidate key is not exact acting information")
        if len(observed.board) == 5 and control.keys[control_info] != candidate_key:
            raise ArithmeticError("historical exact river key changed")
        if len(observed.board) not in (4, 5):
            raise ArithmeticError("outside fixed turn-start game")
        if control.actions[control_info] != source.menus[i]:
            raise ArithmeticError("control action menu changed")
    for name in (
        "player",
        "valid",
        "chance_edges",
        "chance_reach",
        "terminal_values",
    ):
        if not np.array_equal(getattr(exact, name), getattr(control, name)):
            raise ArithmeticError(f"exact game field changed: {name}")
    if not np.array_equal(exact.owners, np.asarray(source.owners)):
        raise ArithmeticError("exact owners changed")
    return exact
