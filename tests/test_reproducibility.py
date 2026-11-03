"""Optional hardware introspection must not prevent simulation in sandboxes."""

import platform
import subprocess

import pytest

from poker_ai import reproducibility


def test_cpu_query_failure_is_recorded_not_fatal(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(platform, "system", lambda: "Darwin")
    monkeypatch.setattr(platform, "processor", lambda: "arm")

    def denied(*args: object, **kwargs: object) -> None:
        raise subprocess.CalledProcessError(1, ["sysctl"])

    monkeypatch.setattr(subprocess, "run", denied)
    environment = reproducibility.runtime_environment()
    assert environment["cpu"] == "arm"
    assert environment["cpu_query_status"] == "sysctl unavailable: CalledProcessError"
