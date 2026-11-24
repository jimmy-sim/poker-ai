"""Check fictional row ranking and additive street accounting before real replay."""

import argparse
from pathlib import Path

import numpy as np
from known_wet_residual.analysis import save
from known_wet_residual.gate import (
    SOURCE,
    clean_head,
    require_archive,
    source_fingerprint,
)
from known_wet_residual.math import rank_street, street_summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path.cwd()
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    identities = [dict(street="TURN" if i < 12 else "RIVER") for i in range(24)]
    contribution = np.asarray([0.05] * 12 + [0.01] * 12, dtype=np.float64)
    contribution[2] = 0.5
    contribution[14] = 0.2
    turn = rank_street(contribution, identities, "TURN")
    river = rank_street(contribution, identities, "RIVER")
    a = street_summary(contribution, identities, turn, "TURN")
    b = street_summary(contribution, identities, river, "RIVER")
    if (
        turn != [2, 0, 1, 3, 4, 5, 6, 7, 8, 9]
        or river != [14, 12, 13, 15, 16, 17, 18, 19, 20, 21]
        or abs(a["total_chips"] + b["total_chips"] - contribution.sum()) > 1e-12
        or a["concentration"] != "concentrated"
        or b["concentration"] != "concentrated"
    ):
        raise ArithmeticError("fictional residual ranking or additivity failed")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    save(
        output / "proof.json",
        dict(
            status="proof_passed",
            head=head,
            source_fingerprint=fingerprint,
            fictional=True,
            turn_selection=turn,
            river_selection=river,
            turn=a,
            river=b,
            policy_outcomes_read=False,
        ),
    )


if __name__ == "__main__":
    main()
