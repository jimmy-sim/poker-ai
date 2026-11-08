"""Own exact/constrained/river scoring; no reference solver or training inputs."""

import math
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

from poker_ai.finite import ArrayTree, FloatArray, IntArray
from poker_ai.postflop.reply_trace import require_recall, response_profile
from poker_ai.postflop.river_distinctions import river_switches
from poker_ai.toy.analysis import best_response

BoolArray = NDArray[np.bool_]


@dataclass(frozen=True)
class OwnScore:
    metrics: dict[str, float]
    responses: list[dict[str, Any]]
    replies: list[dict[str, FloatArray]]
    maximum_accounting_error: float


@dataclass(frozen=True)
class ScoringContext:
    exact: ArrayTree
    partition: ArrayTree
    exact_to_partition: IntArray
    river_masks: tuple[BoolArray, BoolArray]

    def __post_init__(self) -> None:
        a, b, mapping = self.exact, self.partition, self.exact_to_partition
        if (
            len(self.river_masks) != 2
            or mapping.dtype != np.int64
            or mapping.shape != (len(a.keys),)
            or not np.array_equal(np.unique(mapping), np.arange(len(b.keys)))
            or any(
                not np.array_equal(getattr(a, name), getattr(b, name))
                for name in (
                    "children",
                    "valid",
                    "player",
                    "chance_edges",
                    "chance_reach",
                    "terminal_values",
                )
            )
            or len(a.levels) != len(b.levels)
            or any(
                not np.array_equal(x, y)
                for x, y in zip(a.levels, b.levels, strict=True)
            )
            or a.legal.shape[1] != b.legal.shape[1]
            or any(
                a.actions[i] != b.actions[int(group)] or a.owners[i] != b.owners[group]
                for i, group in enumerate(mapping)
            )
        ):
            raise ValueError("scoring partition changes game/menus/owners/mapping")
        decision = a.player >= 0
        if not np.array_equal(
            b.information[decision], mapping[a.information[decision]]
        ):
            raise ValueError("scoring information mapping mismatch")
        for target, mask in enumerate(self.river_masks):
            if (
                mask.dtype != np.bool_
                or mask.shape != (len(a.keys),)
                or np.any(mask & (a.owners != target))
                or any(
                    len(set(mask[mapping == group])) != 1
                    for group in range(len(b.keys))
                )
            ):
                raise ValueError("scoring river mask crosses owners/partition streets")
        require_recall(a)
        require_recall(b)

    def expand(self, policy: FloatArray) -> FloatArray:
        self.partition.validate_policy(policy)
        result = policy[self.exact_to_partition].copy()
        self.exact.validate_policy(result)
        return result

    def score(self, policy: FloatArray, *, tolerance: float = 1e-9) -> OwnScore:
        """Seat-balanced gains in chips; preserve small signed roundoff, never clip.

        Exact-prefix river gain changes only own river rows of an own reply profile
        against the fixed saved opponent. It is not an EV gain from retraining.
        All maximizations sum hidden histories within an information group first.
        """
        if type(tolerance) not in (int, float) or not 0 < tolerance <= 1e-9:
            raise ValueError("invalid controlled-score tolerance")
        exact, limited = self.exact, self.partition
        saved = self.expand(policy)
        value = float(exact.values(exact.edges(saved))[0])
        responses, replies = [], []
        errors = []
        for target in (0, 1):
            sign = 1 if target == 0 else -1
            b = response_profile(exact, saved, target)
            restricted = response_profile(limited, policy, target)
            c = self.expand(restricted)
            b_value = sign * float(exact.values(exact.edges(b))[0])
            c_value = sign * float(exact.values(exact.edges(c))[0])
            baseline = sign * value
            errors += [
                abs(b_value - best_response(exact, saved, target)),
                abs(c_value - best_response(limited, policy, target)),
                abs(
                    c_value - sign * float(limited.values(limited.edges(restricted))[0])
                ),
            ]
            if b_value < c_value - tolerance or c_value < baseline - tolerance:
                raise ArithmeticError("controlled response ordering failed")
            panels = river_switches(
                exact, b, c, target, self.river_masks[target], tolerance=tolerance
            )
            river = panels["exact_prefix"]
            errors.extend(panel.error for panel in panels.values())
            errors.append(abs(river.after_value - b_value))
            responses.append(
                dict(
                    target=target,
                    baseline_value_chips=baseline,
                    exact_reply_value_chips=b_value,
                    restricted_reply_value_chips=c_value,
                    within_partition_gain_chips=c_value - baseline,
                    extra_information_gap_chips=b_value - c_value,
                    river_before_value_chips=river.before_value,
                    river_only_gain_exact_prefix_chips=river.after_value
                    - river.before_value,
                )
            )
            replies.append(dict(exact=b, restricted=c, river_before=river.before))
        metrics = dict(
            exact_exploitability_chips=math.fsum(
                r["exact_reply_value_chips"] - r["baseline_value_chips"]
                for r in responses
            )
            / 2,
            within_partition_gain_chips=math.fsum(
                r["within_partition_gain_chips"] for r in responses
            )
            / 2,
            extra_information_gap_chips=math.fsum(
                r["extra_information_gap_chips"] for r in responses
            )
            / 2,
            river_only_gain_exact_prefix_chips=math.fsum(
                r["river_only_gain_exact_prefix_chips"] for r in responses
            )
            / 2,
            value_player_zero_chips=value,
        )
        errors.append(
            abs(
                metrics["exact_exploitability_chips"]
                - metrics["within_partition_gain_chips"]
                - metrics["extra_information_gap_chips"]
            )
        )
        if (
            any(not math.isfinite(v) for v in metrics.values())
            or any(not math.isfinite(e) or e > tolerance for e in errors)
            or any(
                v < -tolerance
                for k, v in metrics.items()
                if k != "value_player_zero_chips"
            )
        ):
            raise ArithmeticError("controlled-score accounting/nonfinite failure")
        return OwnScore(metrics, responses, replies, max(errors))
