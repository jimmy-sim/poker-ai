"""Measure all72 short B1 prefixes and full old-policy overhead under fixed gates."""

import argparse
import json
from pathlib import Path

from poker_ai.evaluation.matched_update_profile import run


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/matched-update-profile/profile.json"),
    )
    parser.add_argument(
        "--overhead",
        type=Path,
        default=Path("results/runs/matched-update-profile/overhead/own.json"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    saved = run(root, root / args.output, root / args.overhead)
    print(
        json.dumps(
            dict(
                status=saved["status"],
                seconds=saved["seconds"],
                forecast=saved["forecast"],
                overhead_seconds=saved["overhead_seconds"],
            ),
            sort_keys=True,
        )
    )
    return 0 if saved["status"] == "completed_own_profile_native_pending" else 1


if __name__ == "__main__":
    raise SystemExit(main())
