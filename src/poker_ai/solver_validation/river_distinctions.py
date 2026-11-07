"Native evaluation of own river-switch profiles; no reference decisions exported."

import json
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.reply_diagnosis import checked_details
from poker_ai.postflop.river_distinctions import replay, river_mask, river_switches
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.reference import Reference
from poker_ai.validation.five_card import source_provenance


def audit(root: Path, config_path: Path, path: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain existing river audit")
    started = time.perf_counter()
    report, _, error = replay(root, path)
    if json.loads(config_path.read_text()) != report["config"]:
        raise ArithmeticError("river audit config changed")
    _, replies = checked_details(root / report["config"]["input_report"])
    rows = []
    for filename in dict.fromkeys(c["spot_file"] for c in report["cases"]):
        source = SpotTree.build(load_spot(root / filename))
        exact = MatrixTree.build(source)
        reference = Reference(source)
        for case in report["cases"]:
            if case["spot_file"] != filename:
                continue
            detail = next(
                c
                for c in replies
                if c["spot_file"] == filename
                and c["representation"] == case["representation"]
            )
            for target in (0, 1):
                saved = detail["responses"][target]
                b, c = [
                    exact.dense_exact(tuple(tuple(v for v in row) for row in saved[k]))
                    for k in ("exact_reply_profile", "restricted_reply_profile")
                ]
                panels = river_switches(
                    exact,
                    b,
                    c,
                    target,
                    river_mask(exact, target),
                    tolerance=report["config"]["tolerance_chips"],
                )
                for prefix, panel in panels.items():
                    own = next(
                        p
                        for p in case["responses"][target]["panels"]
                        if p["prefix"] == prefix
                    )
                    before, after = [
                        (1 if target == 0 else -1)
                        * reference.value(exact.exact_policy(profile))
                        for profile in (panel.before, panel.after)
                    ]
                    rows.append(
                        {
                            "spot_file": filename,
                            "representation": case["representation"],
                            "target": target,
                            "prefix": prefix,
                            "before_native_chips": before,
                            "after_native_chips": after,
                            "before_error_chips": abs(
                                before - own["before_value_chips"]
                            ),
                            "after_error_chips": abs(after - own["after_value_chips"]),
                            "gain_error_chips": abs(
                                after - before - own["river_gain_chips"]
                            ),
                        }
                    )
            print(
                f"native river audit: {source.spot.name}/{case['representation']}",
                flush=True,
            )
    maximum = max(
        v for row in rows for k, v in row.items() if k.endswith("error_chips")
    )
    passed = (
        len(rows) == 4 * len(report["cases"])
        and maximum <= report["config"]["tolerance_chips"]
    )
    result = {
        "status": "passed" if passed else "failed",
        "input_sha256": digest(path),
        "rows": rows,
        "native_profiles_checked": 2 * len(rows),
        "maximum_native_error_chips": maximum,
        "maximum_own_replay_error_chips": error,
        "reference": {
            "name": "OpenSpiel",
            "version": version("open-spiel"),
            "license": "Apache-2.0",
        },
        "seconds": time.perf_counter() - started,
        "environment": runtime_environment(),
        "source": source_provenance(
            root, config_path, entrypoints=("scripts/audit_river_distinctions.py",)
        ),
        "scope": (
            "own F/G root values on shared exported mechanics; comparison "
            "only, no native actions"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return result
