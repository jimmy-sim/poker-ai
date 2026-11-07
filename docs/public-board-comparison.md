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
iterations after initialization, repeated three times. The published runner
profiles each game/encoding immediately before that cell's learning, rather than
collecting one all-controls profile batch up front. Each profile solver is
discarded before that cell's learning starts; no outcome changes repetitions or
budgets. Profile work is separate; total study wall time includes setup,
profiling, optional JIT compilation and serialization. All cells use materialized
trees and precomputed information keys. Thus traversal timings omit live card
feature generation and do not establish global online inference speed.
Brief base-environment software checks also overlap the early study. Timings are
descriptive process measurements, not an isolated runtime benchmark.

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
Visiting a shared row counts all exact infos mapped to it for this coverage metric;
it does not establish that every physical history in the row was sampled.
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

**The candidate fails development admission.** The exact controls pass both
games. Texture meets the compression requirement in both games and passes all
criteria on the low game, but fails full accuracy, sampled median and sampled
worst-seed accuracy on the medium game. No thresholds, seeds or checkpoints were
changed; no fresh/global experiment or agent-default update follows this result.

Clean source `48051de4d8320e958229b334f676679d15adbb44` completed the entire grid
in **1205.044s**. All 150 own snapshots and ten sets of three profile repetitions
are retained. Source/config/model/game hashes still match at completion. The
test-only CI correction in `3e1d374` changes none of the captured source/scripts/
inputs. Raw outcomes were committed in `142b260` before native audit.

| Game | Raw-public rows | Texture rows | Row reduction | Raw-public sampled median (% pot) | Texture sampled median (% pot) | Texture worst (% pot) |
|---|---:|---:|---:|---:|---:|---:|
| Low OOP | 364 | 92 | 74.73% | 9.14195e-9 | 3.50235e-7 | 4.30443e-7 |
| Medium OOP | 3,336 | 1,392 | 58.27% | 0.233819 | 7.369742 | 9.687537 |

All sampled numbers are at the declared 10 million charged-work checkpoint,
using all three seeds. Median limit is **1% pot**, worst-seed limit **2.5%**.
The medium texture full control has exploitability **2.522516% pot**, versus
**0.00018229%** for the exact full control: excess **2.522334 percentage points**,
above the allowed **0.5**. Its full curve changes little between 1,024 and 4,096
iterations. This supports a representation limitation under the tested learner
and budget, rather than insufficient sampled iterations alone. It does not prove
an irreducible lower bound for every possible strategy using these features.

The medium bucket-only baseline is worse still: final median **15.829884% pot**.
Its median rises from **15.640764%** at one million work, so more work is not
monotonically better in this recorded grid. Canonical and raw-public partitions
have the same row counts and measured trajectories here; canonical suit names
add no sharing on these fixed public prefixes and make keys longer. These
controls remain diagnostics; none replaces the preselected candidate afterward.

Texture merges 68 public-board rows on the low game and 828 on the medium game.
Their uniform-decision-reach collision mass is about 19.03% and 16.95% respectively.
The medium raw and texture representations have zero same-board private-hand
collisions; the extra merging is public. Every representation has zero abstract
recall violations. These observations and the exact/native controls narrow the
diagnosis toward public information loss/its learning effects, while not proving
that every implementation or shared engine component is error-free.

Combined key UTF-8 and unpadded regret/average float bytes fall from 136,874 to
44,084 on low, and 1,209,852 to 654,120 on medium: component reductions of 67.79%
and 45.93%. These exclude containers/shared tree storage. Process-lifetime peak
RSS is **480.47 MiB**, cumulative across the study; no isolated total-process
memory reduction is established. The separate
[hardware observation](../results/public-board/hardware-observation.json)
records Apple M4, 24 GiB RAM; initial sandbox metadata remains unchanged.

Initialized average-row coverage is 100% for every final cell. That is not later
exploration: the low texture runs retain up to 86 initial-only rows and 80%
uniform-reach subsequent-row coverage. Medium texture retains up to 356 initial-only
rows, with minimum subsequent-row coverage 98.29%, versus raw-public 97.60%.
Higher shared-row coverage did not imply better decisions.

The native audit passes all **150 frozen value/best-response checks**, **800
ordered final cross-play profiles**, and **90 checkpoint/visit pairs**. Maximum
native comparison error is **1.63425e-13 chips**; own replay error is zero. Audit
wall time, including own replay/receipt checks, is **14.267s**. Own cross-play
advantages are at most about **0.1027% pot** across this final-policy pool, despite
much larger best-response weaknesses. Being hard for these particular own
opponents to beat does not establish equilibrium play.

Evidence: [raw study](../results/public-board/study.json),
[compressed own policies](../results/public-board/study-own-policies.json.gz),
[native audit](../results/public-board/independent.json),
[all tables/figures](../results/public-board/report/tables.md), and
[machine summary](../results/public-board/report/summary.json).
[PR #13](https://github.com/jimmy-sim/poker-ai/pull/13) contains this block.
Local checks and final hosted CI are recorded separately there.

The next milestone should test a more informative public representation under
another prospective development protocol. No larger global run is justified by
this failed candidate. Issue #4 remains open; these two tiny, previously known
games with separate learners do not establish zero-shot or full-game strength.

## How to read the eventual figures

In `learning-work.png`, each colored line is a representation of the same game
under the same learner, not a different opponent. The x-axis is charged work;
the y-axis is exact-game exploitability divided by initial pot, so 0.01 means
1% of pot. Lower is better. Lines show the three-seed median and shaded min/max,
not confidence intervals. Encodings with the same outcome may overlap.
Both axes are logarithmic, and panels use independent vertical scales.

`full-tree.png` separates full-tree controls from sampled learners. The dotted
line is the exact full-control limit; the candidate's separate excess-over-exact
criterion is in the table. `representation-size.png` separates UTF-8 key bytes
from regret/average float bytes and excludes shared tree/container overhead.
Fewer rows do not automatically mean fewer key bytes or lower total RSS.

In `crossplay.png`, read the first policy on the row and its opponent on the
column. Blue means positive seat-balanced EV for the row policy, red means
negative, and white means near zero. The diagonal is zero by definition. A good
matchup against one own policy does not prove low exploitability or global strength.

## Questions to practice

1. **Why reject a representation that saves 58% of strategy rows?** Its medium
   sampled median is 7.37% pot against a preset 1% limit. Saving rows is useful
   only if the strategy remains accurate enough for the stated purpose.
2. **Why not just keep training?** The full-tree control also remains at about
   2.52% pot at the declared budget. That points toward the representation/learning
   interaction; it is not a proof that more computation can never help. We retain
   the failed gate and require a new controlled hypothesis before another run.
3. **What does independent agreement prove?** Native value and best-response
   calculations agree on our frozen exported game. It checks solver math and
   serialization, while the mechanics are shared. It does not prove competitive
   global Hold'em strength or full engine correctness by itself.
