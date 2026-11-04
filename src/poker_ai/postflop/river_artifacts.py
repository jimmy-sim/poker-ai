"""Read own river artifacts without importing any reference solver."""

import gzip
import json
from pathlib import Path
from typing import Any

from poker_ai.postflop.river_study import FORMAT, POLICY_FORMAT, acceptance, digest

IDENTITY = ("spot_file", "method", "seed", "iteration", "node_threshold")


def checked_artifacts(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    report: dict[str, Any] = json.loads(path.read_text())
    if report["format"] != FORMAT or report["status"] != "completed":
        raise ValueError(
            "requires a complete river study; retain partial data separately"
        )
    if (
        report["acceptance"] != acceptance(report["rows"], report["config"])
        or not report["acceptance"]["complete"]
    ):
        raise ArithmeticError("missing/duplicate or changed learning grid")
    policy_path = path.parent / report["own_policies_file"]
    if digest(policy_path) != report["own_policies_sha256"]:
        raise ArithmeticError("own policy artifact hash mismatch")
    frozen = json.loads(gzip.decompress(policy_path.read_bytes()))
    if frozen["format"] != POLICY_FORMAT:
        raise ValueError("expected own river policy artifact")
    rows = {tuple(r[k] for k in IDENTITY) for r in report["rows"]}
    policies = {tuple(r[k] for k in IDENTITY) for r in frozen["policies"]}
    if rows != policies or len(policies) != len(frozen["policies"]):
        raise ArithmeticError("missing/duplicate frozen own policy")
    config = report["config"]
    expected = {
        (name, policy, target, variant, seed)
        for name in {r["spot"] for r in report["rows"]}
        for policy in config["frozen_panel"]["policies"]
        for target in config["frozen_panel"]["targets"]
        for variant in config["variants"]
        for seed in config["frozen_panel"]["seeds"]
    }
    actual = {
        (r["spot"], r["policy"], r["target"], r["variant"], r["seed"])
        for r in report["frozen_panel"]
    }
    if (
        actual != expected
        or len(actual) != len(report["frozen_panel"])
        or any(
            r["passes"]
            != config["frozen_panel"]["passes_per_seed_target_policy_variant"]
            for r in report["frozen_panel"]
        )
    ):
        raise ArithmeticError("missing/duplicate frozen panel cells")
    return report, frozen["policies"]
