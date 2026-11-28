"""Fixed four-game conclusion from independently checked saved mixed policies."""

import json
import math
from pathlib import Path
from typing import Any

from river_generalization.gate import require_archive

from known_turn_half_policy_mixture.gate import (
    NATIVE,
    OWN,
    clean_head,
    require_own,
    source_fingerprint,
)
from known_turn_half_policy_mixture.math import decision
from known_turn_half_policy_mixture.own import _save
from known_turn_half_policy_mixture.plan import ARMS, GAMES, contract


def report(root: Path, output: Path) -> None:
    """Apply registered gates to all four own results; retain negative outcomes."""
    data = contract(root)
    head = clean_head(root)
    fingerprint = source_fingerprint(root)
    require_own(root, fingerprint)
    require_archive(root, root / NATIVE, "native_audited", fingerprint)
    own: dict[str, Any] = json.loads((root / OWN / "result.json").read_bytes())
    native: dict[str, Any] = json.loads((root / NATIVE / "result.json").read_bytes())
    prior: dict[str, Any] = json.loads((root / data["report_path"]).read_bytes())
    if (
        own["status"] != "completed"
        or native["status"] != "completed"
        or len(own["rows"]) != 4
        or len(native["rows"]) != 4
        or prior["status"] != "completed"
        or prior["primary"]["classification"] != "negative"
    ):
        raise ArithmeticError("fixed own/native/prior report incomplete")
    cases = {
        (row["game"], row["arm"]): row
        for row in prior["cases"]
        if row["work_label"] == 40_000_000 and row["readout"] == "linear_average"
    }
    if set(cases) != {(g, a) for g in GAMES for a in ARMS}:
        raise ArithmeticError("eight fixed parent scores missing")
    rows = []
    for index, game in enumerate(GAMES):
        measured = own["rows"][index]
        audit = native["rows"][index]
        if (
            measured["game"] != game
            or measured["index"] != index
            or audit["game"] != game
            or audit["index"] != index
            or audit["own_policy_sha256"] != measured["receipt"]["policy_sha256"]
            or audit["native"]["maximum_error_chips"]
            > data["reference_tolerance_chips"]
            or measured["recall_violations"] != 0
            or audit["peak_rss_bytes"] >= data["peak_rss_bytes_exclusive"]
        ):
            raise ArithmeticError("mixed policy/native case identity changed")
        control = cases[(game, ARMS[0])]
        other = cases[(game, ARMS[1])]
        if (
            control["policy_sha256"] != data["inputs"][2 * index]["policy_sha256"]
            or other["policy_sha256"] != data["inputs"][2 * index + 1]["policy_sha256"]
            or control["actual_node_work"] != data["charged_work"]
            or other["actual_node_work"] != data["charged_work"]
        ):
            raise ArithmeticError("published parent score/policy binding changed")
        mixed = measured["exploitability_fraction_initial_pot"]
        control_value = control["exploitability_fraction_initial_pot"]
        other_value = other["exploitability_fraction_initial_pot"]
        if (
            not math.isfinite(mixed)
            or abs(
                mixed * 36 - measured["score"]["metrics"]["exact_exploitability_chips"]
            )
            > data["arithmetic_tolerance_chips"]
        ):
            raise ArithmeticError("mixed score/pot arithmetic changed")
        rows.append(
            {
                "game": game,
                "seed_metadata": 0,
                "mixed_policy_sha256": measured["receipt"]["policy_sha256"],
                "mixed_fraction_initial_pot": mixed,
                "control_fraction_initial_pot": control_value,
                "other_parent_fraction_initial_pot": other_value,
                "mixed_minus_control_fraction_initial_pot": mixed - control_value,
                "mixed_minus_other_fraction_initial_pot": mixed - other_value,
                "native_error_chips": audit["native"]["maximum_error_chips"],
                "peak_rss_bytes": measured["peak_rss_bytes"],
                "own_elapsed_seconds": measured["elapsed_seconds"],
            }
        )
    if output.exists():
        raise FileExistsError("retain prior half-mixture report")
    output.mkdir(parents=True)
    _save(
        output / "report.json",
        {
            "status": "completed",
            "head": head,
            "source_fingerprint": fingerprint,
            "classification": decision(rows),
            "cases": rows,
            "own_seconds": own["seconds"],
            "native_seconds": native["seconds"],
            "uncertainty": (
                "deterministic saved policies; four known outcome-inspected games; "
                "no seed sampling interval"
            ),
            "scope": (
                "fixed medium OOP restricted-game exact response, "
                "not unseen full-game play"
            ),
            "default_promoted": False,
        },
    )
