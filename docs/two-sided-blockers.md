# Which hands can each player still represent?

Prospective issue #4 comment
[6814712059](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6814712059)
registers this question before implementation or measurement. The
[fixed config](../configs/two-sided-blockers.json) binds the complete
[PR52 range-weight cache](river-range-reweighting.md). Earlier scientific
source, data, seeds, budgets, failed gates and agent defaults remain intact.

## Question and public information

The earlier QhKh river example still prefers different actions with identical
prior weights and static features. Public 9d removes our alternative 9c9d hand,
while 9h leaves it possible. That may affect how the opponent responds to a
bluff. It is an exploratory explanation, not a measured causal effect.

For each board, compute public availability of every declared hand on BOTH
sides and the ordered seat0-by-seat1 joint card-compatibility matrix. A matrix
entry is true only if the board and both hypothetical hands are disjoint.
The function takes the public board and complete declared ranges. It must not
remove alternative own hands using our actual private hand: the opponent does
not know those cards. No actual hidden opponent hand is provided.

This step tests a public card-removal description only. It does not estimate
new betting posteriors, change policies, recompute Q or train a feature.

## Complete comparison and fixed controls

Retain both known games, all three seeds, all four arms and both responding
seats: 24 profiles/48 responses. Both own river suffixes and both original
range-weight panels give 96 suffix conditions/192 range panels. Retain every
44,160 profile-seat river row, or 88,320 across suffixes, including unsupported
rows. These are dependent repeated records, not independent hands.

On the SAME cached action values, use five nested grouping controls:

1. Original full-static source groups: own full rank, opponent compatibility
   and ordered showdown relations, within the original saved partition.
2. Add public availability of the responding player's entire declared range.
3. Add public availability of both declared ranges.
4. Add the full joint compatibility matrix to those two masks.
5. Give every exact own-information row its own singleton group.

This yields 960 grouped panels. With fixed ranges, the joint matrix is fully
determined by the two public masks and fixed private-card intersections.
Controls 3 and 4 must therefore have identical member partitions; an apparent
extra information gain there is a bug. A board lookup key is storage only:
group by feature values, never board identity or row ID except control 5.

Keep original positive-source-support filtering and pre-filter-normalized
uniform decision weights for every control. Do not renormalize or select a
favorable hand subset. Reconstruct source static costs, counts and weights;
then report each control's cost, supported/total/conflicting groups and how
many conflicting source groups become entirely nonconflicting after splitting.
Denominators differ; a raw conflict count need not decrease under refinement.

## Acceptance and execution

- Independently enumerate physical-card sets; test malformed and duplicate
  inputs, blocked worlds, suit and range-order equivariance, and absence of an
  actual-own-hand input. Changing private card labels by a global suit
  permutation preserves the masks and matrix.
- Match the actual-own-hand row/column of the matrix to every source opponent
  compatibility vector without using that hand to construct alternatives.
  Validate original row/menu/range order, all source partitions and common
  support/weights. Scalar terminal-free sums independently reconstruct cached
  group costs within 1e-9 chips and 1e-12 unitless tolerance.
- Complete disjoint group inventories, nonincreasing convex sharing cost,
  identical-mask/matrix partition equality, unchanged-feature controls and
  singleton zero cost/conflicts. No positive-effect acceptance threshold.
- Bind and revalidate the complete parent cache and its local arithmetic.
  This is cached-data validation, not original full mathematical replay or a
  new native audit. Block learner/reference constructors, keep every finished
  profile before advancing, refuse old outputs and retain failures.
- Publish the protocol before code or outcomes. Publish checked source and
  pass both full local bases, relevant focused optional suites and both hosted
  source jobs before the complete cached comparison. Both final artifact jobs
  pass before merge; keep exact source/config/input/output/runtime records.
- Separate 900s cache-only clock begins at thin entry before numerical imports
  and covers complete parent validation/features/regrouping/writes; interpreter
  startup is excluded. Original 7200/900 learning/audit caps do not change.

## Stopping point and interpretation

The milestone is a checked complete saved-data diagnosis, all-case report,
cached inspector, tests and plain-English learning-journal entry. It may find
no useful separation. Any effect is an association under frozen continuations,
not a causal change in opponent behavior or a learned/global improvement.
A candidate needs a separately registered learning test and applicable
source-bound admission. Codex assistance and actual check outcomes are stated;
human practice, hours and mastery are recorded only when reported.

## Implementation checkpoint — November 11, 2026

The public feature, independent scalar cost reconstruction, five nested group
controls, source-bound cache loader, guarded runner and offline terminal browser
are implemented. Unit fixtures cover physical-card enumeration, alternative
private hands, redundant joint information, fixed support/weights, unchanged
feature values across different boards, all 960 panel slots, malformed caches,
interruption retention and the 900-second cap. Fictional test parents are marked
UNIT_ONLY; they are not new poker results.

Focused tests: 53 passed in 2.35s. Repository-wide Ruff lint/format and strict
mypy checks (622 source files) pass. Full local base/optional and both hosted
source checks remain required before the complete saved-data measurement.
No measured effect, new training or deployed feature is claimed at this point.

## Complete cached result — November 11, 2026

After both full local bases and BOTH hosted source jobs passed on published
21d3420, the unchanged command completed in **11.832719541s < 900s**. It retains
all 24 profiles/48 responses/96 suffix conditions/192 range panels/960 grouped
panels, 44,160 profile-seat river rows (88,320 across suffixes) and 96 public
boards. Independent scalar reconstruction differs from the source by at most
5.33081e-15 chips and 2.22045e-16 unitless, below 1e-9/1e-12 limits.

In the previously investigated harder spot, seed20261302/mixed/seat1/fine suffix:

| Control | Actual-posterior cost | Prior cost | Actual conflicts/groups | Prior conflicts/groups |
| --- | ---: | ---: | --- | --- |
| Source static | 0.386738718 | 0.164204558 | 23/1,386 | 11/1,386 |
| Add own public range | 0.046621048 | 0 | 4/1,440 | 0/1,440 |
| Add both public ranges | 0.046621048 | 0 | 4/1,440 | 0/1,440 |
| Add joint table | 0.046621048 | 0 | 4/1,440 | 0/1,440 |
| Exact-information singleton | 0 | 0 | 0/1,656 | 0/1,656 |

Costs are chips per weighted decision on the SAME source support/exposure,
not root EV, exploitability or training gains. Nineteen of the original 23
actual-posterior conflicting groups are entirely resolved; four remain.
The displayed actual cost falls about 87.95%, a local diagnostic reduction.

Across ALL 192 dependent panels, own-public refinement lowers cost by more than
1e-9 in 36 and changes it by at most 1e-9 in 156. Those 36 are all harder-game
seat1, non-fine-self panels. Sixty-nine panels retain cost above 1e-9 after both
public masks. These descriptive counts are not a success rate or confidence
interval. [All-case tables](../results/two-sided-report/tables.md) and the raw
960-row CSV retain every denominator, support weight and zero outcome.

**Two different redundancies:** adding the other public mask gives no further
split in THESE inputs. Every hypothetical cross-seat private hand pair is
card-disjoint in both declared games, so original actual-own opponent
compatibility already equals the opponent's public availability. This does not
prove that mask is useless with overlapping ranges; the UNIT overlap fixture
explicitly demonstrates a further split. Separately, the joint table is always
determined by BOTH masks and fixed private-hand intersections for fixed ranges.
Its partition equality is an algebraic control, independent of the first fact.

The recorded QhKh9d/9h pair now separates: 9d removes our alternative9c9d, while
9h leaves it possible. Its original static group had the same opponent
compatibility and showdown relations, yet prior raise-to146 values were
−109.500000 and +91.437957 chips (fold−54/call−162). Public own-range masks
distinguish those observations. This association does not establish why the
opponent policy responds differently or the causal effect of retraining.

## Verification and reproduction

Source full local bases: each2,814passed/58skip/149deselect,512.17/497.50s;
lint/format/strict typing/hooks and before/after clean source/runtime/module
guards pass. Focused ALL-EXTRAS53pass3.05/2.90s, not all historical optional
tests. Source [CI43159009130](https://github.com/jimmy-sim/poker-ai/actions/runs/43159009130)
passes both jobs, each2,814/58skip/149deselect/one historical roundoff warning,
935.75/670.86s. Initial optional launcher filename errors remain recorded;
their correction changed no scientific source or gate.

Both runtimes reconstruct all24 new details and exercise all96 browser
selections/navigation/invalid rank/EOF with constructors blocked,20.441678459/
18.489029166s. All five numeric/text/plot report outputs reproduce byte for byte.
Both figures were visually inspected. Formatting is a separate postprocessing
command (15.613303416s in the first report), not a new scientific clock. Exact
records are in `results/two-sided-blockers-checks`; the original Matplotlib
font-cache warning is retained. Final artifact checks/CI remain before merge.

Browse the published cache after updating the project:

```sh
.venv/bin/python scripts/inspect_two_sided_blockers.py --interactive
```

The [terminal exercise](terminal-two-sided-lab.md) explains each column. To
reproduce with clean source, choose a fresh output:

```sh
.venv/bin/python scripts/diagnose_two_sided_blockers.py --output results/runs/two-sided-reproduction
```

The exact retained report-formatting record is runnable with the research extra:

```sh
.venv/bin/python results/two-sided-blockers-checks/complete/render_report.py.txt --output results/runs/two-sided-report-reproduction
```

## Limits and next decision

This is complete cached-data arithmetic validation, not an original full-game
mathematical replay or a new independent solver audit. No strategies, hidden
hands or reference outputs enter training. Both own suffixes, all seeds and
unsupported rows remain; observations are dependent and limited to two known
tiny-range games. Ordered combo masks can be large and are tied to the declared
ranges. Neither scalable memory/compression nor general Hold'em strength is
established. Original learning failure, caps, seeds, defaults and fresh/global
gates remain unchanged.

The result supports considering public own-range removal in a future feature
design. Residual conflicts and range-weight effects remain. A compact deployable
candidate needs a separately prospective definition, correctness/compression
tests and fixed-work learning/admission comparison. No further study starts
automatically at this stopping point.

Three questions to explain this work:

1. **Why can our range matter to the opponent?** Public cards change the strong
   hands we could represent. Our actual private hand must not erase alternatives
   the opponent cannot know are impossible.
2. **Why does the joint table add nothing?** For fixed declared hands it is the
   product of both public availability flags and their fixed private-card
   disjointness. It contains no extra board information beyond those flags.
3. **Did the agent become stronger?** No training ran. Lower fixed-value grouping
   disagreement identifies a useful distinction to test, not learned EV gain.
