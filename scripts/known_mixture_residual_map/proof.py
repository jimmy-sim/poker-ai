"""Fictional-only accounting and fixed-row proof; opens no poker policy."""

from pathlib import Path

import numpy as np

from known_mixture_residual_map.gate import (
    clean_head,
    require_source,
    source_fingerprint,
)
from known_mixture_residual_map.math import summarize
from known_mixture_residual_map.own import fixed_parent_rows, save


def run(root: Path, output: Path) -> None:
    """Prove routing, ties and bad-input rejection with invented values."""
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_source(root, fingerprint)
    if output.exists():
        raise FileExistsError("retain prior fictional proof")
    output.mkdir(parents=True)
    values = np.array([0.6, 0.2, 0.1, 0.1], dtype=np.float64)
    row = summarize(values, ("TURN", "TURN", "RIVER", "RIVER"), 1.0)
    synthetic = {
        "diagnostics": [
            {
                "game": "fictional",
                "exact_info": i,
                "control_final_rank_within_street": i,
            }
            for i in range(1, 7)
        ]
    }
    if row["street_label"] != "turn-dominant" or fixed_parent_rows(
        synthetic, "fictional"
    ) != set(range(1, 7)):
        raise ArithmeticError("fictional residual-map proof failed")
    rejected = False
    try:
        summarize(values, ("TURN", "TURN", "RIVER", "RIVER"), 0.9)
    except ArithmeticError:
        rejected = True
    if not rejected:
        raise ArithmeticError("fictional scalar mismatch was accepted")
    save(
        output / "proof.json",
        {
            "status": "proof_passed",
            "head": head,
            "source_fingerprint": fingerprint,
            "fictional_only": True,
            "real_policy_opened": False,
            "row_order": row["streets"]["TURN"]["top_five_indices"],
            "mismatch_rejected": rejected,
        },
    )
