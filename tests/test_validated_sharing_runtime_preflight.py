"""Check optional runtime admission and one-shot pair launch boundaries."""

import hashlib
import importlib.metadata
import json
import sys
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import compare_validated_prerequisite_sharing as comparison  # noqa: E402
import launch_validated_sharing_optional as launcher  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]


def matching(environment: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    actual: dict[str, Any] = dict(
        python="3.11.17",
        numpy="2.4.6",
        numpy_import="2.4.6",
        numba="0.68.1",
        open_spiel="2.0.2",
        license_bytes=11358,
        license_sha256=launcher.LICENSE_SHA256,
        interpreter=str(environment / "bin/python"),
        prefix=str(environment),
        environment=str(environment),
        uv_project_environment=str(environment),
        launcher_pythonpath_absent=True,
    )
    saved = [dict(python="3.11.17", numpy="2.4.6", numba="0.68.1") for _ in range(2)]
    return actual, saved


def test_exact_optional_runtime_passes(tmp_path: Path) -> None:
    actual, saved = matching(tmp_path)
    launcher.validate_runtime(actual, saved, tmp_path)


@pytest.mark.parametrize(
    ("field", "wrong"),
    [
        ("numba", "missing"),
        ("open_spiel", "2.0.1"),
        ("numpy_import", "2.5.4"),
        ("license_sha256", "changed"),
        ("uv_project_environment", "/wrong"),
        ("launcher_pythonpath_absent", False),
    ],
)
def test_changed_installed_runtime_rejected(
    tmp_path: Path, field: str, wrong: Any
) -> None:
    actual, saved = matching(tmp_path)
    actual[field] = wrong
    with pytest.raises(ArithmeticError, match="actual optional or saved real runtime"):
        launcher.validate_runtime(actual, saved, tmp_path)


def test_changed_saved_numba_rejected(tmp_path: Path) -> None:
    actual, saved = matching(tmp_path)
    saved[1]["numba"] = "0.68.0"
    with pytest.raises(ArithmeticError, match="actual optional or saved real runtime"):
        launcher.validate_runtime(actual, saved, tmp_path)


def test_saved_real_metadata_is_read_without_replay(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    files = ("sampled.json", "full.json")
    monkeypatch.setattr(launcher, "SAVED", files)
    for name, role in zip(files, ("sampled", "full"), strict=True):
        data: dict[str, Any] = dict(
            runtime=dict(python="3.11.17", numpy="2.4.6", numba="0.68.1")
        )
        if role == "sampled":
            data["scope"] = "real"
        else:
            data["software_only"] = False
        (tmp_path / name).write_text(json.dumps(data))
    rows, hashes = launcher.saved_runtimes(tmp_path)
    assert rows == [dict(python="3.11.17", numpy="2.4.6", numba="0.68.1")] * 2
    assert hashes == {
        name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()
        for name in files
    }


def test_failed_preflight_creates_no_pair_or_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    called: list[Path] = []

    def reject(_output: Path, _environment: Path) -> dict[str, Any]:
        raise ArithmeticError("missing numba")

    monkeypatch.setattr(launcher, "preflight", reject)
    monkeypatch.setattr(comparison, "pair", called.append)
    output = tmp_path / "new-pair"
    with pytest.raises(ArithmeticError, match="missing numba"):
        launcher.run_once(output, tmp_path)
    assert called == []
    assert not output.exists()
    assert not output.with_name(output.name + "-preflight.json").exists()


def test_accepted_preflight_calls_pair_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    called: list[Path] = []
    monkeypatch.setattr(
        launcher,
        "preflight",
        lambda output, environment: dict(status="passed", environment=str(environment)),
    )
    monkeypatch.setattr(comparison, "pair", called.append)
    output = tmp_path / "new-pair"
    launcher.run_once(output, tmp_path)
    assert called == [output]
    assert json.loads(
        output.with_name(output.name + "-preflight.json").read_bytes()
    ) == {
        "status": "passed",
        "environment": str(tmp_path),
    }
    assert not output.exists()


def test_actual_optional_metadata_matches_saved_real_inputs() -> None:
    if sys.version.split()[0] != "3.11.17":
        pytest.skip("real complete pair is pinned to Python 3.11.17")
    try:
        importlib.metadata.version("numba")
        importlib.metadata.version("open-spiel")
    except importlib.metadata.PackageNotFoundError:
        pytest.skip("complete optional validation environment required")
    environment = Path(sys.prefix).resolve()
    actual = launcher.installed(environment)
    saved, _ = launcher.saved_runtimes(ROOT)
    launcher.validate_runtime(actual, saved, environment)
