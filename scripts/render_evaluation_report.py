"""Render reviewed local match results without choosing favorable opponents/seeds."""

import argparse
import csv
import hashlib
import json
from pathlib import Path

from poker_ai.validation.five_card import source_provenance


def update(path: Path, body: str) -> None:
    begin, end = "<!-- EVALUATION_RESULTS_BEGIN -->", "<!-- EVALUATION_RESULTS_END -->"
    text = path.read_text()
    block = begin + "\n" + body.strip() + "\n" + end
    if begin in text and end in text:
        first, rest = text.split(begin, 1)
        _, last = rest.split(end, 1)
        text = first + block + last
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    path.write_text(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    report = json.loads(args.report.read_text())
    directory = args.report.parent
    audit_path = directory / "record-audit.json"
    audit = json.loads(audit_path.read_text())
    digest = hashlib.sha256(args.report.read_bytes()).hexdigest()
    if (
        report["status"] != "completed"
        or report["mode"] != "main"
        or audit["status"] != "passed"
        or audit["input_sha256"] != digest
    ):
        raise ValueError("requires a complete, audited main study")
    coverage = []
    for row in audit["opponents"]:
        counts = row["lookup_totals"]
        total = sum(counts.values())
        coverage.append(
            {
                "opponent": row["opponent"],
                "own_decisions": total,
                **counts,
                "saved_average_row_fraction": None
                if total == 0
                else counts["matched"] / total,
            }
        )
    coverage_file = directory / "lookup-coverage.csv"
    with coverage_file.open("w", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(coverage[0]))
        writer.writeheader()
        writer.writerows(coverage)
    results = report["results"]
    hands = sum(r["hands"] for r in results)
    n = report["config"]["main_deals"]
    positive = sum(r["primary_inference"]["positive_mean_significant"] for r in results)
    nonzero = sum(r["primary_inference"]["nonzero_mean_significant"] for r in results)
    ratios = [
        r["primary_inference"]["paired_to_unpaired_variance_ratio"]
        for r in results
        if r["primary_inference"]["paired_to_unpaired_variance_ratio"] is not None
    ]
    ratio_text = "undefined" if not ratios else f"{min(ratios):.3f}–{max(ratios):.3f}"
    summary = (directory / "match-summary.md").read_text()
    loss_names = [
        r["opponent"] for r in results if r["primary_inference"]["mbb_per_hand"] < 0
    ]
    loss_text = (
        "Point-estimate losses occur against " + ", ".join(loss_names) + ". "
        if loss_names
        else "No point estimate is negative in this study. "
    )
    agent_count = len(report["config"]["agent_seeds"])
    stack_bb = (
        report["config"]["rules"]["stacks"][0] / report["config"]["rules"]["big_blind"]
    )
    body = (
        "### Local duplicate-deal evaluation\n\n"
        f"**{hands:,} simulated hands**, six fixed opponents, {agent_count} frozen own "
        f"training seeds. The same **{n:,} independently drawn decks** are reused "
        "across both seats, fixed agents and opponents; each comparison has N="
        f"{n:,} independent clusters. It does not have one independent sample "
        f"per hand or per training seed. Stakes: {stack_bb:g}bb; "
        "matched full-pot/all-in grid.\n\n" + summary + "\n"
        f"Predeclared six-opponent family test: **{positive}/6 positive advantages "
        f"and {nonzero}/6 nonzero means pass** the conservative Bonferroni–Hoeffding "
        "criterion. Pointwise approximate CLT intervals suggest differences, but "
        "they are not the predeclared primary significance rule. Failure of that "
        "test does not establish zero advantage; its worst-case bound has low "
        "power at this N. "
        + loss_text
        + "The small ISMCTS opponent is a limited search baseline, not "
        "an equilibrium strategy or competitive poker benchmark.\n\n"
        f"Estimated paired/covariance-omitted variance ratios: **{ratio_text}**. "
        "This is the documented variance-reduction alternative to AIVAT; no AIVAT "
        "estimator or independent unpaired-match experiment is claimed. All raw "
        "hand records, own fallback counts, seed results and failures are retained.\n\n"
        "![Win rates and pointwise intervals](FIGURE)\n\n"
        "Reproduce with `make evaluate-agents`; `make report-evaluation` re-audits "
        "and renders existing raw results without replaying matches. See WRITEUP "
        "for policy definitions, reference license/rule checks and limitations. "
        "No real-money client is used."
    )
    root = Path(__file__).resolve().parents[1]
    update(
        root / "README.md",
        body.replace("FIGURE", "results/evaluation/winrate-intervals.png").replace(
            "WRITEUP", "[the evaluation writeup](docs/phase4-evaluation.md)"
        ),
    )
    update(
        root / "docs/phase4-evaluation.md",
        body.replace("FIGURE", "../results/evaluation/winrate-intervals.png").replace(
            "WRITEUP", "this document"
        ),
    )
    claims = directory / "verified-claims.md"
    claims.write_text(
        "# Verified evaluation claim drafts\n\n"
        f"- Built a reproducible duplicate-deal evaluator and audited {hands:,} "
        "simulated hands across six opponents, with three fixed policies, "
        "cluster-aware confidence intervals and familywise significance control. "
        "The independent unit is the shared deck, not each replayed hand.\n"
        f"- Measured paired/covariance-omitted variance ratios of {ratio_text} "
        "in this fixed six-opponent study; retained unfavorable matchups and "
        f"reported {positive}/6 positive advantages passing "
        "the primary conservative test. "
        "This is not AIVAT, unrestricted poker exploitability "
        "or a winning-agent claim.\n"
    )
    manifest = {
        "status": "passed",
        "input_sha256": digest,
        "audit_sha256": hashlib.sha256(audit_path.read_bytes()).hexdigest(),
        "source": source_provenance(
            root,
            root / "configs/match-evaluation.json",
            entrypoints=(
                "scripts/render_evaluation_report.py",
                "scripts/audit_match_records.py",
            ),
        ),
        "artifacts_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (coverage_file, claims)
        },
    }
    (directory / "render-manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print("passed: audited local evaluation summary and claim drafts")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
