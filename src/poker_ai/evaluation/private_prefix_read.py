"""Read/replay complete own receipts; never create a learner or native solver."""

import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation import private_prefix_baselines as real_baselines
from poker_ai.evaluation.private_prefix_archive import replay
from poker_ai.evaluation.private_prefix_design import OLD, REAL, TOY, Design
from poker_ai.evaluation.private_prefix_journal import validate as validate_journal
from poker_ai.evaluation.private_prefix_pairs import fixed_pairs, self_pairs
from poker_ai.evaluation.private_prefix_sources import contract, load
from poker_ai.evaluation.private_prefix_toy import fixture, maps, replay_baselines
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import finite, same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import Deadline, digest

FORMAT = "poker-ai-private-prefix-own-v1"


def read(root: Path, path: Path, deadline: Deadline) -> tuple[dict[str, Any], Any]:
    saved: dict[str, Any] = json.loads(path.read_text())
    json.dumps(saved, allow_nan=False)
    config, driver = contract(root)
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed_own_native_pending"
        or saved["failure"] is not None
        or not same(saved["config"], config)
        or not same(saved["driver"], driver)
        or saved["scope"] not in (TOY, OLD, REAL)
        or any(
            saved[k] is not False
            for k in (
                "reference_constructed",
                "reference_output_used_in_training",
                "new_agent_default",
                "fresh_global_admission",
            )
        )
        or not finite(saved["seconds"])
        or saved["seconds"]
        >= (180 if saved["scope"] == TOY else 900 if saved["scope"] == OLD else 7200)
    ):
        raise ArithmeticError("incomplete/changed own private-prefix header")
    check_source(root, saved["source"])
    if sha(saved["source"]["sha256"]) != saved["source_sha256"]:
        raise ArithmeticError("own source inventory identity changed")
    if any(digest(root / p) != h for p, h in saved["input_sha256"].items()):
        raise ArithmeticError("private-prefix used input bytes changed")
    sources: Any
    if saved["scope"] == TOY:
        validate_journal(
            path.with_name(saved["journal_file"]),
            saved["journal"],
            saved["source_sha256"],
            {0: saved["events"], 1: saved["baseline_rows"], 2: saved["baseline_fixed"]},
        )
        design, context, opponents = fixture(config)
        core = replay(
            path, saved, design, lambda _: context, opponents.matches, deadline
        )
        old = replay_baselines(path, saved, design, context, opponents, deadline)
        selves, targets = maps(design, saved["baseline_rows"], saved["baseline_fixed"])
        sources = (design, context, opponents)
    else:
        if saved["scope"] == REAL:
            from poker_ai.evaluation.private_prefix_admission import (
                ADMISSION,
            )
            from poker_ai.evaluation.private_prefix_admission import (
                require as require_admission,
            )
            from poker_ai.evaluation.private_prefix_worker_checks import complete

            admission = require_admission(root, clean=False)
            if not same(saved["admission"], admission) or saved[
                "admission_sha256"
            ] != digest(root / ADMISSION):
                raise ArithmeticError(
                    "real own study differs from its published admission"
                )
            training_events = complete(saved["training_batch"], 48)
            validate_journal(
                path.with_name(saved["journal_file"]),
                saved["journal"],
                saved["source_sha256"],
                {w["slot"]: w["messages"] for w in saved["training_batch"]["workers"]},
            )
            if not same(
                training_events, saved["events"][: saved["training_event_count"]]
            ):
                raise ArithmeticError(
                    "retained training events differ from fixed worker records"
                )
        sources = load(root)
        design = Design.build(config, mode="old" if saved["scope"] == OLD else "real")
        real_baselines.verify_saved(saved, sources)
        if not same(saved["input_sha256"], real_baselines.source_hashes(root, sources)):
            raise ArithmeticError("used original baseline input inventory changed")
        core = replay(
            path,
            saved,
            design,
            sources.context,
            lambda r, p, b: real_baselines.fixed_for(sources, r, p, b),
            deadline,
        )
        old = dict(
            profiles=648,
            fixed_targets=1728,
            origin="reused_original_audited_baselines_not_new_retraining",
        )
        selves, targets = real_baselines.maps(
            design, saved["baseline_rows"], saved["baseline_fixed"]
        )
        if saved["scope"] == REAL:
            from poker_ai.evaluation.private_prefix_quality import summarize

            pots = {
                p["spot_file"]: float(
                    json.loads((root / p["spot_file"]).read_text())["pot"]
                )
                for p in design.paths
            }
            if not same(
                summarize(saved["rows"], pots), saved["known_case_quality_limits"]
            ):
                raise ArithmeticError("known-case quality summary changed")
    if not same(
        self_pairs(design, saved["rows"], selves), saved["self_pairs"]
    ) or not same(fixed_pairs(saved["fixed_matches"], targets), saved["fixed_pairs"]):
        raise ArithmeticError("complete private-prefix paired metrics changed")
    if saved["scope"] == OLD and (
        saved["training_performed"] is not False
        or not same(saved["initialized_training_paths"], 0)
    ):
        raise ArithmeticError("old cost corpus cannot claim new training")
    if saved["scope"] != OLD and (
        saved["training_performed"] is not True
        or not same(saved["initialized_training_paths"], 48)
    ):
        raise ArithmeticError("all48 candidate learning paths must complete")
    saved = dict(saved, replayed_now=dict(core=core, baselines=old))
    for name, h in saved["report"].items():
        if digest(path.parent / "report" / name) != h:
            raise ArithmeticError("published own report artifact changed")
    deadline.check()
    return saved, sources
