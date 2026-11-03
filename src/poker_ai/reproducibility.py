"""Small shared runtime metadata helpers; experiment source hashes stay explicit."""

import os
import platform
import subprocess

import numpy as np


def runtime_environment() -> dict[str, object]:
    cpu = platform.processor()
    if platform.system() == "Darwin":
        cpu = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu": cpu,
        "logical_cpus": os.cpu_count(),
        "numpy": np.__version__,
    }
