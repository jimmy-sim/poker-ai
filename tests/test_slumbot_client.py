"""Offline synthetic sessions test censoring, settlement and token redaction."""

import json
from pathlib import Path
from typing import Any

from numpy.random import Generator

from poker_ai.engine import Action, ActionKind, Observation
from poker_ai.evaluation.slumbot_client import AmbiguousPostError, run_pilot

CONFIG = Path(__file__).resolve().parents[1] / "configs/slumbot-pilot.json"
SECRET = "PRIVATE_ANONYMOUS_SESSION_TOKEN"


class PassivePolicy:
    def choose(
        self, observation: Observation, *, rng: Generator, episode_seed: int
    ) -> tuple[Action, dict[str, Any]]:
        assert observation.legal_actions is not None
        return Action(
            ActionKind.CHECK if observation.legal_actions.can_check else ActionKind.CALL
        ), {}


class FoldPolicy:
    def choose(
        self, observation: Observation, *, rng: Generator, episode_seed: int
    ) -> tuple[Action, dict[str, Any]]:
        return Action(ActionKind.FOLD), {}


class FoldSession:
    def __init__(self, winnings: int = -50) -> None:
        self.calls = 0
        self.winnings = winnings

    def post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        if endpoint == "new_hand":
            return {
                "client_pos": 1,
                "action": "",
                "hole_cards": ["As", "Ad"],
                "board": [],
                "token": SECRET,
            }
        assert data["incr"] == "f" and data["token"] == SECRET
        return {
            "client_pos": 1,
            "action": "f",
            "winnings": self.winnings,
            "hole_cards": ["As", "Ad"],
            "board": [],
            "token": SECRET,
            "debug_echo": SECRET,
        }


class AmbiguousSecondHand:
    def __init__(self) -> None:
        self.calls = 0

    def post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        self.calls += 1
        if self.calls == 1:
            # Server folds its small blind: a confirmed favorable first result.
            return {
                "client_pos": 0,
                "action": "f",
                "winnings": 50,
                "hole_cards": ["As", "Ad"],
                "board": [],
                "token": SECRET,
            }
        if self.calls == 2:
            return {
                "client_pos": 0,
                "action": "c",
                "hole_cards": ["As", "Ad"],
                "board": [],
                "token": SECRET,
            }
        assert endpoint == "act" and data["incr"] == "k"
        raise AmbiguousPostError("simulated response loss after request")


def config(hands: int) -> dict[str, Any]:
    raw: dict[str, Any] = json.loads(CONFIG.read_text())
    raw["hands"] = hands
    return raw


def test_completed_public_session_uses_verified_fold_net_and_redacts_tokens() -> None:
    transport = FoldSession()
    report = run_pilot(config(1), transport, FoldPolicy())
    assert report["status"] == "completed"
    assert report["completed_hands"] == 1
    assert report["records"][0]["winnings"] == -50
    assert transport.calls == 2
    assert SECRET not in json.dumps(report)


def test_ambiguous_post_never_retries_replaces_hand_or_infers_winning_prefix() -> None:
    transport = AmbiguousSecondHand()
    report = run_pilot(config(2), transport, PassivePolicy())
    assert report["status"] == "incomplete"
    assert report["completed_hands"] == 1
    assert report["records"][0]["winnings"] == 50
    assert report["unsettled_or_unconfirmed_hand_requests"] == 1
    assert report["pilot_summary"] is None
    assert transport.calls == 3
    assert SECRET not in json.dumps(report)


def test_inconsistent_server_fold_settlement_blocks_completion() -> None:
    report = run_pilot(config(1), FoldSession(winnings=50), FoldPolicy())
    assert report["status"] == "incomplete"
    assert report["completed_hands"] == 0
    assert report["pilot_summary"] is None
    assert report["failure"]["type"] == "ProtocolError"


def test_budget_stop_before_new_request_does_not_invent_an_unsettled_hand() -> None:
    settings = config(2)
    settings["maximum_requests"] = 1
    transport = AmbiguousSecondHand()
    report = run_pilot(settings, transport, PassivePolicy())
    assert report["status"] == "incomplete"
    assert report["completed_hands"] == 1
    assert report["new_hand_requests_attempted"] == 1
    assert report["unsettled_or_unconfirmed_hand_requests"] == 0
    assert report["pilot_summary"] is None
    assert transport.calls == 1


def test_complete_fixed_sample_summary_keeps_uncertainty_with_zero_empirical_se() -> (
    None
):
    report = run_pilot(config(2), FoldSession(), FoldPolicy())
    assert report["status"] == "completed"
    summary = report["pilot_summary"]
    assert summary["hands"] == 2
    assert summary["mean_mbb_per_hand"] == -500
    low, high = summary["conditional_iid_hoeffding_95_interval_mbb_per_hand"]
    assert low < -500 < high
