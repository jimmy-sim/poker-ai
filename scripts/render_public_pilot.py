"""Render the public pilot, retaining losses and translation limits."""

import argparse
import gzip
import hashlib
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Any


def update(path: Path, body: str) -> None:
    begin, end = "<!-- PUBLIC_PILOT_BEGIN -->", "<!-- PUBLIC_PILOT_END -->"
    text = path.read_text()
    block = begin + "\n" + body.strip() + "\n" + end
    if begin in text:
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
    root = Path(__file__).resolve().parents[1]
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts/benchmark_slumbot.py"),
            "--replay-report",
            str(args.report),
        ],
        check=True,
    )
    report = json.loads(args.report.read_text())
    if report["status"] != "completed":
        raise ValueError("requires the complete predeclared pilot")
    events = json.loads(
        gzip.decompress((args.report.parent / report["events_file"]).read_bytes())
    )
    decisions = [e["diagnostics"] for e in events if e["kind"] == "decision"]
    counts = dict(Counter(d["status"] for d in decisions))
    if counts != report["lookup_counts"] or len(decisions) != sum(
        r["own_decisions"] for r in report["records"]
    ):
        raise ArithmeticError("decision records and lookup totals disagree")
    if any(d["shadow_failure"] or d["starting_stack_mismatch"] for d in decisions):
        raise ArithmeticError("unexpected failed/depth-mismatched public translation")
    summary = report["pilot_summary"]
    lo, hi = summary["approximate_iid_95_interval_mbb_per_hand"]
    hlo, hhi = summary["conditional_iid_hoeffding_95_interval_mbb_per_hand"]
    matched = counts.get("matched", 0)
    history_approx = sum(d["max_history_fraction_error"] > 0 for d in decisions)
    output_approx = sum(
        d["output_mean_raise_fraction_error"] is not None
        and d["output_mean_raise_fraction_error"] > 0
        for d in decisions
    )
    clipped = sum(bool(d["clipped_raise_mass"]) for d in decisions)
    unavailable = sum(bool(d["unavailable_raise_mass"]) for d in decisions)
    folds = sum(r["fold_settlement_checked"] for r in report["records"])
    net = sum(r["winnings"] for r in report["records"])
    audit: dict[str, Any] = {
        "status": "passed",
        "report_sha256": hashlib.sha256(args.report.read_bytes()).hexdigest(),
        "settled_hands": len(report["records"]),
        "own_decisions": len(decisions),
        "lookup_counts": counts,
        "independently_checked_fold_settlements": folds,
        "server_only_showdown_settlements": len(report["records"]) - folds,
        "history_approximation_decisions": history_approx,
        "output_grid_approximation_decisions": output_approx,
        "decisions_with_clipped_raise_mass": clipped,
        "decisions_with_unavailable_raise_mass": unavailable,
        "net_chips": net,
        "interpretation": (
            "nonzero approximation diagnostics are not chip EV estimates; "
            "no solver convergence or competitive strength claim"
        ),
    }
    body = (
        "### Public Slumbot protocol pilot\n\n"
        f"The predeclared **{len(report['records'])}-hand** anonymous 200bb pilot "
        f"completed with **{net / report['config']['big_blind']:+.2f}bb net** "
        f"(**{summary['mean_mbb_per_hand']:+,.0f} mbb/hand**). The approximate "
        f"IID 95% interval is [{lo:,.0f}, {hi:,.0f}] mbb/hand; the much wider "
        f"conditional-IID Hoeffding interval is [{hlo:,.0f}, {hhi:,.0f}]. "
        "Both contain zero. Server independence is unverified: this is an API "
        "and translation pilot, not evidence of a winning agent.\n\n"
        f"All {len(report['records'])} settlements replay offline, including "
        f"{folds} independently checked fold settlements. The remaining showdown "
        "outcomes use server net winnings; no opponent-card showdown verification "
        f"is claimed. Saved average rows were found at {matched}/{len(decisions)} "
        f"decisions ({matched / len(decisions):.1%}); {counts.get('unseen', 0)} "
        f"unseen and {counts.get('unaveraged', 0)} unaveraged rows used fallback. "
        "There were no shadow/depth failures, "
        f"{clipped} decisions with clipped raises and {unavailable} with unavailable "
        f"raise mass. However, {history_approx}/{len(decisions)} decisions had nonzero "
        f"history-size approximation, and {output_approx}/{matched} decoded "
        "distributions had nonzero output-grid approximation. Legal translation "
        "does not preserve strategy or EV.\n\n"
        "The server controls deals and its unreported policy version, so the "
        "live outcomes cannot be reproduced from client seeds. Sanitized logs "
        "reproduce recorded accounting and statistics. No API results train "
        "or update the agent; this pilot remains separate from open-source solver "
        "validation and the 100bb duplicate study.\n\n"
        f"Recorded evidence: `{args.report.as_posix()}`. Re-render and verify "
        f"without network: `uv run --locked python scripts/render_public_pilot.py "
        f"--report {args.report.as_posix()}`."
    )
    for path in (root / "README.md", root / "docs/phase4-evaluation.md"):
        update(path, body)
    (args.report.parent / "recorded-pilot-audit.json").write_text(
        json.dumps(audit, indent=2, sort_keys=True) + "\n"
    )
    print("passed: public pilot settlement/diagnostic audit and summaries rendered")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
