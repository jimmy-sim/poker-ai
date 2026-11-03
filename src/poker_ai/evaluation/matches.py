"""Independent duplicate deals replayed with the two policies in exchanged seats."""

from dataclasses import dataclass

from numpy.random import PCG64, Generator, SeedSequence

from poker_ai.cards import Deck
from poker_ai.engine import new_hand
from poker_ai.evaluation.baselines import Bot
from poker_ai.training.no_limit import NoLimitRules


@dataclass(frozen=True)
class HandResult:
    profit: int
    actions: int


def play_hand(
    own: Bot,
    opponent: Bot,
    rules: NoLimitRules,
    deck: Deck,
    own_seat: int,
    *,
    action_seed: tuple[int, ...],
    episode_seed: int,
    max_actions: int = 256,
) -> HandResult:
    if type(own_seat) is not int or own_seat not in (0, 1):
        raise ValueError("own seat must be zero or one")
    state = new_hand(
        rules.stacks,
        deck,
        button=rules.button,
        small_blind=rules.small_blind,
        big_blind=rules.big_blind,
    )
    streams = SeedSequence(action_seed).spawn(2)
    rngs = [Generator(PCG64(stream)) for stream in streams]
    count = 0
    while not state.terminal:
        if count >= max_actions:
            raise RuntimeError("match action budget exceeded; no truncation/export")
        assert state.actor is not None
        actor = state.actor
        bot = own if actor == own_seat else opponent
        move = bot.act(state.observe(actor), rng=rngs[actor], episode_seed=episode_seed)
        state = state.apply(move)
        count += 1
    if sum(state.net_payoffs) != 0:
        raise ArithmeticError("match is not zero-sum")
    return HandResult(state.net_payoffs[own_seat], count)


def duplicate_pair(
    own: Bot,
    opponent: Bot,
    rules: NoLimitRules,
    deck: Deck,
    *,
    action_seed: tuple[int, ...],
    episode_seed: int,
) -> tuple[HandResult, HandResult]:
    def run(seat: int) -> HandResult:
        return play_hand(
            own,
            opponent,
            rules,
            deck,
            seat,
            action_seed=action_seed + (seat,),
            episode_seed=episode_seed,
        )

    return run(0), run(1)
