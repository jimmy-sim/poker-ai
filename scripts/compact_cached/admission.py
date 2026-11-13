"""Complete checked-source, software, fixed forecast and published study permit.

No gate in this module learns or constructs an independent reference. All
receipts are source-bound; a tiny software proof never admits poker by itself.
"""

import json
import math
import subprocess
from pathlib import Path
from typing import Any

from compact_cached.cache import check_execution
from compact_cached.clock import measurement
from compact_cached.contract import contract, input_pins
from compact_cached.publication import committed, publication
from compact_cached.source import check_source, source
from poker_ai.evaluation.compact_opponent_contexts import build_game
from poker_ai.evaluation.diagnostic_receipts import checks as six_checks
from poker_ai.evaluation.frozen_batch_inputs import paths as old_paths
from poker_ai.evaluation.opponent_learning_design import COST, REAL, WORK, Design
from poker_ai.evaluation.opponent_learning_workers import gather_independent
from poker_ai.evaluation.private_prefix_journal import validate as validate_journal
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.compact_full_artifacts import commit_sources
from poker_ai.postflop.learning_artifacts import sha
from poker_ai.postflop.parallel_profile import same
from poker_ai.postflop.river_study import digest
from poker_ai.solver_validation.opponent_learning import FORMAT as NATIVE_FORMAT
from poker_ai.solver_validation.opponent_learning import validate_rows

FOLDER = "results/compact-cached-learning/"
CHECKS = FOLDER + "checks.json"
ADMISSION = FOLDER + "admission.json"


def published(root: Path, path: Path) -> None:
    committed(root, path)
    result = subprocess.run(
        ["git", "-C", str(root), "merge-base", "--is-ancestor", "HEAD", "@{upstream}"],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ArithmeticError("push complete gate evidence before advancing")


def require_checks(root: Path) -> dict[str, Any]:
    current = source(root)
    path = root / CHECKS
    six_checks(root, path, current)
    published(root, path)
    saved: dict[str, Any] = json.loads(path.read_text())
    for row in saved["checks"]:
        committed(root, root / row["log"]["file"])
    hosted = next(r for r in saved["checks"] if r["role"] == "hosted")
    return dict(
        saved,
        source_sha256=current["fingerprint"],
        ci=dict(checked_commit=hosted["checked_commit"], run_id=hosted["run_id"]),
    )


def all_own_costs_published(root: Path) -> list[dict[str, Any]]:
    """All THREE complete own cost publications precede ANY native cost use.

    Check clocks, source/config, raw archives/reports and pushed Git bytes here.
    Mathematical replay of each cost repetition occurs during creation and the
    complete forecast; this checkpoint does not relabel hashes as another replay.
    """
    result = []
    for repetition in (0, 1, 2):
        path = root / FOLDER / f"cost/{repetition}/own.json"
        saved = json.loads(path.read_text())
        check_execution(root, saved)
        measurement(path, "cost-own")
        if (
            saved["scope"] != COST
            or type(saved["repetition"]) is not int
            or saved["repetition"] != repetition
            or not same(saved["config"], contract(root))
            or saved["poker_training_performed"] is not False
            or type(saved["actual_poker_training_work"]) is not int
            or saved["actual_poker_training_work"] != 0
            or not same(saved["manifest"], Design(COST, WORK).manifest())
        ):
            raise ArithmeticError(
                "publish all three complete own-only cost grids first"
            )
        result.append(publication(root, path, saved))
    return result


def native_receipt(
    root: Path, path: Path, own_path: Path, own: dict[str, Any], operation: str
) -> dict[str, Any]:
    saved: dict[str, Any] = json.loads(path.read_text())
    check_execution(root, saved)
    check_source(root, saved["source"])
    measurement(path, operation)
    if (
        saved["format"] != NATIVE_FORMAT
        or saved["status"] != "completed_scalar_comparison"
        or saved["failure"] is not None
        or saved["source_sha256"] != own["source_sha256"]
        or not same(saved["source"]["sha256"], own["source"]["sha256"])
        or saved["own_sha256"] != digest(own_path)
        or saved["reference_constructed"] is not True
        or saved["reference_output_used_in_training"] is not False
        or saved["long_run_admitted"] is not False
        or saved["new_agent_default"] is not False
        or saved["fresh_global_admission"] is not False
        or saved["publication"]["own_sha256"] != digest(own_path)
        or saved["study_id"] != contract(root)["study_id"]
        or not same(saved["config"], contract(root))
    ):
        raise ArithmeticError("complete source-bound scalar comparison required")
    if operation == "cost-audit":
        validate_cost_publications(root, saved)
    verified = validate_rows(saved, own)
    if not same(verified, saved["verification"]):
        raise ArithmeticError("native whole-grid verification receipt changed")
    gathered = gather_independent(saved["native_batch"], own)
    if any(not same(saved[k], v) for k, v in gathered.items()):
        raise ArithmeticError("native summary differs from its complete raw workers")
    groups = {
        3: saved["events"],
        **{w["slot"]: w["messages"] for w in saved["native_batch"]["workers"]},
    }
    validate_journal(
        path.with_name(saved["journal"]["file"]),
        saved["journal"],
        saved["source_sha256"],
        groups,
    )
    # The installed license record is fixed by the same pinned config.
    license = saved["license"]
    c = contract(root)
    if (
        license["sha256"] != c["native_reference"]["license_sha256"]
        or not license["installed_license_files"]
        or license["previously_read_record"] != "docs/solver_validation.md"
    ):
        raise ArithmeticError("native pinned license identity changed")
    published(root, path)
    for name in (saved["journal"]["file"], saved["complete_command"]["child_file"]):
        committed(root, path.with_name(name))
    return saved


def validate_cost_publications(root: Path, native: dict[str, Any]) -> None:
    """Every declared pre-native own-publication member is checked again."""
    witnesses = native["all_own_cost_publications_before_native"]
    if not isinstance(witnesses, list) or len(witnesses) != 3:
        raise ArithmeticError("all three pre-native own publications required")
    for repetition, saved in enumerate(witnesses):
        path = root / FOLDER / f"cost/{repetition}/own.json"
        own = json.loads(path.read_text())
        expected = publication(root, path, own)
        if (
            set(saved) != set(expected)
            or saved["own_sha256"] != digest(path)
            or saved["source_sha256"] != native["source_sha256"]
            or saved["own_commit"] != native["publication"]["own_commit"]
            or saved["upstream_commit"] != native["publication"]["upstream_commit"]
            or saved["locally_recorded_upstream"]
            != native["publication"]["locally_recorded_upstream"]
            or saved["scope"] != expected["scope"]
            or not same(
                saved["published_input_sha256"], expected["published_input_sha256"]
            )
        ):
            raise ArithmeticError("pre-native own cost publication binding changed")


def software(root: Path, own: dict[str, Any]) -> dict[str, Any]:
    checked = require_checks(root)
    check_execution(root, own)
    own_path = root / FOLDER / "software/own.json"
    native_path = own_path.with_name("native.json")
    from poker_ai.evaluation.opponent_learning_design import TOY

    if (
        own["scope"] != TOY
        or own["source_sha256"] != checked["source_sha256"]
        or own["poker_training_performed"] is not False
        or own["initialized_training_paths"] != 30
        or own["own_replay"]["raw_profiles"] != 324
        or own["own_replay"]["raw_ledgers"] != 216
        or own["own_replay"]["fixed_conditions"] != 1152
    ):
        raise ArithmeticError("complete checked tiny software proof required")
    native = native_receipt(root, native_path, own_path, own, "software-audit")
    return dict(
        own_file=str(own_path.relative_to(root)),
        own_sha256=digest(own_path),
        native_file=str(native_path.relative_to(root)),
        native_sha256=digest(native_path),
        source_sha256=own["source_sha256"],
        shared_seconds=native["complete_command"]["shared_seconds"],
        status="complete_tiny_software_only_not_poker_admission",
    )


def training_forecast(original: dict[str, Any]) -> dict[str, Any]:
    """ALL24 complete old B4 paths; full10m charge for every new path."""
    paths = old_paths(original["config"])
    rows = [
        dict(r, case=paths[r["index"]])
        for b in original["batches"]
        for w in b["workers"]
        for r in w["messages"]
        if r.get("kind") == "cell"
        and r.get("phase") == "trained"
        and 24 <= r.get("index", -1) < 48
    ]
    if (
        len(rows) != 24
        or {r["index"] for r in rows} != set(range(24, 48))
        or any(r["case"]["batch_size"] != 4 for r in rows)
    ):
        raise ArithmeticError("all24 original complete B4 timing paths required")
    for row in rows:
        if (
            type(row["seconds"]) not in (int, float)
            or not math.isfinite(row["seconds"])
            or row["seconds"] <= 0
            or type(row["work"]) is not int
            or row["work"] < 10_000_000
            or type(row["iteration"]) is not int
            or row["iteration"] < 1
            or type(row["initialization_seconds"]) not in (int, float)
            or not 0 <= row["initialization_seconds"] <= row["seconds"]
        ):
            raise ArithmeticError("original timing excludes complete work or setup")
    design = Design(REAL, WORK)
    estimates = []
    for i in range(30):
        path = design.path(i)
        selected = [r for r in rows if r["case"]["spot_file"] == path["spot_file"]]
        if len(selected) != 12:
            raise ArithmeticError("all12 old complete timings per game required")
        estimates.append(max(r["seconds"] for r in selected))
    assignments = partition(30, 3)
    seconds = [math.fsum(estimates[i] for i in group) for group in assignments]
    return dict(
        original_complete_paths=rows,
        path_seconds=estimates,
        assignments=assignments,
        worker_seconds=seconds,
        T=max(seconds),
        half_budget_discount_applied=False,
    )


def kernel_geometry(root: Path) -> dict[str, Any]:
    """No changed historical kernel or mixed dense array larger than old exact."""
    original = json.loads((root / "results/reduced-batch-study/own.json").read_text())
    old = original["source"]
    commit_sources(root, old["git_commit"], old["sha256"])
    layouts = []
    for game in (0, 1):
        context = build_game(root, game)
        fine = context.fine
        for kind in ("coarse", "mixed0", "mixed1", "fine"):
            tree = context.tree(kind)
            if (
                tree.legal.shape[1] != fine.legal.shape[1]
                or len(tree.keys) > len(fine.keys)
                or tree.legal.nbytes > fine.legal.nbytes
                or len(tree.player) != len(fine.player)
            ):
                raise ArithmeticError(
                    "new mixed layout exceeds historical exact arrays"
                )
            layouts.append(
                dict(
                    game=game,
                    kind=kind,
                    rows=len(tree.keys),
                    dense_table_bytes=tree.legal.nbytes,
                    exact_rows=len(fine.keys),
                    exact_dense_table_bytes=fine.legal.nbytes,
                )
            )
    return dict(
        historical_commit=old["git_commit"],
        historical_source_sha256=sha(old["sha256"]),
        unchanged_named_dependencies=len(old["sha256"]),
        layouts=layouts,
        total_process_memory_saving_established=False,
    )


def forecast(
    training: dict[str, Any],
    own_costs: list[dict[str, Any]],
    native_costs: list[dict[str, Any]],
) -> dict[str, Any]:
    for rows in (own_costs, native_costs):
        if (
            len(rows) != 3
            or not same([r["repetition"] for r in rows], [0, 1, 2])
            or any(r["scope"] != COST for r in rows)
        ):
            raise ArithmeticError("all three complete fixed cost repetitions required")
        if any(
            type(r["complete_command"]["seconds"]) not in (int, float)
            or not math.isfinite(r["complete_command"]["seconds"])
            or not 0 < r["complete_command"]["seconds"] < 900
            for r in rows
        ):
            raise ArithmeticError(
                "every complete forecast command must fit its own cap"
            )
    D = max(r["complete_command"]["seconds"] for r in own_costs)
    N = max(r["complete_command"]["seconds"] for r in native_costs)
    T = training["T"]
    if any(
        type(x) not in (int, float) or not math.isfinite(x) or x <= 0 for x in (T, D, N)
    ):
        raise ArithmeticError("forecast requires complete finite positive timings")
    own = 2 * (2 * T + D + 600)
    native = 2 * (N + 60)
    return dict(
        training=training,
        own_repetition_seconds=[r["complete_command"]["seconds"] for r in own_costs],
        native_repetition_seconds=[
            r["complete_command"]["seconds"] for r in native_costs
        ],
        T=T,
        D=D,
        N=N,
        guarded_own_seconds=own,
        guarded_native_seconds=native,
        strict_own_pass=own < 7200,
        strict_native_pass=native < 900,
        long_run_admitted=False,
        new_agent_default=False,
        fresh_global_admission=False,
    )


def permit(root: Path, saved_forecast: dict[str, Any]) -> dict[str, Any]:
    check_execution(root, saved_forecast)
    checked = require_checks(root)
    path = root / FOLDER / "forecast.json"
    published(root, path)
    if (
        not same(saved_forecast, json.loads(path.read_text()))
        or saved_forecast["status"] != "complete_fixed_cost_forecast"
        or saved_forecast["failure"] is not None
        or saved_forecast["source_sha256"] != checked["source_sha256"]
        or saved_forecast["forecast"]["strict_own_pass"] is not True
        or saved_forecast["forecast"]["strict_native_pass"] is not True
    ):
        raise ArithmeticError("complete checked published forecast did not pass")
    measurement(path, "forecast")
    f = saved_forecast["forecast"]
    # Reconstruct timing arithmetic from ALL six original complete command
    # receipts. Archives/scalars were replayed in the published forecast; bind
    # every byte again here without pretending to execute those old trajectories.
    recomputed, required_hashes = sealed_costs(root)
    if not same(recomputed, f) or not same(
        required_hashes, saved_forecast["verified_input_sha256"]
    ):
        raise ArithmeticError("forecast changed its full repetition/input inventory")
    if (
        not same(f["guarded_own_seconds"], 2 * (2 * f["T"] + f["D"] + 600))
        or not same(f["guarded_native_seconds"], 2 * (f["N"] + 60))
        or not f["guarded_own_seconds"] < 7200
        or not f["guarded_native_seconds"] < 900
    ):
        raise ArithmeticError("fixed conservative forecast arithmetic changed")
    hashes = dict(saved_forecast["verified_input_sha256"])
    hashes[str(path.relative_to(root))] = digest(path)
    hashes[CHECKS] = digest(root / CHECKS)
    for p, expected in hashes.items():
        if digest(root / p) != expected:
            raise ArithmeticError("complete forecast inputs changed")
        committed(root, root / p)
    return dict(
        status="compact_own_opponent_learning_admitted",
        source_sha256=checked["source_sha256"],
        checked_commit=checked["ci"]["checked_commit"],
        ci_run=checked["ci"]["run_id"],
        # CLI input_sha256 records routine command pins. Keep the wider sealed
        # admission inventory separate so persistence cannot overwrite it.
        permit_input_sha256=hashes,
        maximum_own_seconds=7200,
        maximum_native_seconds=900,
        guarded_own_seconds=f["guarded_own_seconds"],
        guarded_native_seconds=f["guarded_native_seconds"],
        long_run_admitted=True,
        new_agent_default=False,
        fresh_global_admission=False,
        scope="Complete known-game compute permit, not strength or default admission",
    )


def require_admission(root: Path, binding: str) -> dict[str, Any]:
    path = root / ADMISSION
    saved: dict[str, Any] = json.loads(path.read_text())
    check_execution(root, saved)
    published(root, path)
    measurement(path, "admit")
    forecast_path = root / FOLDER / "forecast.json"
    expected = permit(root, json.loads(forecast_path.read_text()))
    if saved["source_sha256"] != binding or any(
        not same(saved.get(k), v) for k, v in expected.items()
    ):
        raise ArithmeticError("complete checked published study permit changed")
    return saved


def sealed_costs(root: Path) -> tuple[dict[str, Any], dict[str, str]]:
    proof_path = root / FOLDER / "software/own.json"
    proof = json.loads(proof_path.read_text())
    software(root, proof)
    hashes = dict(publication(root, proof_path, proof)["published_input_sha256"])
    proof_native = proof_path.with_name("native.json")
    native_proof = json.loads(proof_native.read_text())
    for member in (
        proof_native,
        proof_native.with_name(native_proof["journal"]["file"]),
        proof_native.with_name(native_proof["complete_command"]["child_file"]),
    ):
        hashes[str(member.relative_to(root))] = digest(member)
    own_costs, native_costs = [], []
    for i in (0, 1, 2):
        path = root / f"{FOLDER}cost/{i}/own.json"
        own = json.loads(path.read_text())
        measurement(path, "cost-own")
        if (
            own["scope"] != COST
            or not same(own["repetition"], i)
            or not same(own["manifest"], Design(COST, WORK).manifest())
            or not same(own["actual_poker_training_work"], 0)
            or own["poker_training_performed"] is not False
        ):
            raise ArithmeticError("complete cost-only own repetitions required")
        hashes.update(publication(root, path, own)["published_input_sha256"])
        native_path = path.with_name("native.json")
        native = native_receipt(root, native_path, path, own, "cost-audit")
        if not same(native["repetition"], i):
            raise ArithmeticError("native cost repetition changed")
        for member in (
            native_path,
            native_path.with_name(native["journal"]["file"]),
            native_path.with_name(native["complete_command"]["child_file"]),
        ):
            hashes[str(member.relative_to(root))] = digest(member)
        own_costs.append(own)
        native_costs.append(native)
    hashes.update(input_pins(root))
    original = json.loads((root / "results/reduced-batch-study/own.json").read_text())
    training = training_forecast(original)
    training["kernel_geometry"] = kernel_geometry(root)
    return forecast(training, own_costs, native_costs), hashes
