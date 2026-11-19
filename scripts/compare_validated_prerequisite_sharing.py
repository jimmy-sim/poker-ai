"""One fixed complete ordinary/validated-share pair using original loaders."""

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any
from unittest.mock import patch

import compare_context_reuse as previous
import profile_checkpoint_cpu as supervisor
from audit_receipt_consumer_mutation import revision
from prerequisite_identity_support import pinned_bytes
from prove_validated_prerequisite_sharing import source_checks
from receipt_consumer_mutation_support import Capture, instrument
from validated_prerequisite_sharing_support import ValidatedShare, read_saved

from poker_ai.evaluation import batch_current_inputs as current
from poker_ai.evaluation.averaging_history_inputs import HistoryInputs

ROOT = Path(__file__).resolve().parents[1]
OWN = ROOT / "results/reduced-batch-study/own.json"
PROOF = ROOT / "results/validated-sharing-count-gate/own/manifest.json"
PREDECESSOR_IDENTITY = (
    "ccd8e493a22a04dd0514c180d234b3ee4b62df68531eb1ddda516ea7175a7185"
)
ORDER = ("ordinary", "validated_share")
CHILD_LIMIT = 900
OUTER_LIMIT = 1800
FAILURE_SAVE_LIMIT = 120
CAPS = dict(
    child_seconds=CHILD_LIMIT,
    failure_save_seconds=FAILURE_SAVE_LIMIT,
    own_proof_seconds=180,
    shared_seconds=OUTER_LIMIT,
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic(path: Path, value: Any) -> None:
    previous.atomic(path, value)


def own_published() -> dict[str, Any]:
    """Authenticate already published own raw bytes; never rerun their reader."""
    from compact_suit.admission import published

    published(ROOT, PROOF)
    manifest: dict[str, Any] = json.loads(PROOF.read_bytes())
    if manifest["status"] != "published_own_proof" or set(manifest["files"]) != {
        "child.json",
        "child.log",
        "outer.json",
    }:
        raise ArithmeticError("published complete own proof required")
    checked = source_checks()
    if manifest["checked_source_commit"] != checked["checked_commit"]:
        raise ArithmeticError("own proof source differs from checked source")
    folder = PROOF.parent
    for name, metadata in manifest["files"].items():
        published(ROOT, folder / name)
        raw = (folder / name).read_bytes()
        if (
            len(raw) != metadata["bytes"]
            or hashlib.sha256(raw).hexdigest() != metadata["sha256"]
        ):
            raise ArithmeticError("published own proof member changed")
    child = json.loads((folder / "child.json").read_bytes())
    outer = json.loads((folder / "outer.json").read_bytes())
    rows = child["observations"]
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", manifest["proof_head"], "HEAD"],
        cwd=ROOT,
        check=True,
    )
    if (
        child["status"] != "seven_original_loaders_six_validated_substitutions_complete"
        or child["checked_source_commit"] != checked["checked_commit"]
        or child["head"] != manifest["proof_head"]
        or child["dirty"] is not False
        or (child["python"], child["numpy"]) != ("3.11.17", "2.4.6")
        or child["lock_sha256"] != digest(ROOT / "uv.lock")
        or child["input_sha256"] != pinned_bytes(ROOT)
        or child["own_sha256"] != digest(OWN)
        or child["saved_status"] != "completed_own_native_pending"
        or child["saved_own_replay"]["status"]
        != "all_batch_profiles_and_raw_observations_replayed"
        or child["saved_own_replay"]["maximum_error_chips"] != 0
        or child["saved_own_replay"]["maximum_error_unitless"] != 0
        or child["reference_constructed"] is not False
        or child["new_postflop_training_performed"] is not False
        or (
            child["saved_batch_count"],
            child["saved_row_count"],
            child["saved_mass_count"],
            child["saved_current_count"],
        )
        != (2, 480, 432, 216)
        or len(rows) != 7
        or [row["kind"] for row in rows] != ["nested"] * 6 + ["direct"]
        or [row["substituted"] for row in rows] != [False] + [True] * 6
        or any(
            row["fresh"] != row["load"] or row["after_archive"] != row["load"]
            for row in rows
        )
        or any(row["after_caller"] != row["load"] for row in rows[:6])
        or outer["status"] != "passed"
        or outer["returncode"] != 0
        or not 0 < child["elapsed_seconds"] < outer["outer_elapsed_seconds"] < 180
    ):
        raise ArithmeticError("published own proof failed original boundaries")
    return manifest


def complete_counts(identity: dict[str, Any]) -> bool:
    """Accept complete profile/condition lists only at their pinned sizes."""
    return (
        type(identity["profiles"]) is list
        and len(identity["profiles"]) == 432
        and type(identity["fixed_conditions"]) is list
        and len(identity["fixed_conditions"]) == 1152
    )


@contextmanager
def observed_archives(output: Path, mode: str) -> Iterator[list[Capture]]:
    """Patch the one importing alias and restore it after both archive roots."""
    if mode not in ORDER:
        raise ArithmeticError("fixed ordinary/validated-share mode required")
    original = vars(current)["read_saved"]
    captures: list[Capture] = []

    def selected(*args: Any, **kwargs: Any) -> tuple[dict[str, Any], HistoryInputs]:
        if len(args) != 2 or kwargs or len(captures) >= 2:
            raise ArithmeticError("two original positional archive reads required")
        root, path = args
        if root != ROOT or path != OWN:
            raise ArithmeticError("original own archive path changed")
        index = len(captures)
        path_out = output / f"archive-{index}.json"

        def publish(rows: list[dict[str, Any]]) -> None:
            atomic(path_out, dict(index=index, mode=mode, rows=rows))

        capture: Capture = (
            ValidatedShare(publish) if mode == "validated_share" else Capture(publish)
        )
        captures.append(capture)
        if isinstance(capture, ValidatedShare):
            result = read_saved(root, path, capture)
        else:
            with instrument(capture):
                result = original(root, path)
            if result[1] is not capture.objects[-1]:
                raise ArithmeticError("ordinary archive returned a different graph")
            capture.finish()
        publish(capture.rows)
        return result

    with patch.object(current, "read_saved", selected):
        try:
            yield captures
        finally:
            if vars(current)["read_saved"] is not selected:
                raise ArithmeticError("archive alias changed during pair")
    if vars(current)["read_saved"] is not original:
        raise ArithmeticError("archive alias not restored")


def child(output: Path, mode: str) -> None:
    origin = time.perf_counter()
    head, dirty = revision()
    state: dict[str, Any] = dict(
        status="running",
        mode=mode,
        head=head,
        dirty=dirty,
        pid=os.getpid(),
        thread=threading.get_ident(),
        python=sys.version.split()[0],
        reference_output_used_in_training=False,
        new_postflop_training_performed=False,
        admission_evidence=False,
    )
    atomic(output / "child.json", state)
    try:
        if mode not in ORDER or state["python"] != "3.11.17" or dirty:
            raise ArithmeticError("clean locked Python 3.11 complete pair required")
        import numpy as np

        if np.__version__ != "2.4.6":
            raise ArithmeticError("locked NumPy 2.4.6 required")
        checked = source_checks()
        own = own_published()
        pins = pinned_bytes(ROOT)
        original_own = digest(OWN)
        c, predecessor_source = previous.binding(ROOT)
        if c["caps"] != CAPS:
            raise ArithmeticError("original complete scientific caps changed")
        previous.checked(ROOT, predecessor_source)
        supervisor.runtime(c)
        from compact_suit import cli  # noqa: F401
        from profile_coarse_reader import clock

        from poker_ai.reproducibility import runtime_environment

        state.update(
            checked_source_commit=checked["checked_commit"],
            own_manifest_sha256=digest(PROOF),
            own_source_commit=own["checked_source_commit"],
            predecessor_source_sha256=predecessor_source["fingerprint"],
            environment=runtime_environment(),
            lock_sha256=digest(ROOT / "uv.lock"),
            input_sha256=pins,
            own_sha256=original_own,
        )
        atomic(output / "child.json", state)
        os.environ["POKER_COMPACT_OPPONENT_STARTED"] = repr(origin)
        state["body_before"] = clock()
        with observed_archives(output, mode) as captures:
            result = previous.execute_child(ROOT, output, c, enabled=False)
        state["body_after"] = clock()
        observed = result.pop("observer")
        summaries = previous.validate_observed(
            observed,
            enabled=False,
            pid=state["pid"],
            thread=state["thread"],
            config=c,
        )
        identity = result["identity"]
        if (
            len(captures) != 2
            or [len(capture.rows) for capture in captures] != [7, 7]
            or [r["scope"] for r in observed["replays"]] != c["expected"]["read_scopes"]
            or not complete_counts(identity)
            or len(identity["worker_summaries"]) != 3
            or identity["reference_actions_exported"] is not False
            or identity["training_performed"] is not False
            or result["base_admission_rejected"] is not True
            or pinned_bytes(ROOT) != pins
            or digest(OWN) != original_own
            or source_checks() != checked
            or revision() != (head, False)
        ):
            raise ArithmeticError("complete reader scope, source or input changed")
        if mode == "validated_share" and any(
            [row["substituted"] for row in capture.rows] != [False] + [True] * 6
            for capture in captures
        ):
            raise ArithmeticError("validated substitutions incomplete")
        after_c, after_source = previous.binding(ROOT, clean=False)
        if after_c != c or after_source["sha256"] != predecessor_source["sha256"]:
            raise ArithmeticError("predecessor scientific source changed")
        state.update(
            status="complete_validated_share_pair_child",
            result=result,
            summaries=summaries,
            archive_roots=len(captures),
            original_loads=sum(len(capture.rows) for capture in captures),
            donor_substitutions=12 if mode == "validated_share" else 0,
            context_identity_sha256=observed["state"]["rows"][1]["collection_sha256"],
            complete_body_parent_cpu_seconds=state["body_after"]["cpu"]
            - state["body_before"]["cpu"],
            seconds=time.perf_counter() - origin,
            reference_constructed=True,
        )
        atomic(output / "child.json", state)
    except BaseException as error:
        state.update(
            status="failed_retained",
            failure=dict(type=type(error).__name__, reason=str(error)),
            seconds=time.perf_counter() - origin,
        )
        atomic(output / "child.json", state)
        raise


def pair_identity(children: list[dict[str, Any]]) -> dict[str, Any]:
    if (
        len(children) != 2
        or [child["mode"] for child in children] != list(ORDER)
        or any(
            child["status"] != "complete_validated_share_pair_child"
            for child in children
        )
        or any(
            child["archive_roots"] != 2 or child["original_loads"] != 14
            for child in children
        )
        or children[0]["donor_substitutions"] != 0
        or children[1]["donor_substitutions"] != 12
        or children[0]["pid"] == children[1]["pid"]
        or children[0]["input_sha256"] != children[1]["input_sha256"]
        or children[0]["context_identity_sha256"]
        != children[1]["context_identity_sha256"]
        or previous.canonical(children[0]["result"]["identity"])
        != previous.canonical(children[1]["result"]["identity"])
    ):
        raise ArithmeticError("complete ordinary/validated-share identity failed")
    identity = hashlib.sha256(
        previous.canonical(children[0]["result"]["identity"])
    ).hexdigest()
    if identity != PREDECESSOR_IDENTITY:
        raise ArithmeticError("published predecessor complete identity changed")
    return dict(
        status="exact_complete_result_and_work_identity", identity_sha256=identity
    )


def pair(output: Path) -> None:
    started = time.perf_counter()
    if (
        output.exists()
        or output.is_symlink()
        or not output.is_relative_to(ROOT / "results/runs")
    ):
        raise FileExistsError("fresh ignored complete pair output required")
    output.mkdir(parents=True)
    state: dict[str, Any] = dict(status="running", order=list(ORDER), measurements=[])
    atomic(output / "pair.json", state)
    try:
        source_checks()
        own_published()
        if previous.contract(ROOT)["caps"] != CAPS:
            raise ArithmeticError("original complete scientific caps changed")
        for mode in ORDER:
            remaining = OUTER_LIMIT - (time.perf_counter() - started)
            if remaining <= 0:
                raise TimeoutError("unchanged shared1800-second cap exhausted")
            measurement = supervisor.supervise(
                [sys.executable, __file__, "--child", mode, str(output / mode)],
                output / mode,
                min(CHILD_LIMIT, remaining),
            )
            state["measurements"].append(measurement)
            atomic(output / "pair.json", state)
            if measurement["returncode"] != 0:
                raise ArithmeticError("retained failed complete child")
        state.update(
            pair_identity(
                [
                    json.loads((output / mode / "child.json").read_bytes())
                    for mode in ORDER
                ]
            )
        )
        state["seconds"] = time.perf_counter() - started
        if state["seconds"] >= OUTER_LIMIT:
            raise TimeoutError("complete pair exceeded original shared cap")
        atomic(output / "pair.json", state)
    except BaseException as error:
        failure_started = time.perf_counter()
        state.update(
            status="failed_retained",
            failure_kind=type(error).__name__,
            seconds=time.perf_counter() - started,
        )
        atomic(output / "pair.json", state)
        if time.perf_counter() - failure_started >= FAILURE_SAVE_LIMIT:
            raise TimeoutError("failure-save120-second limit exhausted") from error
        raise


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--pair":
        pair(Path(sys.argv[2]).resolve())
    elif len(sys.argv) == 4 and sys.argv[1] == "--child":
        child(Path(sys.argv[3]).resolve(), sys.argv[2])
    else:
        raise SystemExit(
            "usage: compare_validated_prerequisite_sharing.py --pair OUTPUT"
        )


if __name__ == "__main__":
    main()
