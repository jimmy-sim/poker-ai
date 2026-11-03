"""Two-player Kuhn and Leduc, with explicit physical-card chance nodes.

Payoffs are net ante-sized chips, positive for player zero. A Leduc physical card
is rank*2+copy (J/Q/K ranks 0/1/2). Information sets distinguish physical copies,
as in default OpenSpiel Leduc; copies have no showdown priority. Both players
ante one. Player zero opens each street. Leduc allows two bets/raises per street,
size two then four. Kuhn permits a single one-chip bet.
"""

from dataclasses import dataclass, replace
from enum import IntEnum
from typing import Literal

GameName = Literal["kuhn", "leduc"]


class Move(IntEnum):
    FOLD = 0
    CALL = 1  # Check when commitments are equal.
    RAISE = 2


@dataclass(frozen=True, slots=True)
class ToyState:
    game: GameName
    cards: tuple[int, ...] = ()
    board: int | None = None
    street: int = 0
    histories: tuple[tuple[int, ...], ...] = ((),)
    paid: tuple[int, int] = (1, 1)
    actor: int = 0
    raises: int = 0
    checks: int = 0
    terminal: bool = False
    folded: int | None = None

    def __post_init__(self) -> None:
        if self.game not in ("kuhn", "leduc"):
            raise ValueError("unknown toy game")

    @property
    def chance(self) -> bool:
        return not self.terminal and (
            len(self.cards) < 2
            or (self.game == "leduc" and self.street == 1 and self.board is None)
        )

    @property
    def actions(self) -> tuple[int, ...]:
        if self.terminal:
            return ()
        if self.chance:
            size = 3 if self.game == "kuhn" else 6
            return tuple(card for card in range(size) if card not in self.cards)
        owed = self.paid[self.actor] < max(self.paid)
        cap = 1 if self.game == "kuhn" else 2
        return (
            ((int(Move.FOLD),) if owed else ())
            + (int(Move.CALL),)
            + ((int(Move.RAISE),) if self.raises < cap else ())
        )

    @property
    def chance_probabilities(self) -> tuple[float, ...]:
        if not self.chance:
            raise ValueError("chance probabilities require a chance node")
        return (1 / len(self.actions),) * len(self.actions)

    @property
    def information(self) -> str:
        if self.chance or self.terminal:
            raise ValueError("information key requires an acting player")
        history = "/".join("".join(map(str, seq)) for seq in self.histories)
        return f"{self.actor}:{self.cards[self.actor]}:{self.board}:{history}"

    @property
    def payoff(self) -> float:
        if not self.terminal:
            raise ValueError("payoff requires terminal state")
        if self.folded is not None:
            return float(-self.paid[0] if self.folded == 0 else self.paid[1])
        if self.game == "kuhn":
            ranks = tuple((False, card) for card in self.cards)
        else:
            assert self.board is not None
            public = self.board // 2
            ranks = tuple((card // 2 == public, card // 2) for card in self.cards)
        if ranks[0] == ranks[1]:
            return (self.paid[1] - self.paid[0]) / 2
        return float(self.paid[1] if ranks[0] > ranks[1] else -self.paid[0])

    def child(self, action: int) -> "ToyState":
        if type(action) is not int or action not in self.actions:
            raise ValueError("illegal action")
        if self.chance:
            if len(self.cards) < 2:
                return replace(self, cards=self.cards + (action,))
            return replace(self, board=action)
        actor = self.actor
        histories = self.histories[:-1] + (self.histories[-1] + (action,),)
        if action == Move.FOLD:
            return replace(self, histories=histories, terminal=True, folded=actor)
        paid = list(self.paid)
        raises, checks = self.raises, self.checks
        if action == Move.RAISE:
            size = 1 if self.game == "kuhn" else (2 if self.street == 0 else 4)
            paid[actor] = max(paid) + size
            raises, checks = raises + 1, 0
            closed = False
        else:
            paid[actor] = max(paid)
            checks += 1
            closed = raises > 0 or checks == 2
        result = replace(
            self,
            histories=histories,
            paid=(paid[0], paid[1]),
            actor=1 - actor,
            raises=raises,
            checks=checks,
        )
        if not closed:
            return result
        if self.game == "kuhn" or self.street == 1:
            return replace(result, terminal=True)
        return replace(
            result, street=1, actor=0, raises=0, checks=0, histories=histories + ((),)
        )
