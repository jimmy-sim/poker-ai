"""Exact spot comparisons; reference policies are analysis inputs only."""

import hashlib
import json
import math
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import numpy as np

from poker_ai.agents.no_limit import InferenceContext, OwnNoLimitAgent
from poker_ai.engine import Action, ActionKind
from poker_ai.solver_validation.gaps import action_frequency_gap
from poker_ai.solver_validation.reference import Policy, Reference, SpotTree
from poker_ai.training.no_limit import NoLimitState


@dataclass(frozen=True)
class AgentPolicy:
    policy: Policy
    statuses: tuple[str, ...]
    projection_mass: float
    shadow_changes: int


def prepare_contexts(
    tree: SpotTree, agent: OwnNoLimitAgent, episode_seed: int
) -> tuple[InferenceContext, ...]:
    contexts = []
    for node in tree.representatives:
        state = tree.states[node]
        assert state.dealer is not None
        contexts.append(
            agent.prepare(
                state.dealer.observe(state.actor),
                episode_seed=episode_seed,
                actual_blinds=(tree.spot.rules.small_blind, tree.spot.rules.big_blind),
            )
        )
    return tuple(contexts)


def compile_agent(
    tree: SpotTree, agent: OwnNoLimitAgent, contexts: tuple[InferenceContext, ...]
) -> AgentPolicy:
    """Require identical concrete menus; never silently project an off-tree size."""
    if len(contexts) != len(tree.keys):
        raise ValueError("prepared contexts must align with the spot")
    rows, statuses = [], []
    projection = 0.0
    shadow_changes = 0
    for node, context in zip(tree.representatives, contexts, strict=True):
        state = tree.states[node]
        assert state.dealer is not None
        if context.observation != state.dealer.observe(state.actor):
            raise ValueError("prepared observation does not match the information set")
        adapter = NoLimitState(state.dealer, tree.spot.rules)
        actions = tuple(adapter.decode(a) for a in state.actions)
        decision = agent.distribution_prepared(context)
        if set(actions) != set(decision.actions):
            raise ValueError("agent/spot concrete action menus differ")
        probabilities = dict(zip(decision.actions, decision.probabilities, strict=True))
        rows.append(tuple(probabilities[action] for action in actions))
        statuses.append(decision.status)
        shadow = decision.shadow
        shadow_changes += int(
            shadow.failure is not None
            or shadow.starting_stack_mismatch
            or shadow.passive_kind_changes != 0
            or any(r.actual_total != r.virtual_total for r in shadow.raises)
        )
        if decision.decoded is not None:
            projection = max(
                projection,
                decision.decoded.clipped_raise_mass,
                decision.decoded.unavailable_raise_mass,
                decision.decoded.mean_raise_fraction_error,
            )
    policy = tuple(rows)
    tree.validate_policy(policy)
    return AgentPolicy(policy, tuple(statuses), projection, shadow_changes)


def information_reach(tree: SpotTree, policy: Policy) -> np.ndarray[Any, Any]:
    reach = tree.reaches(policy)
    mass = np.zeros(len(tree.keys), dtype=np.float64)
    for node, info in enumerate(tree.information):
        if info >= 0:
            mass[info] += reach[node]
    return mass


def weighted_gap(
    first: Policy, second: Policy, mass: np.ndarray[Any, Any], indices: list[int]
) -> float | None:
    if not indices or math.fsum(float(mass[i]) for i in indices) <= 0:
        return None
    width = max(len(first[i]) for i in indices)
    p = np.zeros((len(indices), width))
    q = np.zeros_like(p)
    legal = np.zeros_like(p, dtype=np.bool_)
    for row, info in enumerate(indices):
        p[row, : len(first[info])] = first[info]
        q[row, : len(second[info])] = second[info]
        legal[row, : len(first[info])] = True
    return action_frequency_gap(p, q, mass[indices], legal)


def hand_class(cards: tuple[int, ...]) -> str:
    ranks = "23456789TJQKA"
    first, second = sorted(cards, key=lambda c: c // 4, reverse=True)
    label = ranks[first // 4] + ranks[second // 4]
    return (
        label
        if first // 4 == second // 4
        else label + ("s" if first % 4 == second % 4 else "o")
    )


def root_hand_values(
    tree: SpotTree, values: tuple[float, ...], hero: int
) -> dict[str, float]:
    """Conditional on hero class, before the uniformly dealt hidden future."""
    sums: dict[str, float] = defaultdict(float)
    masses: dict[str, float] = defaultdict(float)
    joint = {(i, j): p for i, j, p in tree.spot.joint}
    for node, state in enumerate(tree.states):
        if (
            state.dealer is None
            and state.first is not None
            and state.second is not None
            and not state.future
        ):
            index = state.first if hero == 0 else state.second
            label = hand_class(tree.spot.ranges[hero][index].cards)
            mass = joint[(state.first, state.second)]
            sums[label] += mass * values[node] * (1 if hero == 0 else -1)
            masses[label] += mass
    return {label: sums[label] / mass for label, mass in masses.items()}


def ev_attribution(
    tree: SpotTree,
    candidate: Policy,
    baseline: Policy,
    statuses: tuple[str, ...],
    hero: int,
) -> dict[str, float]:
    """Performance-difference identity with the SAME fixed opponent.

    Sum candidate joint reach times (candidate-baseline) action probability times
    baseline continuation value over hero decision histories. The contributions
    exactly sum to candidate EV - baseline EV; grouping by lookup status is an
    accounting diagnosis, not a causal estimate for changing training settings.
    """
    for info, owner in enumerate(tree.owners):
        if owner != hero and candidate[info] != baseline[info]:
            raise ValueError("EV attribution requires the same opponent")
    values, reach = tree.values(baseline), tree.reaches(candidate)
    groups: dict[str, list[float]] = defaultdict(list)
    sign = 1 if hero == 0 else -1
    for node, info in enumerate(tree.information):
        if info < 0 or tree.owners[info] != hero:
            continue
        advantage = math.fsum(
            (p - q) * values[child]
            for p, q, child in zip(
                candidate[info], baseline[info], tree.children[node], strict=True
            )
        )
        groups[statuses[info]].append(sign * reach[node] * advantage)
    result = {status: math.fsum(parts) for status, parts in groups.items()}
    expected = sign * (tree.values(candidate)[0] - values[0])
    if abs(math.fsum(result.values()) - expected) > 1e-9:
        raise ArithmeticError("performance-difference decomposition failed")
    return result


def action_label(action: Action, current_bet: int) -> str:
    return (
        ("bet" if current_bet == 0 else "raise")
        if action.kind == ActionKind.RAISE_TO
        else action.kind.value
    )


def compare(
    tree: SpotTree,
    reference: Reference,
    ref_policy: Policy,
    agent: AgentPolicy,
    *,
    tolerance: float,
    detailed: bool = False,
) -> dict[str, Any]:
    own = agent.policy
    profiles = {
        "reference": ref_policy,
        "own": own,
        "own0_reference1": tree.cross(own, ref_policy),
        "reference0_own1": tree.cross(ref_policy, own),
    }
    values = {name: tree.values(p) for name, p in profiles.items()}
    errors = {
        name: abs(v[0] - reference.value(profiles[name])) for name, v in values.items()
    }
    if max(errors.values()) > tolerance:
        raise ArithmeticError("own/native cross-play values disagree")
    ref_exploit = reference.exploitability(ref_policy)
    mass = information_reach(tree, ref_policy)
    total = float(mass.sum())
    indices = list(range(len(tree.keys)))
    statuses = sorted(set(agent.statuses))
    by_status = {}
    for status in statuses:
        selected = [i for i in indices if agent.statuses[i] == status]
        status_mass = float(mass[selected].sum()) / total
        gap = weighted_gap(own, ref_policy, mass, selected)
        by_status[status] = {
            "reach_fraction": status_mass,
            "information_sets": len(selected),
            "action_gap": gap,
            "overall_gap_contribution": 0.0 if gap is None else status_mass * gap,
        }
    per_street = {}
    for street in (2, 3):
        selected = [
            i
            for i, n in enumerate(tree.representatives)
            if tree.states[n].dealer is not None
            and int(tree.states[n].dealer.street) == street  # type: ignore[union-attr]
        ]
        per_street[str(street)] = weighted_gap(own, ref_policy, mass, selected)
    hero = tree.spot.hero
    ref_opp_candidate = "own0_reference1" if hero == 0 else "reference0_own1"
    own_opp_baseline = "reference0_own1" if hero == 0 else "own0_reference1"
    sign = 1 if hero == 0 else -1
    gap_ref = sign * (values[ref_opp_candidate][0] - values["reference"][0])
    gap_own = sign * (values["own"][0] - values[own_opp_baseline][0])
    if gap_ref > 2 * ref_exploit + tolerance:
        raise ArithmeticError("EV gain exceeds reference NashConv bound")
    root_values = {name: root_hand_values(tree, v, hero) for name, v in values.items()}
    hand_gaps = {
        label: {
            "versus_reference_opponent": root_values[ref_opp_candidate][label]
            - root_values["reference"][label],
            "versus_own_opponent": root_values["own"][label]
            - root_values[own_opp_baseline][label],
        }
        for label in root_values["reference"]
    }
    result: dict[str, Any] = {
        "action_gap": weighted_gap(own, ref_policy, mass, indices),
        "action_gap_per_street": per_street,
        "status_diagnosis": by_status,
        "exploitability": reference.exploitability(own),
        "reference_exploitability": ref_exploit,
        "hero_ev_gap_vs_reference_opponent": gap_ref,
        "hero_ev_gap_vs_own_opponent": gap_own,
        "hero_hand_class_ev_gaps": hand_gaps,
        "crossplay_p0_values": {name: v[0] for name, v in values.items()},
        "max_native_value_error": max(errors.values()),
        "projection_mass": agent.projection_mass,
        "shadow_changes": agent.shadow_changes,
        "ev_gap_attribution_vs_reference": ev_attribution(
            tree, profiles[ref_opp_candidate], ref_policy, agent.statuses, hero
        ),
        "ev_gap_attribution_vs_own": ev_attribution(
            tree, own, profiles[own_opp_baseline], agent.statuses, hero
        ),
    }
    if detailed:
        # Full decision-node/class rows and conditional range-level frequencies.
        reaches = tree.reaches(ref_policy)
        weighted_values = {name: np.zeros(len(tree.keys)) for name in values}
        for node, info in enumerate(tree.information):
            if info >= 0:
                for name, vector in values.items():
                    weighted_values[name][info] += reaches[node] * vector[node]
        rows: list[dict[str, Any]] = []
        public: dict[str, dict[str, Any]] = {}
        for info, node in enumerate(tree.representatives):
            state = tree.states[node]
            assert state.dealer is not None
            key = json.loads(tree.keys[info])
            cards = tuple(key.pop("hole"))
            public_key = json.dumps(key, sort_keys=True, separators=(",", ":"))
            public_id = hashlib.sha256(public_key.encode()).hexdigest()[:20]
            adapter = NoLimitState(state.dealer, tree.spot.rules)
            actions = [adapter.decode(a) for a in tree.menus[info]]
            labels = [action_label(a, state.dealer.current_bet) for a in actions]
            owner = tree.owners[info]
            candidate = "own0_reference1" if owner == 0 else "reference0_own1"
            baseline = "reference0_own1" if owner == 0 else "own0_reference1"
            conditional = {
                name: float(v[info] / mass[info]) if mass[info] > 0 else 0.0
                for name, v in weighted_values.items()
            }
            owner_sign = 1 if owner == 0 else -1
            rows.append(
                {
                    "information_set": info,
                    "public_node": public_id,
                    "public_state": key,
                    "owner": owner,
                    "street": int(state.dealer.street),
                    "hand_class": hand_class(cards),
                    "hole_cards": cards,
                    "reference_reach": float(mass[info]),
                    "status": agent.statuses[info],
                    "actions": [(a.kind.value, a.amount) for a in actions],
                    "reference_probabilities": ref_policy[info],
                    "own_probabilities": own[info],
                    "continuation_ev_gap_vs_reference_opponent": None
                    if mass[info] <= 0
                    else owner_sign
                    * (conditional[candidate] - conditional["reference"]),
                    "continuation_ev_gap_vs_own_opponent": None
                    if mass[info] <= 0
                    else owner_sign * (conditional["own"] - conditional[baseline]),
                }
            )
            group = public.setdefault(
                public_id,
                {
                    "public_node": public_id,
                    "public_state": key,
                    "reference_reach": 0.0,
                    "reference": defaultdict(float),
                    "own": defaultdict(float),
                },
            )
            group["reference_reach"] += float(mass[info])
            for label, p, q in zip(labels, ref_policy[info], own[info], strict=True):
                group["reference"][label] += float(mass[info]) * p
                group["own"][label] += float(mass[info]) * q
        for group in public.values():
            for name in ("reference", "own"):
                group[name] = {
                    label: None
                    if group["reference_reach"] <= 0
                    else value / group["reference_reach"]
                    for label, value in group[name].items()
                }
        result["decision_rows"] = rows
        result["node_frequencies"] = list(public.values())
    return result
