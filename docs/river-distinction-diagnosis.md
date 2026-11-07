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

Protocol/config published before new measurements; implementation, checks and
results pending. Existing failed evidence and source bytes remain unchanged.


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
