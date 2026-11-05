"""Prepare the predeclared cohort once, or verify its development admission gate."""

import argparse
import json
from pathlib import Path

from poker_ai.postflop.fresh_cohort import development_gate, prepare_cohort


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/fresh-validation.json")
    )
    parser.add_argument("--gate-only", action="store_true")
    parser.add_argument(
        "--receipt", type=Path, default=Path("results/runs/fresh-admission.json")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    if not args.gate_only:
        freeze = prepare_cohort(root, args.config)
        print(
            f"prepared: {len(freeze['spot_sha256'])} structurally selected fresh cases"
        )
        print("Commit and publish the cohort/freeze before admission or training.")
        return 0
    result = development_gate(root, args.config)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        f"admission={result['status']}; "
        f"replayed {result['replayed_final_policies']} final development policies"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
