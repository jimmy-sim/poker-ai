"""Reproduce the fixed diagnostic; failed learning gates remain nonzero outcomes."""

import json
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

from poker_ai.validation.five_card import source_provenance


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    started = time.perf_counter()
    stage = (
        root
        / "results/holdem-learning/runs"
        / datetime.now(UTC).strftime("%Y%m%dT%H%M%S.%fZ")
    )
    stage.mkdir(parents=True)
    source = source_provenance(
        root,
        root / "configs/holdem-learning-extended-linear-warm.json",
        entrypoints=("scripts/reproduce_postflop_learning.py",),
    )
    experiments = []

    def run(script: str, *args: str) -> None:
        subprocess.run(
            [sys.executable, str(root / "scripts" / script), *args],
            cwd=root,
            check=True,
        )

    def train(
        name: str, config: Path, phase: str, encodings: list[str], gate: list[str]
    ) -> tuple[Path, Path]:
        directory = stage / name
        report, independent = (
            directory / "training.json",
            directory / "independent.json",
        )
        run(
            "train_postflop.py",
            "--config",
            str(config),
            "--phase",
            phase,
            "--encodings",
            *encodings,
            "--output",
            str(report),
            *gate,
        )
        run(
            "validate_postflop_learning.py",
            "--report",
            str(report),
            "--output",
            str(independent),
        )
        experiments.append(
            {
                "name": name,
                "config": str(config),
                "report": str(report),
                "independent": str(independent),
            }
        )
        return report, independent

    config = root / "configs/holdem-learning-extended-linear-warm.json"
    candidate, independent = (
        stage / "linear-warm/training.json",
        stage / "linear-warm/independent.json",
    )
    status = "incomplete"
    try:
        for name in ("uniform", "warm", "linear", "linear-warm"):
            train(
                name,
                root / f"configs/holdem-learning-extended-{name}.json",
                "development",
                ["exact"],
                [],
            )
        if not json.loads(candidate.read_text())["exact_acceptance"]["passed"]:
            status = "development_gate_failed"
        else:
            train(
                "representations", config, "development", ["legacy_b8", "public_b8"], []
            )
            experiments[-1]["exact_control"] = str(candidate)
            heldout, _ = train(
                "heldout",
                config,
                "heldout",
                ["exact", "legacy_b8", "public_b8"],
                [
                    "--development-report",
                    str(candidate),
                    "--development-independent",
                    str(independent),
                ],
            )
            manifest = stage / "evidence.json"
            manifest.write_text(
                json.dumps({"experiments": experiments}, indent=2) + "\n"
            )
            run(
                "report_postflop_learning.py",
                "--manifest",
                str(manifest),
                "--output",
                str(stage / "report"),
            )
            status = (
                "passed"
                if json.loads(heldout.read_text())["exact_acceptance"]["passed"]
                else "heldout_gate_failed"
            )
    finally:
        (stage / "reproduction.json").write_text(
            json.dumps(
                {
                    "status": status,
                    "source": source,
                    "seconds": time.perf_counter() - started,
                    "experiments": experiments,
                    "scope": (
                        "fixed bounded diagnostic only; "
                        "no global training or live requests"
                    ),
                },
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
        print(f"{status}; retained reproduction: {stage}", flush=True)
    return 0 if status == "passed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
