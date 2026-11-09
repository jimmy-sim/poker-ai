"""Clearly labeled tiny software fixtures, never Hold'em intervention outcomes."""

import copy
import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation.averaging_history_correctness import (
    software_roundtrip as history_roundtrip,
)
from poker_ai.evaluation.averaging_history_inputs import inputs as history_config
from poker_ai.evaluation.averaging_history_replay import replay_archives
from poker_ai.evaluation.averaging_history_software import (
    software_inputs as history_inputs,
)
from poker_ai.evaluation.window_fallback_inputs import FallbackInputs, inputs
from poker_ai.postflop.river_study import Deadline


def software_inputs(root: Path, folder: Path, deadline: Deadline) -> FallbackInputs:
    """Build a separate nonuniform-Kuhn corpus to exercise the full offline grid.

    The existing toy baseline generator uses tiny toy learning paths. This new
    stage only reads them; no real Hold'em spot or native solver is constructed.
    The explicit fixture marker cannot pass the formal input config validator.
    """
    parent = history_config(root)
    history_roundtrip(parent, folder, "f" * 64, deadline)
    history = history_inputs(parent, deadline)
    path = folder / "own.json"
    saved = json.loads(path.read_text())
    proof, matches = replay_archives(folder, path, saved, history, deadline)
    saved["fixed_matches"] = matches
    config = copy.deepcopy(inputs(root))
    config["status"] = "EXPLICIT_SOFTWARE_FIXTURE_NOT_HOLDEM_RESULTS"
    config["spot_files"] = history.config["spot_files"]
    return FallbackInputs(
        config,
        history,
        saved,
        path,
        proof,
        dict(status="EXPLICIT_SOFTWARE_FIXTURE_NO_NATIVE_AUDIT"),
    )


def software_roundtrip(
    root: Path,
    folder: Path,
    deadline: Deadline,
) -> tuple[FallbackInputs, dict[str, Any], Path]:
    """Complete tiny archive/replay fixture. Formal run readers reject its markers."""
    from poker_ai.evaluation.window_fallback_compute import (
        evaluate_window,
        fixed_targets,
    )
    from poker_ai.evaluation.window_fallback_inputs import windows
    from poker_ai.evaluation.window_fallback_replay import (
        replay_archives as replay_fills,
    )
    from poker_ai.postflop.controlled_checkpoints import write_snapshot
    from poker_ai.postflop.learning_artifacts import sha, write_archive
    from poker_ai.postflop.learning_run import persist

    if folder.exists():
        raise FileExistsError(
            "retain complete/partial explicit fallback software fixture"
        )
    folder.mkdir(parents=True)
    output = folder / "software.json"
    saved: dict[str, Any] = dict(
        scope="EXPLICIT_SOFTWARE_FIXTURE_NOT_HOLDEM_RESULTS",
        status="running",
        failure=None,
        source_sha256="f" * 64,
        rows=[],
        panels=[],
        fixed_matches=[],
        new_postflop_training_performed=False,
    )
    persist(output, saved)
    try:
        data = software_inputs(root, folder / "upstream", deadline)
        scratch = folder / "scratch"
        for window in windows(data, deadline):
            profiles, panel = evaluate_window(window, data.config, "f" * 64, deadline)
            for profile in profiles:
                metadata = profile.metadata
                relative = f"snapshots/{metadata['id']}.json.gz"
                receipt = write_snapshot(
                    scratch / relative,
                    window.context.partition,
                    profile.policy,
                    metadata,
                )
                saved["rows"].append(
                    dict(
                        **metadata,
                        file=relative,
                        receipt=receipt,
                        metadata_sha256=sha(metadata),
                    )
                )
            saved["panels"].append(panel)
            matches, _ = fixed_targets(window, profiles, data, deadline)
            saved["fixed_matches"].extend(matches)
        archive = folder / "own-profiles.jsonl.gz"
        saved["details_sha256"] = write_archive(archive, scratch, saved["rows"])
        saved["details_file"] = archive.name
        saved["own_replay"] = replay_fills(data, output, saved, deadline)
        saved["status"] = "EXPLICIT_SOFTWARE_FIXTURE_COMPLETED_NOT_RESEARCH"
    except BaseException as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
        raise
    finally:
        persist(output, saved)
    return data, saved, scratch
