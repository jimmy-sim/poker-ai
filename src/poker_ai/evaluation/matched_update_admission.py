"""Checked, published software/forecast admission for this bounded known-game study."""

import json
from pathlib import Path
from typing import Any

from poker_ai.evaluation import matched_update_code_gate as gate
from poker_ai.evaluation import matched_update_inputs as inputs
from poker_ai.evaluation import matched_update_overhead as overhead
from poker_ai.evaluation import matched_update_profile as profile
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import Deadline, digest
from poker_ai.solver_validation.matched_update_audit import published
from poker_ai.solver_validation.matched_updates import read as read_native

PATH = profile.FOLDER + "admission.json"


def expected(root: Path, *, clean: bool) -> dict[str, Any]:
    config = inputs.config_inputs(root)
    checked = gate.require(root, clean=clean)
    proof = profile.software_proof(root)
    timing, _ = profile.read(root, root / profile.PROFILE)
    own, _ = overhead.read(root, root / profile.OVERHEAD, Deadline(900))
    native_path = root / profile.OVERHEAD_NATIVE
    native = read_native(root, native_path, root / profile.OVERHEAD, own)
    raw_native = json.loads(native_path.read_text())
    if (
        any(
            h != checked["source_sha256"]
            for h in (
                proof["source_sha256"],
                timing["source_sha256"],
                own["source_sha256"],
                raw_native["source_sha256"],
            )
        )
        or timing["status"] != "completed_own_profile_native_pending"
        or timing["forecast"]["strict_below7200"] is not True
        or not timing["forecast"]["guarded_own_seconds"] < 7200
        or not 2 * raw_native["seconds"] < 900
        or native["maximum_error_chips"] > 1e-9
    ):
        raise ArithmeticError(
            "full matched-update software/forecast/native gate failed"
        )
    paths = (
        inputs.CONFIG,
        gate.CHECKS,
        profile.SOFTWARE,
        profile.SOFTWARE_NATIVE,
        profile.PROFILE,
        profile.OVERHEAD,
        profile.OVERHEAD_NATIVE,
    )
    hashes = {p: digest(root / p) for p in paths}
    hashes.update(timing["source_inputs"])
    # Bind every immutable own archive in both the tiny proof and old corpus.
    for key, saved in (
        (profile.SOFTWARE, json.loads((root / profile.SOFTWARE).read_text())),
        (profile.OVERHEAD, own),
    ):
        for name in ("captures", "masses", "details"):
            relative = str(Path(key).parent / saved[name + "_file"])
            hashes[relative] = digest(root / relative)
    return dict(
        status="admitted_complete_known_game_matched_update_only",
        source_sha256=checked["source_sha256"],
        checked_commit=checked["ci"]["checked_commit"],
        ci_run=checked["ci"]["run_id"],
        input_sha256=hashes,
        guarded_own_seconds=timing["forecast"]["guarded_own_seconds"],
        measured_old_policy_overhead_seconds=own["seconds"],
        guarded_native_seconds=2 * raw_native["seconds"],
        maximum_own_seconds=config["maximum_own_seconds"],
        maximum_native_seconds=config["maximum_native_seconds"],
        contexts=24,
        targets=48,
        profiles=144,
        ledgers=96,
        fixed_targets=1152,
        scope=(
            "all declared contexts/seeds/readouts; known-game second compute axis; "
            "no pure variance/default/fresh/global admission"
        ),
        new_agent_default=False,
        fresh_global_admission=False,
    )


def record(root: Path) -> dict[str, Any]:
    return expected(root, clean=True)


def require_admission(root: Path, binding: str) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads((root / PATH).read_text())
    if saved["source_sha256"] != binding or saved["source_sha256"] != sha(
        gate.require(root, clean=False)["source"]["sha256"]
    ):
        raise ArithmeticError("real study differs from checked admitted source")
    published(root, root / PATH)
    if not same(saved, expected(root, clean=False)):
        raise ArithmeticError("complete published matched-update admission changed")
    return saved
