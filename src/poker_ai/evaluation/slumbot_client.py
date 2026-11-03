"""Bounded anonymous public-benchmark driver; no live calls occur on import."""

import json
import math
import ssl
import time
import urllib.error
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from statistics import NormalDist
from typing import Any, Protocol

import numpy as np
from numpy.random import PCG64, Generator

from poker_ai.agents.no_limit import OwnNoLimitAgent
from poker_ai.cards import parse_card
from poker_ai.engine import Action, ActionKind, ActionRecord, Observation
from poker_ai.evaluation.slumbot_protocol import (
    ProtocolError,
    encode_action,
    replay_public,
    verify_result,
)


class AmbiguousPostError(RuntimeError):
    """A non-idempotent request might have taken effect; never replay blindly."""


class Transport(Protocol):
    def post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]: ...


class PublicPolicy(Protocol):
    def choose(
        self, observation: Observation, *, rng: Generator, episode_seed: int
    ) -> tuple[Action, dict[str, Any]]: ...


class OwnPublicPolicy:
    def __init__(self, agent: OwnNoLimitAgent, blinds: tuple[int, int]) -> None:
        self.agent, self.blinds = agent, blinds

    def choose(
        self, observation: Observation, *, rng: Generator, episode_seed: int
    ) -> tuple[Action, dict[str, Any]]:
        result = self.agent.distribution(
            observation, episode_seed=episode_seed, actual_blinds=self.blinds
        )
        details: dict[str, Any] = {
            "status": result.status,
            "shadow_failure": result.shadow.failure,
            "starting_stack_mismatch": result.shadow.starting_stack_mismatch,
            "mapped_raises": len(result.shadow.raises),
            "max_history_fraction_error": max(
                (
                    abs(r.actual_pot_fraction - r.virtual_pot_fraction)
                    for r in result.shadow.raises
                ),
                default=0.0,
            ),
            "history_virtual_bound_clips": sum(
                r.clipped_to_virtual_bounds for r in result.shadow.raises
            ),
        }
        details["clipped_raise_mass"] = (
            None if result.decoded is None else result.decoded.clipped_raise_mass
        )
        details["unavailable_raise_mass"] = (
            None if result.decoded is None else result.decoded.unavailable_raise_mass
        )
        details["output_mean_raise_fraction_error"] = (
            None if result.decoded is None else result.decoded.mean_raise_fraction_error
        )
        return result.sample(rng), details


class HTTPTransport:
    def __init__(self, config: dict[str, Any]) -> None:
        if config["base_url"] != "https://slumbot.com/slumbot/api/":
            raise ValueError(
                "only the documented public simulation benchmark is allowed"
            )
        self.config = config
        self.last_request: float | None = None
        self.context = ssl.create_default_context()
        # Managed Python on macOS may not discover the system CA bundle. Load
        # that trusted bundle when present; verification/hostname checks remain on.
        roots = Path("/etc/ssl/cert.pem")
        if roots.is_file():
            self.context.load_verify_locations(cafile=str(roots))

    def post(self, endpoint: str, data: dict[str, Any]) -> dict[str, Any]:
        if endpoint not in ("new_hand", "act"):
            raise ValueError("unsupported public API endpoint")
        if self.last_request is not None:
            delay = self.config["minimum_request_interval_seconds"] - (
                time.perf_counter() - self.last_request
            )
            if delay > 0:
                time.sleep(delay)
        request = urllib.request.Request(
            self.config["base_url"] + endpoint,
            data=json.dumps(data).encode(),
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "User-Agent": "poker-ai-research-pilot/0.1",
            },
            method="POST",
        )
        self.last_request = time.perf_counter()
        try:
            with urllib.request.urlopen(
                request,
                context=self.context,
                timeout=self.config["http_timeout_seconds"],
            ) as response:
                raw = response.read(1_000_001)
            if len(raw) > 1_000_000:
                raise ValueError("unexpected oversized public response")
            packet = json.loads(raw)
            if not isinstance(packet, dict):
                raise ValueError("public response must be an object")
            return packet
        except (urllib.error.URLError, TimeoutError, OSError, ValueError) as error:
            # Stopping after a cooldown avoids retrying an action the server may
            # already have processed, and avoids burdening an overloaded server.
            time.sleep(self.config["error_cooldown_seconds"])
            raise AmbiguousPostError(
                f"public POST failed ({type(error).__name__}: {error}); "
                "session stopped without retry"
            ) from error


def sanitize(value: Any, tokens: set[str]) -> Any:
    if isinstance(value, dict):
        return {
            key: "[redacted]" if str(key).lower() == "token" else sanitize(item, tokens)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [sanitize(item, tokens) for item in value]
    if isinstance(value, str):
        for token in tokens:
            value = value.replace(token, "[redacted]")
    return value


def _cards(value: Any, *, hole: bool) -> tuple[int, ...]:
    if not isinstance(value, list) or any(not isinstance(card, str) for card in value):
        raise ProtocolError("missing public own-card/board list")
    cards = tuple(parse_card(card) for card in value)
    if (hole and len(cards) != 2) or (not hole and len(cards) not in (0, 3, 4, 5)):
        raise ProtocolError("invalid public card count")
    return cards


def _legal(observation: Observation, action: Action) -> bool:
    legal = observation.legal_actions
    if legal is None:
        return False
    if action.kind == ActionKind.FOLD:
        return legal.can_fold
    if action.kind == ActionKind.CHECK:
        return legal.can_check
    if action.kind == ActionKind.CALL:
        return legal.call_amount > 0
    return (
        action.amount is not None
        and legal.min_raise_to is not None
        and legal.max_raise_to is not None
        and legal.min_raise_to <= action.amount <= legal.max_raise_to
    )


def pilot_statistics(
    records: list[dict[str, Any]], config: dict[str, Any]
) -> dict[str, Any] | None:
    if len(records) < 2:
        return None
    values = np.asarray([row["winnings"] for row in records], dtype=np.float64)
    mean = float(values.mean())
    se = float(values.std(ddof=1) / math.sqrt(len(values)))
    normal = NormalDist().inv_cdf(0.975) * se
    support = max(config["starting_stacks"])
    radius = 2 * support * math.sqrt(math.log(40) / (2 * len(values)))
    scale = 1000 / config["big_blind"]
    return {
        "hands": len(values),
        "mean_mbb_per_hand": mean * scale,
        "approximate_iid_95_interval_mbb_per_hand": [
            (mean - normal) * scale,
            (mean + normal) * scale,
        ],
        "conditional_iid_hoeffding_95_interval_mbb_per_hand": [
            max(-support, mean - radius) * scale,
            min(support, mean + radius) * scale,
        ],
        "assumptions": (
            "server hands independent; not verified from opaque API; "
            "no familywise or competitive-strength claim"
        ),
        "duplicate_deals": False,
    }


def run_pilot(
    config: dict[str, Any],
    transport: Transport,
    policy: PublicPolicy,
    *,
    progress: bool = False,
) -> dict[str, Any]:
    """Never infer from a truncated/ambiguous prefix or start a replacement hand."""
    started = time.perf_counter()
    started_utc = datetime.now(UTC).isoformat()
    rng = Generator(PCG64(config["action_seed"]))
    token: str | None = None
    tokens: set[str] = set()
    events: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    attempted = confirmed = requests = 0
    failure = None
    lookup_counts: Counter[str] = Counter()

    def call(endpoint: str, data: dict[str, Any], hand: int) -> dict[str, Any]:
        nonlocal token, requests, attempted
        if (
            requests >= config["maximum_requests"]
            or time.perf_counter() - started > config["maximum_elapsed_seconds"]
        ):
            raise TimeoutError("declared public pilot request/time budget exhausted")
        requests += 1
        if endpoint == "new_hand":
            attempted += 1
        events.append(
            {
                "kind": "request",
                "hand": hand,
                "endpoint": endpoint,
                "data": sanitize(data, tokens),
                "utc": datetime.now(UTC).isoformat(),
            }
        )
        packet = transport.post(endpoint, data)
        if isinstance(packet.get("token"), str) and packet["token"]:
            token = packet["token"]
            tokens.add(token)
        events.append(
            {
                "kind": "response",
                "hand": hand,
                "packet": sanitize(packet, tokens),
                "utc": datetime.now(UTC).isoformat(),
            }
        )
        if packet.get("error_msg"):
            raise ProtocolError("public server reported an API error")
        if token is None:
            raise ProtocolError("public response did not establish an anonymous token")
        return packet

    try:
        for hand in range(config["hands"]):
            packet = call("new_hand", {} if token is None else {"token": token}, hand)
            confirmed += 1
            previous: tuple[ActionRecord, ...] = ()
            sent: Action | None = None
            known_hole = None
            known_board: list[str] = []
            client = None
            decisions = 0
            while True:
                seat = packet.get("client_pos", client)
                if (
                    type(seat) is not int
                    or seat not in (0, 1)
                    or (client is not None and client != seat)
                ):
                    raise ProtocolError("public client position changed within a hand")
                client = seat
                raw_hole = packet.get("hole_cards", known_hole)
                hole = _cards(raw_hole, hole=True)
                if known_hole is not None and set(hole) != set(
                    _cards(known_hole, hole=True)
                ):
                    raise ProtocolError("own private cards changed within a hand")
                known_hole = raw_hole
                raw_board = packet.get("board", known_board)
                board = _cards(raw_board, hole=False)
                old_board = _cards(known_board, hole=False)
                if (
                    len(board) < len(old_board)
                    or (len(old_board) >= 3 and set(board[:3]) != set(old_board[:3]))
                    or (
                        len(old_board) >= 4
                        and board[3 : len(old_board)] != old_board[3:]
                    )
                ):
                    raise ProtocolError("public board changed inconsistently")
                known_board = raw_board
                text = packet.get("action")
                if not isinstance(text, str):
                    raise ProtocolError("missing public action string")
                replay = replay_public(
                    text,
                    client_seat=seat,
                    hole=hole,
                    board=board,
                    stacks=tuple(config["starting_stacks"]),
                    small_blind=config["small_blind"],
                    big_blind=config["big_blind"],
                    button=config["button"],
                )
                if replay.history[: len(previous)] != previous:
                    raise ProtocolError(
                        "server public history lost its confirmed prefix"
                    )
                if sent is not None and (
                    len(replay.history) <= len(previous)
                    or replay.history[len(previous)].seat != seat
                    or replay.history[len(previous)].action != sent
                ):
                    raise ProtocolError("server did not confirm the requested action")
                if packet.get("winnings") is not None:
                    winnings = verify_result(
                        replay, packet["winnings"], max(config["starting_stacks"])
                    )
                    records.append(
                        {
                            "hand": hand,
                            "client_pos": seat,
                            "winnings": winnings,
                            "action": packet["action"],
                            "hole_cards": known_hole,
                            "board": known_board,
                            "own_decisions": decisions,
                            "fold_settlement_checked": replay.fold_payoff is not None,
                        }
                    )
                    if progress and (
                        len(records) % 10 == 0 or len(records) == config["hands"]
                    ):
                        print(
                            f"Slumbot protocol pilot: {len(records)}/{config['hands']} "
                            "hands settled",
                            flush=True,
                        )
                    break
                if replay.terminal or replay.observation is None:
                    raise ProtocolError(
                        "public terminal hand lacks an observed settlement"
                    )
                move, details = policy.choose(
                    replay.observation,
                    rng=rng,
                    episode_seed=config["mapping_episode_seed"] + hand,
                )
                if not _legal(replay.observation, move):
                    raise ProtocolError("own public policy proposed an illegal action")
                decisions += 1
                lookup_counts[str(details.get("status", "test_policy"))] += 1
                events.append(
                    {
                        "kind": "decision",
                        "hand": hand,
                        "action": encode_action(move),
                        "diagnostics": details,
                    }
                )
                previous = replay.history
                sent = move
                packet = call(
                    "act", {"token": token, "incr": encode_action(move)}, hand
                )
    except (Exception, KeyboardInterrupt) as error:
        failure = {"type": type(error).__name__, "reason": str(error)}
        events.append({"kind": "failure", "error": sanitize(failure, tokens)})
    completed = failure is None and len(records) == config["hands"]
    return {
        "status": "completed" if completed else "incomplete",
        "config": config,
        "started_utc": started_utc,
        "ended_utc": datetime.now(UTC).isoformat(),
        "seconds": time.perf_counter() - started,
        "requests_attempted": requests,
        "new_hand_requests_attempted": attempted,
        "confirmed_hand_responses": confirmed,
        "completed_hands": len(records),
        "unsettled_or_unconfirmed_hand_requests": attempted - len(records),
        "failure": sanitize(failure, tokens),
        "lookup_counts": dict(lookup_counts),
        "records": records,
        "events": events,
        "pilot_summary": pilot_statistics(records, config) if completed else None,
        "server_version": (
            "not supplied/verified; configured from official public API documentation"
        ),
        "replay_limit": (
            "client seeds fixed; server deals/opponent are not controlled "
            "or exactly live-replayable"
        ),
    }
