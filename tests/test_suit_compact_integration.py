"""Fresh three-worker toy fixture with mocked qualification; never formal evidence.

The direct terminal and exhaustive-response oracle comes from the historical
cached-family fixture. Only execution namespace/role checks are extended.
"""

import base64
import gzip
import json
import os
import shutil
import subprocess
import sys
import tempfile
from itertools import product
from pathlib import Path
from typing import Any

# Private execution modules stay in scripts; allow direct single-file pytest.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import numpy as np
import pytest

from poker_ai.evaluation.opponent_learning_own import fixture as own_fixture
from poker_ai.evaluation.opponent_learning_score import scoring
from poker_ai.evaluation.private_prefix_journal import validate as journal_validate
from poker_ai.postflop.controlled_checkpoints import unpack_policy
from poker_ai.postflop.learning_artifacts import decode, read_archive


@pytest.fixture(scope="module")
def captured_own(tmp_path_factory: pytest.TempPathFactory) -> Path:
    tmp_path = tmp_path_factory.mktemp("suit-own-fixture")
    # This mocked gate is UNIT COVERAGE ONLY on draft source. It cannot be
    # published as a clean-source proof, forecast or actual training admission.
    root = Path(__file__).resolve().parents[1]
    output = tmp_path / "draft-unit-own.json"
    script = tmp_path / "unit_child.py"
    script.write_text("""import os,sys,time
from pathlib import Path
if __name__ == "__main__":
    from compact_suit import cli
    from compact_suit import admission as gates
    from compact_suit.source import source
    from poker_ai.evaluation.opponent_learning_report import write
    root,output,scratch=map(Path,sys.argv[1:])
    saved=dict(source(root),dirty=False)
    cli.source=lambda r,**kwargs:saved
    gates.require_checks=lambda r:{"UNIT_ONLY_NOT_ACTUAL_CHECKS":True}
    cli.write_report=lambda p,s,d,scales:write(p,s,d,scales,no_plots=True)
    os.environ["POKER_COMPACT_OPPONENT_STARTED"]=repr(time.perf_counter())
    raise SystemExit(cli.child_main(root,["software-own","--output",str(output),
                         "--scratch",str(scratch),"--_child"]))
""")
    result = subprocess.run(
        [
            sys.executable,
            str(script),
            str(root),
            str(output),
            str(tmp_path / "scratch"),
        ],
        cwd=root,
        env=dict(
            os.environ,
            PYTHONPATH=os.pathsep.join((str(root / "src"), str(root / "scripts"))),
        ),
        capture_output=True,
        text=True,
        check=False,
        timeout=180,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    s = json.loads(output.read_text())
    assert s["status"] == "completed_own_native_pending"
    assert len(s["training_batch"]["workers"]) == 3
    assert s["own_replay"]["unique_profiles"] == 432
    assert s["own_replay"]["fixed_conditions"] == 1152
    assert s["reference_constructed"] is s["long_run_admitted"] is False
    groups = {
        3: s["events"],
        **{w["slot"]: w["messages"] for w in s["training_batch"]["workers"]},
    }
    journal_validate(
        output.with_name(s["journal"]["file"]), s["journal"], s["source_sha256"], groups
    )
    # Direct terminal sums and exhaustive pure choices are independent of the
    # production tree-value/BR routines. Check this NEW spawned dataset, not
    # only identity aliases or a previously published software archive.
    contexts, _ = own_fixture()
    positive_gaps = 0
    for row, blob in read_archive(
        output.parent / s["details_file"], s["details_sha256"], s["rows"]
    ):
        game = row["coordinate"] // 3
        context = scoring(contexts[game], row)
        detail = decode(blob, context, row)
        fine = context.expand(unpack_policy(context.partition, detail["policy"]))

        def value(p: np.ndarray[Any, Any], game: int = game) -> float:
            a, b, c, d = p
            v = 0.5 * (a[1] * (c[0] - c[1]) + b[1] * (-d[0] + d[1]))
            return float(v if game == 0 else -v)

        assert abs(value(fine) - row["metrics"]["value_player_zero_chips"]) < 1e-12
        for target in (0, 1):
            choices = []
            owned = np.flatnonzero(context.exact.owners == target)
            for moves in product((0, 1), repeat=len(owned)):
                p = fine.copy()
                for info, action in zip(owned, moves, strict=True):
                    p[info] = 0
                    p[info, action] = 1
                choices.append((1 if target == 0 else -1) * value(p))
            expected = max(choices)
            assert (
                abs(expected - row["responses"][target]["exact_reply_value_chips"])
                < 1e-12
            )
            positive_gaps += (
                row["responses"][target]["extra_information_gap_chips"] > 1e-9
            )
    assert positive_gaps > 0
    from compact_suit.cache import check_execution

    check_execution(root, s)
    # Semantic vector bytes are unchanged; source-bearing metadata must differ.
    old_folder = root / "results/compact-own-opponent-learning/software"
    for name in ("captures", "masses", "warms"):

        def vectors(path: Path) -> dict[str, Any]:
            with gzip.open(path, "rt") as stream:
                next(stream)
                result = {}
                for line in stream:
                    record = json.loads(line)
                    blob = json.loads(gzip.decompress(base64.b64decode(record["blob"])))
                    result[record["id"]] = {
                        k: v for k, v in blob.items() if k != "metadata"
                    }
                return result

        before = vectors(old_folder / ("own-" + name + ".jsonl.gz"))
        after = vectors(output.parent / s[name + "_file"])
        assert json.dumps(before, sort_keys=True, allow_nan=False) == json.dumps(
            after, sort_keys=True, allow_nan=False
        )
    assert s["validation_cache"]["hits"] > 0
    assert s["normalization"]["restored"] is True
    assert s["normalization"]["enabled"] is True
    assert all(
        w["messages"][-1]["summary"]["normalization"]["enabled"] is False
        for w in s["training_batch"]["workers"]
    )
    assert s["normalization_contract"]["source_sha256"] == s["source_sha256"]

    return output


def test_full_fictional_child_uses_three_workers_and_checked_archives(
    captured_own: Path,
) -> None:
    assert (
        captured_own.exists()
    )  # All independent numerical assertions run in the fixture.


def test_optional_native_integration_checks_all_tiny_rows(
    captured_own: Path, tmp_path: Path
) -> None:
    pytest.importorskip("pyspiel")
    root = Path(__file__).resolve().parents[1]
    parent = root / "results/runs"
    parent.mkdir(parents=True, exist_ok=True)
    container = Path(tempfile.mkdtemp(prefix="suit-unit-native-", dir=parent))
    own = captured_own.parent
    saved = json.loads(captured_own.read_text())
    assert saved["poker_training_performed"] is False
    names = [
        saved[key + "_file"]
        for key in ("captures", "masses", "warms", "composed", "details")
    ]
    names.append(saved["journal"]["file"])
    for name in names:
        shutil.copyfile(own / name, container / name)
    for name in ("report", "own-card-contract"):
        shutil.copytree(own / name, container / name)
    saved["unit_fixture_not_published_evidence"] = True
    path = container / "own.json"
    path.write_text(json.dumps(saved))
    script = tmp_path / "native_fixture.py"
    result_path = tmp_path / "native_fixture.json"
    script.write_text("""import json,sys
from pathlib import Path
from compact_suit import native
from poker_ai.evaluation.opponent_learning_design import TOY
from poker_ai.postflop.cell_process import partition
from poker_ai.postflop.river_study import digest
root,own_path,result_path=map(Path,sys.argv[1:])
own=json.loads(own_path.read_text())
assert own["scope"]==TOY and own["unit_fixture_not_published_evidence"] is True
def fixture_publication(r,p):
    assert r==root and p==own_path
native.published=fixture_publication
payload=dict(root=str(root),own=str(own_path),own_sha256=digest(own_path),
             source_sha256=own["source_sha256"],publication={"own_sha256":digest(own_path)},
             deadline_started=__import__("time").perf_counter())
rows=[native.independent(i,indices,payload,lambda event:None)
      for i,indices in enumerate(partition(6,3))]
assert sum(r["profiles"] for r in rows)==432
assert sum(r["fixed_conditions"] for r in rows)==1152
assert max(r["maximum_error_chips"] for r in rows)<=1e-9
assert all(r["normalization"]["enabled"] is False
           and r["normalization"]["restored"] is True
           and r["normalization"]["requests"]==0 for r in rows)
result_path.write_text(json.dumps({"scope":"UNIT_ONLY_MOCKED_PUBLICATION_NOT_FORMAL_PROOF",
                                  "profiles":432,"fixed_conditions":1152,"rows":rows}))
""")
    result = subprocess.run(
        [sys.executable, str(script), str(root), str(path), str(result_path)],
        cwd=root,
        env=dict(
            os.environ,
            PYTHONPATH=os.pathsep.join((str(root / "src"), str(root / "scripts"))),
        ),
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert result.returncode == 0, (
        result.stdout + result.stderr + f"\nRetained fixture: {container}"
    )
    assert (
        json.loads(result_path.read_text())["scope"]
        == "UNIT_ONLY_MOCKED_PUBLICATION_NOT_FORMAL_PROOF"
    )
    assert container.parent == parent and container.name.startswith("suit-unit-native-")
    shutil.rmtree(
        container
    )  # Only this successfully checked, newly created unit directory.
