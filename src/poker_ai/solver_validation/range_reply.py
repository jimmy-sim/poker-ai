"""Native best-response roots and achieved OWN profiles; no native action export."""

import json
import math
import time
from importlib.metadata import version
from pathlib import Path
from typing import Any

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.range_protocol import build_representation_control
from poker_ai.postflop.range_reply import IDENTITY, check_source, load_inputs, replay
from poker_ai.postflop.river_study import digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.reference import Reference
from poker_ai.solver_validation.reply_diagnosis import partition_source
from poker_ai.validation.five_card import source_provenance


def audit(root: Path, config_path: Path, path: Path, output: Path) -> dict[str, Any]:
    if output.exists():
        raise FileExistsError("retain existing range-reply audit")
    started = time.perf_counter()
    source_record = source_provenance(
        root, config_path, entrypoints=("scripts/audit_range_replies.py",)
    )
    if source_record["dirty"] is not False:
        raise ValueError("publish own evidence before native audit")
    report, details, error = replay(root, path)
    if json.loads(config_path.read_text()) != report["config"]:
        raise ArithmeticError("audit config changed")
    original, policies = load_inputs(root, report["config"])
    model = CardAbstraction.load(root / original["config"]["model"])
    rows = []
    for filename in report["config"]["spot_files"]:
        source = SpotTree.build(load_spot(root / filename))
        matrix = MatrixTree.build(source)
        exact = Reference(source)
        for name in report["config"]["representations"]:
            abstract = build_representation_control(source, name, model)
            limited = Reference(partition_source(abstract))
            first = np.unique(abstract.exact_to_abstract, return_index=True)[1]
            for case in report["cases"]:
                if case["spot_file"] != filename or case["representation"] != name:
                    continue
                identity = {k: case[k] for k in IDENTITY}
                detail = next(
                    c for c in details if all(c[k] == v for k, v in identity.items())
                )
                selected = next(
                    c for c in policies if all(c[k] == v for k, v in identity.items())
                )
                baseline = tuple(tuple(float(v) for v in r) for r in selected["policy"])
                dense = matrix.dense_exact(baseline)
                restricted = tuple(
                    tuple(float(v) for v in dense[i, : len(menu)])
                    for i, menu in zip(first, abstract.actions, strict=True)
                )
                for target in (0, 1):
                    row = {
                        **identity,
                        "target": target,
                        "range_context_sha256": case["range_context_sha256"],
                    }
                    for label, reference, policy in (
                        ("exact", exact, baseline),
                        ("restricted", limited, restricted),
                    ):
                        native_policy = reference.native_policy(policy)
                        response = reference.pyspiel.TabularBestResponse(
                            reference.game, target, native_policy
                        )
                        value = float(response.value(""))
                        own_profile = tuple(
                            tuple(float(v) for v in r)
                            for r in detail["responses"][target][
                                label + "_reply_profile"
                            ]
                        )
                        achieved = (1 if target == 0 else -1) * exact.value(own_profile)
                        row.update(
                            {
                                label + "_native_value_chips": value,
                                label + "_achieved_value_chips": achieved,
                                label + "_root_error_chips": abs(
                                    value
                                    - case["responses"][target][
                                        label + "_reply_value_chips"
                                    ]
                                ),
                                label + "_achieved_error_chips": abs(value - achieved),
                            }
                        )
                    rows.append(row)
                print(
                    f"native range reply: {source.spot.name}/{name}/"
                    f"{case['training']}/{case['seed']}",
                    flush=True,
                )
    tolerance = report["config"]["tolerance_chips"]
    errors = [
        r[label + suffix]
        for r in rows
        for label in ("exact", "restricted")
        for suffix in ("_root_error_chips", "_achieved_error_chips")
    ]
    passed = len(rows) == 2 * len(report["cases"]) and all(
        math.isfinite(v) and 0 <= v <= tolerance for v in errors
    )
    check_source(root, source_record)
    result = {
        "status": "passed" if passed else "failed",
        "input_sha256": digest(path),
        "rows": rows,
        "maximum_native_error_chips": max(errors),
        "maximum_own_replay_error_chips": error,
        "reference": {
            "name": "OpenSpiel",
            "version": version("open-spiel"),
            "license": "Apache-2.0",
        },
        "source": source_record,
        "environment": runtime_environment(),
        "seconds": time.perf_counter() - started,
        "scope": (
            "exact/restricted native roots and achieved own profiles on shared "
            "mechanics; no native actions exported"
        ),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    )
    return result
