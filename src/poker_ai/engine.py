"""Immutable 2–6-seat single-board no-limit Hold'em simulation.

Integer chips, two forced blinds, no ante/rake/straddle. All chance is supplied
through an explicit ordered Deck. Production code uses only the own evaluator;
independent poker libraries belong exclusively to validation runners.
"""

from collections.abc import Iterable
from dataclasses import dataclass, replace
from enum import Enum, IntEnum

from poker_ai.cards import Deck
from poker_ai.evaluator import evaluate_best


class Street(IntEnum):
    PREFLOP = 0
    FLOP = 1
    TURN = 2
    RIVER = 3


class ActionKind(Enum):
    FOLD = "fold"
    CHECK = "check"
    CALL = "call"
    RAISE_TO = "raise_to"


def _integer(value: int, name: str, minimum: int = 0) -> None:
    if type(value) is not int:
        raise TypeError(f"{name} must be a built-in int")
    if value < minimum:
        raise ValueError(f"{name} must be at least {minimum}")


@dataclass(frozen=True, slots=True)
class Action:
    """A raise amount is total street commitment, not its incremental cost."""

    kind: ActionKind
    amount: int | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.kind, ActionKind):
            raise TypeError("kind must be an ActionKind")
        if self.kind == ActionKind.RAISE_TO:
            if self.amount is None:
                raise ValueError("raise_to requires an amount")
            _integer(self.amount, "raise amount", 1)
        elif self.amount is not None:
            raise ValueError("only raise_to takes an amount")


@dataclass(frozen=True, slots=True)
class LegalActions:
    """Inclusive raise bounds; a short all-in has identical min/max bounds."""

    can_fold: bool
    can_check: bool
    call_amount: int
    min_raise_to: int | None
    max_raise_to: int | None


@dataclass(frozen=True, slots=True)
class Pot:
    amount: int
    eligible: tuple[int, ...]
    uncalled: bool = False


def build_pots(
    contributions: tuple[int, ...], folded: tuple[bool, ...]
) -> tuple[Pot, ...]:
    """Build eligibility layers, merging identical contested eligibility sets.

    A sole-contributor top layer is uncalled money and is returned. Folded players
    fund pots but cannot win contested chips. Merging identical eligibility avoids
    allocating an odd chip multiple times to an artificial series of side pots.
    """
    if not 2 <= len(contributions) <= 6 or len(contributions) != len(folded):
        raise ValueError("pot vectors need equal lengths for two through six seats")
    for amount in contributions:
        _integer(amount, "contribution")
    if any(type(flag) is not bool for flag in folded):
        raise TypeError("folded flags must be booleans")
    pots: list[Pot] = []
    previous = 0
    for cap in sorted({amount for amount in contributions if amount > 0}):
        contributors = tuple(
            i for i, amount in enumerate(contributions) if amount >= cap
        )
        uncalled = len(contributors) == 1
        eligible = (
            contributors
            if uncalled
            else tuple(i for i in contributors if not folded[i])
        )
        if not eligible:
            raise ValueError("contested pot has no eligible player")
        amount = (cap - previous) * len(contributors)
        if (
            pots
            and not uncalled
            and not pots[-1].uncalled
            and pots[-1].eligible == eligible
        ):
            pots[-1] = Pot(pots[-1].amount + amount, eligible)
        else:
            pots.append(Pot(amount, eligible, uncalled))
        previous = cap
    return tuple(pots)


@dataclass(frozen=True, slots=True)
class ActionRecord:
    seat: int
    street: Street
    action: Action
    chips_paid: int


@dataclass(frozen=True, slots=True)
class Observation:
    """Player-facing data: own cards and public data, never the dealer's state."""

    seat: int
    actor: int | None
    hole_cards: tuple[int, ...]
    board: tuple[int, ...]
    button: int
    street: Street
    stacks: tuple[int, ...]
    folded: tuple[bool, ...]
    street_commitments: tuple[int, ...]
    total_commitments: tuple[int, ...]
    pot: int
    history: tuple[ActionRecord, ...]
    legal_actions: LegalActions | None
    terminal: bool


@dataclass(frozen=True, slots=True)
class HoldemState:
    """Dealer state, produced by new_hand/apply; do not hand this object to bots."""

    starting_stacks: tuple[int, ...]
    stacks: tuple[int, ...]
    hole_cards: tuple[tuple[int, ...], ...]
    board: tuple[int, ...]
    burned: tuple[int, ...]
    deck: Deck
    button: int
    small_blind: int
    big_blind: int
    street: Street
    folded: tuple[bool, ...]
    street_commitments: tuple[int, ...]
    total_commitments: tuple[int, ...]
    current_bet: int
    last_full_raise: int
    last_action_bet: tuple[int | None, ...]
    pending: tuple[int, ...]
    payouts: tuple[int, ...]
    uncalled_returns: tuple[int, ...]
    history: tuple[ActionRecord, ...] = ()
    terminal: bool = False
    pots: tuple[Pot, ...] = ()
    pot_winners: tuple[tuple[int, ...], ...] = ()
    settlement_pots: tuple[Pot, ...] = ()

    def __post_init__(self) -> None:
        size = len(self.starting_stacks)
        vectors = (
            self.stacks,
            self.hole_cards,
            self.folded,
            self.street_commitments,
            self.total_commitments,
            self.last_action_bet,
            self.payouts,
            self.uncalled_returns,
        )
        if not 2 <= size <= 6 or any(
            not isinstance(vec, tuple) or len(vec) != size for vec in vectors
        ):
            raise ValueError("inconsistent immutable seat vectors")
        if any(
            value < 0
            for vec in (self.stacks, self.street_commitments, self.total_commitments)
            for value in vec
        ):
            raise ValueError("negative chips in state")
        if any(
            street > total
            for street, total in zip(
                self.street_commitments, self.total_commitments, strict=True
            )
        ):
            raise ValueError("street commitment exceeds total commitment")
        if sum(self.stacks) + self.pot != sum(self.starting_stacks):
            raise ValueError("state violates chip conservation")
        if self.terminal and self.pending:
            raise ValueError("terminal state cannot have pending actions")

    @property
    def actor(self) -> int | None:
        return None if self.terminal or not self.pending else self.pending[0]

    @property
    def pot(self) -> int:
        return 0 if self.terminal else sum(self.total_commitments)

    @property
    def net_payoffs(self) -> tuple[int, ...]:
        if not self.terminal:
            raise ValueError("net payoffs require a terminal hand")
        return tuple(
            end - start
            for end, start in zip(self.stacks, self.starting_stacks, strict=True)
        )

    @property
    def legal_actions(self) -> LegalActions:
        actor = self.actor
        if actor is None:
            raise ValueError("no actor can act in this state")
        owed = max(0, self.current_bet - self.street_commitments[actor])
        previous = self.last_action_bet[actor]
        reopened = (
            previous is None
            or previous == 0
            or self.current_bet - previous >= self.last_full_raise
        )
        opponent_can_respond = any(
            i != actor
            and not self.folded[i]
            and self.street_commitments[i] + self.stacks[i] > self.current_bet
            for i in range(len(self.stacks))
        )
        maximum = self.street_commitments[actor] + self.stacks[actor]
        low = high = None
        if reopened and opponent_can_respond and maximum > self.current_bet:
            low, high = min(self.current_bet + self.last_full_raise, maximum), maximum
        return LegalActions(True, owed == 0, min(owed, self.stacks[actor]), low, high)

    def observe(self, seat: int) -> Observation:
        _integer(seat, "seat")
        if seat >= len(self.stacks):
            raise ValueError("seat is outside the table")
        return Observation(
            seat=seat,
            actor=self.actor,
            hole_cards=self.hole_cards[seat],
            board=self.board,
            button=self.button,
            street=self.street,
            stacks=self.stacks,
            folded=self.folded,
            street_commitments=self.street_commitments,
            total_commitments=self.total_commitments,
            pot=self.pot,
            history=self.history,
            legal_actions=self.legal_actions if seat == self.actor else None,
            terminal=self.terminal,
        )

    def apply(self, action: Action) -> "HoldemState":
        """Validate and apply one actor action, then deal/settle automatic steps."""
        if not isinstance(action, Action):
            raise TypeError("action must be an Action")
        actor = self.actor
        if actor is None:
            raise ValueError("no actor can act in this state")
        legal = self.legal_actions
        stacks, street_paid, total = (
            list(self.stacks),
            list(self.street_commitments),
            list(self.total_commitments),
        )
        folded, last = list(self.folded), list(self.last_action_bet)
        price, last_raise, paid = self.current_bet, self.last_full_raise, 0
        pending = self.pending[1:]
        settlement_pots = self.settlement_pots
        if action.kind == ActionKind.FOLD:
            folded[actor] = True
            # The last funded player may fold the main pot after already winning
            # a side pot by default. Preserve that earned pot; it cannot vanish.
            funded = tuple(
                i for i in range(len(stacks)) if not self.folded[i] and stacks[i] > 0
            )
            if funded == (actor,):
                existing = build_pots(self.total_commitments, self.folded)
                if any(
                    not pot.uncalled and pot.eligible == (actor,) for pot in existing
                ):
                    settlement_pots = tuple(
                        pot
                        if pot.uncalled or len(pot.eligible) == 1
                        else Pot(
                            pot.amount, tuple(i for i in pot.eligible if not folded[i])
                        )
                        for pot in existing
                    )
        elif action.kind == ActionKind.CHECK:
            if not legal.can_check:
                raise ValueError("cannot check while facing a bet")
            last[actor] = price
        elif action.kind == ActionKind.CALL:
            if legal.call_amount == 0:
                raise ValueError("nothing to call; use check")
            paid = legal.call_amount
            last[actor] = price
        else:
            target = action.amount
            if (
                target is None
                or legal.min_raise_to is None
                or legal.max_raise_to is None
            ):
                raise ValueError("raise is not available")
            if not legal.min_raise_to <= target <= legal.max_raise_to:
                raise ValueError("raise target is outside legal bounds")
            paid = target - street_paid[actor]
            increment = target - price
            if increment >= last_raise:
                last_raise = increment
            price = target
            last[actor] = target
            pending = tuple(
                i
                for i in _clockwise(actor + 1, len(stacks))
                if i != actor and not folded[i] and stacks[i] > 0
            )
        stacks[actor] -= paid
        street_paid[actor] += paid
        total[actor] += paid
        record = ActionRecord(actor, self.street, action, paid)
        updated = replace(
            self,
            stacks=tuple(stacks),
            street_commitments=tuple(street_paid),
            total_commitments=tuple(total),
            folded=tuple(folded),
            current_bet=price,
            last_full_raise=last_raise,
            last_action_bet=tuple(last),
            pending=pending,
            settlement_pots=settlement_pots,
            history=self.history + (record,),
        )
        return _progress(updated)


def _clockwise(start: int, size: int) -> tuple[int, ...]:
    return tuple((start + offset) % size for offset in range(size))


def _settle(state: HoldemState) -> HoldemState:
    live = tuple(i for i, folded in enumerate(state.folded) if not folded)
    pots = state.settlement_pots or build_pots(state.total_commitments, state.folded)
    payouts = [0] * len(state.stacks)
    returned = [0] * len(state.stacks)
    winners_by_pot = []
    ranks = (
        {}
        if len(live) == 1
        else {i: evaluate_best(state.hole_cards[i] + state.board) for i in live}
    )
    for pot in pots:
        if pot.uncalled:
            winners = pot.eligible
            returned[winners[0]] += pot.amount
        elif len(pot.eligible) == 1:
            winners = pot.eligible
        else:
            best = max(ranks[i] for i in pot.eligible)
            winners = tuple(i for i in pot.eligible if ranks[i] == best)
        order = tuple(
            i for i in _clockwise(state.button + 1, len(state.stacks)) if i in winners
        )
        share, odd = divmod(pot.amount, len(order))
        for index, seat in enumerate(order):
            payouts[seat] += share + (1 if index < odd else 0)
        winners_by_pot.append(winners)
    return replace(
        state,
        stacks=tuple(
            stack + payout for stack, payout in zip(state.stacks, payouts, strict=True)
        ),
        payouts=tuple(payouts),
        uncalled_returns=tuple(returned),
        pending=(),
        terminal=True,
        pots=pots,
        pot_winners=tuple(winners_by_pot),
    )


def _deal_next_street(state: HoldemState) -> HoldemState:
    burn, deck = state.deck.draw(1)
    shown, deck = deck.draw(3 if state.street == Street.PREFLOP else 1)
    pending = tuple(
        i
        for i in _clockwise(state.button + 1, len(state.stacks))
        if not state.folded[i] and state.stacks[i] > 0
    )
    return replace(
        state,
        street=Street(state.street + 1),
        board=state.board + shown,
        burned=state.burned + burn,
        deck=deck,
        street_commitments=(0,) * len(state.stacks),
        current_bet=0,
        last_full_raise=state.big_blind,
        last_action_bet=(None,) * len(state.stacks),
        pending=pending,
    )


def _progress(state: HoldemState) -> HoldemState:
    """Close completed rounds and all-in runouts without meaningless side bets."""
    while True:
        live = tuple(i for i in range(len(state.stacks)) if not state.folded[i])
        if len(live) == 1:
            return _settle(state)
        funded = tuple(i for i in live if state.stacks[i] > 0)
        if len(funded) == 1:
            actor = funded[0]
            effective_price = max(
                state.street_commitments[i] for i in live if i != actor
            )
            if state.street_commitments[actor] < effective_price:
                return replace(state, current_bet=effective_price, pending=(actor,))
            # A free fold can leave an unacted check/fold choice this street.
            # Preserve it once; all-in calls and later runout streets close
            # automatically.
            if (
                actor in state.pending
                and state.history
                and state.history[-1].street == state.street
                and state.history[-1].action.kind == ActionKind.FOLD
            ):
                return replace(state, current_bet=effective_price, pending=(actor,))
            state = replace(state, pending=())
        elif not funded:
            state = replace(state, pending=())
        else:
            pending = tuple(i for i in state.pending if i in funded)
            if pending:
                return replace(state, pending=pending)
        if state.street == Street.RIVER:
            return _settle(state)
        state = _deal_next_street(state)


def new_hand(
    stacks: Iterable[int],
    deck: Deck,
    *,
    button: int = 0,
    small_blind: int = 1,
    big_blind: int = 2,
) -> HoldemState:
    """Deal from an explicit full deck, post blinds, and expose the first action.

    Use Deck.shuffled(caller_rng) for stochastic deals. Heads-up button posts the
    small blind and acts first preflop; otherwise the first seat left of button
    posts the small blind. Cards are dealt one per seat per pass left of button.
    """
    initial = tuple(stacks)
    size = len(initial)
    if not 2 <= size <= 6:
        raise ValueError("table must have two through six seats")
    for stack in initial:
        _integer(stack, "starting stack", 1)
    _integer(button, "button")
    _integer(small_blind, "small blind", 1)
    _integer(big_blind, "big blind", 1)
    if button >= size or small_blind > big_blind:
        raise ValueError("invalid button or blind configuration")
    if not isinstance(deck, Deck):
        raise TypeError("deck must be an explicit Deck")
    if len(deck) != 52:
        raise ValueError("a hand requires a full 52-card deck")
    holes: list[list[int]] = [[] for _ in initial]
    for _ in range(2):
        for seat in _clockwise(button + 1, size):
            card, deck = deck.draw(1)
            holes[seat].append(card[0])
    small = button if size == 2 else (button + 1) % size
    big = (small + 1) % size
    paid = [0] * size
    paid[small] = min(initial[small], small_blind)
    paid[big] = min(initial[big], big_blind)
    remaining = tuple(
        stack - amount for stack, amount in zip(initial, paid, strict=True)
    )
    pending = tuple(i for i in _clockwise(big + 1, size) if remaining[i] > 0)
    state = HoldemState(
        starting_stacks=initial,
        stacks=remaining,
        hole_cards=tuple(tuple(hand) for hand in holes),
        board=(),
        burned=(),
        deck=deck,
        button=button,
        small_blind=small_blind,
        big_blind=big_blind,
        street=Street.PREFLOP,
        folded=(False,) * size,
        street_commitments=tuple(paid),
        total_commitments=tuple(paid),
        current_bet=big_blind,
        last_full_raise=big_blind,
        last_action_bet=(None,) * size,
        pending=pending,
        payouts=(0,) * size,
        uncalled_returns=(0,) * size,
    )
    return _progress(state)
