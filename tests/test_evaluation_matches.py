from numpy.random import PCG64, Generator

from poker_ai.abstraction.actions import ActionAbstraction
from poker_ai.cards import Deck
from poker_ai.evaluation.baselines import Baseline
from poker_ai.evaluation.matches import duplicate_pair
from poker_ai.training.no_limit import NoLimitRules

RULES = NoLimitRules(
    action_abstraction=ActionAbstraction(
        fractions=((1, 1),), include_minimum=False, include_all_in=True
    )
)


def test_callbot_duplicate_cancels_each_deal_exactly() -> None:
    rng = Generator(PCG64(12))
    bot = Baseline("always_call", RULES)
    for i in range(25):
        first, second = duplicate_pair(
            bot, bot, RULES, Deck.shuffled(rng), action_seed=(31, i), episode_seed=i
        )
        assert first.profit + second.profit == 0
        assert first.actions == second.actions == 8


def test_random_and_value_baselines_complete_with_reproducible_actions() -> None:
    deck = Deck.shuffled(Generator(PCG64(24)))
    for kind in ("random", "always_call", "always_raise", "tight_aggressive", "equity"):
        bot = Baseline(kind, RULES)
        call = Baseline("always_call", RULES)
        a = duplicate_pair(bot, call, RULES, deck, action_seed=(91,), episode_seed=3)
        b = duplicate_pair(bot, call, RULES, deck, action_seed=(91,), episode_seed=3)
        assert a == b
        assert all(-200 <= hand.profit <= 200 for hand in a)
