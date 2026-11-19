# Bounded learning test of exact river information

The [prospective issue #4 contract](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-7002496679)
was posted before this branch's source change or new measurement. The
[fixed config](../configs/river-strength-known-vulnerabilities.json) binds
both known games, seeds, arms, work labels, metrics and caps. This is a new
learning comparison; earlier local river diagnostics and raw-public-board
studies remain known evidence, not fresh validation.

## Question and definition of done

Can the existing q8 learner's river decision vulnerabilities improve at the
same training node work if only its river decisions remember the acting
player's exact legal information? The `q8_turn_exact_river` candidate keeps
the unchanged `texture_range_q8_b8` key through the turn. On the river it
uses the acting player's own two cards, observed five-card board, seat and
public betting history. The control retrains the unchanged q8 key. Neither
key may read the opponent's private cards, future cards, a saved opponent
policy or a reference solver. **Example:** the saved `Qh Kh` river 9d versus
9h conflict has different frozen bluff-raise values even under one compatible
prior. Exact observed river cards can separate those rows; this experiment
must measure whether finite learning uses that separation effectively.

1. Prove the candidate's observation-only inputs, q8 pre-river byte identity,
   owner, menu, depth and abstract-recall consistency; reject hidden/future
   card access and incompatible merges. Test actual B4 update, averaging,
   source-bound replay, completeness, partial retention and tampering on tiny
   fixtures. Complete locked base and applicable optional local checks, hooks
   and both hosted jobs on the exact tested source before real trajectories.
2. Publish and GitHub-byte-verify a small own proof, then run all twelve
   100k-path profile prefixes three times under the 900-second whole-profile
   cap. Charge complete source/context setup and preserve every failed attempt.
   Publish a source-bound conservative forecast/admission before long learning.
   The [prospective forecast amendment](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-7002846466)
   fixes the calculation before any profile: for each of twelve paths, take
   the maximum over three repeats of complete path seconds from construction
   through replay times `10,000,000 / actual_final_node_work`. This scales
   setup and scoring too. Sum those maxima in fixed path-index modulo-three
   worker partitions and let `T` be the largest sum. Admit long learning only
   if all 36 profiles finish within 900 seconds and `2*(2*T+600)<7200`.
   The 180-second proof, 600-second profile overhead, 7,200-second whole-own,
   900-second native and 120-second failure-save caps remain unchanged. A
   failed forecast stops long learning; no favorable retry.
3. Run both known turn-root games, `dev_low_oop` and `dev_medium_oop`, all three
   seeds 20261301/02/03 and both arms: twelve new own trajectories. Use the
   existing IID B4 external-sampling update, signed regrets, linear regret
   and average weights, exact uniform initialization and target 0 then 1
   update order. Three spawned workers get fixed path indices modulo three.
   Save the first complete 100k/1m/10m node-work crossing including
   initialization and overshoot, with current, uniform-average and
   linear-average readouts: 108 logical profiles. Final 10m linear average
   is primary; retain all other readouts and failures.
4. Report every seed/arm/game's exact restricted-game exploitability, where
   exploitability is NashConv/2 for this two-player zero-sum finite game,
   in chips and fraction of initial pot. Also report within-group and
   extra-information gains, exact-prefix river-only gain, average-row and
   post-initial river coverage, initial-only river rows, table cost, node
   work and wall time. The primary descriptive contrast is the final 10m
   medium-OOP median of three paired candidate-minus-control exploitability
   differences; retain each signed seed difference. Separately apply the
   unchanged historical 1% median, 2.5% worst and 95% coverage gates to
   each arm, with zero recall violations and 1e-9-chip scalar tolerance.
5. Publish and GitHub-byte-verify own raw outputs before constructing any
   comparison-only OpenSpiel 2.0.2 audit. Check its pinned installed
   Apache-2.0 license, reproduce every own value/reply/exploitability scalar
   within 1e-9 chips and retain discrepancies. Complete data-only report
   reproduction, final local/optional/hosted checks, a dated learning-journal
   and work-log result, and a history-preserving PR merge.

This panel contains two previously observed games and three dependent training
seeds. Pairing seed labels does not force identical sampled hands after the
strategies diverge. A lower river-only reply gain is a mechanism diagnostic,
not itself stronger play; exact exploitability is the strength measure here.
The earlier medium-IP held-out 1.0153%/1% miss and the q8 B4 known-game
2.390%/1% failure remain failed. No new default, fresh/global admission or
general Hold'em strength claim follows even if this known panel improves.
A new fresh cohort needs its own predeclared gate before any promotion.

## Source checkpoint

The candidate key falls back to the unchanged q8 key before a five-card
board, then uses the existing exact legal observation at acting river nodes.
The learner uses the existing IID B4 trainer with the fixed signed/linear
rules. Each crossing saves three policies, cumulative average masses, exact
own scores and an fsynced event trail; replay verifies policy and mass bytes,
scores and river coverage. The fixed three-worker runner retains completed
path files on failure. The comparison-only adapter reconstructs own reply
policies from published snapshots, asks pinned OpenSpiel only for independent
scalar values and saves each audited row. The data-only report retains all
108 readouts and applies the historical gates separately to each arm.

Focused software tests cover pre-river identity, legal/hidden observations,
recall on both real game trees, frozen B4 callbacks, durable capture/replay,
tampering, forecast arithmetic, stage ordering and all-row report pairing.
These are source-development checks; the locked full local and hosted source
qualification, own proof, real profile and candidate outcome are still
pending at this checkpoint.

## Source qualification outcome: stopped

The committed candidate source at `b6946880e7713e2857fe52434c4ebec7d59acf63`
failed a required source gate before any real river trajectory. Both locked
base runtimes passed Ruff, format and strict mypy, but each complete fast
suite reported **5,425 passed, 53 failed, 227 errors, 72 skipped and 150
deselected**. The [retained source-failure archive](../results/river-strength/source-failure/manifest.json)
contains both complete logs, earlier launcher and test-typing failures,
source fingerprint and exact commands. A first failure authenticates an older
published archive and rejects the changed pinned `matrix.py`; other historical
source guards and their fixtures fail on the changed source as well. The
candidate also changed `range_protocol.py`, another historically pinned file.
The required optional local checks and hosted qualification of this source
were not passed. No own proof, real 100k profile, forecast admission, 10m
training, native audit or poker-strength report was run. **Scientific result:
inconclusive**, because no trained candidate exists for the declared paired
comparison. This is a failed source-qualification gate, not evidence that
exact river information improves or harms play. Work stops here under the
prospective gate; no budget, acceptance criterion or scientific run was
changed or retried.

## Source integration repair after explicit resumption

On November 19, the user authorized diagnosis and repair of the software
source gate while retaining its failed evidence. The first direct failure
was an older archive reader authenticating the changed `matrix.py` bytes.
Other tests directly authenticated `range_protocol.py` or named historical
source inventories. A first focused repair restored those two files, but
representative historical tests still failed: older provenance hashes every
Python file under `src/`, so adding a new module there changed its aggregate.
The 227 errors in each local role were mostly setup
cascades: shared historical proof fixtures failed before their dependent
tests ran. The [official hosted failure](../results/river-strength/hosted-failure/manifest.json)
is retained separately from the earlier local failure archive.

All new candidate adapters now live in an isolated `scripts/river_strength/`
package, outside historical `src` provenance. The representation adapter
builds the original q8 tree through the unchanged historical builder and
refines only acting river information rows with the existing exact legal
observation. `matrix.py` and `range_protocol.py` are restored byte for byte
to their pre-candidate versions. The new experiment explicitly fingerprints
every member of its own closed adapter package. The candidate key, games, seeds, update,
metrics, caps and acceptance rules in the published protocol are unchanged;
this is a software integration repair, not a new scientific protocol or a
retry of a scientific outcome. No real measurement has yet occurred. Source
qualification and publication must pass again before the own proof.

Before measurement, the data-only report was corrected to read each complete
path's construction-through-replay wall time from the own worker record and
count all four persistent float64 trainer tables (regret, linear strategy,
uniform and warm mass). It now verifies the saved zero structural-recall count
and finite 1e-9-chip native scalar gate explicitly. The report imports only
standard-library gate code, leaving the comparison-only reference outside the
reporting process. These changes alter the experiment source fingerprint, so
the earlier passing local checks on `147e624` are retained as an intermediate
checkpoint and cannot qualify the corrected source. The frozen scientific
contract, inputs, seeds, budgets, tolerances and gates are unchanged.

Corrected source `7d2cb377fd8326557ebba4d83811c132368b0ec2` passed the
full exact-source qualification. Both local base roles passed 5,704 tests
(73 skipped, 150 deselected) plus lint, format and strict typing; optional
Python 3.11 passed 2,584 tests and optional 3.12 passed 2,582 with two
expected skips. Local hooks passed. [Hosted run 44494459961](https://github.com/jimmy-sim/poker-ai/actions/runs/44494459961)
passed both Python jobs, including full tests and hooks. All four local roles
recorded clean pre/post source, lock and runtime guards; optional roles also
recorded installed OpenSpiel license bytes. The complete
[qualification receipt](../results/river-strength/source-checks/manifest.json)
retains logs, official hosted metadata, scope and hashes. No own measurement
had started when this receipt was assembled.

The bounded own proof on the published source completed in 0.266 seconds
including startup, below its 180-second cap. Its fictional signal-game path
saved and replayed all nine readouts at work labels 80, 240 and 720, ending
at 726 node work. The complete [own proof archive](../results/river-strength/own-proof/manifest.json)
retains its snapshots, masses, events, runner log and exact source binding.
This is a synthetic software proof; it does not measure real river strength.

The fixed real 100k profile completed all 36 paths and 108 readouts in
35.806 seconds inside the stage (36.057 seconds including startup), below
900 seconds. The [raw profile archive](../results/river-strength/profile/manifest.json)
retains every path, snapshot, mass, event, score, whole-path time and forecast.
Recomputing the published rule gives fixed-worker sums 1218.014, 1209.015 and
1199.947 seconds, so `T=1218.014` and `2*(2*T+600)=6072.057<7200` seconds.
This is a compute admission only. Its three-repeat maxima and full-path costs
are not a poker-strength result; the admission receipt must be published and
verified separately before 10m learning.

After the profile archive was published and all 294 blobs were GitHub-byte
verified, the data-only admission independently recomputed the same
`6072.057<7200` strict bound. Its separate
[admission receipt](../results/river-strength/admission/manifest.json) binds
the published profile and source. The fixed long study can start only after
this receipt is itself published and verified.

The full gated workflow may take a few hours. The cheaper first stage is the
synthetic key/update checks and capped 100k profiling; long learning starts
only after its measured forecast and published admission. Further validation
performance investigation is deferred unless it blocks correctness or this
budget. Codex assisted with this prospective protocol; human hands-on time
was not recorded. At prospective publication, no candidate source, new
trajectories or outcome existed.
