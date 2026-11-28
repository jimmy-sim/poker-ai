"""Thin CLI for the frozen read-only residual-map stages."""

import argparse
from pathlib import Path

from known_mixture_residual_map import proof
from known_mixture_residual_map.admission import forecast
from known_mixture_residual_map.gate import (
    clean_head,
    require_proof,
    source_fingerprint,
)
from known_mixture_residual_map.own import run as run_own
from known_mixture_residual_map.own import save
from known_mixture_residual_map.report import report


def main() -> None:
    """Run one explicitly selected stage, never advancing automatically."""
    parser = argparse.ArgumentParser()
    parser.add_argument("stage", choices=("proof", "admission", "own", "report"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path.cwd()
    output: Path = args.output
    if args.stage == "proof":
        proof.run(root, output)
    elif args.stage == "admission":
        head = clean_head(root)
        fingerprint = source_fingerprint(root)
        require_proof(root, fingerprint)
        decision = forecast(root)
        if output.exists():
            raise FileExistsError("retain prior residual-map admission")
        output.mkdir(parents=True)
        save(output / "decision.json", decision)
        save(
            output / "stage.json",
            {
                "status": decision["status"],
                "head": head,
                "source_fingerprint": fingerprint,
            },
        )
    elif args.stage == "own":
        run_own(root, output)
    else:
        report(root, output)


if __name__ == "__main__":
    main()
