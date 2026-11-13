"""Exact new toy vector parity with the originally published own-only proof."""

import gzip
import json
import subprocess
from pathlib import Path
from typing import Any

from poker_ai.evaluation.compact_opponent_source import check_source
from poker_ai.evaluation.opponent_learning_design import TOY
from poker_ai.evaluation.opponent_learning_replay import member
from poker_ai.postflop.learning_artifacts import canonical, read_archive
from poker_ai.postflop.river_study import Deadline, digest

OLD_COMMIT = "37ca53d734a50386a37ea6d04a7c2e070e627aa1"
OLD_FOLDER = "results/compact-own-opponent-learning/software"
EXPECTED = {"captures": 324, "masses": 216, "warms": 30}


def old_blob(root: Path, path: Path) -> None:
    relative = str(path.relative_to(root))
    result = subprocess.run(
        ["git", "-C", str(root), "show", OLD_COMMIT + ":" + relative],
        capture_output=True,
        check=False,
    )
    if result.returncode != 0 or result.stdout != path.read_bytes():
        raise ArithmeticError("original published toy baseline bytes changed")


def vectors(
    root: Path, folder: Path, own: dict[str, Any], deadline: Deadline
) -> dict[str, Any]:
    if own["scope"] != TOY:
        raise ArithmeticError("toy parity cannot substitute for poker evidence")
    old_folder = root / OLD_FOLDER
    old_path = old_folder / "own.json"
    old_blob(root, old_path)
    old = json.loads(old_path.read_text())
    check_source(root, old["source"])
    if (
        old["source_sha256"]
        != "2ace916f0812efd1d93d0f16f533a9ecab15deceda482e94553df9a158d6a989"
        or old["scope"] != TOY
    ):
        raise ArithmeticError("wrong original own toy baseline")
    rows = {}
    for name, count in EXPECTED.items():
        left = member(old_folder, old[name + "_file"])
        right = member(folder, own[name + "_file"])
        old_blob(root, left)
        if len(old[name]) != count or len(own[name]) != count:
            raise ArithmeticError("complete toy vector parity inventory required")
        before = read_archive(left, old[name + "_sha256"], old[name])
        after = read_archive(right, own[name + "_sha256"], own[name])
        seen = 0
        for (a, x), (b, y) in zip(before, after, strict=True):
            deadline.check()
            p, q = json.loads(gzip.decompress(x)), json.loads(gzip.decompress(y))
            if a["id"] != b["id"] or canonical(
                {k: v for k, v in p.items() if k != "metadata"}
            ) != canonical({k: v for k, v in q.items() if k != "metadata"}):
                raise ArithmeticError("cached toy policy/book/warm contents changed")
            seen += 1
        if seen != count:
            raise ArithmeticError("incomplete toy vector parity")
        rows[name] = dict(
            count=seen,
            original_archive_sha256=digest(left),
            new_archive_sha256=digest(right),
        )
    return dict(
        status="all324policies216books30warms_exact_with_original_own_toy",
        original_commit=OLD_COMMIT,
        original_own_sha256=digest(old_path),
        streams=rows,
        scope="metadata intentionally differs; own toy vectors, not poker/reference",
    )
