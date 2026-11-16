# Where checkpoint replay spends CPU

The latest complete audit forecast is **912.54 seconds against a 900-second
limit**. Before changing another part of validation, this investigation asks how
much CPU the current checkpoint reader spends decoding saved policies,
recomputing scores, and doing the remaining checkpoint work.

[The prospective plan in issue #4](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6910138688)
was published on November 15, before implementation or outcomes. The preceding
[complete pipeline report](compact-suit-pipeline.md) retains the failed forecast.
This is a measurement tool, with no change to poker decisions or training.

## What is measured

A checkpoint is a saved strategy and its recorded results. Replaying it checks
that the same strategy still produces those results.

The observer starts at the own-archive reader's `replay_snapshot` callsite. It
measures `learning_artifacts.decode` and `ScoringContext.score` only inside that
call. Other callers keep their original function. Three complete reads each
contain 432 checkpoints, with one decode and one score apiece: **3,888 selected
calls**, below the fixed 4,096-call limit.

The three inner regions are reported without double counting:

- Decode and validation CPU.
- Score recomputation CPU.
- Remaining checkpoint CPU after subtracting those two selected children.

The remainder includes any other checkpoint work and observer overhead. It does
not identify serializer self time. CPU outside the selected checkpoint is also
reported. Parent CPU, worker CPU and whole-command elapsed time stay separate.

## Correctness before collection

The private entry, support and config add three files to the preserved 433-file
scientific source identity. Tests check actual tiny checkpoint encoding/replay
against independent terminal sums and exhaustive pure choices. Other tests cover
arguments, return/error identity, alias and descriptor restoration, nested CPU
accounting, malformed records, process/thread ownership, recursion, call limits,
timeouts and failed writes. Synthetic clock fixtures are explicitly test data.

On November 16, **134 focused tests pass on Python 3.11.17**. Full local/optional
checks on both environments and both hosted jobs remain pending. No formal
observer proof, measured pair or new Hold'em training has run.

The prescribed sequence is unchanged: publish all six source-check receipts and
operators; publish a fresh own-only proof within 180 seconds; run one complete
ordinary/profiled audit pair; publish raw evidence; then analyze it. Each child
keeps its 900-second cap, with 1,800 seconds shared. Failed and partial outcomes
remain; there is no favorable retry or smaller replacement workload. OpenSpiel
2.0.2 remains a pinned, licensed scalar comparison only.

The installed Apache-2.0 license was read in both optional environments before
new optional validation. Both copies have SHA256
`cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`;
the pinned license record remains in [solver validation](solver_validation.md).

## Explore the tests

From the project directory:

```sh
.venv/bin/python -m pytest -q tests/test_checkpoint_observer.py tests/test_checkpoint_cpu.py
```

The tests exercise software fixtures and saved data. They do not start the formal
measurement or authorize the blocked training comparison. A single ordered pair
will not establish stable timing overhead, production savings or stronger play.
