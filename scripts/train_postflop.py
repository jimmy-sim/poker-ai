"""Train own postflop controls; never import reference solvers or outputs."""

import argparse
import hashlib
import json
from pathlib import Path
from typing import cast

from poker_ai.postflop.learning import run_training
from poker_ai.postflop.matrix import Encoding


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config", type=Path, default=Path("configs/holdem-learning.json")
    )
    parser.add_argument(
        "--phase", choices=("development", "heldout"), default="development"
    )
    parser.add_argument(
        "--encodings",
        nargs="+",
        choices=("exact", "legacy_b8", "public_b8"),
        default=["exact"],
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/holdem-learning/development-exact.json"),
    )
    parser.add_argument("--development-report", type=Path)
    parser.add_argument("--development-independent", type=Path)
    args = parser.parse_args()
    if args.phase == "heldout":
        if args.development_report is None or args.development_independent is None:
            parser.error(
                "heldout training requires development learning/independent gates"
            )
        own = json.loads(args.development_report.read_text())
        independent = json.loads(args.development_independent.read_text())
        config = json.loads(args.config.read_text())
        if (
            own["status"] != "completed"
            or own["config"] != config
            or own.get("exact_acceptance", {}).get("passed") is not True
            or independent["status"] != "passed"
            or independent["input_sha256"]
            != hashlib.sha256(args.development_report.read_bytes()).hexdigest()
        ):
            parser.error("heldout gate not satisfied for this exact frozen config")

    report = run_training(
        Path(__file__).resolve().parents[1],
        args.config,
        args.output,
        phase=args.phase,
        encodings=tuple(cast(Encoding, e) for e in args.encodings),
    )
    print(
        f"{report['status']}: own postflop training; gate={report['exact_acceptance']}"
    )
    return 0 if report["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
