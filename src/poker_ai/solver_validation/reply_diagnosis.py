"""Native response-root comparison only; never export reference actions."""

import json
import time
from dataclasses import replace
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.made_admission import build_representation, checked_artifacts
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.reply_diagnosis import IDENTITY, replay
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.reference import Reference
from poker_ai.validation.five_card import source_provenance


def partition_source(tree: MatrixTree) -> SpotTree:
    """Export the OWN partition for a separate native constrained-response check."""
    source = tree.source
    nodes = [
        int(np.flatnonzero(tree.information == i)[0]) for i in range(len(tree.keys))
    ]
    return replace(
        source,
        information=tuple(int(i) for i in tree.information),
        representatives=tuple(nodes),
        keys=tree.keys,
        owners=tuple(int(v) for v in tree.owners),
        menus=tree.actions,
    )


def audit(root: Path, config_path: Path, path: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain existing reply audit")
    started = time.perf_counter()
    report, details, error = replay(root, path)
    if json.loads(config_path.read_text()) != report["config"]:
        raise ArithmeticError("reply audit config changed")
    original, saved_policies = checked_artifacts(
        root / report["config"]["input_report"]
    )
    model = CardAbstraction.load(root / original["config"]["model"])
    rows = []
    for filename in original["config"]["spot_files"]:
        source = SpotTree.build(load_spot(root / filename))
        exact = Reference(source)
        for case in report["cases"]:
            if case["spot_file"] != filename:
                continue
            detail = next(c for c in details if all(c[k] == case[k] for k in IDENTITY))
            abstract = build_representation(source, case["representation"], model)
            limited = Reference(partition_source(abstract))
            selected = next(
                p
                for p in saved_policies
                if all(p[k] == case[k] for k in IDENTITY)
                and p["iteration"] == report["config"]["iteration"]
            )
            baseline = tuple(tuple(float(v) for v in row) for row in selected["policy"])
            dense = MatrixTree.build(source).dense_exact(baseline)
            first = np.unique(abstract.exact_to_abstract, return_index=True)[1]
            limited_policy = tuple(
                tuple(float(v) for v in dense[i, : len(menu)])
                for i, menu in zip(first, abstract.actions, strict=True)
            )
            for target in (0, 1):
                own = case["responses"][target]
                errors, roots = {}, {}
                for label, reference, policy in (
                    ("exact", exact, baseline),
                    ("restricted", limited, limited_policy),
                ):
                    # TabularBestResponse borrows its Policy pointer. Keep the
                    # Python wrapper alive through value(), rather than passing
                    # a temporary whose destruction leaves a dangling pointer.
                    native_policy = reference.native_policy(policy)
                    native_response = reference.pyspiel.TabularBestResponse(
                        reference.game, target, native_policy
                    )
                    native = float(native_response.value(""))
                    own_profile = tuple(
                        tuple(float(v) for v in r)
                        for r in detail["responses"][target][label + "_reply_profile"]
                    )
                    achieved = (1 if target == 0 else -1) * exact.value(own_profile)
                    roots[label + "_native_value_chips"] = native
                    errors[label + "_root_error_chips"] = abs(
                        native - own[label + "_reply_value_chips"]
                    )
                    errors[label + "_achieved_error_chips"] = abs(native - achieved)
                rows.append(
                    {
                        **{k: case[k] for k in IDENTITY},
                        "target": target,
                        **roots,
                        **errors,
                    }
                )
            print(
                f"native reply audit: {source.spot.name}/{case['representation']}",
                flush=True,
            )
    tolerance = report["config"]["tolerance_chips"]
    maximum = max(v for r in rows for k, v in r.items() if k.endswith("error_chips"))
    passed = (
        len(rows) == 2 * len(report["cases"])
        and np.isfinite(maximum)
        and maximum <= tolerance
    )
    result = {
        "status": "passed" if passed else "failed",
        "input_sha256": digest(path),
        "rows": rows,
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
            root, config_path, entrypoints=("scripts/audit_saved_replies.py",)
        ),
        "scope": (
            "native exact/restricted root and own reply value checks on shared "
            "own mechanics/partitions; no reference actions exported"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return result
