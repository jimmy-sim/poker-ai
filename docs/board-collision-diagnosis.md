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
