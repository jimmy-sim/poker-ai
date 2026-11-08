"""Audit retained old-own/native pipeline costs and regenerate forecasts."""

import argparse
import json
from pathlib import Path

from poker_ai.postflop.pipeline_report import summary, tables


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--own", type=Path, default=Path("results/controlled-pipeline-check/own.json")
    )
    parser.add_argument(
        "--native",
        type=Path,
        default=Path("results/controlled-pipeline-check/native.json"),
    )
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    result = summary(root, root / args.own, root / args.native)
    print(tables(result))
    if args.output:
        output = root / args.output
        output.mkdir(parents=True, exist_ok=False)
        (output / "summary.json").write_text(
            json.dumps(result, sort_keys=True, indent=2) + "\n"
        )
        (output / "tables.md").write_text(tables(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
