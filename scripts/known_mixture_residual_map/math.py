"""Pure, synthetic-testable summary of additive reply-gain vectors."""

import math
from typing import Any

import numpy as np
from numpy.typing import NDArray

FloatArray = NDArray[np.float64]


def summarize(
    gains: FloatArray,
    streets: tuple[str, ...],
    published_chips: float,
    *,
    tolerance: float = 1e-9,
    nonnegative_slack: float = 1e-12,
) -> dict[str, Any]:
    """Reconcile exact NashConv/2 row gains and apply frozen routing labels.

    Gains are chips to the replying seats, averaged across both seats. A best
    response optimizes against this policy's saved opponent and continuation.
    Thus policy-to-policy differences in these rows are descriptive, not causal.
    """
    if (
        gains.ndim != 1
        or len(gains) != len(streets)
        or set(streets) != {"TURN", "RIVER"}
    ):
        raise ArithmeticError("fixed turn/river row grid changed")
    if not np.isfinite(gains).all() or not math.isfinite(published_chips):
        raise ArithmeticError("nonfinite reply gain")
    if float(gains.min(initial=0)) < -nonnegative_slack:
        raise ArithmeticError("negative additive reply gain")
    total = math.fsum(float(v) for v in gains)
    if abs(total - published_chips) > tolerance or total <= 0:
        raise ArithmeticError("published scalar and row gains disagree")
    by_street: dict[str, Any] = {}
    for street in ("TURN", "RIVER"):
        indices = [i for i, label in enumerate(streets) if label == street]
        ordered = sorted(indices, key=lambda i: (-float(gains[i]), i))
        street_sum = math.fsum(float(gains[i]) for i in indices)
        positive = math.fsum(max(0.0, float(gains[i])) for i in indices)
        top_ten = math.fsum(max(0.0, float(gains[i])) for i in ordered[:10])
        by_street[street] = {
            "gain_chips": street_sum,
            "share_of_total": street_sum / total,
            "positive_rows": sum(gains[i] > 0 for i in indices),
            "top_ten_positive_share": None if positive == 0 else top_ten / positive,
            "concentration": "none"
            if positive == 0
            else ("concentrated" if top_ten / positive >= 0.50 else "distributed"),
            "top_five_indices": ordered[:5],
        }
    if abs(sum(row["gain_chips"] for row in by_street.values()) - total) > tolerance:
        raise ArithmeticError("street gains do not reconcile")
    turn = by_street["TURN"]["share_of_total"]
    river = by_street["RIVER"]["share_of_total"]
    label = (
        "turn-dominant"
        if turn >= 0.60
        else "river-dominant"
        if river >= 0.60
        else "split"
    )
    return {"total_chips": total, "street_label": label, "streets": by_street}
