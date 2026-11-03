"""One command: gated Tier A, own self-play, postflop controls, tables and plots."""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from poker_ai.solver_validation.reporting import markdown_table
from poker_ai.validation.five_card import source_provenance


def update_block(path: Path, body: str, name: str = "RESULTS") -> None:
    start, end = (
        f"<!-- SOLVER_VALIDATION_{name}_BEGIN -->",
        f"<!-- SOLVER_VALIDATION_{name}_END -->",
    )
    text = path.read_text()
    block = start + "\n" + body.strip() + "\n" + end
    if start in text and end in text:
        first, remainder = text.split(start, 1)
        _, last = remainder.split(end, 1)
        text = first + block + last
    else:
        text = text.rstrip() + "\n\n" + block + "\n"
    path.write_text(text)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir", type=Path, default=Path("results/solver-validation")
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    build = root / "results/runs/solver-validation-build"
    build.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
    os.environ.setdefault("OMP_NUM_THREADS", "1")
    for path, status in (
        ("results/cfr-validation.json", "passed"),
        ("results/no-limit-training.json", "completed"),
        ("results/agent-interface-validation.json", "passed"),
    ):
        if json.loads((root / path).read_text())["status"] != status:
            raise ValueError(f"Phase 2/3 prerequisite missing or failed: {path}")
    source = source_provenance(
        root,
        root / "configs/solver-validation-postflop.json",
        entrypoints=(
            "scripts/validate_solvers.py",
            "scripts/validate_cfr.py",
            "scripts/train_holdem.py",
            "scripts/validate_postflop.py",
            "scripts/render_solver_report.py",
        ),
    )
    started = time.perf_counter()
    commands = [
        [
            "scripts/validate_cfr.py",
            "--config",
            "configs/solver-validation-tier-a.json",
            "--output",
            str(build / "tier-a.json"),
        ],
        [
            "scripts/train_holdem.py",
            "--config",
            "configs/solver-agent-ablation.json",
            "--output",
            str(build / "agent-training.json"),
        ],
        [
            "scripts/validate_postflop.py",
            "--config",
            "configs/solver-validation-postflop.json",
            "--training-report",
            str(build / "agent-training.json"),
            "--output",
            str(build / "postflop.json"),
        ],
    ]
    commands.append(["scripts/render_solver_report.py", "--output-dir", str(build)])
    for command in commands:
        print("Running " + " ".join(command), flush=True)
        subprocess.run([sys.executable, *command], cwd=root, check=True)
    reports: dict[str, Any] = {
        name: json.loads((build / name).read_text())
        for name in (
            "tier-a.json",
            "agent-training.json",
            "postflop.json",
            "render-manifest.json",
        )
    }
    if any(
        reports[name]["status"] != status
        for name, status in (
            ("tier-a.json", "passed"),
            ("agent-training.json", "completed"),
            ("postflop.json", "passed"),
            ("render-manifest.json", "passed"),
        )
    ):
        raise ArithmeticError(
            "a validation stage failed; reviewed outputs not replaced"
        )
    artifacts = set(reports)
    for name in ("tier-a.json", "postflop.json", "render-manifest.json"):
        for relative, expected in reports[name]["artifacts_sha256"].items():
            if Path(relative).name != relative:
                raise ValueError("artifact must be a single filename")
            if hashlib.sha256((build / relative).read_bytes()).hexdigest() != expected:
                raise ValueError("generated artifact fingerprint mismatch")
            artifacts.add(relative)
    destination = args.output_dir.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    for name in sorted(artifacts):
        shutil.copyfile(build / name, destination / name)
    postflop = reports["postflop.json"]
    tier_a = reports["tier-a.json"]
    max_gap = max(r["exploitability_gap"] for r in tier_a["rows"])
    rows = postflop["primary_summary"]
    worse = sum(
        r["own_exploitability_pot_fraction"]
        > r["reference_exploitability_pot_fraction"]
        for r in rows
    )
    losses = sum(r["ev_gap_vs_reference_chips"] < 0 for r in rows)
    coverage = [r["trained_policy_reach_fraction"] for r in rows]
    diagnosis = (
        f"Own restricted exploitability exceeds the reference in {worse}/{len(rows)} "
        f"spots; hero EV against the same reference opponent is lower in "
        f"{losses}/{len(rows)}. Trained-policy coverage spans "
        f"{100 * min(coverage):.1f}–{100 * max(coverage):.1f}% "
        "of reference decision reach; "
        "the rest uses explicit uniform fallbacks. "
    )
    body = (
        "### Reproduced external-solver comparison\n\n"
        f"Exact-game CFR variants matched OpenSpiel 2.0.2 within **{max_gap:.3g} "
        "ante chips/hand** exploitability at matched iterations.\n\n"
        "Five **turn subgames**, two physical combos per player, "
        "matched full-pot/all-in "
        "actions. Primary own agent: eight potential buckets, 1,000 global self-play "
        "iterations, three fixed seeds. Entries below are seed means; raw reports "
        "include seed ranges, node frequencies, hand-class EVs and all ablations.\n\n"
        + markdown_table(rows)
        + "\n"
        "Action gap is reference-reach-weighted per-node action MAE, in percentage "
        "points. Exploitability is NashConv/2; EV compares the hero policy against "
        "the same reference opponent. Pot-normalized EV gaps use root-pot units. "
        "These are exact restricted-game expectations, "
        "not measured full-game win rates.\n\n"
        + diagnosis
        + "Three training seeds do not establish a population confidence interval.\n\n"
        "![Root strategy by the two configured hand classes](HEATMAP_PATH)\n\n"
        "Reproduce: `make validate-solvers` (minutes on the recorded Mac; optional "
        "solver/evaluator/plot dependencies are installed from the lockfile). "
        "No commercial solver data are used. See WRITEUP_PATH for methodology, "
        "licenses, convergence, diagnostics and limits."
    )
    update_block(
        root / "README.md",
        body.replace(
            "HEATMAP_PATH", "results/solver-validation/strategy-heatmap.png"
        ).replace("WRITEUP_PATH", "[the technical writeup](docs/solver_validation.md)"),
    )
    update_block(
        root / "docs/solver_validation.md",
        body.replace(
            "HEATMAP_PATH", "../results/solver-validation/strategy-heatmap.png"
        ).replace("WRITEUP_PATH", "this document"),
    )
    for name, filename in (
        ("TIER_A", "tier-a-summary.md"),
        ("DIAGNOSIS", "diagnosis.md"),
        ("CLAIMS", "verified-claims.md"),
        ("ABSTRACTION", "abstraction-aliases.md"),
        ("HAND_EV", "hand-class-ev.md"),
    ):
        update_block(
            root / "docs/solver_validation.md",
            (destination / filename).read_text(),
            name,
        )
    manifest = {
        "schema_version": 1,
        "status": "passed",
        "source": source,
        "seconds": time.perf_counter() - started,
        "commands": commands,
        "artifacts_sha256": {
            name: hashlib.sha256((destination / name).read_bytes()).hexdigest()
            for name in sorted(artifacts)
        },
        "checkpoint_retention": (
            "ignored results/runs/solver-validation-build/runs/agent-training/"
            "checkpoints; recreated by this command"
        ),
        "limitations": (
            "Local reproducibility on the recorded environment; "
            "no hosted CI or full-game playing-strength claim"
        ),
    }
    (destination / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )
    print(
        f"passed: complete solver-validation pipeline; outputs: {destination}",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
