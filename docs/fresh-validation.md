# Issue #3: fresh small-game validation

## Acceptance before outcomes — November 5

The four earlier games are development data. Issue #2 found mixed benefit from
river integration, so the ordinary external sampler remains the selected
procedure. This choice is frozen before generating or training the new games.

This block will publish the selection procedure, fully specified fresh inputs,
source/input freeze and checked development gate before collecting fresh results.
Only after that gate passes may the fixed-work run start. Stop after a complete
audited report, or at a retained numerical/budget failure; do not tune on the new
games. No global training or abstraction work belongs to this block.

Definition of done:

1. Publish `configs/fresh-validation.json` before generating fresh game inputs.
2. Deterministically select four cases by texture/position constraints, not
   strategy scores. Publish exact boards, ranges/weights, actions, pot/stacks,
   seeds and source/input hashes before training. No replacing difficult cases.
3. Validate a receipt tied to the archived development report, frozen own
   strategies, native audit and unchanged learning implementation. Require all
   selected development seeds and unchanged final limits before unblinding.
4. Train each fresh game independently at the same total-node thresholds and
   retain every seed/checkpoint, work overshoot, initialization cost and coverage.
5. Independently audit every frozen own policy, render tables/plots, retain all
   failed gates, pass applicable software checks and hosted CI, and update the
   learning journal and work log.

## Fixed procedure

Exact cards; ordinary external sampling; linear regret/average weighting; one
exact initial expectation; three new seeds; 100k/1m/10m work thresholds. Charge
initialization as 2*N node equivalents and all later recursive visits, including
terminals. Finish complete iterations and retain overshoot. Own fused-Numba CFR+
controls run at 256 and 4096 iterations. Full controls are diagnostics at their
recorded work, not matched-iteration sampled controls.

The previous limits remain: full final exploitability <=0.001 pots; sampled
three-seed median <=0.01 and worst <=0.025; positive-average-row coverage >=95%;
native value/BR error <=1e-9 chips. Subsequent sampling coverage and initial-only
rows are reported separately. A positive average row can come from initialization.
All four fresh cases must satisfy their final limits for the procedure gate.

The study has a two-hour total own-study cap and a 200k-node tree cap. A cap or
numerical failure retains partial evidence and stops. A performance miss does not
stop collection of the other predeclared cases. Do not add iterations or seeds to
turn a miss into a pass. Native audit/report time is recorded separately.

## Case selection and freshness

The config defines four strata: low/dry/OOP, medium/wet/OOP, low/wet/IP and
medium/dry/IP. They reuse known legal public betting prefixes and action menus;
the new inputs are the cards and weighted ranges. For the low-IP root, append a
legal turn check to the low-OOP prefix so the button acts next. Positions are
relative to postflop betting order, and the existing pot/stacks are preserved.

One explicit PCG64 stream selects ordered boards by the published structural
rules, rejecting known/duplicate rank signatures. Dry/wet labels describe the
flop part of the turn board. Aces are high for these selection predicates; the
predicates are not a general poker-texture classifier. Eight distinct remaining
cards give two physical combinations per seat, with integer weights 1..3.
This deliberately tiny design has no overlapping cards across listed combos;
it is not a realistic or representative full range.

Board/legality/novelty checks are allowed before training. Solver values,
exploitability, learning curves or strategically favorable cards are not selection
criteria. The inputs are public once committed; "fresh" means their outcomes
have not been used to choose/tune the procedure, not that input files are secret.
The new seeds also differ from the recorded development training/panel seeds.

## Interpretation

This tests a frozen training procedure on new small games, with separate training
for each game. It does not test one trained policy on unseen boards. Reusing
public betting templates and four structural strata limits novelty. Three seeds
give descriptive ranges, not a confidence guarantee about all games. Even a pass
does not establish competitive global Hold'em strength. The older failed hold-out
experiment stays failed in its own record.

Outcome and verification sections will be added after the declared gates/run.

## Reproduction and admission

The selection program imports no reference solver and calls no game-tree builder
or strategy evaluator while selecting cases. Its structural tests use a separate
test seed. Once the actual cases/freeze are published, the generator refuses to
replace them. Admission requires the freeze bytes to match Git HEAD, every source
and input hash to match that freeze, and the relevant learner dependencies to
match the accepted development implementation. It also replays all 16 final
ordinary/control development policies against their recorded metrics, after
checking the linked native audit and complete seed grid. This is a read-only
gate; development/reference policies are never supplied to the new learners.

```sh
make fresh-admission       # Verify the published freeze and known evidence only
make validate-fresh-games  # Full admitted own training, native audit, then report
make report-fresh-games    # Replay the reviewed fresh policies/audit; no training
```

Full reproduction writes under ignored `results/runs/fresh-validation-reproduction/`
and refuses to overwrite an existing report. Choose another retained directory
with `FRESH_OUTPUT=results/runs/fresh-reproduction-2`. A complete failed performance
gate returns nonzero only after all cells and the report are retained. Budget or
numerical failures stop and retain partial evidence. Large resumable own
checkpoints stay under the selected run's `runs/study/`; raw rows include their
hash receipts. Small frozen policy exports suffice to replay published metrics.

Initial cohort publication uses `scripts/prepare_fresh_validation.py` once,
then commits/publishes the generated configs and freeze before `--gate-only` or
training. The generator is not part of ordinary reproduction; cases are already
fixed in the repository. A later software change that invalidates source hashes
needs an explicit versioned protocol decision, not silent resealing.
