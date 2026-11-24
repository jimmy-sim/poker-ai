"""Fictional arithmetic proof without reading any saved poker policy."""

import argparse
import json
from pathlib import Path

import numpy as np
from known_turn_loss_attribution.gate import (
    SOURCE,
    clean_head,
    require_archive,
    source_fingerprint,
)
from known_turn_loss_attribution.math import summarize


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    control = np.array(
        [0.25, 0.125, 0.375, 0, 0.5, 0.125, 0, 0.25, 0.125, 0, 0.25],
        dtype=np.float64,
    )
    candidate = np.array(
        [0.5, 0, 0.25, 0, 0.625, 0.125, 0, 0.125, 0.25, 0, 0.125],
        dtype=np.float64,
    )
    args.output.mkdir(parents=True, exist_ok=False)
    np.savez_compressed(
        args.output / "fictional-contributions.npz",
        control=control,
        candidate=candidate,
    )
    with np.load(
        args.output / "fictional-contributions.npz", allow_pickle=False
    ) as replay:
        old = replay["control"]
        new = replay["candidate"]
    np.testing.assert_array_equal(old, control)
    np.testing.assert_array_equal(new, candidate)
    result = summarize(old, new, list(range(len(old))), [0, 1])
    assert (
        abs(result["net_change_chips"] - float(candidate.sum() - control.sum())) < 1e-12
    )
    assert result["top_ten_by_delta"][0] == 0
    assert result["positive_worsening_chips"] > 0
    (args.output / "proof.json").write_text(
        json.dumps(
            {
                "status": "passed",
                "head": head,
                "source_fingerprint": fingerprint,
                "fictional_only": True,
                "result": result,
            },
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )


if __name__ == "__main__":
    main()
