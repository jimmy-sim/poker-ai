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
.venv/bin/python scripts/diagnose_board_collisions.py
.venv/bin/python scripts/inspect_board_collision.py --rank 1
```

Diagnosis results and the selected replacement definition are pending at this
protocol's first publication. Existing failed evidence/configs are unchanged.
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
