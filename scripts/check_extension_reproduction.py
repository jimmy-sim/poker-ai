"""Compare exact extension numerics while excluding runtime/source metadata."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any


def compare(first: Path, second: Path) -> dict[str, Any]:
    counts = {}
    inputs = {}
    for name in ("opponents.json", "bankroll.json"):
        left, right = (
            json.loads((directory / name).read_text()) for directory in (first, second)
        )
        if left["config"] != right["config"] or left["rows"] != right["rows"]:
            raise ArithmeticError(f"extension numerics/configs differ: {name}")
        if name == "bankroll.json" and left["ruin_controls"] != right["ruin_controls"]:
            raise ArithmeticError("analytic/Monte Carlo ruin controls differ")
        counts[name] = len(left["rows"])
        inputs[name] = [
            hashlib.sha256((d / name).read_bytes()).hexdigest() for d in (first, second)
        ]
    for name in ("own-risk-profiles.json.gz", "public-transcripts.json.gz"):
        left, right = (
            json.loads(gzip.decompress((d / name).read_bytes()))
            for d in (first, second)
        )
        left.pop("source", None)
        right.pop("source", None)
        if left != right:
            raise ArithmeticError(f"own policy or censored observations differ: {name}")
    return {
        "status": "passed",
        "counts": counts,
        "input_sha256": inputs,
        "scope": (
            "exact Bayesian rows, conditional risk cells, ruin controls, "
            "own profiles and censored observations; timing/source metadata "
            "excluded; empirical follow-up not present in first run"
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, default=Path("results/extensions"))
    parser.add_argument(
        "--output", type=Path, default=Path("results/extensions/reproduction.json")
    )
    args = parser.parse_args()
    report = compare(args.first, args.second)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print("passed: exact extension numerics and own transcript/profile replay")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
