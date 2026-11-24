"""Make the separate data-only 900-second diagnostic compute decision."""

import argparse
import json
from pathlib import Path

from known_wet_residual.analysis import save
from known_wet_residual.gate import (
    PROOF,
    SOURCE,
    clean_head,
    contract,
    require_archive,
    source_fingerprint,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path.cwd()
    plan = contract(root)
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    for stage, status in ((SOURCE, "source_qualified"), (PROOF, "proof_passed")):
        require_archive(root, root / stage, status, fingerprint)
    parent = root / "results/known-wet-turn-mechanism/report/job-state.json"
    state = json.loads(parent.read_bytes())
    wall = state["observed_wall_seconds"]
    bound = 2 * wall + 120
    if (
        state["status"] != "passed"
        or wall != plan["parent_report_wall_seconds"]
        or bound != plan["forecast_bound_seconds"]
    ):
        raise ArithmeticError("pinned parent diagnostic forecast changed")
    status = "admitted" if bound < plan["hard_cap_seconds"] else "rejected"
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    save(
        output / "decision.json",
        dict(
            status=status,
            head=head,
            source_fingerprint=fingerprint,
            parent_report_job_state=parent.relative_to(root).as_posix(),
            parent_report_wall_seconds=wall,
            forecast_bound_seconds=bound,
            hard_cap_seconds=plan["hard_cap_seconds"],
            formula="2*parent_report_wall_seconds+120<900",
        ),
    )
    if status != "admitted":
        raise ArithmeticError("conservative diagnostic compute forecast rejected")


if __name__ == "__main__":
    main()
