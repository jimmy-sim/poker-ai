"""Full-shape tiny OWN pipeline; explicit software evidence, never poker admission."""

import json
import socket
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import matched_update_code_gate as code_gate
from poker_ai.evaluation import matched_update_inputs as inputs
from poker_ai.evaluation.averaging_history_software import toy_context
from poker_ai.evaluation.matched_update_capture import collect
from poker_ai.evaluation.matched_update_records import (
    inventory,
    paired_fixed,
    paired_self,
)
from poker_ai.evaluation.matched_update_replay import replay_archives
from poker_ai.evaluation.matched_update_run import archive, fresh, gather, source
from poker_ai.evaluation.matched_update_scoring import score_capture
from poker_ai.evaluation.matched_update_software_inputs import (
    SCOPE,
    Fixture,
    build,
    pack,
    restore,
)
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.pipeline_report import check_source
from poker_ai.postflop.river_study import Deadline
from poker_ai.reproducibility import runtime_environment


def exercise(
    output: Path, saved: dict[str, Any], fixture: Fixture, deadline: Deadline
) -> None:
    """Same capture/scoring/archive/replay primitives, explicit fixture contexts."""
    scratch = Path(saved["scratch"])
    saved["fixture_inputs"] = pack(fixture)
    saved["fixture_inputs_sha256"] = sha(saved["fixture_inputs"])

    def event_batch() -> dict[str, Any]:
        return dict(
            execution="SEQUENTIAL_FIXTURE_EVENT_ROUTES_NOT_SPAWNED_WORKERS",
            assignments=partition(24, 3),
            workers=[dict(slot=i, messages=[]) for i in range(3)],
        )

    batch = event_batch()
    saved["batches"] = [batch]

    def retain(event: dict[str, Any]) -> None:
        batch["workers"][event["index"] % 3]["messages"].append(event)

    try:
        for index, path in enumerate(fixture.paths):
            retain(dict(kind="cell", phase="training_started", index=index))
            collect(
                toy_context(),
                path,
                index,
                [
                    t
                    for t in fixture.manifest["iteration_targets"]
                    if t["baseline_path_index"] == index
                ],
                [r for r in fixture.expected if r["path_index"] == index],
                scratch,
                saved["source_sha256"],
                SCOPE,
                retain,
                deadline,
            )
            gather(saved)
            persist(output, saved)
    finally:
        gather(saved)
    for name in ("captures", "masses"):
        archive(output, saved, scratch, name, name)
    inventory(saved, fixture.manifest, fixture.expected)
    # All source cases have passed. No new captured policy was scored above.
    batch = event_batch()
    saved["batches"].append(batch)
    try:
        for row in saved["captures"]:
            scored, policy = score_capture(
                toy_context(),
                row,
                (scratch / row["file"]).read_bytes(),
                scratch,
                retain,
                deadline,
            )
            for fixed in fixture.fixed(scored, policy):
                retain(
                    dict(kind="cell", phase="fixed", index=row["path_index"], row=fixed)
                )
    finally:
        gather(saved)
    saved["self_pairs"] = paired_self(fixture.manifest, saved["rows"], fixture.right)
    saved["fixed_pairs"] = paired_fixed(
        fixture.manifest, saved["fixed_matches"], fixture.right_fixed
    )
    archive(output, saved, scratch, "details", "profiles")
    saved["replay"] = replay_archives(
        output,
        saved,
        fixture.manifest,
        fixture.expected,
        lambda _: toy_context(),
        fixture.fixed,
        fixture.right,
        fixture.right_fixed,
        deadline,
    )
    if any(
        v != 0
        for p in saved["self_pairs"]
        for v in p["difference_prefix_minus_batched_chips"].values()
    ) or any(
        p["difference_prefix_minus_batched_ev_chips"] != 0
        or p["difference_prefix_minus_batched_gain_chips"] != 0
        for p in saved["fixed_pairs"]
    ):
        raise ArithmeticError("identical-strategy tiny control must have zero gap")


def run(root: Path, output: Path) -> dict[str, Any]:
    fresh(output)
    started = time.perf_counter()
    deadline = Deadline(180)
    deadline.started = started
    saved: dict[str, Any] = dict(
        scope=SCOPE,
        status="running",
        failure=None,
        source=None,
        source_sha256=None,
        config=None,
        code_checks=None,
        environment=runtime_environment(),
        proof_host=socket.gethostname(),
        proof_started_perf_counter=started,
        captures=[],
        masses=[],
        checkpoints=[],
        rows=[],
        fixed_matches=[],
        self_pairs=[],
        fixed_pairs=[],
        replay=None,
        software_training_attempted=False,
        software_training_performed=False,
        poker_training_performed=False,
        reference_constructed=False,
        long_run_admitted=False,
        seconds=0.0,
        dependency=(
            "24 logical labels, one tiny tree, six seed/rule paths; "
            "right profiles equal independently generated B1 prefixes"
        ),
        scratch=str(
            root / "results/runs/matched-update-software" / str(time.time_ns())
        ),
    )
    try:
        saved["source"] = source(root)
        saved["source_sha256"] = sha(saved["source"]["sha256"])
        persist(output, saved)
        if saved["source"]["dirty"] is not False:
            raise ArithmeticError("complete tiny proof requires clean committed source")
        saved["config"] = inputs.config_inputs(root)
        saved["code_checks"] = code_gate.require(root, clean=False)
        saved["software_training_attempted"] = True

        def mark_started() -> None:
            saved["software_training_performed"] = True

        fixture = build(saved["source_sha256"], deadline, mark_started)
        exercise(output, saved, fixture, deadline)
        deadline.check()
        saved["status"] = "completed_tiny_own_native_pending_not_poker"
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        saved["software_training_performed"] = saved[
            "software_training_performed"
        ] or bool(saved["checkpoints"])
        saved["seconds"] = time.perf_counter() - started
        for name in ("captures", "masses", "checkpoints", "rows", "fixed_matches"):
            saved["completed_" + name] = len(saved[name])
        persist(output, saved)
    return saved


def read(
    root: Path, path: Path, deadline: Deadline | None = None
) -> tuple[dict[str, Any], Fixture, dict[str, Any]]:
    saved: dict[str, Any] = json.loads(path.read_text())
    check_source(root, saved["source"])
    checked = code_gate.require(root, clean=False)
    if (
        saved["scope"] != SCOPE
        or saved["status"] != "completed_tiny_own_native_pending_not_poker"
        or saved["failure"] is not None
        or saved["source_sha256"] != sha(saved["source"]["sha256"])
        or saved["config"] != inputs.config_inputs(root)
        or saved["code_checks"] != checked
        or saved["software_training_attempted"] is not True
        or saved["software_training_performed"] is not True
        or any(
            saved[k] is not False
            for k in (
                "poker_training_performed",
                "reference_constructed",
                "long_run_admitted",
            )
        )
        or type(saved["seconds"]) not in (int, float)
        or not 0 <= saved["seconds"] < 180
        or any(
            type(saved["completed_" + k]) is not int or saved["completed_" + k] != n
            for k, n in dict(
                captures=144, masses=96, checkpoints=72, rows=144, fixed_matches=1152
            ).items()
        )
    ):
        raise ArithmeticError("incomplete/mislabeled full tiny own proof")
    rebuilt = dict(saved)
    gather(rebuilt)
    if any(
        rebuilt[k] != saved[k]
        for k in ("captures", "masses", "checkpoints", "rows", "fixed_matches")
    ):
        raise ArithmeticError("tiny rows differ from production event collection")
    if len(saved["batches"]) != 2 or any(
        b["execution"] != "SEQUENTIAL_FIXTURE_EVENT_ROUTES_NOT_SPAWNED_WORKERS"
        for b in saved["batches"]
    ):
        raise ArithmeticError("tiny fixture cannot claim actual spawned workers")
    deadline = deadline or Deadline(180)
    if sha(saved["fixture_inputs"]) != saved["fixture_inputs_sha256"]:
        raise ArithmeticError("archived tiny source inputs changed")
    fixture = restore(saved["fixture_inputs"])
    proof = replay_archives(
        path,
        saved,
        fixture.manifest,
        fixture.expected,
        lambda _: toy_context(),
        fixture.fixed,
        fixture.right,
        fixture.right_fixed,
        deadline,
    )
    from poker_ai.evaluation.prefix_capture_software import compare_proofs

    actual, recorded = dict(proof), dict(saved["replay"])
    actual["maximum_error_fixture_chips"] = actual.pop("maximum_error_chips")
    recorded["maximum_error_fixture_chips"] = recorded.pop("maximum_error_chips")
    compare_proofs(actual, recorded)
    return saved, fixture, proof
