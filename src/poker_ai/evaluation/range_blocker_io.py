"""Pinned parent/cache schemas for the public two-range blocker diagnosis."""

import csv
import gzip
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from poker_ai.cards import parse_card
from poker_ai.evaluation.range_blocker_probe import (
    CONTROLS,
    SUFFIXES,
    WEIGHTS,
    FeatureBook,
    analyse,
    declared_ranges,
)
from poker_ai.evaluation.river_range_io import load as parent_load
from poker_ai.evaluation.river_range_io import load_detail as parent_detail
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import digest

CONFIG = "configs/two-sided-blockers.json"
CONFIG_SHA = "fdeef4c5ea0d7a5c321cf5a2e14b8a2df27e72bd8e5eb232778df5769c3dbe65"
FOLDER = "results/two-sided-blockers"
ENTRIES = (
    "scripts/diagnose_two_sided_blockers.py",
    "scripts/inspect_two_sided_blockers.py",
)
IDENTITY = ("coordinate", "game", "seed", "arm", "source_id", "policy_sha256")
FLAGS = (
    "training_performed",
    "reference_constructed",
    "new_independent_audit",
    "original_full_math_replay",
    "feature_deployed",
    "new_agent_default",
    "fresh_global_admission",
)


def contract(root: Path) -> dict[str, Any]:
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("frozen two-sided blocker protocol changed")
    result: dict[str, Any] = json.loads((root / CONFIG).read_text())
    return result


def parents(root: Path, config: dict[str, Any]) -> list[dict[str, Any]]:
    folder = root / config["source_folder"]
    if not folder.resolve().is_relative_to(root.resolve()):
        raise ArithmeticError("source cache escapes repository")
    for path, checksum in (
        (root / "configs/river-range-reweighting.json", config["source_config_sha256"]),
        (folder / "manifest.json", config["source_manifest_sha256"]),
        (folder / "summary.json", config["source_summary_sha256"]),
        (folder / "panels.csv", config["source_panels_sha256"]),
    ):
        if digest(path) != checksum:
            raise ArithmeticError("bound complete parent publication changed")
    return parent_load(root, folder)


def source_detail(root: Path, profile: dict[str, Any]) -> dict[str, Any]:
    return parent_detail(root / contract(root)["source_folder"], profile)


def same(expected: Any, actual: Any, path: str = "") -> None:
    """Typed cache comparison, with explicit chip versus unitless tolerances."""
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(expected) != set(actual):
            raise ArithmeticError("cached dictionary inventory changed: " + path)
        for k in expected:
            same(expected[k], actual[k], path + "." + k)
    elif isinstance(expected, list):
        if not isinstance(actual, list) or len(expected) != len(actual):
            raise ArithmeticError("cached list inventory changed: " + path)
        for i, (e, a) in enumerate(zip(expected, actual, strict=True)):
            same(e, a, path + f".{i}")
    elif type(expected) is float:
        tolerance = 1e-12 if "weight" in path or "unitless" in path else 1e-9
        if (
            type(actual) not in (int, float)
            or not math.isfinite(actual)
            or abs(actual - expected) > tolerance
        ):
            raise ArithmeticError("cached numerical reconstruction failed: " + path)
    elif type(expected) is not type(actual) or expected != actual:
        raise ArithmeticError("cached identity/type changed: " + path)


def validate_profiles(
    profiles: list[dict[str, Any]], source: list[dict[str, Any]], config: dict[str, Any]
) -> None:
    json.dumps(profiles, allow_nan=False)
    old = {p["source_id"]: p for p in source}
    if (
        len(profiles) != config["expected_profiles"]
        or len({p["source_id"] for p in profiles}) != len(old)
        or [p["source_id"] for p in profiles] != [p["source_id"] for p in source]
    ):
        raise ArithmeticError("complete unique parent profile inventory required")
    rows = panels = 0
    for p in profiles:
        parent = old[p["source_id"]]
        if (
            any(
                p[k] != parent[k] or type(p[k]) is not type(parent[k]) for k in IDENTITY
            )
            or p["source_details_file"] != parent["details_file"]
            or p["source_details_sha256"] != parent["_detail_sha256"]
        ):
            raise ArithmeticError("profile source identity/order/hash changed")
        if [r["target"] for r in p["responses"]] != [0, 1] or any(
            type(r["target"]) is not int for r in p["responses"]
        ):
            raise ArithmeticError("both ordered responding seats required")
        for target, r in enumerate(p["responses"]):
            expected_ids = parent["responses"][target]["suffixes"][0]["river_info_ids"]
            if (
                r["river_info_ids"] != expected_ids
                or any(type(i) is not int for i in r["river_info_ids"])
                or [s["suffix"] for s in r["suffixes"]] != list(SUFFIXES)
            ):
                raise ArithmeticError(
                    "complete source river rows and own suffixes required"
                )
            rows += len(expected_ids)
            for s in r["suffixes"]:
                if [w["range_weights"] for w in s["panels"]] != list(WEIGHTS):
                    raise ArithmeticError("both source range-weight panels required")
                for w in s["panels"]:
                    if (
                        set(w["group_controls"]) != set(CONTROLS)
                        or any(
                            type(w[k]) not in (int, float)
                            for k in (
                                "maximum_source_chip_error",
                                "maximum_unitless_error",
                            )
                        )
                        or not 0 <= w["maximum_source_chip_error"] <= 1e-9
                        or not 0 <= w["maximum_unitless_error"] <= 1e-12
                    ):
                        raise ArithmeticError(
                            "source reconstruction/control inventory failed"
                        )
                    prior_cost = math.inf
                    baseline = w["group_controls"][CONTROLS[0]][
                        "source_conflicting_groups"
                    ]
                    for control in CONTROLS:
                        panels += 1
                        m = w["group_controls"][control]
                        counts = (
                            "strict_conflicting_groups",
                            "total_groups",
                            "supported_groups",
                            "source_conflicting_groups",
                            "source_conflicting_groups_resolved",
                        )
                        if (
                            any(type(m[k]) is not int for k in counts)
                            or not 0
                            <= m["strict_conflicting_groups"]
                            <= m["supported_groups"]
                            <= m["total_groups"]
                            or m["source_conflicting_groups"] != baseline
                            or not 0
                            <= m["source_conflicting_groups_resolved"]
                            <= baseline
                            or type(m["supported_uniform_decision_weight"])
                            not in (int, float)
                            or not 0
                            <= m["supported_uniform_decision_weight"]
                            <= 1 + 1e-12
                        ):
                            raise ArithmeticError(
                                "invalid group/support/conflict denominators"
                            )
                        cost = m["local_sharing_cost_chips_per_weighted_decision"]
                        if (
                            type(cost) not in (int, float)
                            or cost < 0
                            or cost > prior_cost + 1e-9
                        ):
                            raise ArithmeticError("invalid convex refinement cost")
                        prior_cost = cost
                        if control == CONTROLS[-1] and (
                            cost != 0
                            or m["strict_conflicting_groups"] != 0
                            or m["source_conflicting_groups_resolved"] != baseline
                            or m["total_groups"] != len(expected_ids)
                        ):
                            raise ArithmeticError("exact singleton control failed")
                        if p["arm"] == "fine_self" and (
                            cost != 0 or m["strict_conflicting_groups"] != 0
                        ):
                            raise ArithmeticError("fine-self singleton source changed")
                    same(
                        w["group_controls"][CONTROLS[2]],
                        w["group_controls"][CONTROLS[3]],
                    )
    if (
        rows != config["expected_profile_river_rows"]
        or 2 * rows != config["expected_suffix_river_rows"]
        or panels != config["expected_group_panels"]
    ):
        raise ArithmeticError("complete row/panel inventory failed")


def csv_rows(profiles: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {k: p[k] for k in ("game", "seed", "arm", "coordinate")}
        | dict(
            target=r["target"],
            suffix=s["suffix"],
            range_weights=w["range_weights"],
            group_control=c,
            **w["group_controls"][c],
        )
        for p in profiles
        for r in p["responses"]
        for s in r["suffixes"]
        for w in s["panels"]
        for c in CONTROLS
    ]


@dataclass
class Cache:
    root: Path
    folder: Path
    manifest: dict[str, Any]
    profiles: list[dict[str, Any]]
    sources: dict[str, dict[str, Any]]
    book: FeatureBook
    decoded: dict[str, tuple[dict[str, Any], dict[str, Any]]] = field(
        default_factory=dict
    )

    def detail(self, profile: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
        identity = profile["source_id"]
        if identity in self.decoded:
            return self.decoded[identity]
        path = self.folder / profile["details_file"]
        if digest(path) != self.manifest["outputs"][profile["details_file"]]:
            raise ArithmeticError("lazy cached detail bytes changed")
        with gzip.open(path, "rt") as stream:
            detail = json.load(stream)
        parent = self.sources[identity]
        source = source_detail(self.root, parent)
        summary, expected = analyse(parent, source, self.book)
        same({k: profile[k] for k in IDENTITY}, {k: detail[k] for k in IDENTITY})
        same(summary["responses"], profile["responses"])
        same(expected["responses"], detail["responses"])
        self.decoded[identity] = detail, source
        return detail, source


def load(root: Path, folder: Path) -> Cache:
    config = contract(root)
    source = parents(root, config)
    if (folder / "failure.json").exists() or any(folder.rglob("*.tmp")):
        raise ArithmeticError("refuse failed/interrupted blocker publication")
    m = json.loads((folder / "manifest.json").read_text())
    json.dumps(m, allow_nan=False)
    required = {
        CONFIG,
        *ENTRIES,
        *(
            f"src/poker_ai/evaluation/range_blocker_{name}.py"
            for name in ("features", "probe", "io", "run", "view")
        ),
    }
    if (
        m["status"] != "complete_cached_two_sided_blockers"
        or m["config_sha256"] != CONFIG_SHA
        or m["source_manifest_sha256"] != config["source_manifest_sha256"]
        or m["source_sha256"] != sha(m["source"]["sha256"])
        or not required <= set(m["source"]["sha256"])
        or m["constructors_blocked"] is not True
        or any(m[k] is not False for k in FLAGS)
        or type(m["seconds"]) not in (int, float)
        or not 0 <= m["seconds"] <= 900
        or m["maximum_seconds"] != 900
    ):
        raise ArithmeticError("complete source-bound cache-only receipt required")
    check_source(root, m["source"])
    paths = {
        f"details/{i:02d}-{a}.json.gz" for i in range(6) for a in config["arms"]
    } | {"catalog.json", "summary.json", "partial.json", "panels.csv"}
    if set(m["outputs"]) != paths:
        raise ArithmeticError("complete raw output inventory required")
    for name, checksum in m["outputs"].items():
        p = folder / name
        if not p.resolve().is_relative_to(folder.resolve()) or digest(p) != checksum:
            raise ArithmeticError("cached blocker output bytes changed")
    profiles = json.loads((folder / "summary.json").read_text())["profiles"]
    validate_profiles(profiles, source, config)
    for key in ("maximum_source_chip_error", "maximum_unitless_error"):
        expected = max(
            w[key]
            for p in profiles
            for r in p["responses"]
            for s in r["suffixes"]
            for w in s["panels"]
        )
        same(float(expected), m[key], key)
    with (folder / "panels.csv").open() as stream:
        actual = list(csv.DictReader(stream))
    if actual != [{k: str(v) for k, v in row.items()} for row in csv_rows(profiles)]:
        raise ArithmeticError("complete CSV differs from checked summaries")
    for key, expected in (
        ("profiles", 24),
        ("responses", 48),
        ("suffix_conditions", 96),
        ("range_panels", 192),
        ("group_panels", 960),
        ("profile_river_rows", config["expected_profile_river_rows"]),
        ("suffix_river_rows", config["expected_suffix_river_rows"]),
    ):
        if type(m[key]) is not int or m[key] != expected:
            raise ArithmeticError("complete manifest dimensions changed")
    book = FeatureBook()
    catalog = json.loads((folder / "catalog.json").read_text())
    if (
        set(catalog["ranges"]) != set(config["games"])
        or type(m["public_boards"]) is not int
        or not catalog["features"]
        or len(catalog["features"]) != m["public_boards"]
    ):
        raise ArithmeticError("complete public catalog required")
    by_id = {p["source_id"]: p for p in source}
    for game, raw_ranges in catalog["ranges"].items():
        ranges = tuple(
            tuple(tuple(parse_card(c) for c in h) for h in side) for side in raw_ranges
        )
        example = next(p for p in source if p["game"] == game)
        if ranges != declared_ranges(source_detail(root, example)):
            raise ArithmeticError("catalog reordered source declared ranges")
        book.ranges[game] = ranges
    for key, entry in catalog["features"].items():
        actual_key, _ = book.bind(
            entry["game"], book.ranges[entry["game"]], entry["board"]
        )
        if key != actual_key:
            raise ArithmeticError("public catalog lookup changed")
        same(book.entries[key], entry)
    book.frozen = True
    for p in profiles:
        expected = f"details/{p['coordinate']:02d}-{p['arm']}.json.gz"
        if p["details_file"] != expected:
            raise ArithmeticError("profile detail path changed")
    return Cache(root, folder, m, profiles, by_id, book)
