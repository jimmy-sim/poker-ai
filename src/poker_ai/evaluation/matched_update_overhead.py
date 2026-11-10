"""Complete fixed-shape overhead exercise on published OLD policies, never training."""

import json
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import matched_update_inputs as inputs
from poker_ai.evaluation.batch_current_math import matches
from poker_ai.evaluation.matched_update_records import (
    inventory,
    paired_fixed,
    paired_self,
)
from poker_ai.evaluation.matched_update_replay import replay_archives
from poker_ai.evaluation.matched_update_report import write_report
from poker_ai.evaluation.matched_update_run import archive, fresh, gather, source
from poker_ai.evaluation.matched_update_scoring import scoring_job
from poker_ai.evaluation.matched_update_timing_corpus import SCOPE, corpus, job
from poker_ai.postflop.cell_process import run_batch
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment


def run(
    root: Path, output: Path, outer: Deadline, original_source: dict[str, Any]
) -> dict[str, Any]:
    fresh(output)
    started = time.perf_counter()
    deadline = Deadline(min(600, outer.seconds - (started - outer.started)))
    deadline.started = started
    saved: dict[str, Any] = dict(
        scope=SCOPE,
        status="running",
        failure=None,
        source=None,
        source_sha256=None,
        config=None,
        environment=runtime_environment(),
        batches=[],
        captures=[],
        masses=[],
        checkpoints=[],
        rows=[],
        fixed_matches=[],
        self_pairs=[],
        fixed_pairs=[],
        source_inputs=None,
        manifest=None,
        checkpoint_origin="archival_source_identity_not_new_trajectory",
        new_prefix_training=False,
        strength_results=False,
        reference_constructed=False,
        long_run_admitted=False,
        seconds=0.0,
        scratch=str(
            root / "results/runs/matched-update-overhead" / str(time.time_ns())
        ),
    )
    try:
        # The parent profile is already a new output. Bind exact code bytes;
        # source cleanliness was checked before that parent attempt was written.
        saved["attempt_source"] = source(root)
        check_source(root, original_source)
        if not same(saved["attempt_source"]["sha256"], original_source["sha256"]):
            raise ArithmeticError("overhead source differs from clean parent profile")
        saved["source"] = original_source
        saved["source_sha256"] = sha(original_source["sha256"])
        persist(output, saved)
        saved["config"] = inputs.config_inputs(root)
        required = saved["config"]["required_runtime"]
        if any(saved["environment"][k] != required[k] for k in ("python", "numpy")):
            raise ArithmeticError("old poker overhead requires original runtime")
        sources = inputs.load(root)
        manifest, right, right_fixed = corpus(sources)
        saved["manifest"] = manifest
        saved["source_inputs"] = sources.manifest["input_sha256"]
        expected = [
            sources.original(i, w)
            for i in range(24)
            for w in (100000, 1000000, 10000000)
        ]
        for phase, worker in (("copy_old", job), ("score_old", scoring_job)):
            batch: dict[str, Any] = {}
            saved["batches"].append(batch)
            remaining = min(
                600 - (time.perf_counter() - started),
                outer.seconds - (time.perf_counter() - outer.started),
            )
            if remaining <= 0:
                raise TimeoutError(
                    "complete old-policy overhead exceeded fixed allowance"
                )
            run_batch(
                24,
                3,
                worker,
                dict(
                    root=str(root),
                    own_path=str(output),
                    own=saved,
                    manifest=manifest,
                    scratch=saved["scratch"],
                    binding=saved["source_sha256"],
                    checkpoints=saved["checkpoints"],
                    remaining_seconds=remaining,
                ),
                deadline,
                batch,
            )
            gather(saved)
            persist(output, saved)
            if phase == "copy_old":
                archive(output, saved, Path(saved["scratch"]), "captures", "captures")
                archive(output, saved, Path(saved["scratch"]), "masses", "masses")
                inventory(saved, manifest, expected)
        saved["self_pairs"] = paired_self(manifest, saved["rows"], right)
        saved["fixed_pairs"] = paired_fixed(
            manifest, saved["fixed_matches"], right_fixed
        )
        archive(output, saved, Path(saved["scratch"]), "details", "profiles")
        saved["own_replay"] = replay_archives(
            output,
            saved,
            manifest,
            expected,
            sources.context,
            lambda row, policy: matches(
                sources.archived, row, policy, saved["source_sha256"]
            ),
            right,
            right_fixed,
            deadline,
        )
        saved["report"] = write_report(saved, output.parent / "report")
        outer.check()
        if time.perf_counter() - started >= 600:
            raise TimeoutError("complete old-policy overhead did not fit600s allowance")
        saved["status"] = "completed_old_policy_overhead_timing_only"
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        gather(saved)
        saved["seconds"] = time.perf_counter() - started
        persist(output, saved)
    return saved


def read(
    root: Path, path: Path, deadline: Deadline
) -> tuple[dict[str, Any], inputs.Sources]:
    saved: dict[str, Any] = json.loads(path.read_text())
    check_source(root, saved["source"])
    if (
        saved["scope"] != SCOPE
        or saved["status"] != "completed_old_policy_overhead_timing_only"
        or saved["failure"] is not None
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["config"] != inputs.config_inputs(root)
        or saved["checkpoint_origin"] != "archival_source_identity_not_new_trajectory"
        or any(
            saved[k] is not False
            for k in (
                "new_prefix_training",
                "strength_results",
                "reference_constructed",
                "long_run_admitted",
                "training_performed",
            )
        )
        or type(saved["seconds"]) not in (int, float)
        or not 0 <= saved["seconds"] < 600
    ):
        raise ArithmeticError("incomplete/mislabeled old-policy timing corpus")
    from poker_ai.evaluation.matched_update_workers import complete

    complete(
        saved["batches"][0],
        dict(
            paths=8,
            captures=48,
            masses=32,
            source_metadata_checks=24,
            new_training=False,
        ),
    )
    complete(saved["batches"][1], dict(paths=8, profiles=48, fixed_targets=384))
    rebuilt = dict(saved)
    gather(rebuilt)
    if any(
        not same(rebuilt[k], saved[k])
        for k in ("captures", "masses", "checkpoints", "rows", "fixed_matches")
    ):
        raise ArithmeticError("old timing rows differ from raw worker messages")
    sources = inputs.load(root)
    manifest, right, fixed = corpus(sources)
    if not same(manifest, saved["manifest"]) or not same(
        sources.manifest["input_sha256"], saved["source_inputs"]
    ):
        raise ArithmeticError("old-policy corpus/inputs changed")
    expected = [
        sources.original(i, w) for i in range(24) for w in (100000, 1000000, 10000000)
    ]
    replay_archives(
        path,
        saved,
        manifest,
        expected,
        sources.context,
        lambda row, policy: matches(
            sources.archived, row, policy, saved["source_sha256"]
        ),
        right,
        fixed,
        deadline,
    )
    return saved, sources
