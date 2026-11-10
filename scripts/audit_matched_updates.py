"""Audit published OWN tiny, old-timing or admitted real matched-update evidence."""

import argparse
import json
from pathlib import Path

from poker_ai.solver_validation.matched_updates import audit


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--own", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    scope = parser.add_mutually_exclusive_group()
    scope.add_argument("--tiny", action="store_true")
    scope.add_argument("--timing", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    saved = audit(
        root, root / args.own, root / args.output, tiny=args.tiny, timing=args.timing
    )
    print(
        json.dumps(
            dict(
                status=saved["status"],
                profiles=saved["completed_profiles"],
                fixed_targets=saved["completed_fixed_targets"],
                seconds=saved["seconds"],
                maximum_error_chips=saved["maximum_error_chips"],
            ),
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
