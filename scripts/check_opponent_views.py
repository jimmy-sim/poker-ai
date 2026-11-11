"""Check own mixed-information views; this command cannot admit poker training."""

import argparse
import json
import time
from contextlib import ExitStack
from pathlib import Path
from typing import Any
from unittest.mock import patch

import numpy as np

from poker_ai.abstraction.model import CardAbstraction
from poker_ai.evaluation.opponent_view_correctness import analytic_proof
from poker_ai.postflop.game import load_spot
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.matrix import MatrixTree
from poker_ai.postflop.opponent_views import bind_policy, build_view, compose
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.range_protocol import build_representation_control
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.postflop.tree import SpotTree
from poker_ai.reproducibility import runtime_environment
from poker_ai.validation.five_card import source_provenance

CONFIG = "configs/exact-opponent-views.json"
CONFIG_SHA = "6c1060ee37c544e8ad3aee97ae3cf2574a36b8a4bf01224a3e7c211319c9c880"
ENTRY = "scripts/check_opponent_views.py"


def structural(
    root: Path, cfg: dict[str, Any], deadline: Deadline
) -> list[dict[str, Any]]:
    model = CardAbstraction.load(root / cfg["model"])
    results = []
    for filename in cfg["spot_files"]:
        deadline.check()
        source = SpotTree.build(load_spot(root / filename))
        fine = MatrixTree.build(source)
        coarse = build_representation_control(
            source, cfg["coarse_representation"], model
        )
        mapping = coarse.exact_to_abstract
        uniform = coarse.normalize(coarse.legal)
        bundles = []
        for target in (0, 1):
            view = build_view(fine, coarse, mapping, target)
            policy = np.zeros_like(view.tree.legal)
            for info, group in enumerate(view.fine_to_view):
                policy[group] = uniform[mapping[info]]
            if not np.array_equal(view.tree.edges(policy), coarse.edges(uniform)):
                raise ArithmeticError("mixed view changed original policy edges")
            own = fine.owners == target
            for group in np.unique(mapping[own]):
                if len(np.unique(view.fine_to_view[(mapping == group) & own])) != 1:
                    raise ArithmeticError("own coarse information was refined")
            if len(np.unique(view.fine_to_view[~own])) != np.count_nonzero(~own):
                raise ArithmeticError("fine opponent information was merged")
            bundles.append((view, bind_policy(view, policy)))
        if not np.array_equal(compose(coarse, bundles[0], bundles[1]), uniform):
            raise ArithmeticError("seatwise uniform composition changed policy")
        results.append(
            dict(
                spot_file=filename,
                views=[v.sha256 for v, _ in bundles],
                policy_edge_error=0,
                own_information_refined=False,
                finer_opponent_merged=False,
                recall_checked=True,
            )
        )
        deadline.check()
    return results


def run(root: Path, output: Path) -> None:
    if output.exists() or output.is_symlink():
        raise FileExistsError("retain prior opponent-view software output")
    started = time.perf_counter()
    if digest(root / CONFIG) != CONFIG_SHA:
        raise ArithmeticError("opponent-view software protocol changed")
    cfg = json.loads((root / CONFIG).read_text())
    source = source_provenance(root, root / CONFIG, entrypoints=(ENTRY,))
    if source["dirty"] is not False:
        raise ValueError("publish software source first; use a clean checkout")
    deadline = Deadline(cfg["maximum_software_seconds"])
    deadline.started = started
    saved: dict[str, Any] = dict(
        status="running_software_only",
        source=source,
        source_sha256=sha(source["sha256"]),
        config_sha256=CONFIG_SHA,
        toy=[],
        structural=[],
        failure=None,
        poker_training_performed=False,
        toy_learning_performed=False,
        reference_constructed=False,
        long_run_admitted=False,
        new_agent_default=False,
        fresh_global_admission=False,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    persist(output, saved)
    try:
        if digest(root / cfg["historical_own"]) != cfg["historical_own_sha256"]:
            raise ArithmeticError("historical parent bytes changed")
        parent = json.loads((root / cfg["historical_own"]).read_text())
        check_source(root, parent["source"])
        if parent["source_sha256"] != cfg["historical_source_sha256"]:
            raise ArithmeticError("historical source identity changed")
        inputs = {cfg["model"]: cfg["model_sha256"], **cfg["spot_sha256"]}
        if any(digest(root / p) != h for p, h in inputs.items()):
            raise ArithmeticError("fixed own model/spot bytes changed")

        def forbidden(*a: Any, **k: Any) -> None:
            raise AssertionError("software fixture constructed learner/reference")

        with ExitStack() as stack:
            for name in (
                "poker_ai.postflop.controlled_training.ControlledTrainer.__init__",
                "poker_ai.postflop.stratified_batches.StratifiedBatchTrainer.__init__",
                "poker_ai.solver_validation.matched_array_reference.ScalarReference.__init__",
                "poker_ai.solver_validation.reference.Reference.__init__",
            ):
                stack.enter_context(patch(name, forbidden))
            saved["toy"] = analytic_proof()
            saved["structural"] = structural(root, cfg, deadline)
        if [row["risk_target"] for row in saved["toy"]] != [0, 1] or [
            row["spot_file"] for row in saved["structural"]
        ] != cfg["spot_files"]:
            raise ArithmeticError("both toy signs and known-game structures required")
        deadline.check()
        if any(digest(root / p) != h for p, h in inputs.items()):
            raise ArithmeticError("software input changed during checks")
        current = source_provenance(root, root / CONFIG, entrypoints=(ENTRY,))
        if source["sha256"] != current["sha256"]:
            raise ArithmeticError("software source changed during checks")
        saved.update(
            status="software_views_checked_not_training_admission",
            input_sha256=inputs,
            constructors_blocked=True,
            historical_source_unchanged=True,
            source_checks="not assessed by this command",
            environment=runtime_environment(),
            limits=cfg["limits"],
            seconds=time.perf_counter() - started,
        )
        persist(output, saved)
        deadline.check()
    except BaseException as exc:
        saved.update(
            status="failed_software_only",
            failure=dict(type=type(exc).__name__, message=str(exc)),
            seconds=time.perf_counter() - started,
        )
        persist(output, saved)
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("results/runs/opponent-views/correctness.json"),
    )
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    run(root, root / args.output)
    print("Checked analytic fixtures and both poker structures; no training admission.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
