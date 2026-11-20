# Fixed river average-readout comparison

## Definition of done and reason

PR #101's B1 update-frequency test ended **negative**. Saved B4 exact-river
policies suggest that uniform versus linear averaging can reverse direction
across known card/range inputs. A uniform average gives each sampled iteration
equal weight; a linear average gives later iterations greater weight. This
experiment asks whether the uniform readout of the **same unchanged B4 signed
training path** improves exact restricted-game decisions on a structurally
selected panel. Finish one panel, source and compute gates, own publication
before comparison-only reference, fixed report and final checks; classify and
stop. It is neither a new learner nor zero-shot play.

## Prospective cohort and comparison

The [machine-readable contract](../configs/river-uniform-readout-spots.json)
fixes four strata: two independent medium/dry/OOP inputs from known
`dev_medium_oop`, one medium/wet/OOP from known `fresh_medium_wet_oop`, and
one low/wet/IP from known `heldout_low_oop`. These public betting templates
and all prior outcome cases are **known**. One PCG64 stream seeded 20261410
draws ordered four-card turn boards. Dry means four distinct ranks, three
flop suits and pairwise flop-rank gaps ≥3. Wet means four distinct ranks,
exactly two flop suits and flop-rank span ≤4. Reject every `(sorted flop
ranks, turn rank)` signature in tracked learning, fresh, original spot and
river-generalization directories or already selected strata. Allow at most
10,000 structural attempts per stratum. After accepting a board, draw eight
distinct remaining physical cards for two combos per seat and four integer
weights 1–3. Preserve each template's public pot, stacks and action
abstraction; append one deterministic legal check only if needed to put the
declared seat next. Never choose by tree size, policy, score or reference
value. Freeze the cases, attempt counts and hashes before any outcomes. A
failed legal or 200,000-node tree check retains the case and stops; no swap.
These are newly selected card/range inputs on known templates, not an
unbiased sample of Hold'em.

For every spot and seed 20261411–13, run one unchanged `q8_turn_exact_river`
B4 external-sampling path: signed regrets, linear regret and average ledger,
batch four, exact uniform initialization charged to node work, target order
0 then 1. Save current, uniform and linear policies at first complete 100k,
1m and 10m node-work crossings: 12 paths and 108 logical readouts. The final
10m **linear average is control**; the final 10m **uniform average is
candidate** from the identical path. Three spawned workers use fixed path
index modulo three. No retraining, seed substitution or extra work follows
an unfavorable result.

The primary metric is exact restricted-game NashConv/2 exploitability, in
chips and initial-pot fraction, lower better. Report every paired
uniform-minus-linear seed, each stratum's median/worst, all checkpoint
readouts, charged work/overshoot, positive-average uniform-reach coverage,
post-initial river coverage, recall violations, information rows,
four-float64-table bytes, whole-path wall time and peak RSS. For each spot,
rank the control's three largest additive best-response contributions at
turn and river (ties by information index) and report those same nodes under
candidate, including cards, public board, legal actions, probabilities,
reach and alternative-action values. State opponent and continuation
assumptions; diagnostic node scores are not universal poker advice.

**Positive** requires both medium/dry paired medians ≤−0.001 initial pots,
each medium/wet and low/wet guard median ≤+0.001, and candidate final median
exploitability ≤0.01, worst ≤0.025, coverage ≥0.95 and recall violations zero
in **every** stratum. Apply and report these unchanged historical absolute
gates separately to control. **Negative** means any candidate absolute gate
fails, either medium/dry median ≥+0.001, or either guard median >+0.001.
Other complete outcomes are **inconclusive**. Three paired seeds do not give
population confidence. No outcome promotes a default or erases older results.

## Compute, source and publication gates

Planning estimate: four times the earlier two-spot B4 workload, about 308
seconds per fixed worker if its slowest 77-second path transfers; this is not
a measured forecast. New adapter and tests must preserve all historical
source pins and receipts byte-for-byte. Focused correctness tests, exact-source
base and optional Python 3.11/3.12 roles, guards, hooks and both hosted jobs
precede real trajectories. Publish and GitHub-byte-verify a fictional own
proof under 180 seconds. Profile all 12 paths at 100k work three times (36
complete paths under 900 seconds), timing context construction through own
scoring and replay. For each path take the maximum of its three complete
`whole_path_seconds × 10m / actual_final_node_work` values. Sum by fixed
worker partition and let `T` be the largest sum. Publish profile, then a
separate admission requiring strictly `2 × (2 × T + 600) < 7200` seconds.
A rejected forecast ends the experiment without a 10m run. One admitted own
run has a 7200-second cap and 120-second failure-save window. Publish and
byte-verify its complete or partial policies/scores **before** pinned
OpenSpiel 2.0.2 (Apache-2.0) comparison-only audit. Check all 108 own value,
best-reply and exploitability scalars within 1e-9 chips under a separate
900-second cap. Reference outputs never enter training. Reproduce the report
from published bytes; complete final exact-source local/optional/hosted checks
and solo review. Retain all failures and stop at a failed source, compute,
numerical or scientific gate. No favorable retry, threshold change, budget
extension, spot replacement or next experiment belongs to this contract.

At publication, no cases have been selected and no profile or training run
has started. Codex assisted; human hands-on time was not recorded.
