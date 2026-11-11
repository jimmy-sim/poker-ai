"""Static river refinement probes on saved own replies; no training."""

import argparse
import gzip
import json
import math
import time
from collections import defaultdict
from contextlib import ExitStack
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np

from poker_ai.abstraction.range_mass import RangePrior, mass_bin, river_mass
from poker_ai.cards import format_card
from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.matched_update_lifecycle import measured
from poker_ai.evaluation.private_prefix_admission import native_journal
from poker_ai.evaluation.private_prefix_read import read
from poker_ai.postflop.collision_diagnosis import conditional_actions, sharing_cost
from poker_ai.postflop.learning_artifacts import canonical, sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_distinctions import river_features
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.private_prefix import validate
from poker_ai.training.no_limit import NoLimitState
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/river-refinement-diagnosis.json"
CONFIG_SHA = "ae7e9cf8b068641d2cc046d3fb600f1ee3e50fd2d763528f705f2717d1e1cc6d"
ENTRY = "scripts/diagnose_river_refinement.py"
FOLDER = "results/river-refinement"
SUFFIXES = ("exact", "restricted")
PROBES = ("q8", "exact_mass", "ordered_relations", "exact_info")


@lru_cache(maxsize=8192)
def features(
    hole: tuple[int, ...], board: tuple[int, ...], prior: RangePrior
) -> dict[str, Any]:
    """Observed-card static signatures; never a hidden deal or policy input."""
    mass = river_mass(hole, board, prior)
    relations = river_features(hole, board, prior.combos)["range_relations"]
    # 0 blocked, 1 own loss, 2 tie, 3 own win. Check independent aggregation.
    ordered = [0 if r is None else int(r) + 2 for r in relations]
    reconstructed = tuple(
        sum(
            (w for r, w in zip(ordered, prior.masses, strict=True) if r == i),
            Fraction(),
        )
        for i in range(4)
    )
    if reconstructed != mass.masses:
        raise ArithmeticError("ordered relations do not reconstruct exact masses")
    return dict(
        bins=list(mass.bins),
        masses=[[m.numerator, m.denominator] for m in mass.masses],
        relations=ordered,
    )


def probe_keys(row: dict[str, Any]) -> tuple[str, ...]:
    f = row["features"]
    try:
        raw = f["masses"]
        if (
            set(f) != {"bins", "masses", "relations"}
            or not isinstance(raw, list)
            or len(raw) != 4
            or any(
                not isinstance(p, list)
                or len(p) != 2
                or any(type(v) is not int for v in p)
                or p[1] <= 0
                for p in raw
            )
            or not isinstance(f["bins"], list)
            or any(type(v) is not int for v in f["bins"])
            or not isinstance(f["relations"], list)
            or not f["relations"]
            or any(type(v) is not int or v not in range(4) for v in f["relations"])
        ):
            raise ValueError("invalid static feature schema")
        masses = tuple(Fraction(*p) for p in raw)
        if (
            any(m < 0 for m in masses)
            or sum(masses) != 1
            or masses[0] == 1
            or [mass_bin(m) for m in masses] != f["bins"]
            or [[m.numerator, m.denominator] for m in masses] != raw
        ):
            raise ValueError("noncanonical static masses/bins")
    except (KeyError, TypeError, ValueError, ZeroDivisionError) as exc:
        raise ArithmeticError("invalid static river refinement feature") from exc
    parent = row["parent"]
    parts = [
        parent,
        [parent, f["masses"]],
        [parent, f["masses"], f["relations"]],
        row["exact_info"],
    ]
    return tuple(json.dumps(v, separators=(",", ":")) for v in parts)


def summarize(rows: list[dict[str, Any]], target: int) -> dict[str, Any]:
    """Local fixed-Q sharing only. Scores at successive decisions overlap."""
    if type(target) is not int or target not in (0, 1) or not rows:
        raise ValueError("need responding seat and complete nonempty river inventory")
    seen: set[int] = set()
    menus: dict[int, list[str]] = {}
    for r in rows:
        info, parent = r["exact_info"], r["parent"]
        if (
            type(info) is not int
            or info < 0
            or info in seen
            or type(parent) is not int
            or parent < 0
            or type(r["target"]) is not int
            or r["target"] != target
            or r["street"] != "RIVER"
            or not isinstance(r["actions"], list)
            or not r["actions"]
            or any(type(a) is not str for a in r["actions"])
            or len(set(r["actions"])) != len(r["actions"])
            or menus.setdefault(parent, r["actions"]) != r["actions"]
            or type(r["counterfactual_mass"]) not in (int, float)
            or not math.isfinite(r["counterfactual_mass"])
            or r["counterfactual_mass"] < 0
            or set(r["q"]) != set(SUFFIXES)
            or any(
                len(v) != len(r["actions"])
                or any(type(q) not in (int, float) or not math.isfinite(q) for q in v)
                for v in r["q"].values()
            )
        ):
            raise ArithmeticError("invalid/duplicate river row, owner, menu or values")
        seen.add(info)
    total = math.fsum(r["counterfactual_mass"] for r in rows)
    if not math.isfinite(total):
        raise ArithmeticError("nonfinite total river support")
    weights = np.array([r["counterfactual_mass"] / total if total else 0 for r in rows])
    keys = [probe_keys(r) for r in rows]
    results: list[dict[str, Any]] = []
    partitions = []
    parent_bins: dict[int, list[int]] = {}
    for row in rows:
        if (
            parent_bins.setdefault(row["parent"], row["features"]["bins"])
            != row["features"]["bins"]
        ):
            raise ArithmeticError("original q8 parent has incompatible mass bins")
    for column, probe in enumerate(PROBES):
        groups: dict[str, list[int]] = defaultdict(list)
        for i, key in enumerate(keys):
            groups[key[column]].append(i)
        partitions.append({frozenset(g) for g in groups.values()})
        panels = {}
        for suffix in SUFFIXES:
            costs, conflicts = [], set()
            supported_groups = 0
            for indexes in groups.values():
                first = rows[indexes[0]]
                q = np.array([rows[i]["q"][suffix] for i in indexes], dtype=float)
                costs.append(sharing_cost(q, weights[indexes]))
                active = [i for i in indexes if rows[i]["counterfactual_mass"] > 0]
                supported_groups += bool(active)
                sets = [
                    {
                        a
                        for a, v in enumerate(rows[i]["q"][suffix])
                        if max(rows[i]["q"][suffix]) - v <= 1e-9
                    }
                    for i in active
                ]
                if len(sets) >= 2 and not set.intersection(*sets):
                    conflicts.add(first["parent"])
            panels[suffix] = dict(
                local_sharing_cost_chips_per_cf_decision=math.fsum(costs),
                unresolved_parents=len(conflicts),
                supported_groups=supported_groups,
            )
        results.append(dict(probe=probe, groups=len(groups), panels=panels))
    for coarse, fine in zip(results[:-1], results[1:], strict=True):
        if fine["groups"] < coarse["groups"] or any(
            fine["panels"][s]["unresolved_parents"]
            > coarse["panels"][s]["unresolved_parents"]
            or fine["panels"][s]["local_sharing_cost_chips_per_cf_decision"]
            > coarse["panels"][s]["local_sharing_cost_chips_per_cf_decision"] + 1e-9
            for s in SUFFIXES
        ):
            raise ArithmeticError("refinement increased conflicts/cost or lost groups")
    if results[-1]["groups"] != len(rows) or any(
        results[-1]["panels"][s]["unresolved_parents"] != 0
        or abs(results[-1]["panels"][s]["local_sharing_cost_chips_per_cf_decision"])
        > 1e-9
        for s in SUFFIXES
    ):
        raise ArithmeticError("exact singleton control must have zero sharing cost")
    return dict(
        target=target,
        river_infos=len(rows),
        supported_infos=int(np.count_nonzero(weights)),
        unsupported_infos=int(np.count_nonzero(weights == 0)),
        total_counterfactual_mass=total,
        no_supported_evidence=total == 0,
        q8_exact_mass_same_partition=partitions[0] == partitions[1],
        probes=results,
    )


def write_gzip(path: Path, payload: Any) -> None:
    with path.open("wb") as stream:
        with gzip.GzipFile(fileobj=stream, mode="wb", filename="", mtime=0) as zipped:
            zipped.write(canonical(payload))


def run(root: Path, output: Path) -> None:
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain complete/partial river refinement output")
    started = time.perf_counter()
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("prospective river refinement config changed")
    cfg = json.loads((root / CONFIG).read_text())
    if digest(root / cfg["panel_config"]) != cfg["panel_config_sha256"]:
        raise ArithmeticError("original complete saved panel changed")
    source = source_provenance(
        root,
        root / CONFIG,
        entrypoints=(ENTRY, "scripts/trace_private_prefix_decisions.py"),
    )
    if source["dirty"] is not False:
        raise ValueError(
            "publish river refinement source first; clean checkout required"
        )
    deadline = Deadline(cfg["diagnostic_wall_seconds"])
    deadline.started = started
    inputs = {cfg[k]: digest(root / cfg[k]) for k in ("own", "native", "panel_config")}
    output.mkdir(parents=True)
    persist(output / "partial.json", dict(status="validating_inputs", profiles=[]))
    try:
        calculate(root, output, cfg, source, deadline)
        if any(digest(root / p) != h for p, h in inputs.items()):
            raise ArithmeticError("bound input changed during diagnosis")
        deadline.check()
        manifest = dict(
            status="complete_saved_river_refinement_diagnostic",
            source=source,
            source_sha256=sha(source["sha256"]),
            config_sha256=CONFIG_SHA,
            input_sha256=inputs,
            environment=runtime_environment(),
            seconds=time.perf_counter() - started,
            constructors_blocked=True,
            training_performed=False,
            reference_constructed=False,
            new_agent_default=False,
            fresh_global_admission=False,
            limits=cfg["limits"],
            outputs={p.name: digest(p) for p in sorted(output.iterdir())},
        )
        persist(output / "manifest.json", manifest)
        deadline.check()
    except BaseException as exc:
        if (output / "manifest.json").exists():
            manifest = json.loads((output / "manifest.json").read_text())
            manifest["status"] = "failed_saved_river_refinement_diagnostic"
            persist(output / "manifest.json", manifest)
        persist(
            output / "failure.json",
            dict(
                type=type(exc).__name__,
                message=str(exc),
                seconds=time.perf_counter() - started,
            ),
        )
        raise


def calculate(
    root: Path,
    output: Path,
    cfg: dict[str, Any],
    source: dict[str, Any],
    deadline: Deadline,
) -> None:
    # Load the existing experiment-specific panel adapter without changing frozen src.
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "river_refinement_trace", root / "scripts/trace_private_prefix_decisions.py"
    )
    assert spec is not None and spec.loader is not None
    trace = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(trace)

    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("river refinement constructed learner/reference")

    with ExitStack() as stack:
        for name in (
            "poker_ai.postflop.controlled_training.ControlledTrainer.__init__",
            "poker_ai.postflop.stratified_batches.StratifiedBatchTrainer.__init__",
            "poker_ai.solver_validation.matched_array_reference.ScalarReference.__init__",
            "poker_ai.solver_validation.reference.Reference.__init__",
        ):
            stack.enter_context(patch(name, forbidden))
        path, native_path = root / cfg["own"], root / cfg["native"]
        if digest(path) != cfg["own_sha256"]:
            raise ArithmeticError("bound own study changed")
        print("Checking complete saved evidence; constructors blocked...", flush=True)
        own, sources = read(root, path, deadline)
        native = json.loads(native_path.read_text())
        check_source(root, native["source"])
        native_journal(native_path, native)
        measured(root, native_path, "real_native")
        validate(native, own, path)
        if own["source_sha256"] != cfg["model_source_sha256"]:
            raise ArithmeticError("frozen model source changed")
        selected = trace.panel(
            json.loads((root / cfg["panel_config"]).read_text()), own
        )
        saved = trace.policies(root, path, own, sources, selected)
        summaries, details = [], []
        for record in selected:
            deadline.check()
            row = record["row"]
            candidate_id = next(
                p["row"]["id"]
                for p in selected
                if p["seed"] == record["seed"] and p["role"] == "stratified"
            )
            index = next(
                r["path_index"] for r in own["rows"] if r["id"] == candidate_id
            )
            scoring = sources.context(index)
            exact = scoring.exact
            policy = saved[row["id"]]
            fingerprint = array_sha(policy)
            if fingerprint != row["receipt"]["policy_sha256"]:
                raise ArithmeticError("saved source policy changed")
            score = scoring.score(policy)
            if (
                max(abs(score.metrics[k] - row["metrics"][k]) for k in score.metrics)
                > cfg["tolerance_chips"]
            ):
                raise ArithmeticError("score differs from audited source")
            identity = dict(
                seed=record["seed"],
                role=record["role"],
                source_id=row["id"],
                policy_sha256=fingerprint,
            )
            responses, inventories = [], []
            for target in (0, 1):
                qs, supports, roots = {}, [], {}
                for suffix in SUFFIXES:
                    p = score.replies[target][suffix]
                    if not np.array_equal(
                        p[exact.owners != target],
                        scoring.expand(policy)[exact.owners != target],
                    ):
                        raise ArithmeticError("reply changed fixed opponent")
                    root_value = (1 if target == 0 else -1) * float(
                        exact.values(exact.edges(p))[0]
                    )
                    expected = row["responses"][target][suffix + "_reply_value_chips"]
                    if abs(root_value - expected) > cfg["tolerance_chips"]:
                        raise ArithmeticError("reply root changed")
                    qs[suffix], mass = conditional_actions(exact, p)
                    supports.append(mass)
                    roots[suffix] = root_value
                mask = scoring.river_masks[target]
                error = float(
                    np.max(
                        np.abs(
                            supports[0][exact.owners == target]
                            - supports[1][exact.owners == target]
                        ),
                        initial=0,
                    )
                )
                if error > cfg["tolerance_unitless"]:
                    raise ArithmeticError("responding counterfactual support changed")
                prior = RangePrior.create(
                    (h.cards, h.weight) for h in exact.source.spot.ranges[1 - target]
                )
                records = []
                for raw in np.flatnonzero(mask):
                    info = int(raw)
                    state = exact.source.states[exact.source.representatives[info]]
                    assert state.dealer is not None
                    obs = state.dealer.observe(target)
                    moves = [
                        NoLimitState(state.dealer, exact.source.spot.rules).decode(a)
                        for a in exact.actions[info]
                    ]
                    actions = [
                        m.kind.value + ("" if m.amount is None else f" {m.amount}")
                        for m in moves
                    ]
                    records.append(
                        dict(
                            exact_info=info,
                            parent=int(scoring.exact_to_partition[info]),
                            target=target,
                            street=obs.street.name,
                            hole=[format_card(c) for c in obs.hole_cards],
                            board=[format_card(c) for c in obs.board],
                            actions=actions,
                            counterfactual_mass=float(supports[0][info]),
                            q={
                                s: qs[s][info, : len(actions)].tolist()
                                for s in SUFFIXES
                            },
                            features=features(obs.hole_cards, obs.board, prior),
                        )
                    )
                if [r["exact_info"] for r in records] != np.flatnonzero(mask).tolist():
                    raise ArithmeticError("complete river inventory required")
                summary = summarize(records, target)
                summary.update(
                    roots_chips=roots,
                    maximum_support_error=error,
                    prior=prior.canonical_payload(),
                )
                responses.append(summary)
                inventories.append(dict(target=target, rows=records))
            if array_sha(policy) != fingerprint:
                raise ArithmeticError("saved policy mutated")
            summaries.append(dict(**identity, responses=responses))
            detail = dict(**identity, responses=inventories)
            details.append(detail)
            write_gzip(
                output / f"partial-{record['seed']}-{record['role']}.json.gz", detail
            )
            persist(
                output / "partial.json", dict(status="in_progress", profiles=summaries)
            )
            print(f"probed {record['seed']}/{record['role']}", flush=True)
            deadline.check()
        if (
            len(summaries) != cfg["profiles"]
            or sum(len(p["responses"]) for p in summaries) != cfg["responses"]
        ):
            raise ArithmeticError("complete nine/eighteen refinement panel required")
        write_gzip(output / "rows.json.gz", dict(profiles=details))
        persist(output / "summary.json", dict(profiles=summaries))
        persist(output / "partial.json", dict(status="complete", profiles=summaries))
        if sha(source["sha256"]) != sha(
            source_provenance(
                root,
                root / CONFIG,
                entrypoints=(ENTRY, "scripts/trace_private_prefix_decisions.py"),
            )["sha256"]
        ):
            raise ArithmeticError("source changed during diagnosis")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(FOLDER))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    run(root, root / args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
