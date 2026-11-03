"""Small shared runtime metadata helpers; experiment source hashes stay explicit."""

import os
import platform
import subprocess

import numpy as np


def runtime_environment() -> dict[str, object]:
    cpu = platform.processor()
    query_status = "platform processor"
    if platform.system() == "Darwin":
        try:
            cpu = subprocess.run(
                ["sysctl", "-n", "machdep.cpu.brand_string"],
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()
            query_status = "sysctl"
        except (OSError, subprocess.CalledProcessError) as error:
            query_status = f"sysctl unavailable: {type(error).__name__}"
    return {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "cpu": cpu,
        "cpu_query_status": query_status,
        "logical_cpus": os.cpu_count(),
        "numpy": np.__version__,
    }
