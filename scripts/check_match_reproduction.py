"""Audit raw/numerical equality of two fixed-protocol local match runs."""

import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--first", type=Path, required=True)
    parser.add_argument("--second", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    first, second = (
        json.loads(args.first.read_text()),
        json.loads(args.second.read_text()),
    )
    if (
        first["status"] != "completed"
        or second["status"] != "completed"
        or first["config"] != second["config"]
        or first["mode"] != second["mode"]
        or first["native_controls"] != second["native_controls"]
    ):
        raise ValueError(
            "requires completed local runs with identical designs/controls"
        )
    fields = (
        "opponent",
        "completed_deals",
        "hands",
        "raw_sha256",
        "primary_inference",
        "per_seed",
        "lookup_counts_by_seed",
        "projected_decisions",
    )
    for before, after in zip(first["results"], second["results"], strict=True):
        if any(before[key] != after[key] for key in fields):
            raise ArithmeticError(f"match replay differs: {before['opponent']}")
    report = {
        "status": "passed",
        "mode": first["mode"],
        "first_report_sha256": hashlib.sha256(args.first.read_bytes()).hexdigest(),
        "second_report_sha256": hashlib.sha256(args.second.read_bytes()).hexdigest(),
        "sources": [first["source"], second["source"]],
        "raw_opponents_matched": len(first["results"]),
        "hands_per_run": sum(row["hands"] for row in first["results"]),
        "comparison_fields": fields,
        "excluded": ["elapsed time", "provenance", "rendered figures"],
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(f"passed: {len(first['results'])} opponent hand records replay exactly")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
