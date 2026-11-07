# Missing river distinctions

## Definition of done, fixed before measurement

Continue issue #4 from PR #15's eight saved final controls: both known turn-start
games, all four representations, both responding seats and two fixed prefix
panels. Publish the method/config before outcomes; publish tested implementation
before measuring those retained cases. Recheck the saved own replies, compute
river-only switches, retain complete data and native own-profile root checks,
show concrete river conflicts and update journal step 19. Stop without selecting
or training another feature, changing failed limits, fresh/global work or defaults.
No random draws or new seeds are needed: exact traversal of pinned own policies.

## Hold earlier choices fixed

For responder i against its saved opponent, let b be the saved exact reply and c
the saved same-partition reply. Their values B and C are target net chips.
Opponent rows stay fixed throughout. Construct two river-only switch panels:

- Restricted prefix: F=c; G takes c's turn rows and b's river rows. Call G's
  value H. The upgrade is H-C.
- Exact prefix: F takes b's turn rows and c's river rows; G=b. Call F's value D.
  The upgrade is B-D.

Both upgrades are nonnegative up to 1e-9 chips because b's river continuation is
an exact information-constrained response against this fixed opponent, regardless
of the responder's earlier reach. Check perfect recall. All infos are same-depth;
all games start on the turn. Retain both panels, including zero gains. B-C also
equals (H-C)+(B-H); the second term is reoptimizing earlier choices with the exact
river continuation. B-D is a different conditional comparison, not another term
to add to this decomposition. None predicts retraining gains.

For each panel use G-continuation values W and **F's full prefix reach**:
`loss(I) = sum_{h in I} reach_F(h) [W(h)-sum_a F(a|I) W(ha)]`.
Only responding river rows differ, so summed river losses equal value(G)-value(F).
Sum hidden histories before interpreting/maximizing actions; own decisions never
see actual opponent cards. Group losses by deployed row. Unlike PR #15's earlier
saved-prefix accounting, this switch explicitly changes only river responses.
Attribution among sequential river decisions remains continuation-dependent.

## Reachable strict conflicts, ties and diagnostic probes

At each river exact info, compute conditional action values under the own exact
river reply, averaging chance times saved-opponent reach over hidden histories.
Record both panels' full reach. A first-maximizer action difference is not enough:
report tie-only differences separately. Strict missed infos have positive panel
reach/support and the restricted action loses more than the fixed chip tolerance.
A genuinely conflicting merged row has at least two reachable exact infos and
no common action within 1e-9 chips of each info's optimum. Include support and
unreachable counts. Rank conflicting rows by additive loss under the fixed
**exact-prefix** panel, with abstract-row ID as tie breaker; display up to eight
and four examples per row, distinct near-optimal action sets first. Keep the
entire per-info table, including zeros, in a hash-bound gzip sidecar.

Before inspecting outcomes, fix three signatures, used only to partition each
already shared row for diagnostic conflict counts:

1. Full own river hand rank (category and tiebreakers).
2. A compatibility bit for each combo in the declared opponent range, using own
   hole cards and public board for card removal.
3. For each declared combo, blocked / own loss / tie / own win at showdown.

They accept only own cards, the five observed board cards and the whole declared
range. No actual opponent deal, policy output or future card is an input. Range
signatures depend on the explicit tiny spot ranges; they are not proposed global
features. Count unresolved conflicting subgroups after each probe; splitting a
row is not evidence of an EV improvement. A feature may leave mixing/future
conflicts even if current best actions agree.

For displayed examples also aggregate the conditional opponent-hand posterior
from the saved opponent's chance/action reach. This is an offline diagnostic,
not an added agent input. Keep structural card compatibility distinct from zero
posterior due to opponent actions. Never choose an action per hidden world.

## Verification and limits

Test hidden-history aggregation, both prefix panels and telescoping, opponents
unchanged, player signs, zero reach/support, tie-only disagreements, probe
semantics/blockers/showdown relations, whole-input suit/flop symmetry and actual
hidden-deal invariance. Test complete grids, pinned inputs and mutation rejection.
Use optional native fixtures and report smoke tests with lazy research imports;
check base-only typing/tests as well as both all-extras Python versions.

The already selected OpenSpiel 2.0.2 / Apache-2.0 reference evaluates the 64 own
F/G profiles (eight cases x two seats x two panels x two roots). It provides no
native actions or learner inputs. Its license is recorded in
[solver_validation.md](solver_validation.md). Mechanics/partitions are shared
own exports; this does not independently prove the whole engine or features.
Require complete grids and agreement within 1e-9 chips; retain failures rather
than filtering cases. No new strength gate or feature-selection success target.

Known development cases, tiny explicit ranges, fixed saved opponents and exact
own reply choices limit generalization. Tie rules and prefix reach change which
conflicts are encountered. Counts and conditional switch gains do not establish
which abstraction would work after training, or competitive Hold'em strength.

## Status

At protocol publication, implementation/checks/results were pending. Completed
results follow below. Existing failed evidence and source bytes are unchanged.


## Implementation checkpoint, before outcomes

New reusable diagnosis, native comparison and lazy-import reporting modules leave
all previous learner/encoder/report source bytes unchanged. The 20 new tests
cover both prefix panels and signs, hidden-world aggregation, conditional gain
accounting, zero reach, tie sets, static full-rank/blocker/relative-strength
semantics, whole-input suit and observation invariance, complete receipts and
mutations, tiny native roots, figures and the terminal viewer. Tiny fixtures are
software checks, not the retained research cases.

Before measurement, `make check` passes with all extras on Python 3.11.17 and
3.12.15: **753 tests each**, Ruff lint/format and strict typing. A separate base
install passes **728 tests, 16 optional skips**; hooks pass. No retained-case
probe or switch outcomes exist at this code checkpoint.

After code publication, from clean source:

```sh
make diagnose-river-distinctions
```

The target diagnoses, audits and renders in ignored
`results/runs/river-distinctions/`. Set `RIVER_DISTINCTION_OUTPUT` to a new path
to preserve an earlier run. Once reviewed evidence is published,
`make report-river-distinctions` replays it offline. The inspector is
`.venv/bin/python scripts/inspect_river_distinction.py`; it reads saved examples
and cannot train, deploy or play online. Native checks require the locked
solver-validation extra; plots require the research extra.


## Completed diagnosis and native checks

Clean source `bb5f2cc953f07593644d189e7052c0d6e56479aa` completes all eight cases
in 8.670s. Native evaluation starts from clean
`86d8f97b43d7cae6133a7b79d24f5feb942bba35` and takes 10.630s including own replay.
All **64 own F/G profile values** pass OpenSpiel 2.0.2 expected-return checks.
Maximum native disagreement is 9.94760e-14 chips; own full replay error is zero.
All 32 panel loss identities pass. No native action or strategy is used by the
own diagnostic. Shared exported mechanics remain a limitation.

For the medium category candidate, half-summing the two responding seats and
normalizing by the initial 36-chip spot pot gives:

| Frozen comparison | Value (% initial pot) |
| --- | ---: |
| Previously measured total exact-information premium B-C | 2.593489588 |
| River upgrade after restricted prefix H-C | 0.000013695 |
| Earlier readjustment with exact river decisions B-H | 2.593475893 |
| River upgrade after exact prefix B-D (separate panel) | 3.774592382 |

The first two switch components H-C and B-H sum to B-C. B-D holds a different
prefix fixed, so it must not be added to them or compared as a new win rate.
In particular, the exact-prefix panel uses the **saved c river actions**; it
does not refit the best shared river action to a changed prefix distribution.
The small H-C is not evidence river information is harmless: the restricted
prefix reaches different opportunities. All controls/panels, including zero
low-game category gains and tiny old-texture residuals, remain in the
[generated tables](../results/river-distinctions/report/tables.md).

## Which static details separate conflicts?

These counts aggregate the category candidate's responding seats on the medium
game. They count original merged rows still containing reachable exact infos
with no common near-optimal action after one static probe partitions that row.
Each column is a separate probe; they are not sequentially trained additions.

| Prefix held fixed | Before probe | Full own rank | Range compatibility | Range showdown relations |
| --- | ---: | ---: | ---: | ---: |
| Restricted | 19 | 10 | 8 | 4 |
| Exact | 24 | 11 | 14 | 4 |

The low category game has zero reachable conflicting rows in both panels.
Two exact-prefix seat-0 action differences are ties within tolerance and are
reported separately, not counted as strict missed actions. Full counts/support,
posteriors and per-info losses are retained in the compressed sidecar; the
[conflicts CSV](../results/river-distinctions/report/conflicts.csv) contains all
32 panel summaries. The second figure visualizes these counts.

Resolving 20 of 24 current-action conflicts with the relative-range probe is
**not** a measured EV improvement or feature acceptance result. The probe knows
the explicit two-combo spot range, and static outcome relations do not capture
all action-conditioned beliefs, mixing or subsequent betting behavior.

## Concrete saved examples

`--rank 1` shows row 1251: own `Tc Td`, public `Ts 9s 4d 2h`, facing a river
all-in. `Kd` leaves both declared opponent combos (`Kh Qh`, `9c 9d`) behind your
three tens, so the exact reply calls. `Jd` lets `Kh Qh` make a straight, and the
reply folds against the fixed saved opponent's betting distribution. Your own
category is trips in both cases; relative strength against the range differs.

`--rank 2` shows row 1089. Rivers `9h` and `9d` both make **tens full of nines**,
with the same full own rank `(6,10,9)`. On `9h`, opponent `9c 9d` remains possible
and makes quads; its conditional weight after the observed betting is about
83.93%. Fold/call values are -18 / -135.707548 net chips. On `9d`, that combo is
blocked, leaving `Kh Qh` alone: fold/call values are -18 / 200. The exact reply
folds on `9h` and calls on `9d`; the restricted reply calls on both. The row's
additive loss is 0.692145 chips in the exact-prefix panel. This is fixed-opponent
research evidence, not a universal rule for playing full houses.

A remaining example appears with `--seat 1 --rank 1`, row 954. Own `9c 9d` on a
`Qd` versus `Qh` river has the same full rank, compatible range and showdown
relations against `As Js` / `Tc Td`. Yet the current conditional weight on
`As Js` is about 33.70% versus 9.13%; the displayed reply checks versus raises
all-in respectively. This illustrates information absent from the static
signatures. Different current beliefs and future opponent betting may both
matter; we have not ablated their separate causal contributions or identified
why the saved opponent produces those frequencies. No extra feature was tried
to erase these remaining conflicts.

```sh
.venv/bin/python scripts/inspect_river_distinction.py
.venv/bin/python scripts/inspect_river_distinction.py --rank 2
.venv/bin/python scripts/inspect_river_distinction.py --seat 1
open results/river-distinctions/report/probe-conflicts.png
```

All examples sum hidden hands before decisions. The posterior is an offline
calculation from the saved opponent's chance/action reach, not privileged access
to its actual dealt hand or an input added to the agent.

## Stopping point

The diagnosis, complete receipts, native comparison, two figures and journal
step 19 are complete. The prior candidate still fails; no training/default or
strength upgrade follows. Next proposed work is to declare one observable
range/blocker-aware representation and its bounded admission protocol, with
explicit limits on dependence on known tiny ranges. No representation is
selected or implemented by this block. Any later training must use a separately
published design and the unchanged development/hold-out requirements.

[PR #16](https://github.com/jimmy-sim/poker-ai/pull/16),
[raw diagnosis](../results/river-distinctions/diagnosis.json),
[native audit](../results/river-distinctions/independent.json).

## Questions to practice

1. **Why is full hand rank insufficient?** The `9h`/`9d` example has the same
   own full house but different compatible opponent hands. Blockers affect
   conditional relative strength without changing your own rank.
2. **Why report two prefix panels?** River information is encountered under
   earlier decisions. Holding each prefix fixed avoids mistaking a low-reach
   river upgrade for evidence that river distinctions do not matter.
3. **Did the relative-range probe improve the agent?** No. It partitions observed
   conflicts on known ranges without training. Counts do not measure retrained
   EV or prove generalization, and four current-action conflicts remain.
