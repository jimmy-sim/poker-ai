"""Check numerical reproduction against a retained, verified Git run."""

import argparse
import gzip
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any


def historical(root: Path, commit: str, relative: str) -> bytes:
    # Explicit positional Git object, no shell interpolation. Only known result
    # paths from this script are requested, never checkpoint/credential paths.
    return subprocess.run(
        ["git", "show", f"{commit}:{relative}"],
        cwd=root,
        check=True,
        capture_output=True,
    ).stdout


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-commit", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    directory = root / "results/solver-validation"
    old_raw = historical(
        root, args.reference_commit, "results/solver-validation/postflop.json"
    )
    old = json.loads(old_raw)
    current_raw = (directory / "postflop.json").read_bytes()
    current = json.loads(current_raw)
    if (
        old["status"] != "passed"
        or current["status"] != "passed"
        or old["config"] != current["config"]
    ):
        raise ValueError("requires two passed runs of the same protocol")
    checked_profiles = checked_nodes = node_files = reference_files = 0
    for first, second in zip(old["spots"], current["spots"], strict=True):
        a, b = dict(first), dict(second)
        a.pop("seconds")
        b.pop("seconds")
        for left, right in zip(a["comparisons"], b["comparisons"], strict=True):
            left.pop("checkpoint_sha256")
            right.pop("checkpoint_sha256")
            checked_profiles += 1
            if "details_file" in left:
                relative = "results/solver-validation/" + left["details_file"]
                before = json.loads(
                    gzip.decompress(historical(root, args.reference_commit, relative))
                )
                after = json.loads(gzip.decompress((root / relative).read_bytes()))
                before["metadata"].pop("checkpoint_sha256")
                after["metadata"].pop("checkpoint_sha256")
                if before != after:
                    raise ArithmeticError("detailed decision/frequency numbers changed")
                checked_nodes += len(after["decision_rows"])
                node_files += 1
        if a != b:
            raise ArithmeticError("spot metrics/convergence/diagnosis changed")
        relative = "results/solver-validation/" + first["reference_file"]
        if (
            historical(root, args.reference_commit, relative)
            != (root / relative).read_bytes()
        ):
            raise ArithmeticError("reference policy artifact changed")
        reference_files += 1
    before_tier = json.loads(
        historical(root, args.reference_commit, "results/solver-validation/tier-a.json")
    )
    after_tier = json.loads((directory / "tier-a.json").read_text())
    for left, right in zip(before_tier["rows"], after_tier["rows"], strict=True):
        for row in (left, right):
            row.pop("own_training_seconds")
            row.pop("reference_training_seconds")
        if left != right:
            raise ArithmeticError("exact-game numerical metrics changed")
    result: dict[str, Any] = {
        "status": "passed",
        "reference_commit": args.reference_commit,
        "reference_report_sha256": hashlib.sha256(old_raw).hexdigest(),
        "current_report_sha256": hashlib.sha256(current_raw).hexdigest(),
        "current_experiment_source": current["source"],
        "exact_comparison_profiles": checked_profiles,
        "exact_detailed_decision_rows": checked_nodes,
        "exact_detailed_files": node_files,
        "byte_identical_reference_policies": reference_files,
        "exact_tier_a_rows": len(after_tier["rows"]),
        "excluded": [
            "runtime",
            "provenance",
            "own checkpoint hashes containing provenance",
            "rendered figures",
        ],
        "scope": (
            "Exact numeric equality on this locked local environment; "
            "not a cross-platform guarantee"
        ),
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(
        f"passed: {checked_profiles} profiles and "
        f"{checked_nodes} detailed decisions reproduce",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
