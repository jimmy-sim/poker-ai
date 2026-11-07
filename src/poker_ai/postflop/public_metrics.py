"""Fixed-design public-board diagnostics and gates; no reference strategy inputs."""

import math
from typing import Any

import numpy as np

from poker_ai.finite import FloatArray
from poker_ai.postflop.matrix import MatrixTree, recall_violations

ENCODINGS = ["exact", "legacy_b8", "public_b8", "canonical_b8", "texture_b8"]
IDENTITY = ("spot_file", "encoding", "method", "seed", "node_threshold", "iteration")
LIMITS = {
    "exact_full_exploitability_pot",
    "exact_sampled_median_exploitability_pot",
    "exact_sampled_worst_exploitability_pot",
    "minimum_initialized_uniform_reach_average_coverage",
    "candidate_full_exploitability_excess_over_exact_pot",
    "candidate_sampled_median_exploitability_pot",
    "candidate_sampled_worst_exploitability_pot",
    "candidate_maximum_information_sets_relative_to_public_b8",
    "maximum_recall_violations",
    "independent_value_br_tolerance_chips",
}


def validate_config(config: dict[str, Any]) -> None:
    if (
        config["schema_version"] != 1
        or config["status"] != "preregistered_not_run"
        or config["encodings"] != ENCODINGS
        or config["candidate"] != "texture_b8"
        or config["sampling"] != "ordinary_external"
        or config["sampling_weighting"] != "linear"
        or config["initial_exact_expectation"] is not True
        or config["full_tree_backend"] not in ("numpy", "fused_numba")
        or not config["development_spots"]
        or len(set(config["development_spots"])) != len(config["development_spots"])
        or set(config["limits"]) != LIMITS
        or config["limits"]["maximum_recall_violations"] != 0
    ):
        raise ValueError("unsupported public-board comparison design")
    for key in ("seeds", "sampled_node_checkpoints", "full_tree_checkpoints"):
        values = config[key]
        if (
            not values
            or any(type(v) is not int or v < 1 for v in values)
            or len(set(values)) != len(values)
            or (key != "seeds" and values != sorted(values))
        ):
            raise ValueError("invalid fixed seeds/work checkpoints")
    for key in ("profile_iterations", "profile_repetitions", "maximum_nodes_per_game"):
        if type(config[key]) is not int or config[key] < 1:
            raise ValueError("invalid profile/tree budget")
    if not math.isfinite(config["maximum_seconds"]) or config["maximum_seconds"] <= 0:
        raise ValueError("invalid total wall-time budget")
    if (
        any(not math.isfinite(v) or not 0 <= v <= 1 for v in config["limits"].values())
        or not 0 < config["limits"]["independent_value_br_tolerance_chips"] <= 1e-8
    ):
        raise ValueError("invalid limits/tolerance")


def collision_summary(tree: MatrixTree, exact_mass: FloatArray) -> dict[str, Any]:
    """Group physical observations; weights are normalized uniform decision reach.

    A private collision means multiple own hands WITH THE SAME public board in
    a row. Public collisions mean distinct physical boards, including intentional
    suit symmetries. They are information loss counts, not strategic error proofs.
    """
    source = tree.source
    if (
        exact_mass.shape != (len(source.keys),)
        or not np.all(np.isfinite(exact_mass))
        or np.any(exact_mass < 0)
        or exact_mass.sum() <= 0
    ):
        raise ValueError("invalid exact decision weights")
    groups: list[dict[tuple[int, ...], set[tuple[int, ...]]]] = [{} for _ in tree.keys]
    for info, node in enumerate(source.representatives):
        dealer = source.states[node].dealer
        assert dealer is not None
        observation = dealer.observe(source.states[node].actor)
        group = groups[int(tree.exact_to_abstract[info])]
        group.setdefault(observation.board, set()).add(
            tuple(sorted(observation.hole_cards))
        )
    counts = np.bincount(tree.exact_to_abstract, minlength=len(tree.keys))
    public = np.array([len(g) > 1 for g in groups])
    private = np.array([any(len(h) > 1 for h in g.values()) for g in groups])

    def mass(flags: np.ndarray[Any, np.dtype[np.bool_]]) -> float:
        return float(exact_mass @ flags[tree.exact_to_abstract] / exact_mass.sum())

    return {
        "nodes": len(tree.player),
        "information_sets": len(tree.keys),
        "exact_information_sets": len(source.keys),
        "rows_merging_exact_infos": int((counts > 1).sum()),
        "rows_merging_public_boards": int(public.sum()),
        "rows_merging_private_hands_on_same_board": int(private.sum()),
        "maximum_exact_infos_per_row": int(counts.max()),
        "uniform_decision_reach_any_collision": mass(counts > 1),
        "uniform_decision_reach_public_collision": mass(public),
        "uniform_decision_reach_private_collision": mass(private),
        "recall_violations": recall_violations(tree),
        "key_utf8_bytes": sum(len(key.encode()) for key in tree.keys),
        "dense_regret_average_bytes": 2 * tree.legal.nbytes,
        "unpadded_regret_average_bytes": 16 * sum(map(len, tree.actions)),
    }


def mixed_value(tree: MatrixTree, first: FloatArray, second: FloatArray) -> float:
    """Net chips to seat 0: first controls seat 0, second controls seat 1."""
    tree.validate_policy(first)
    tree.validate_policy(second)
    mixed = np.where((tree.owners == 0)[:, None], first, second)
    return float(tree.values(tree.edges(mixed))[0])


def acceptance(
    rows: list[dict[str, Any]],
    diagnostics: list[dict[str, Any]],
    config: dict[str, Any],
) -> dict[str, Any]:
    """Complete grids before final-only gates. Candidate never selected by result."""
    expected = {
        (p, e, "external", s, n)
        for p in config["development_spots"]
        for e in config["encodings"]
        for s in config["seeds"]
        for n in config["sampled_node_checkpoints"]
    } | {
        (p, e, "full_cfr_plus", None, t)
        for p in config["development_spots"]
        for e in config["encodings"]
        for t in config["full_tree_checkpoints"]
    }
    ids = [
        (
            r["spot_file"],
            r["encoding"],
            r["method"],
            r["seed"],
            r["node_threshold"] if r["method"] == "external" else r["iteration"],
        )
        for r in rows
    ]
    diagnostic_ids = [(r["spot_file"], r["encoding"]) for r in diagnostics]
    diagnostic_expected = {
        (p, e) for p in config["development_spots"] for e in config["encodings"]
    }
    complete = (
        len(ids) == len(set(ids))
        and set(ids) == expected
        and len(diagnostic_ids) == len(set(diagnostic_ids))
        and set(diagnostic_ids) == diagnostic_expected
    )
    checks = []
    limits = config["limits"]
    for path in config["development_spots"]:

        def full(encoding: str, filename: str = path) -> list[dict[str, Any]]:
            return [
                r
                for r in rows
                if r["spot_file"] == filename
                and r["encoding"] == encoding
                and r["method"] == "full_cfr_plus"
                and r["iteration"] == config["full_tree_checkpoints"][-1]
            ]

        exact_full = full("exact")
        for encoding in config["encodings"]:
            selected = [
                r
                for r in rows
                if r["spot_file"] == path
                and r["encoding"] == encoding
                and r["method"] == "external"
                and r["node_threshold"] == config["sampled_node_checkpoints"][-1]
            ]
            control = full(encoding)
            diag = [
                r
                for r in diagnostics
                if r["spot_file"] == path and r["encoding"] == encoding
            ]
            raw = [
                r
                for r in diagnostics
                if r["spot_file"] == path and r["encoding"] == "public_b8"
            ]
            if (
                len(exact_full) != 1
                or len(control) != 1
                or len(diag) != 1
                or len(raw) != 1
                or sorted(r["seed"] for r in selected) != sorted(config["seeds"])
            ):
                checks.append(
                    {
                        "spot_file": path,
                        "encoding": encoding,
                        "passed": False,
                        "reason": "missing/duplicate final cells or diagnostics",
                    }
                )
                continue
            epsilon = [r["exploitability_pot_fraction"] for r in selected]
            coverage = min(
                r["uniform_reach_average_row_coverage"] for r in selected + control
            )
            ratio = diag[0]["information_sets"] / raw[0]["information_sets"]
            full_epsilon = control[0]["exploitability_pot_fraction"]
            excess = full_epsilon - exact_full[0]["exploitability_pot_fraction"]
            is_exact = encoding == "exact"
            tests = {
                "full_accuracy": (
                    full_epsilon <= limits["exact_full_exploitability_pot"]
                    if is_exact
                    else excess
                    <= limits["candidate_full_exploitability_excess_over_exact_pot"]
                ),
                "sampled_median": float(np.median(epsilon))
                <= limits[
                    "exact_sampled_median_exploitability_pot"
                    if is_exact
                    else "candidate_sampled_median_exploitability_pot"
                ],
                "sampled_worst": max(epsilon)
                <= limits[
                    "exact_sampled_worst_exploitability_pot"
                    if is_exact
                    else "candidate_sampled_worst_exploitability_pot"
                ],
                "initialized_average_coverage": coverage
                >= limits["minimum_initialized_uniform_reach_average_coverage"],
                "recall": diag[0]["recall_violations"] == 0,
                "compression": is_exact
                or ratio
                <= limits["candidate_maximum_information_sets_relative_to_public_b8"],
            }
            checks.append(
                {
                    "spot_file": path,
                    "encoding": encoding,
                    "full_epsilon_pot": full_epsilon,
                    "full_excess_pot": excess,
                    "median_epsilon_pot": float(np.median(epsilon)),
                    "worst_epsilon_pot": max(epsilon),
                    "minimum_coverage": coverage,
                    "information_sets_relative_to_public_b8": ratio,
                    "criteria": tests,
                    "passed": bool(all(tests.values())),
                }
            )
    exact_ok = all(r["passed"] for r in checks if r["encoding"] == "exact")
    candidate_ok = all(
        r["passed"] for r in checks if r["encoding"] == config["candidate"]
    )
    return {
        "complete": complete,
        "checks": checks,
        "exact_control_passed": complete and exact_ok,
        "candidate_learning_gate_passed": complete and exact_ok and candidate_ok,
        "independent_audit_required": True,
    }
