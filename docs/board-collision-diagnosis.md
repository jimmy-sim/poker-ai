# Diagnose shared rows before choosing a replacement

This continues issue #4 after the retained texture accuracy failure. It is
post-hoc diagnosis on known development games, not a new hold-out result.
The [config](../configs/board-collision-diagnosis.json) fixes input hashes, two
continuation panels, tie tolerance and the number of displayed examples.

## Definition of done

Publish and test the diagnostic before computing its results. Recheck frozen own
exact-control values, rank costly texture merges, and retain concrete visible
examples. Then declare one richer candidate, its full-control admission criteria
and budget before measuring its compression or learning. Test the candidate's
observable-input/symmetry/recall rules and run that bounded admission check.
Stop with the diagnosis and tested candidate; no fresh/global training here.

## Diagnostic quantities

Use only the saved OWN exact full-tree policy and the uniform policy as separate
fixed continuation panels. Never load OpenSpiel policies, values or best-response
actions into this analysis or a learner. The old native results remain independent
checks only. Frozen own input hashes and baseline source dependencies are checked.

At each exact information set, sum chance times opponent reach over its hidden
histories BEFORE selecting an action. Exclude acting-player reach, divide by
that information set's support mass, and sign values for its acting player.
Continue future decisions under the chosen panel. These are conditional local
action values, not a newly optimized best response. Zero-support infos are omitted
and the omitted uniform-decision weight is reported, never silently filled in.

For each abstract row, compare individually choosing the best local action in
each supported exact info with choosing one shared local action. Its score is
`sum_i w_i max_a Q_i(a) - max_a sum_i w_i Q_i(a)`, with weights normalized by
the whole game's uniform-policy decision reach. It is nonnegative. Legal menus
and acting players must match; ties within the fixed chip tolerance are allowed.
Only rows without a common near-optimal action and positive score are ranked.

The score has units of chips per weighted decision. It is NOT exploitability,
actual game EV loss, or an additive causal decomposition of the failed gate.
Continuation assumptions, reach weights and sequential overlap limit its meaning.
It identifies disagreements worth inspecting, not an optimal feature prescription.
Zero local cost does not certify harmless sharing: changed mixing frequencies
can matter when the opponent adapts, even if local actions tie under a frozen
opponent. Both continuation panels and their supported weight must be reported.
Displayed hole cards are the acting player's own cards; hidden opponent cards
are averaged, not revealed or used to choose actions.

## Commands and status

After checked code/config publication, from a clean worktree:

```sh
make diagnose-board-collisions
.venv/bin/python scripts/inspect_board_collision.py --rank 2
```

At this protocol's first publication, diagnosis and replacement outcomes were
pending. The completed results follow below; earlier failed evidence is preserved.
`make diagnose-board-collisions` reproduces into ignored output; supply a new
`BOARD_DIAGNOSIS_OUTPUT` path to retain an earlier run. No native solver or
training job is invoked by this target.

## Retained diagnosis and prospective replacement

Diagnostic code/config/tests were published in `9189c40` before the retained-case
run. It finds 7 low-game and 115 medium-game conflicting rows under the frozen
own exact control. Under uniform continuation it finds 4 and 0 respectively.
Both panels have effectively 100% supported uniform decision weight; rounding
can exceed one by about 2e-16. This panel dependence is retained, not filtered.

In medium-game row 761, the actor holds `9c 9d` on `Ts 9s 4d 2h` and faces an
all-in on the river. The `2d` river makes a full house; `9h` makes quads. Their
old texture/bucket key merges them. Under the frozen own exact continuation,
fold/call values are `-18/-78.294109` net chips on `2d`, versus `-18/200` on `9h`.
They prefer different actions. Another retained merge combines `Kh Qh` making
a straight on `Jd` with one pair on `Kd`.

These are local counterfactual comparisons, not recommended moves against every
opponent. Positive support can be very small; normalizing Q and weighting with
uniform decision reach can emphasize rare rows. The conflicts do not account
for the full measured exploitability and can exist even in the passing low game.
Uniform continuation hiding the medium conflicts illustrates why one panel is
insufficient; both players' continuation play changes between the panels.

The single selected replacement is **`texture_made_b8`**: retain the existing
private bucket/history and board texture, and append the acting player's exact
made-hand CATEGORY at each already-observed prefix of lengths 3, 4 and 5. Compute
categories with the own evaluator on own hole cards plus that public prefix.
Preflop adds an empty sequence. Use the standard nine categories; do not retain
tiebreakers or consult actual opponent/future cards. Category history preserves
earlier abstract observations. This separates the concrete conflicts above while
deliberately retaining other information loss.

The [admission config](../configs/made-category-admission.json) is published
before candidate implementation/partition measurement/training. It fixes the
same two known games, four controls (exact, raw-public, failed texture, candidate),
six full-tree checkpoints through 4,096, existing own fused CFR+ backend, a
15-minute cap and the unchanged accuracy/compression targets:

- Exact full exploitability <=0.001 initial pots.
- Candidate full exploitability excess over exact <=0.005 pots.
- Candidate information sets <=75% of the raw-public control.
- Average-row uniform-reach coverage >=95%, zero abstract recall violations.
- Native own-policy value/BR agreement within 1e-9 chips.

Retain all 48 full-control snapshots even if the candidate fails. Controls train
from scratch; diagnostic or reference policies/values do not initialize them.
The candidate's strategy-key version and encoder source are bound in its own
admission format; it is not a global-agent checkpoint. Existing encoders/model
files/defaults and failed study inputs are preserved.

This block stops after the full-control admission and independent checks. A pass
only permits proposing the later fixed-work sampled comparison; it does not
establish sampled learning, fresh-case or global strength. The original three
seeds/work checkpoints and 1%/2.5% sampled limits are recorded for that later
comparison and will not run here. No new candidate performance outcome exists
at this declaration.

## Candidate implementation and reproduction

The candidate is an opt-in `MadeCategoryAbstraction` wrapping the same pinned
quantizers/config. It adds its versioned own-category history to the information
key, then uses the existing finite matrix's texture encoding. It preserves the
base private bucket/public betting context; it does not install a strategy rule
such as "always call quads." All controls learn their probabilities from scratch.

Only new reusable modules/entrypoints are added. Existing model, encoder, matrix,
learner and old report sources are unchanged, so the preceding comparison's
recorded dependency hashes still match. The global agent cannot load this
separate admission-policy format as a deployment checkpoint.

Before candidate outcomes, `make check` passes on Python 3.11.17/3.12.15 with all
extras: 712 tests, lint/format and strict typing. The 26 new candidate/admission
tests cover category meanings, suit/flop symmetry, prefix history, actual hidden
opponent/future invariance, acting-seat guards, the two retained counterexamples,
refinement/recall on both games, complete grids, work/coverage replay and native
checks of a tiny eight-policy fixture. Tiny fixture outcomes are not admission
results. The ten diagnostic tests remain in the same suite.

After checked code/config publication, from clean source:

```sh
make admit-made-category
```

This trains/audits/reports in ignored `results/runs/made-category-admission/`.
Choose a new `MADE_ADMISSION_OUTPUT` to preserve an earlier run. Completion of
the command means the report was produced, not that its accuracy gate passed.
After reviewed evidence is published, `make report-made-category` replays its
tables/two figures offline. Direct `.venv/bin/python` entrypoints are also
available when their locked optional extras are already installed.

At code publication, candidate outcomes were pending. The following measurements
were produced afterward, without changing the fixed config or tested source.

## Completed admission: candidate rejected

Clean training source `f3c28f04df745abbc264d2ea3ef43664cfa32e09` completes all
48 own full-tree snapshots in 9.454 seconds. The native audit starts from clean
`a846df4e975c521ecda6f7af8b076c2a137d1995` and checks all 48 in 5.630 seconds.
Maximum native disagreement is 1.27898e-13 chips; own replay error is zero.
OpenSpiel 2.0.2 / Apache-2.0 evaluates only frozen own strategies on shared
exported mechanics. It supplies no learner inputs and does not independently
validate the entire engine. See the [license record](solver_validation.md).

| Known game | Exact full epsilon (% pot) | Old texture (% pot) | Category candidate (% pot) | Candidate / raw rows |
| --- | ---: | ---: | ---: | ---: |
| Low OOP | 0.00000245451 | 0.00000266778 | 0.00000258098 | 96 / 364 |
| Medium OOP | 0.000182290 | 2.522516 | 2.593658 | 1,428 / 3,336 |

Epsilon is the project's exact-game exploitability convention. All columns here
use **4,096 full-tree CFR+ iterations**. The medium candidate's excess over exact
is 2.593476 percentage points of pot, above the preset 0.5 limit. It passes
compression (57.19% fewer medium rows), coverage and recall checks but fails the
overall admission. Low passes. Key bytes also increase relative to old texture;
row reduction alone is not a whole-process memory or speed claim.

The previous 7.37% texture result was sampled learning under a different work
schedule. Comparing it to this 2.59% full-control result would not measure an
improvement. The correct full-control comparison is **2.52% versus 2.59%**.
No sampled-learning grid, fresh cases, global training or default change follows.

The retained diagnosis also contains conflicts this feature cannot separate.
Rank 7 (row 885) has `9c 9d` on `Ts 9s 4d 2h`, with either `Th` or `Td` on
the river. Both make the same full house and share the same category history,
but the frozen own continuation prefers folding on `Th` and raising to 144 on
`Td`. In the fixed opponent range, `Tc Td` is possible on `Th` (making
quads) but impossible when `Td` is public. This card-removal distinction survives
equal own categories. Own-card/board suit and range interactions can matter
beyond made-hand category. This is an inspected example from the already retained diagnosis,
not proof that this row causes the measured final gap. The frozen diagnostic
and the newly trained candidate are different policies.

Splitting conspicuous conflicts does not guarantee lower deployed exploitability
at a fixed training procedure and budget. The local ranking is a proxy. The
next proposed block should inspect an own best response to the actual failed
candidate and the remaining information it exploits, before selecting another
feature or spending more compute. That work has not started.

[Reviewed tables and figures](../results/made-category-admission/report/tables.md),
[raw study](../results/made-category-admission/study.json),
[native audit](../results/made-category-admission/independent.json),
[PR #14](https://github.com/jimmy-sim/poker-ai/pull/14).

## Questions to practice

1. **Why did the obvious category fix fail?** It separates selected examples but
   still discards distinctions. A local frozen-policy score does not optimize the
   full game's exploitability; the measured candidate missed the unchanged gate.
2. **What did the independent check establish?** Native values and best responses
   agree for all 48 saved own strategies on shared exported game mechanics. It
   does not prove competitive Hold'em strength or full-engine independence.
3. **Why stop before the sampled run?** The cheaper full-control admission already
   fails the required accuracy limit. Preserve the result and diagnose the actual
   failing strategy before proposing another experiment.
