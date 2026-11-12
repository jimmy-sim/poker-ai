"""No-training frozen-policy diagnosis, immutable own details and replay."""

import json
import math
import time
from pathlib import Path
from typing import Any

from poker_ai.evaluation import compact_fixed_inputs as inputs
from poker_ai.evaluation.compact_sampled_own import (
    no_reference_runtime as old_own_guard,
)
from poker_ai.postflop import compact_full_artifacts as files
from poker_ai.postflop.compact_fixed import (
    detail,
    fixed_identities,
    mix,
    native_check,
    replay_detail,
)
from poker_ai.postflop.compact_full_clock import measurement
from poker_ai.postflop.compact_full_run import check_runtime, runtime
from poker_ai.postflop.learning_artifacts import canonical
from poker_ai.postflop.public_study import peak_rss_bytes
from poker_ai.postflop.river_study import Deadline, digest

FORMAT = "compact-fixed-own-v1"
NATIVE = "compact-fixed-native-v1"


def validate_native(
    own: dict[str, Any], native: dict[str, Any], own_sha: str, reference: dict[str, Any]
) -> None:
    if (
        native["format"] != NATIVE
        or native["status"] != "completed"
        or native["failure"] is not None
        or native["own_sha256"] != own_sha
        or native["scope"] != own["scope"]
        or native["source"]["fingerprint"] != own["source"]["fingerprint"]
        or native["reference"] != reference
        or native["installed_license"]["sha256"] != reference["license_sha256"]
        or native["installed_license"]["previously_read_record"]
        != "docs/solver_validation.md"
        or native["reference_output_used_in_training"] is not False
        or any(
            native[k] is not False
            for k in ("new_training", "actual_admission", "fresh_global_admission")
        )
    ):
        raise ArithmeticError("complete scalar-only diagnostic audit required")
    originals = {inputs.identity(r): r for r in own["rows"]}
    rows = native["comparisons"]
    ids = [inputs.identity(r) for r in rows]
    if (
        len(own["rows"]) != 144
        or len(originals) != 144
        or len(ids) != 144
        or len(set(ids)) != 144
        or set(ids) != set(originals)
    ):
        raise ArithmeticError("all144joint/288target native comparisons required")
    for row in rows:
        old = originals[inputs.identity(row)]
        if row["detail_sha256"] != old["receipt"]["sha256"]:
            raise ArithmeticError("native own detail binding changed")
        native_check(
            old,
            {k: row[k] for k in ("native_metrics", "responses", "maximum_error_chips")},
        )


def verify_data(
    root: Path, path: Path, saved: dict[str, Any], *, parents_checked: bool = False
) -> dict[str, Any]:
    if saved["scope"] not in ("software", "real"):
        raise ArithmeticError("invalid diagnostic scope")
    software = saved["scope"] == "software"
    inputs.check_source(root, saved["source"])
    check_runtime(saved["runtime"], real=not software)
    if not parents_checked and canonical(
        inputs.replay_sources(root, software)
    ) != canonical(saved["parents"]):
        raise ArithmeticError("historical source/raw replay changed")
    rows = saved["rows"]
    ids = [inputs.identity(r) for r in rows]
    if (
        len(ids) != 144
        or len(set(ids)) != 144
        or set(ids) != inputs.expected(root, software)
        or saved["new_training"] is not False
        or saved["native_constructed"] is not False
        or saved["actual_admission"] is not False
        or saved["fresh_global_admission"] is not False
    ):
        raise ArithmeticError("complete144-grid/no-training flags required")
    lookup = {inputs.identity(r): r for r in rows}
    counts = 0
    for index, pair in enumerate(inputs.pairs(root, software)):
        context = pair.context
        for mode in inputs.config(root)["mixtures"]:
            identity = dict(
                spot_file=context.spot_file,
                representation=context.representation,
                seed=pair.seed,
                mixture=mode,
            )
            row = lookup[inputs.identity(identity)]
            if (
                row["receipt"]["file"] != f"{index:02d}-{mode}.json.gz"
                or canonical(row["origins"]) != canonical(pair.origins)
                or canonical(row["binding"]) != canonical(context.binding)
            ):
                raise ArithmeticError(
                    "diagnostic context/selector/source receipt changed"
                )
            raw = files.load_snapshot(path.parent / "details", row["receipt"])
            policy = mix(context, pair.sampled, pair.full, mode)
            replay_detail(context, policy, raw)
            expected = dict(
                **identity,
                binding=context.binding,
                origins=pair.origins,
                receipt=row["receipt"],
                metrics=raw["metrics"],
                responses=raw["responses"],
            )
            if canonical(expected) != canonical(row):
                raise ArithmeticError("detail/manifest scalar or identity mismatch")
            baseline = (
                pair.sampled_metrics
                if mode == "SS"
                else pair.full_metrics
                if mode == "FF"
                else None
            )
            if baseline is not None:
                errors = [
                    abs(
                        row["metrics"]["value_player_zero_chips"]
                        - baseline["value_player_zero_chips"]
                    ),
                    abs(
                        row["metrics"]["exact_exploitability_chips"]
                        - baseline["exploitability_chips"]
                    ),
                ]
                errors.extend(
                    abs(row["responses"][t]["exact_reply_value_chips"] - baseline[k])
                    for t, k in enumerate(
                        ("best_response_zero_chips", "best_response_one_chips")
                    )
                )
                if any(not math.isfinite(e) or e > 1e-9 for e in errors):
                    raise ArithmeticError(
                        "SS/FF no longer reproduces original primary metric"
                    )
            counts += 1
    identities = fixed_identities(rows)
    if canonical(identities) != canonical(saved["fixed_opponent_conditions"]):
        raise ArithmeticError("fixed opponent identities/EV effects changed")
    return dict(
        source_profiles=48,
        logical_profiles=counts,
        target_conditions=2 * counts,
        fixed_opponent_conditions=len(identities),
        maximum_identity_error_chips=max(r["maximum_error_chips"] for r in identities),
        new_training=False,
        native_constructed=False,
        actual_admission=False,
    )


def replay(root: Path, path: Path) -> dict[str, Any]:
    saved = json.loads(path.read_text())
    if (
        saved["format"] != FORMAT
        or saved["status"] != "completed"
        or saved["failure"] is not None
    ):
        raise ArithmeticError("incomplete diagnostic own archive")
    return verify_data(root, path, saved)


def proof(root: Path) -> dict[str, Any]:
    folder = root / inputs.FOLDER / "software"
    op = folder / "own.json"
    np = folder / "native.json"
    own = json.loads(op.read_text())
    native = json.loads(np.read_text())
    measurement(op, "software-own")
    measurement(np, "software-native")
    replay(root, op)
    validate_native(own, native, digest(op), inputs.config(root)["native_reference"])
    inputs.check_source(root, native["source"])
    for path in (
        op,
        np,
        folder / "own-child.json",
        folder / "native-child.json",
        *[folder / "details" / r["receipt"]["file"] for r in own["rows"]],
    ):
        files.published(root, path)
    return dict(
        own=inputs.bound(root, op),
        native=inputs.bound(root, np),
        logical_profiles=144,
        target_conditions=288,
    )


def run(
    root: Path, output: Path, software: bool, checks: Path, started: float
) -> dict[str, Any]:
    if output.exists() or (output.parent / "details").exists():
        raise FileExistsError("retain complete/partial diagnostic")
    cap = 180 if software else 900
    deadline = Deadline(cap)
    deadline.started = started
    cpu = time.process_time()
    saved: dict[str, Any] = dict(
        format=FORMAT,
        status="running",
        failure=None,
        scope="software" if software else "real",
        source=inputs.source(root),
        runtime=runtime(),
        new_training=False,
        native_constructed=False,
        actual_admission=False,
        fresh_global_admission=False,
        rows=[],
        fixed_opponent_conditions=[],
        partial_progress="No work after last persisted row is inferred",
    )

    def persist() -> None:
        saved.update(
            seconds=time.perf_counter() - started,
            cpu_seconds=time.process_time() - cpu,
            peak_process_rss_bytes=peak_rss_bytes(),
        )
        files.atomic(output, saved)

    try:
        old_own_guard()
        persist()
        saved["checks"] = inputs.checks(root, checks)
        check_runtime(saved["runtime"], real=not software)
        if not software:
            saved["software_proof"] = proof(root)
        saved["parents"] = inputs.replay_sources(root, software)
        deadline.check()
        for index, pair in enumerate(inputs.pairs(root, software)):
            context = pair.context
            for mode in inputs.config(root)["mixtures"]:
                deadline.check()
                identity = dict(
                    spot_file=context.spot_file,
                    representation=context.representation,
                    seed=pair.seed,
                    mixture=mode,
                )
                packet = detail(
                    context, mix(context, pair.sampled, pair.full, mode), identity
                )
                receipt = files.write_snapshot(
                    output.parent / "details" / f"{index:02d}-{mode}.json.gz", packet
                )
                saved["rows"].append(
                    dict(
                        **identity,
                        binding=context.binding,
                        origins=pair.origins,
                        receipt=receipt,
                        metrics=packet["metrics"],
                        responses=packet["responses"],
                    )
                )
                persist()
        saved["fixed_opponent_conditions"] = fixed_identities(saved["rows"])
        saved["replay"] = verify_data(root, output, saved, parents_checked=True)
        deadline.check()
        old_own_guard()
        inputs.check_source(root, saved["source"])
        saved["status"] = "completed"
    except (Exception, KeyboardInterrupt) as error:
        saved.update(
            status="incomplete",
            failure=dict(type=type(error).__name__, reason=str(error)),
        )
    finally:
        persist()
    return saved
