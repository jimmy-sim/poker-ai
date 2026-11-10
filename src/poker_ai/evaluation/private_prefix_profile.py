"""All144 new short timing prefixes plus complete old-policy cost workload."""

import os
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation.private_prefix_admission import require_software
from poker_ai.evaluation.private_prefix_forecast import forecast
from poker_ai.evaluation.private_prefix_gates import require as require_checks
from poker_ai.evaluation.private_prefix_jobs import timing
from poker_ai.evaluation.private_prefix_journal import Batch, Journal
from poker_ai.evaluation.private_prefix_sources import contract, load, source
from poker_ai.evaluation.private_prefix_worker_checks import complete, partial_cells
from poker_ai.postflop.cell_process import run_batch
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.learning_run import persist
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.reproducibility import runtime_environment


def run(root: Path, path: Path) -> dict[str, Any]:
    from poker_ai.evaluation.private_prefix_run import old

    if path.exists() or path.with_suffix(".tmp").exists():
        raise FileExistsError("retain complete/partial private-prefix profiling")
    started = time.perf_counter()
    config, driver = contract(root)
    current = source(root)
    if current["dirty"] is not False:
        raise ArithmeticError("publish clean checked profiling source")
    env = runtime_environment()
    if env["python"] != "3.11.17" or env["numpy"] != "2.4.6":
        raise ArithmeticError(
            "real short-prefix profiling requires original recorded runtime"
        )
    deadline = Deadline(900)
    deadline.started = started
    saved: dict[str, Any] = dict(
        format="poker-ai-private-prefix-profile-v1",
        status="running",
        failure=None,
        source=current,
        source_sha256=sha(current["sha256"]),
        config=config,
        driver=driver,
        environment=env,
        batch={},
        rows=[],
        forecast=None,
        reference_constructed=False,
        real_short_prefixes=0,
        long_run_admitted=False,
        new_agent_default=False,
        fresh_global_admission=False,
        parent_cpu_started=time.process_time(),
        children_cpu_started=os.times().children_user + os.times().children_system,
    )
    journal = Journal(
        path.with_name(path.stem + "-events.jsonl"),
        saved["source_sha256"],
        "profile_timing",
    )
    saved["batch"] = Batch(journal)
    saved["journal_file"] = journal.path.name
    try:
        persist(path, saved)
        require_checks(root, clean=False)
        saved["software"] = require_software(root)
        sources = load(root)
        try:
            run_batch(
                144,
                3,
                timing,
                dict(
                    root=str(root),
                    binding=saved["source_sha256"],
                    remaining_seconds=900 - (time.perf_counter() - started),
                ),
                deadline,
                saved["batch"],
            )
            events = complete(saved["batch"], 144)
        finally:
            events = partial_cells(saved["batch"])
            saved["rows"] = [e["row"] for e in events if e["phase"] == "timing"]
            saved["rows"].sort(key=lambda r: (r["repeat"], r["index"]))
            saved["real_short_prefixes"] = len(saved["rows"])
            persist(path, saved)
        saved["forecast"] = forecast(saved["rows"], config, saved["source_sha256"])
        if saved["forecast"]["passes"] is not True:
            raise ArithmeticError(
                "fixed full-grid conservative forecast fails7200 gate"
            )
        old_path = path.parent / "overhead/own.json"
        old(
            root,
            old_path,
            sources=sources,
            bound_source=current,
            shared_deadline=deadline,
        )
        saved["old_own_sha256"] = digest(old_path)
        deadline.check()
        saved["status"] = "completed_profile_inputs_not_admission"
    except BaseException as error:
        saved.update(
            status="failed_profile_not_admitted",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        saved["journal"] = journal.close()
        saved["seconds"] = time.perf_counter() - started
        saved["parent_cpu_seconds"] = time.process_time() - saved.pop(
            "parent_cpu_started"
        )
        saved["reaped_children_cpu_seconds"] = (
            os.times().children_user
            + os.times().children_system
            - saved.pop("children_cpu_started")
        )
        persist(path, saved)
    return saved
