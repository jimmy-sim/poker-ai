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

Status: prospective design only. Implementation and measurements are pending.
