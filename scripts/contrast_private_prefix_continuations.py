"""Fixed saved-opponent continuation contrasts; no learning or native solver."""

import argparse
import gzip
import importlib.util
import json
import time
from contextlib import ExitStack
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest.mock import patch

import numpy as np

from poker_ai.cards import format_card
from poker_ai.evaluation.averaging_history_artifacts import array_sha
from poker_ai.evaluation.matched_update_lifecycle import measured
from poker_ai.evaluation.private_prefix_admission import native_journal
from poker_ai.evaluation.private_prefix_read import read
from poker_ai.finite import ArrayTree, FloatArray
from poker_ai.postflop.collision_diagnosis import conditional_actions
from poker_ai.postflop.learning_artifacts import canonical, sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment
from poker_ai.solver_validation.private_prefix import validate
from poker_ai.training.no_limit import NoLimitState
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/private-prefix-continuations.json"
CONFIG_SHA = "20169784768a0e6c2be49ac6d1b594273bbdbfba120d4cbaeae44f85ed22949b"
ENTRY = "scripts/contrast_private_prefix_continuations.py"
FOLDER = "results/private-prefix/continuations"


def cli(root: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        name, root / "scripts" / (name + ".py")
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def values(
    tree: ArrayTree,
    saved: FloatArray,
    profiles: dict[str, FloatArray],
    river: np.ndarray[Any, Any],
    target: int,
    roots: dict[str, float],
    chip: float,
    unitless: float,
) -> tuple[dict[str, FloatArray], FloatArray, float, float]:
    """Change own river rows only in the exact-prefix hybrid; fix opponent."""
    if type(target) is not int or target not in (0, 1):
        raise ValueError("target must be seat zero or one")
    if set(profiles) != {"exact", "restricted", "river_before"}:
        raise ArithmeticError("complete continuation profile trio required")
    if (
        set(roots) != set(profiles)
        or any(
            type(v) not in (int, float) or not np.isfinite(v) for v in roots.values()
        )
        or not 0 < chip <= 1e-9
        or not 0 < unitless <= 1e-12
    ):
        raise ArithmeticError("finite bound roots and fixed tolerances required")
    tree.validate_policy(saved)
    before = {name: array_sha(p) for name, p in profiles.items()}
    opponent = tree.owners != target
    own_river = river
    if (
        own_river.dtype != np.bool_
        or own_river.shape != tree.owners.shape
        or np.any(own_river & opponent)
    ):
        raise ArithmeticError("own river mask changed")
    q, support, root_error, support_error = {}, None, 0.0, 0.0
    for name, policy in profiles.items():
        tree.validate_policy(policy)
        if not np.array_equal(policy[opponent], saved[opponent]):
            raise ArithmeticError("continuation changed fixed opponent")
        actual = (1 if target == 0 else -1) * float(tree.values(tree.edges(policy))[0])
        root_error = max(root_error, abs(actual - roots[name]))
        action_values, mass = conditional_actions(tree, policy)
        if not np.isfinite(action_values).all() or not np.isfinite(mass).all():
            raise ArithmeticError("nonfinite continuation values/support")
        if support is None:
            support = mass
        else:
            support_error = max(
                support_error,
                float(np.max(np.abs(mass[~opponent] - support[~opponent]), initial=0)),
            )
        q[name] = action_values
    hybrid, exact, restricted = (
        profiles[k] for k in ("river_before", "exact", "restricted")
    )
    if not np.array_equal(hybrid[~own_river], exact[~own_river]) or not np.array_equal(
        hybrid[own_river], restricted[own_river]
    ):
        raise ArithmeticError("hybrid changes more than own river continuation")
    if not np.isfinite(root_error) or root_error > chip or support_error > unitless:
        raise ArithmeticError("continuation roots/support differ from bound source")
    if any(array_sha(profiles[k]) != h for k, h in before.items()):
        raise ArithmeticError("continuation calculation mutated input")
    assert support is not None
    return q, support, root_error, support_error


def choice(q: list[float], support: float) -> int | None:
    if not q or not np.isfinite(q).all() or not np.isfinite(support) or support < 0:
        raise ArithmeticError("finite legal action values/support required")
    return int(np.argmax(q)) if support > 0 else None


def run(root: Path, output: Path) -> None:
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain complete/partial continuation output")
    started = time.perf_counter()
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("fixed continuation protocol changed")
    cfg = json.loads((root / CONFIG).read_text())
    folder = root / cfg["decision_report"]
    if digest(folder / "summary.json") != cfg["decision_summary_sha256"]:
        raise ArithmeticError(
            "safeguarded decision summary must reproduce pinned bytes"
        )
    trace = cli(root, "trace_private_prefix_decisions")
    viewer = cli(root, "inspect_private_prefix_decisions")
    decision_profiles = viewer.load(root, folder)

    def forbidden(*a: Any, **k: Any) -> None:
        raise AssertionError("continuation contrast constructed learner/reference")

    print("Checking complete saved evidence; constructors blocked...", flush=True)
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
            raise ArithmeticError("bound own continuation source changed")
        own, sources = read(root, path, Deadline(900))
        native = json.loads(native_path.read_text())
        check_source(root, native["source"])
        native_journal(native_path, native)
        measured(root, native_path, "real_native")
        validate(native, own, path)
        if own["source_sha256"] != cfg["model_source_sha256"]:
            raise ArithmeticError("frozen continuation model source changed")
        selected = trace.panel(json.loads((root / trace.CONFIG).read_text()), own)
        policies = trace.policies(root, path, own, sources, selected)
        source = source_provenance(
            root,
            root / CONFIG,
            entrypoints=(
                ENTRY,
                "scripts/trace_private_prefix_decisions.py",
                "scripts/inspect_private_prefix_decisions.py",
            ),
        )
        output.mkdir(parents=True, exist_ok=False)
        rows, roots, groups = [], [], 0
        for record in selected:
            prior = next(
                p
                for p in decision_profiles
                if p["seed"] == record["seed"] and p["role"] == record["role"]
            )
            row = record["row"]
            if prior["source_id"] != row["id"]:
                raise ArithmeticError("decision continuation source identity changed")
            index = next(
                r["path_index"]
                for r in own["rows"]
                if r["id"]
                == next(
                    x["row"]["id"]
                    for x in selected
                    if x["seed"] == record["seed"] and x["role"] == "stratified"
                )
            )
            scoring = sources.context(index)
            policy = policies[row["id"]]
            fingerprint = array_sha(policy)
            if fingerprint != prior["policy_sha256"]:
                raise ArithmeticError("continuation source policy fingerprint changed")
            score = scoring.score(policy)
            if (
                max(abs(score.metrics[k] - row["metrics"][k]) for k in score.metrics)
                > cfg["tolerance_chips"]
            ):
                raise ArithmeticError("continuation score differs from audited metrics")
            expanded = scoring.expand(policy)
            for target in (0, 1):
                expected = {
                    k: row["responses"][target][v]
                    for k, v in (
                        ("exact", "exact_reply_value_chips"),
                        ("restricted", "restricted_reply_value_chips"),
                        ("river_before", "river_before_value_chips"),
                    )
                }
                q, support, error, mass_error = values(
                    scoring.exact,
                    expanded,
                    score.replies[target],
                    scoring.river_masks[target],
                    target,
                    expected,
                    cfg["tolerance_chips"],
                    cfg["tolerance_unitless"],
                )
                identity = dict(seed=record["seed"], role=record["role"], target=target)
                roots.append(
                    dict(
                        **identity,
                        values_chips=expected,
                        maximum_error_chips=error,
                        maximum_support_error=mass_error,
                    )
                )
                for rank, group in enumerate(
                    prior["responses"][target]["top_groups"], 1
                ):
                    members = np.flatnonzero(
                        scoring.exact_to_partition == group["abstract_info"]
                    )
                    if len(members) != group["exact_members"] or any(
                        scoring.exact.owners[i] != target for i in members
                    ):
                        raise ArithmeticError(
                            "complete ranked continuation members required"
                        )
                    groups += 1
                    for raw_info in members:
                        info = int(raw_info)
                        state = scoring.exact.source.states[
                            scoring.exact.source.representatives[info]
                        ]
                        assert state.dealer is not None
                        observation = state.dealer.observe(state.actor)
                        actions = []
                        for action in scoring.exact.actions[info]:
                            move = NoLimitState(
                                state.dealer, scoring.exact.source.spot.rules
                            ).decode(action)
                            actions.append(
                                move.kind.value
                                + ("" if move.amount is None else f" {move.amount}")
                            )
                        qs = {k: v[info, : len(actions)].tolist() for k, v in q.items()}
                        mass = float(support[info])
                        rows.append(
                            dict(
                                **identity,
                                group_rank=rank,
                                group=group["abstract_info"],
                                exact_info=info,
                                street=observation.street.name,
                                hole=[format_card(c) for c in observation.hole_cards],
                                board=[format_card(c) for c in observation.board],
                                actions=actions,
                                counterfactual_mass=mass,
                                supported=mass > 0,
                                action_values_chips=qs,
                                choices={k: choice(v, mass) for k, v in qs.items()},
                            )
                        )
                persist(
                    output / "partial.json", dict(rows=rows, roots=roots, groups=groups)
                )
            if array_sha(policy) != fingerprint:
                raise ArithmeticError("continuation contrast mutated saved policy")
    if (len(roots), groups, len(rows)) != (
        cfg["responses"],
        cfg["groups"],
        cfg["exact_members"],
    ):
        raise ArithmeticError(
            "complete eighteen/ninety/415 continuation panel required"
        )
    with (output / "rows.json.gz").open("wb") as stream:
        with gzip.GzipFile(fileobj=stream, mode="wb", filename="", mtime=0) as zipped:
            zipped.write(canonical(dict(rows=rows)))
    persist(
        output / "summary.json",
        dict(
            roots=roots,
            groups=groups,
            exact_members=len(rows),
            supported=sum(r["supported"] for r in rows),
            turn_choice_changes=sum(
                r["supported"]
                and r["street"] == "TURN"
                and r["choices"]["exact"] != r["choices"]["river_before"]
                for r in rows
            ),
        ),
    )
    persist(
        output / "manifest.json",
        dict(
            status="complete_saved_continuation_contrast",
            source=source,
            source_sha256=sha(source["sha256"]),
            config_sha256=CONFIG_SHA,
            own_sha256=digest(path),
            native_sha256=digest(native_path),
            decision_manifest_sha256=digest(folder / "manifest.json"),
            decision_summary_sha256=digest(folder / "summary.json"),
            outputs={p.name: digest(p) for p in sorted(output.iterdir())},
            environment=runtime_environment(),
            seconds=time.perf_counter() - started,
            constructors_blocked=True,
            training_performed=False,
            reference_constructed=False,
            new_agent_default=False,
            fresh_global_admission=False,
            limits=cfg["limits"],
        ),
    )
    print("Completed18responses/90groups/415members; no training.", flush=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path(FOLDER))
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    run(root, root / args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
