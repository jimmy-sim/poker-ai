"""Fail closed on the pinned optional runtime before one complete sharing pair.

The PR #92 candidate and pair runner remain unchanged. This launcher checks
saved and installed metadata only, then invokes that runner exactly once.
"""

import hashlib
import json
import os
import platform
import subprocess
import sys
from importlib.metadata import distribution, version
from pathlib import Path
from typing import Any

import compare_context_reuse as baseline
import compare_validated_prerequisite_sharing as previous
from audit_receipt_consumer_mutation import revision
from prerequisite_identity_support import pinned_bytes

ROOT = Path(__file__).resolve().parents[1]
CHECKS = (
    ROOT / "results/validated-sharing-runtime-preflight/source-checks/manifest.json"
)
SCRIPT = "scripts/launch_validated_sharing_optional.py"
SAVED = (
    "results/compact-sampled/real/own.json",
    "results/compact-full-control/own.json",
)
PYTHON = "3.11.17"
NUMPY = "2.4.6"
NUMBA = "0.68.1"
OPEN_SPIEL = "2.0.2"
LICENSE_SHA256 = "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"
LICENSE_BYTES = 11358


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_checks() -> dict[str, Any]:
    """Require the public six-role qualification of these exact launcher bytes."""
    from compact_suit.admission import published

    published(ROOT, CHECKS)
    saved: dict[str, Any] = json.loads(CHECKS.read_bytes())
    if saved["status"] != "six_roles_qualified_before_optional_pair":
        raise ArithmeticError("published optional launcher qualification required")
    checked = saved["checked_commit"]
    subprocess.run(
        ["git", "merge-base", "--is-ancestor", checked, "HEAD"],
        cwd=ROOT,
        check=True,
    )
    current = (ROOT / SCRIPT).read_bytes()
    original = subprocess.check_output(["git", "show", f"{checked}:{SCRIPT}"], cwd=ROOT)
    if (
        current != original
        or hashlib.sha256(current).hexdigest() != saved["source_sha256"]
    ):
        raise ArithmeticError("qualified optional launcher source changed")
    return saved


def installed(environment: Path) -> dict[str, Any]:
    """Read actual package metadata and complete pinned comparison license."""
    import numpy as np

    provider = distribution("open-spiel")
    licenses = [
        file for file in provider.files or () if str(file).endswith("licenses/LICENSE")
    ]
    if len(licenses) != 1:
        raise ArithmeticError("one installed OpenSpiel license required")
    raw_license = Path(str(provider.locate_file(licenses[0]))).read_bytes()
    return dict(
        python=platform.python_version(),
        numpy=version("numpy"),
        numpy_import=np.__version__,
        numba=version("numba"),
        open_spiel=version("open-spiel"),
        license_bytes=len(raw_license),
        license_sha256=hashlib.sha256(raw_license).hexdigest(),
        interpreter=sys.executable,
        prefix=sys.prefix,
        environment=str(environment),
        uv_project_environment=os.environ.get("UV_PROJECT_ENVIRONMENT"),
        launcher_pythonpath_absent="PYTHONPATH" not in os.environ,
    )


def validate_runtime(
    actual: dict[str, Any], saved: list[dict[str, Any]], environment: Path
) -> None:
    """Compare real saved runtime fields with actual locked optional metadata."""
    if (
        (actual["python"], actual["numpy"], actual["numpy_import"])
        != (PYTHON, NUMPY, NUMPY)
        or (actual["numba"], actual["open_spiel"]) != (NUMBA, OPEN_SPIEL)
        or (actual["license_bytes"], actual["license_sha256"])
        != (LICENSE_BYTES, LICENSE_SHA256)
        or not actual["launcher_pythonpath_absent"]
        or Path(actual["prefix"]).resolve() != environment
        or Path(actual["interpreter"]).parent.resolve() != environment / "bin"
        or actual["uv_project_environment"] != str(environment)
        or len(saved) != 2
        or any(
            (row["python"], row["numpy"], row["numba"]) != (PYTHON, NUMPY, NUMBA)
            for row in saved
        )
    ):
        raise ArithmeticError("actual optional or saved real runtime differs")


def saved_runtimes(root: Path) -> tuple[list[dict[str, Any]], dict[str, str]]:
    """Read the two original real own metadata records without replaying them."""
    rows: list[dict[str, Any]] = []
    hashes: dict[str, str] = {}
    for name in SAVED:
        path = root / name
        raw = path.read_bytes()
        saved: dict[str, Any] = json.loads(raw)
        if name == SAVED[0] and saved["scope"] != "real":
            raise ArithmeticError("sampled own artifact is not real")
        if name == SAVED[1] and saved["software_only"] is not False:
            raise ArithmeticError("full own artifact is not real")
        rows.append(saved["runtime"])
        hashes[name] = hashlib.sha256(raw).hexdigest()
    return rows, hashes


def preflight(output: Path, environment: Path) -> dict[str, Any]:
    """Reject before pair output or child on any source, own or runtime drift."""
    expected = (ROOT / "results/runs").resolve()
    environment = environment.resolve()
    if (
        output.exists()
        or output.is_symlink()
        or not output.is_relative_to(expected)
        or output.with_name(output.name + "-preflight.json").exists()
    ):
        raise FileExistsError("fresh ignored pair and preflight paths required")
    head, dirty = revision()
    if dirty:
        raise ArithmeticError("clean pushed launcher required")
    checked = source_checks()
    own = previous.own_published()
    original, hashes = saved_runtimes(ROOT)
    actual = installed(environment)
    validate_runtime(actual, original, environment)
    config, predecessor = baseline.binding(ROOT)
    baseline.checked(ROOT, predecessor)
    if (
        previous.CAPS
        != dict(
            child_seconds=900,
            failure_save_seconds=120,
            own_proof_seconds=180,
            shared_seconds=1800,
        )
        or config["caps"] != previous.CAPS
        or own["checked_source_commit"] != "04d19ed4c419d14cbe3fc41ccca1b1df8f3dd62b"
        or revision() != (head, False)
        or source_checks() != checked
    ):
        raise ArithmeticError(
            "unchanged pair caps, source or public own proof required"
        )
    return dict(
        status="optional_runtime_preflight_passed_before_pair",
        head=head,
        checked_launcher_commit=checked["checked_commit"],
        checked_launcher_manifest_sha256=digest(CHECKS),
        carried_own_manifest_sha256=digest(previous.PROOF),
        carried_own_proof_head=own["proof_head"],
        pinned_inputs=pinned_bytes(ROOT),
        lock_sha256=digest(ROOT / "uv.lock"),
        saved_real_artifacts=hashes,
        saved_runtimes=original,
        installed=actual,
        original_caps=previous.CAPS,
        pair_output=str(output),
        no_reference_constructed_in_preflight=True,
    )


def run_once(output: Path, environment: Path) -> None:
    """Write a separate preflight receipt, then call the old pair once."""
    result = preflight(output, environment)
    previous.atomic(output.with_name(output.name + "-preflight.json"), result)
    previous.pair(output)


def main() -> None:
    if len(sys.argv) != 5 or sys.argv[1] != "--pair" or sys.argv[3] != "--environment":
        raise SystemExit(
            "usage: launch_validated_sharing_optional.py "
            "--pair OUTPUT --environment ENV"
        )
    run_once(Path(sys.argv[2]).resolve(), Path(sys.argv[4]).resolve())


if __name__ == "__main__":
    main()
