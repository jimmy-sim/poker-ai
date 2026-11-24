"""Separate data-only admission from pinned prior whole-process clocks."""

import argparse
import json
from pathlib import Path

from known_turn_loss_attribution.forecast import forecast
from known_turn_loss_attribution.gate import (
    PROOF,
    SOURCE,
    clean_head,
    require_archive,
    source_fingerprint,
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_archive(root, root / SOURCE, "source_qualified", fingerprint)
    require_archive(root, root / PROOF, "proof_passed", fingerprint)
    decision = forecast(root)
    args.output.mkdir(parents=True, exist_ok=False)
    (args.output / "decision.json").write_text(
        json.dumps(decision, sort_keys=True, indent=2) + "\n"
    )
    (args.output / "context.json").write_text(
        json.dumps(
            {"head": head, "source_fingerprint": fingerprint, "data_only": True},
            sort_keys=True,
            indent=2,
        )
        + "\n"
    )
    if decision["status"] != "admitted":
        raise ArithmeticError("strict conservative read-only admission rejected")


if __name__ == "__main__":
    main()
