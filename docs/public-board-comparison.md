# Public-board fixed-work learning comparison

This continues [issue #4](https://github.com/jimmy-sim/poker-ai/issues/4) after
[PR #12](https://github.com/jimmy-sim/poker-ai/pull/12). The
[protocol](public-board-abstraction.md) and
[config](../configs/public-board-study.json) were published in `d120490` before
new representation outcomes. Their games, encodings, candidate, seeds, work
budgets and limits remain unchanged. The config's `preregistered_not_run` label
records its prospective origin; the separate study report records execution.

## Definition of done for this block

1. Publish the tested runner, independent audit and offline report code before
   full-study outcomes. Run on clean published source, with source/config/model/
   game hashes captured before setup and verified afterward.
2. Profile all controls at the declared iteration count/repetitions. Retain every
   fixed development cell, even when a candidate misses a limit, within the
   two-hour study cap. Never retry a seed to improve its outcome.
3. Keep all 150 exact-game policy snapshots and 90 paired checkpoint/visit hash
   receipts. Replay metrics/coverage/collisions/work. Independently check all
   frozen values/best responses and all 800 ordered final cross-play profiles.
4. Publish reviewed raw evidence, tables and plots, including failures and
   limitations; update the learning journal/work log and hosted CI. Stop at this
   result. No new fresh cases, global training or default-agent change.

The counts above follow mechanically from two games, five encodings, six full
checkpoints, three sampled seeds and three work checkpoints. Each game has 20
final policies: five full controls plus fifteen sampled policies. These counts
are the expected grid, not measured success.

## Execution details fixed before outcomes

The ordinary external sampler uses linear weighting and one exact initial
expectation. Charged work is initialization's `2 * materialized_nodes` equivalent
plus subsequent recursive node visits. A checkpoint finishes the current whole
iteration, retains actual work and overshoot, and never truncates an update.
The overshoot must be less than `2 * materialized_nodes`. Full-tree CFR+ controls
run at matched iterations, not the sampled work budget; their own work is shown.

Profiles use fresh solvers at the first declared study seed, with 1,000 sampled
iterations after initialization, repeated three times. They are discarded before
learning starts. Profile work is separate; total study wall time includes setup,
profiling, optional JIT compilation and serialization. All cells use materialized
trees and precomputed information keys. Thus traversal timings omit live card
feature generation and do not establish global online inference speed.

The complete exact control gate is checked before any later-stage admission.
The development comparison still retains every configured control/seed when a
gate fails. `texture_b8` is the only preselected candidate. Other controls remain
diagnostics, regardless of their measured outcomes. Only final checkpoints enter
the acceptance gate; every intermediate checkpoint is required for completeness.

Collisions group exact acting-player observations into their deployed abstract
row. A public collision merges distinct physical boards (including intentional
suit renamings). A private collision merges distinct own hands **on the same
physical board**. Collision mass is the sum of uniform-policy decision reach of
all exact infos in affected rows, divided by total decision reach. It is not an
error probability or a proof that those decisions need different strategies.

Coverage uses exact decision reach too. Positive average mass includes initialized
rows; later sampled-visit coverage and initial-only row counts are separate.
Frozen coverage masks permit offline replay without loading large checkpoints.
The native-audit stage additionally reloads every local checkpoint/visit pair,
verifies its hashes and matches its strategy, masks, iteration and work counters.
Those large files stay ignored under the output directory's `runs/` subdirectory.

Memory counters include information-set counts, UTF-8 key bytes and regret plus
average float-array bytes, both padded dense and actual unpadded forms. They
exclude Python object/container overhead, current-policy arrays and the shared
game tree. RSS is the process-lifetime high-water mark, normalized to bytes on
Mac/Linux. It is cumulative across cells; it cannot rank isolated memory savings.

For cross-play, the first policy controls seat 0 and the second seat 1. Record
player 0's net EV in chips. Also report first-policy seat-balanced advantage:
`(V(first0,second1) - V(second0,first1)) / 2`. This cancels position advantage;
self-play advantage is zero by definition. Include every ordered final pair,
not just favorable matchups. Independent checks evaluate those same frozen
mixtures in OpenSpiel's native EFG parser. Neither reference strategies nor
reference values are loaded into any own learner.

Reference: pinned OpenSpiel 2.0.2, Apache-2.0. Its installed full license was read
again for this block; see the existing
[license record and comparison boundary](solver_validation.md#solvers-versions-and-licenses).
No commercial output is used. Native checks share our exported mechanics, so
agreement validates solver math/serialization rather than independently proving
the entire poker engine correct.

## Commands

From a clean checkout with the locked dependencies and uv installed:

```sh
make study-public-boards
```

This writes a fresh run in ignored `results/runs/public-board-reproduction/`,
then audits and renders it. Choose a new `PUBLIC_BOARD_OUTPUT` to keep an earlier
run. Existing reports/policies/checkpoint directories and audits are never
overwritten. A completed negative performance gate still proceeds through audit
and rendering; successful command execution is not candidate acceptance.

To regenerate the reviewed tables and four figures without training or invoking
a native solver, after reviewed evidence has been published:

```sh
make report-public-boards
```

The direct command is `.venv/bin/python scripts/report_public_boards.py` if the
existing environment already includes the research extra. Offline replay verifies
the recorded complete native grid but never relabels an own check as a new native
run. Later source changes require a checkout of the recorded study revision;
do not update old hashes to make reproduction pass.

## Results and interpretation

At runner publication, only tiny software fixtures have run. Full-study results,
raw artifact links, actual runtimes, independent-check counts and interpretation
will be added after the declared grid finishes. No new playing-strength or
memory-saving claim is made at this stage.
