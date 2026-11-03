"""Reconcile public off-grid betting history with a trained abstract public tree.

The actual ledger is replayed unchanged using synthetic cards, which cannot
change nonterminal betting rules. A separate virtual ledger follows translated
raises. Only the resulting virtual public fields are used for lookup, with the
player's ACTUAL own cards/public board attached. No hidden real cards are inputs.
Irreconcilable virtual all-ins/turn order return explicit failure, never rewrite
actual stacks. Mapping coins are stable per episode/public prefix.
"""

import hashlib
import json
from dataclasses import dataclass, replace
from typing import Literal

from numpy.random import PCG64, Generator

from poker_ai.cards import Deck
from poker_ai.engine import Action, ActionKind, Observation, new_hand
from poker_ai.training.no_limit import NoLimitRules

Scheme = Literal["nearest", "pseudo_harmonic"]


@dataclass(frozen=True, slots=True)
class MappedRaise:
    history_index: int
    actual_total: int
    virtual_total: int
    actual_pot_fraction: float
    virtual_pot_fraction: float
    clipped_to_virtual_bounds: bool


@dataclass(frozen=True)
class ShadowResult:
    observation: Observation | None
    raises: tuple[MappedRaise, ...]
    failure: str | None
    seat_offset: int
    starting_stack_mismatch: bool
    passive_kind_changes: int


def _price(observation: Observation) -> int:
    assert observation.legal_actions is not None
    return (
        observation.street_commitments[observation.seat]
        + observation.legal_actions.call_amount
    )


def reconcile(
    observation: Observation,
    rules: NoLimitRules,
    *,
    episode_seed: int,
    scheme: Scheme = "pseudo_harmonic",
    actual_blinds: tuple[int, int] = (1, 2),
) -> ShadowResult:
    """Map public history; return an explicit failure if the virtual tree closes.

    Actual and virtual monetary ledgers remain separate. Seat rotation maps the
    actual button to the trained button. Initial stack-depth differences are
    recorded; normalization does not make different depths strategically equal.
    The caller must discard failed shadows or use a documented legal fallback.
    """
    if (
        observation.terminal
        or observation.actor != observation.seat
        or observation.legal_actions is None
        or len(observation.stacks) != 2
    ):
        raise ValueError("need an acting heads-up observation")
    if type(episode_seed) is not int or episode_seed < 0:
        raise ValueError("mapping episode seed must be a nonnegative integer")
    if scheme not in ("nearest", "pseudo_harmonic"):
        raise ValueError("unknown public history mapping")
    starting = tuple(
        s + p
        for s, p in zip(observation.stacks, observation.total_commitments, strict=True)
    )
    actual = new_hand(
        starting,
        Deck(),
        button=observation.button,
        small_blind=actual_blinds[0],
        big_blind=actual_blinds[1],
    )
    contexts = []
    for record in observation.history:
        if actual.actor != record.seat or actual.street != record.street:
            raise ValueError("inconsistent actual public history actor/street")
        context = actual.observe(record.seat)
        contexts.append(context)
        actual = actual.apply(record.action)
        if actual.history[-1].chips_paid != record.chips_paid:
            raise ValueError("inconsistent actual public history chip cost")
    if (
        actual.terminal
        or actual.actor != observation.actor
        or actual.street != observation.street
        or actual.stacks != observation.stacks
        or actual.total_commitments != observation.total_commitments
        or actual.street_commitments != observation.street_commitments
        or actual.pot != observation.pot
        or len(actual.board) != len(observation.board)
    ):
        raise ValueError("public history does not reconstruct the observation")
    offset = (rules.button - observation.button) % 2
    mismatch = any(
        starting[i] * rules.big_blind
        != rules.stacks[(i + offset) % 2] * actual_blinds[1]
        for i in range(2)
    )
    virtual = new_hand(
        rules.stacks,
        Deck(),
        button=rules.button,
        small_blind=rules.small_blind,
        big_blind=rules.big_blind,
    )
    mapped: list[MappedRaise] = []
    passive_changes = 0
    prefix = hashlib.sha256(
        json.dumps((episode_seed, starting, observation.button, actual_blinds)).encode()
    )

    def failure(reason: str) -> ShadowResult:
        return ShadowResult(
            None, tuple(mapped), reason, offset, mismatch, passive_changes
        )

    for index, (record, context) in enumerate(
        zip(observation.history, contexts, strict=True)
    ):
        if virtual.terminal:
            return failure("virtual hand terminated before actual history")
        if (
            virtual.actor != (record.seat + offset) % 2
            or virtual.street != record.street
        ):
            return failure("virtual actor/street differs from actual public path")
        assert virtual.actor is not None
        virtual_context = virtual.observe(virtual.actor)
        legal = virtual.legal_actions
        prefix.update(
            json.dumps(
                (
                    record.seat,
                    int(record.street),
                    record.action.kind.value,
                    record.action.amount,
                    record.chips_paid,
                )
            ).encode()
        )
        if record.action.kind == ActionKind.RAISE_TO:
            if legal.min_raise_to is None or legal.max_raise_to is None:
                return failure("virtual context cannot raise")
            assert (
                context.legal_actions is not None and record.action.amount is not None
            )
            actual_pot = context.pot + context.legal_actions.call_amount
            virtual_pot = virtual_context.pot + legal.call_amount
            increment = record.action.amount - _price(context)
            desired = _price(virtual_context) + (
                2 * increment * virtual_pot + actual_pot
            ) // (2 * actual_pot)
            bounded = min(legal.max_raise_to, max(legal.min_raise_to, desired))
            rng = Generator(
                PCG64(int.from_bytes(prefix.copy().digest()[:16], "little"))
            )
            total = rules.action_abstraction.translate(
                virtual_context, bounded, rng=rng, scheme=scheme
            )
            mapped.append(
                MappedRaise(
                    index,
                    record.action.amount,
                    total,
                    increment / actual_pot,
                    (total - _price(virtual_context)) / virtual_pot,
                    desired != bounded,
                )
            )
            move = Action(ActionKind.RAISE_TO, total)
        elif record.action.kind in (ActionKind.CALL, ActionKind.CHECK):
            move = Action(ActionKind.CHECK if legal.can_check else ActionKind.CALL)
            passive_changes += int(move.kind != record.action.kind)
        else:
            move = Action(ActionKind.FOLD)
        virtual = virtual.apply(move)
    if virtual.terminal:
        return failure("virtual hand terminated while actual hand still acts")
    if (
        virtual.actor != (observation.seat + offset) % 2
        or virtual.street != observation.street
    ):
        return failure("current virtual actor/street mismatch")
    assert virtual.actor is not None
    translated = replace(
        virtual.observe(virtual.actor),
        hole_cards=observation.hole_cards,
        board=observation.board,
    )
    return ShadowResult(
        translated, tuple(mapped), None, offset, mismatch, passive_changes
    )
