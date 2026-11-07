"""Compare all own diagnosis cases after an optional-renderer import fix."""

import argparse
import json
from pathlib import Path

from poker_ai.postflop.reply_diagnosis import numerical_difference
from poker_ai.postflop.river_study import digest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--before",
        type=Path,
        default=Path("results/saved-replies-initial/diagnosis.json"),
    )
    parser.add_argument(
        "--after", type=Path, default=Path("results/saved-replies/diagnosis.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("results/saved-replies/reproduction.json")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    before, after = root / args.before, root / args.after
    old, new = json.loads(before.read_text()), json.loads(after.read_text())
    error = numerical_difference(old["cases"], new["cases"])
    identical_details = old["details_sha256"] == new["details_sha256"]
    result = {
        "status": "identical_cases"
        if error == 0 and identical_details
        else "different",
        "maximum_numeric_difference": error,
        "details_byte_identical": identical_details,
        "cases_compared": len(new["cases"]),
        "before_sha256": digest(before),
        "after_sha256": digest(after),
        "before_source": old["source"]["git_commit"],
        "after_source": new["source"]["git_commit"],
        "script_sha256": digest(Path(__file__)),
        "excluded": (
            "source/environment/timing receipts and native audit; compares all "
            "nested case fields, including examples"
        ),
    }
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    print(f"case reproduction: {result['status']}; {result['cases_compared']} cases")
    return 0 if error == 0 and identical_details else 1


if __name__ == "__main__":
    raise SystemExit(main())
