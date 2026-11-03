"""Inference over independent duplicate-deal clusters, never individual seats."""

import math
from statistics import NormalDist
from typing import Any

import numpy as np
from numpy.typing import NDArray


def summarize_pairs(
    profits: NDArray[np.float64],
    *,
    big_blind: int,
    maximum_loss: int,
    alpha: float = 0.05,
    family_size: int = 1,
) -> dict[str, Any]:
    """Rows are independent deals; columns are the two exchanged agent seats.

    Caller may average fixed agent policies WITHIN each deck/seat before this
    function; those policies are then a fixed mixture target, not independent
    statistical samples. The normal interval uses a large-N CLT approximation.
    Hoeffding interval/test require independent rows with support [-L,L], not
    symmetric profits or normality. The two-sided test is H0: E[profit] = 0.
    Bonferroni controls the declared family without assuming test independence.
    """
    if (
        profits.ndim != 2
        or profits.shape[1] != 2
        or profits.shape[0] < 2
        or not np.all(np.isfinite(profits))
        or type(big_blind) is not int
        or big_blind < 1
        or type(maximum_loss) is not int
        or maximum_loss < 1
        or type(family_size) is not int
        or family_size < 1
        or type(alpha) not in (float, int)
        or not 0 < alpha < 1
        or np.any(np.abs(profits) > maximum_loss)
    ):
        raise ValueError(
            "bounded finite duplicate profits and valid inference settings required"
        )
    pairs = profits.mean(axis=1)
    count = len(pairs)
    mean = float(pairs.mean())
    variance = float(pairs.var(ddof=1))
    paired_variance = variance / count
    unpaired_variance = float(profits.var(axis=0, ddof=1).sum()) / (4 * count)
    standard_error = math.sqrt(paired_variance)
    normal_radius = NormalDist().inv_cdf(1 - alpha / 2) * standard_error
    width = 2 * maximum_loss
    guaranteed_radius = width * math.sqrt(math.log(2 / alpha) / (2 * count))
    log_p_bound = min(0.0, math.log(2) - 2 * count * (mean / width) ** 2)
    log_adjusted = min(0.0, math.log(family_size) + log_p_bound)
    log_smallest = math.log(float.fromhex("0x0.0000000000001p-1022"))
    # Keep a positive display bound when a tiny mathematical tail underflows;
    # use the log bound for the significance decision.
    p_bound = math.exp(max(log_smallest, log_p_bound))
    adjusted = math.exp(max(log_smallest, log_adjusted))
    significant = log_adjusted <= math.log(alpha)
    scale = 1000 / big_blind
    return {
        "independent_deals": count,
        "mean_chips_per_hand": mean,
        "mbb_per_hand": scale * mean,
        "cluster_se_mbb_per_hand": scale * standard_error,
        "clt_interval_mbb_per_hand": [
            scale * (mean - normal_radius),
            scale * (mean + normal_radius),
        ],
        "hoeffding_interval_mbb_per_hand": [
            scale * max(-maximum_loss, mean - guaranteed_radius),
            scale * min(maximum_loss, mean + guaranteed_radius),
        ],
        "two_sided_p_bound": p_bound,
        "log_two_sided_p_bound": log_p_bound,
        "family_adjusted_two_sided_p_bound": adjusted,
        "nonzero_mean_significant": significant,
        "positive_mean_significant": mean > 0 and significant,
        "family_size": family_size,
        "alpha": alpha,
        "paired_to_unpaired_variance_ratio": None
        if unpaired_variance == 0
        else paired_variance / unpaired_variance,
        "empirical_zero_variance": variance == 0,
        "units": "milli-big-blinds per hand; each row is a duplicate-deal cluster",
    }
