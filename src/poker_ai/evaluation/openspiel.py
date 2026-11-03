"""Optional OpenSpiel Python ISMCTS opponent over native ACPC mechanics.

The synthetic opponent cards used to reconstruct a native root are NOT the real
opponent cards. Native ISMCTS resamples compatible worlds from the acting player's
information state. No reference strategy is imported into own training/lookup.
"""

import importlib
import math
from typing import Any

from numpy.random import Generator, RandomState, SeedSequence

from poker_ai.abstraction.shadow import legal_actions
from poker_ai.cards import Deck, cards_to_mask, parse_card
from poker_ai.engine import Action, ActionKind, Observation, new_hand
from poker_ai.training.no_limit import NoLimitRules


class OpenSpielBaseline:
    def __init__(
        self,
        rules: NoLimitRules,
        *,
        simulations: int = 32,
        world_samples: int = 16,
        uct_c: float = 200.0,
    ) -> None:
        if rules.button != 1 or rules.small_blind != 1 or rules.big_blind != 2:
            raise ValueError("native adapter currently uses button1 and 1/2 blinds")
        if (
            type(simulations) is not int
            or simulations < 4
            or type(world_samples) is not int
            or world_samples < 1
            or not math.isfinite(uct_c)
            or uct_c <= 0
        ):
            raise ValueError("invalid native search budget")
        self.pyspiel: Any = importlib.import_module("pyspiel")
        self.ismcts: Any = importlib.import_module(
            "open_spiel.python.algorithms.ismcts"
        )
        self.mcts: Any = importlib.import_module("open_spiel.python.algorithms.mcts")
        self.rules = rules
        self.simulations, self.world_samples, self.uct_c = (
            simulations,
            world_samples,
            uct_c,
        )
        self.game: Any = self.pyspiel.load_game(
            "universal_poker",
            {
                "betting": "nolimit",
                "numPlayers": 2,
                "numRounds": 4,
                "blind": "2 1",
                "firstPlayer": "2 1 1 1",
                "numSuits": 4,
                "numRanks": 13,
                "numHoleCards": 2,
                "numBoardCards": "0 3 1 1",
                "stack": " ".join(map(str, rules.stacks)),
                "bettingAbstraction": "fcpa",
            },
        )
        initial = self.game.new_initial_state()
        self.cards = {
            parse_card(initial.action_to_string(a).rsplit(" ", 1)[-1]): a
            for a in initial.legal_actions()
        }
        if set(self.cards) != set(range(52)):
            raise ArithmeticError("native chance-card encoding mismatch")

    def menu(self, state: Any, observation: Observation) -> dict[int, Action]:
        legal = observation.legal_actions
        if legal is None or state.current_player() != observation.actor:
            raise ValueError("native/own actor mismatch")
        actor = observation.seat
        previous_streets = (
            observation.total_commitments[actor] - observation.street_commitments[actor]
        )
        result = {}
        for action in state.legal_actions():
            label = state.action_to_string(action).rsplit("=", 1)[-1]
            if label == "Fold":
                move = Action(ActionKind.FOLD)
            elif label == "Call":
                move = Action(ActionKind.CHECK if legal.can_check else ActionKind.CALL)
            elif label in ("Bet", "AllIn"):
                total = state.pot_size() if label == "Bet" else state.all_in_size()
                move = Action(ActionKind.RAISE_TO, int(total) - previous_streets)
            else:
                raise ValueError("unknown native abstract action label")
            result[action] = move
        if set(result.values()) != set(legal_actions(observation, self.rules)[1]):
            raise ValueError("native/own concrete action abstraction mismatch")
        return result

    def from_observation(
        self, observation: Observation, dummy: tuple[int, int] | None = None
    ) -> Any:
        if observation.terminal or observation.actor != observation.seat:
            raise ValueError("native opponent needs an acting observation")
        starting = tuple(
            s + p
            for s, p in zip(
                observation.stacks, observation.total_commitments, strict=True
            )
        )
        if starting != self.rules.stacks or observation.button != self.rules.button:
            raise ValueError("native starting stacks/button mismatch")
        known = observation.hole_cards + observation.board
        if dummy is None:
            unused = [c for c in range(52) if c not in known]
            dummy = (unused[0], unused[1])
        if len(dummy) != 2:
            raise ValueError("synthetic opponent needs exactly two cards")
        cards_to_mask(known + dummy)
        holes = [dummy, dummy]
        holes[observation.seat] = (observation.hole_cards[0], observation.hole_cards[1])
        native = self.game.new_initial_state()
        for hand in holes:
            for card in hand:
                native.apply_action(self.cards[card])
        # Cards cannot affect this NONTERMINAL monetary replay. Its dummy dealer
        # world never enters native search or the own policy's private inputs.
        public = new_hand(
            self.rules.stacks,
            Deck(),
            button=self.rules.button,
            small_blind=self.rules.small_blind,
            big_blind=self.rules.big_blind,
        )
        board_index = 0

        def reveal() -> None:
            nonlocal board_index
            while native.is_chance_node():
                if board_index >= len(observation.board):
                    raise ValueError(
                        "native replay requested an unrevealed public card"
                    )
                native.apply_action(self.cards[observation.board[board_index]])
                board_index += 1

        for record in observation.history:
            reveal()
            if public.actor != record.seat or public.street != record.street:
                raise ValueError("own public replay actor/street mismatch")
            menu = self.menu(native, public.observe(record.seat))
            inverse = {move: action for action, move in menu.items()}
            if record.action not in inverse:
                raise ValueError("native history contains an off-grid action")
            native.apply_action(inverse[record.action])
            public = public.apply(record.action)
        reveal()
        data = native.to_struct()
        if (
            public.terminal
            or public.actor != observation.actor
            or public.street != observation.street
            or public.stacks != observation.stacks
            or public.total_commitments != observation.total_commitments
            or tuple(data.player_contributions) != observation.total_commitments
            or data.pot_size != observation.pot
            or board_index != len(observation.board)
        ):
            raise ArithmeticError("native/own public ledger mismatch")
        # Compare actual own cards/public board, never native dummy opponent cards.
        own = data.player_hands[observation.seat]
        board = data.board_cards
        if {parse_card(own[i : i + 2]) for i in range(0, len(own), 2)} != set(
            observation.hole_cards
        ) or {parse_card(board[i : i + 2]) for i in range(0, len(board), 2)} != set(
            observation.board
        ):
            raise ArithmeticError("native known-card mismatch")
        self.menu(native, observation)
        return native

    def search(
        self,
        observation: Observation,
        seed: int,
        *,
        dummy: tuple[int, int] | None = None,
    ) -> tuple[Action, tuple[tuple[Action, float], ...]]:
        state = self.from_observation(observation, dummy)
        search_seed, rollout_seed, world_seed = map(
            int, SeedSequence(seed).generate_state(3)
        )
        evaluator = self.mcts.RandomRolloutEvaluator(
            1, random_state=RandomState(rollout_seed)
        )
        bot = self.ismcts.ISMCTSBot(
            self.game,
            evaluator=evaluator,
            uct_c=self.uct_c,
            max_simulations=self.simulations,
            max_world_samples=self.world_samples,
            random_state=RandomState(search_seed),
            final_policy_type=self.ismcts.ISMCTSFinalPolicyType.NORMALIZED_VISITED_COUNT,
        )
        # OpenSpiel's Python default resampler constructs an unseeded sampler.
        # Its public hook lets us supply a separately seeded callback instead.
        world_rng = RandomState(world_seed)
        bot.set_resampler(
            lambda root, player: root.resample_from_infostate(
                player, lambda: float(world_rng.uniform())
            )
        )
        probabilities, action = bot.step_with_policy(state)
        menu = self.menu(state, observation)
        policy = tuple((menu[int(a)], float(p)) for a, p in probabilities)
        if (
            any(p < 0 or not math.isfinite(p) for _, p in policy)
            or abs(sum(p for _, p in policy) - 1) > 1e-12
        ):
            raise ArithmeticError("invalid native search policy")
        return menu[int(action)], policy

    def act(
        self, observation: Observation, *, rng: Generator, episode_seed: int
    ) -> Action:
        return self.search(observation, int(rng.integers(2**31)))[0]
