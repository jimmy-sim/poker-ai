"""Independent evaluator/passive-payout controls on every configured card world."""

import importlib
from typing import Any

from poker_ai.engine import Action, ActionKind
from poker_ai.solver_validation.spots import Spot, spot_dealer


def verify_card_worlds(spot: Spot) -> dict[str, Any]:
    """Treys ranks showdown; own passive engine must pay +/- half the root pot.

    These prefixes have balanced paid amounts and an even pot. This exhaustive
    control covers configured private pairs/rivers, not every betting action or
    general engine rule; native EFG alignment covers all exported action/payoff
    nodes, and Phase 1 supplies the separate independent engine validation.
    """
    if len(spot.board) != 4 or spot.pot % 2:
        raise ValueError("passive control currently requires an even-pot turn spot")
    treys: Any = importlib.import_module("treys")
    evaluator = treys.Evaluator()

    def encoded(card: int) -> int:
        return int(treys.Card.new("23456789TJQKA"[card // 4] + "cdhs"[card % 4]))

    checked = 0
    for first, second, _ in spot.joint:
        holes = (spot.ranges[0][first].cards, spot.ranges[1][second].cards)
        used = set(holes[0] + holes[1] + spot.board)
        for river in (c for c in range(52) if c not in used):
            state = spot_dealer(spot, first, second, (river,))
            if state.total_commitments != (spot.pot // 2, spot.pot // 2):
                raise ValueError("passive control requires balanced root contributions")
            board = [encoded(c) for c in spot.board + (river,)]
            ranks = [evaluator.evaluate(board, [encoded(c) for c in h]) for h in holes]
            expected = (spot.pot // 2) * ((ranks[0] < ranks[1]) - (ranks[0] > ranks[1]))
            while not state.terminal:
                state = state.apply(
                    Action(
                        ActionKind.CHECK
                        if state.legal_actions.can_check
                        else ActionKind.CALL
                    )
                )
            if state.net_payoffs != (expected, -expected):
                raise ArithmeticError("independent passive showdown/payout mismatch")
            checked += 1
    if checked != spot.worlds:
        raise ArithmeticError("card-world enumeration missed a configured world")
    return {"worlds_checked": checked, "mismatches": 0, "reference": "treys==0.1.8"}
