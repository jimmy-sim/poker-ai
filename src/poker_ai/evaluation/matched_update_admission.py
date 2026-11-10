"""Fail-closed admission placeholder until complete proof/forecast gates exist.

The runner is intentionally unusable for real trajectories at this implementation
stage. A file named admission.json cannot bypass the missing checked gates.
"""

from pathlib import Path
from typing import Any


def require_admission(root: Path, binding: str) -> dict[str, Any]:
    del root, binding
    raise ArithmeticError(
        "complete matched-update software/forecast admission not implemented; "
        "real study blocked"
    )
