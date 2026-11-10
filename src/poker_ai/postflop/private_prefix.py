"""Two-level joint-chance stratification; no policy or reference information.

Each equal-probability stratum supplies one raw external-sampling increment.
The batch mean is unbiased under ideal independent uniforms. Its fixed-policy
component variance is no greater than IID proportional sampling, before clipping
and normalization. This is not an adaptive-convergence or fixed-work claim.
"""

import bisect
import math
from dataclasses import dataclass

import numpy as np
from numpy.random import Generator

from poker_ai.finite import FloatArray
from poker_ai.postflop.cached_nodes import CachedNode


def probabilities(node: CachedNode) -> tuple[float, ...]:
    """Check the original categorical law, including zero-probability edges."""
    if node.terminal or not node.chance or not node.actions:
        raise ValueError("private prefix requires two nonempty chance levels")
    values = node.chance_probabilities
    if (
        len(values) != len(node.actions)
        or node.actions != tuple(range(len(values)))
        or any(not math.isfinite(p) or p < 0 for p in values)
        or not math.isclose(math.fsum(values), 1, rel_tol=0, abs_tol=1e-12)
    ):
        raise ValueError("invalid private-prefix categorical probabilities")
    return values


@dataclass(frozen=True, slots=True)
class PrefixPlan:
    """Immutable original-edge-order joint prefix and selector-call contracts.

    CDF construction normalizes roundoff in the product probability total only;
    each original node law must already sum to one within1e-12. Refuse positive
    masses that underflow or collapse in the double-precision CDF, rather than
    silently removing their support. No payoff, private key or strategy is read.
    """

    root_node: int
    child_nodes: tuple[int, ...]
    first: tuple[float, ...]
    second: tuple[tuple[float, ...], ...]
    paths: tuple[tuple[int, int], ...]
    joint: tuple[float, ...]
    cdf: tuple[float, ...]

    @classmethod
    def build(cls, root: CachedNode) -> "PrefixPlan":
        first = probabilities(root)
        children = tuple(root.child(i) for i in root.actions)
        second = tuple(probabilities(child) for child in children)
        paths = tuple((i, j) for i in root.actions for j in children[i].actions)
        joint = tuple(first[i] * second[i][j] for i, j in paths)
        if any(
            first[i] > 0 and second[i][j] > 0 and p == 0
            for (i, j), p in zip(paths, joint, strict=True)
        ):
            raise ValueError("private-prefix positive mass underflow")
        total = math.fsum(joint)
        if not math.isfinite(total) or total <= 0:
            raise ValueError("private-prefix joint law has no mass")
        normalized = tuple(p / total for p in joint)
        cumulative = [math.fsum(normalized[: i + 1]) for i in range(len(joint))]
        cumulative[-1] = 1.0
        previous = 0.0
        for p, edge in zip(joint, cumulative, strict=True):
            if edge < previous or (p > 0 and edge <= previous):
                raise ValueError("private-prefix positive mass lost in CDF")
            previous = edge
        return cls(
            root.node,
            tuple(c.node for c in children),
            first,
            second,
            paths,
            joint,
            tuple(cumulative),
        )

    def choose(self, u: float) -> tuple[int, int]:
        if isinstance(u, (bool, np.bool_)) or not math.isfinite(u) or not 0 <= u < 1:
            raise ValueError("joint selector requires u in [0,1)")
        # Right search skips zero masses and chooses the next half-open interval
        # at exact CDF boundaries, including u=0 with leading zero edges.
        return self.paths[bisect.bisect_right(self.cdf, u)]


def stratum_point(index: int, count: int, uniform: float) -> float:
    """One uniform per bin; protect the excluded upper edge from FP rounding."""
    if (
        type(count) is not int
        or not 1 <= count <= 2**53
        or type(index) is not int
        or not 0 <= index < count
        or isinstance(uniform, (bool, np.bool_))
        or not math.isfinite(uniform)
        or not 0 <= uniform < 1
    ):
        raise ValueError("invalid private-prefix stratum or uniform")
    lower, upper = index / count, (index + 1) / count
    return min(max((index + uniform) / count, lower), math.nextafter(upper, lower))


class PrefixSelector:
    """Force exactly the two planned chance choices; ordinary sampling follows."""

    def __init__(self, plan: PrefixPlan, u: float, rng: Generator) -> None:
        self.path = plan.choose(u)
        self.expected = (plan.first, plan.second[self.path[0]])
        self.rng = rng
        self.consumed = 0

    def __call__(self, incoming: FloatArray) -> int:
        if self.consumed < 2:
            if not np.array_equal(incoming, self.expected[self.consumed]):
                raise ArithmeticError("private-prefix selector call law changed")
            chosen = self.path[self.consumed]
            self.consumed += 1
            return chosen
        return int(self.rng.choice(len(incoming), p=incoming))

    def finish(self) -> None:
        if self.consumed != 2:
            raise ArithmeticError(
                "private-prefix traversal did not consume both choices"
            )
