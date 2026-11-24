"""Pure fixed-row ranking and contribution arithmetic for a saved policy."""

import math
from typing import Any

import numpy as np
from numpy.typing import NDArray

FloatVector = NDArray[np.float64]


def rank_street(
    contributions: FloatVector, identities: list[dict[str, Any]], street: str
) -> list[int]:
    """Select ten highest additive gains, with exact index as stable tie break."""
    if street not in ("TURN", "RIVER") or len(contributions) != len(identities):
        raise ValueError("invalid street or exact-row inventory")
    if (
        not np.all(np.isfinite(contributions))
        or float(contributions.min(initial=0)) < -1e-12
    ):
        raise ArithmeticError("nonfinite or negative additive gain")
    rows = [i for i, identity in enumerate(identities) if identity["street"] == street]
    if len(rows) < 10:
        raise ArithmeticError("fewer than ten exact rows on registered street")
    return sorted(rows, key=lambda i: (-float(contributions[i]), i))[:10]


def street_summary(
    contributions: FloatVector,
    identities: list[dict[str, Any]],
    selected: list[int],
    street: str,
) -> dict[str, Any]:
    """Describe one street without treating local gain as a causal action swap."""
    if (
        len(selected) != 10
        or len(set(selected)) != 10
        or any(identities[i]["street"] != street for i in selected)
    ):
        raise ArithmeticError("fixed ten-row street selection changed")
    total = math.fsum(
        float(contributions[i])
        for i, identity in enumerate(identities)
        if identity["street"] == street
    )
    top = math.fsum(float(contributions[i]) for i in selected)
    if total < -1e-12 or top < -1e-12 or top > total + 1e-9:
        raise ArithmeticError("invalid street contribution sum")
    share = top / total if total > 0 else 0.0
    return dict(
        total_chips=total,
        selected_chips=top,
        selected_share=share,
        concentration="concentrated" if share >= 0.5 else "diffuse",
    )
