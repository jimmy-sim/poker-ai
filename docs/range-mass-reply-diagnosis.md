# Diagnose the saved range-mass strategies

Issue [#4](https://github.com/jimmy-sim/poker-ai/issues/4), November 7, 2026.
Codex-assisted implementation/reporting; personal hands-on time not recorded.

## Question and stopping point

The [sampled comparison](range-mass-sampled.md) fails the deeper-game limits.
Before choosing a remedy, measure how much a best reply can gain using the
existing representation, and how much additional gain exact information allows.
Use the unchanged saved policies: all five representations, both known games,
all three final sampled seeds at 10m work, plus all final full controls at 4096
iterations. The pinned [config](../configs/range-mass-reply-diagnosis.json) binds
all raw input reports, own policy/checkpoint bundles and independent audits.
There are 40 profiles, 80 responding seats and 160 exact/restricted reply roots.

For each responding seat i, freeze the saved opponent. Let V_i be the saved value,
B_i the exact best-reply value and R_i the best-reply value within the saved
information partition. Record B_i - V_i = (R_i - V_i) + (B_i - R_i).
Half-sum over seats to reproduce exact exploitability (NashConv/2).
Require equal-depth perfect recall before response dynamic programming; maximize
after summing hidden histories, never separately inside each hidden world.
Use the first legal exact maximizer, with no approximate tie substitution.

Keep per-seat, per-street and per-information-row saved-prefix/reply-suffix losses.
Their sum must equal each unilateral gain. Retain all zero-loss rows too. Display
up to eight positive groups and four supported examples per group, in deterministic
loss/index order. These are own counterstrategy examples, not deployed-agent play
or universal poker advice. A turn loss can include later river opportunities;
street attribution is not causal feature localization.

Report all seeds separately. When summarizing additive components, use arithmetic
means so the components still add to the mean total. A median total is a separate
statistic; median components generally do not add. Full-tree versus sampled
results use different update/work conditions and are not a causal variance ablation.

Publish tested code before computing new responses. Cap the own stage at 1800
seconds including input replay. Retain all 40 cases, source/config/input/context
hashes and own exact/restricted reply profiles. Replay every nested summary/detail
and accounting identity. Independently check all 160 roots and the 160 achieved
own reply-profile values with OpenSpiel 2.0.2 (Apache-2.0), comparison-only, within
1e-9 chips. The [license/shared-mechanics limitations](solver_validation.md) remain.
No native actions enter the own learner or reply computation.

Definition of done: checked own diagnosis, complete native audit, reproducible
tables/two figures, a terminal inspector, local/hosted software checks and journal
step 23. Stop there. No training, new representation, budget rescue, remedy
selection, fresh/global admission or default change. A large within-partition
value shows available deviations against this frozen opponent, not guaranteed
self-play improvement. Extra-information value is specific to that opponent and
policy, not a universal irreducible abstraction floor.

## Reproduction and checks

`make diagnose-range-replies` reproduces the own diagnosis, independent audit and
plots into ignored `results/runs/range-mass-replies/` from a clean checkout. The
1800-second cap applies to the own stage including input replay; audit and later
reporting have separate timers. Existing outputs are not overwritten. To publish
reviewed evidence, use the scripts' default paths and commit the own diagnosis
and details before running the clean-source native audit. `make report-range-replies`
only replays and renders the reviewed diagnosis with the saved audit.

The inspector defaults to the first predeclared sampled seed, not a selected
favorable or worst seed. Use `--training full` for the separate full control.
It is an offline viewer; regeneration/replay is the numerical verification path.
Test fixtures use a labeled one-game/one-seed uniform policy grid with a mocked
input loader; production has no loader bypass. The full real 40-profile input
selection is separately replayed in tests without computing new research replies.

## Recorded diagnosis

All **40 saved profiles** complete: 30 final sampled policies and ten full
controls. All 80 per-seat decompositions and complete information-row traces
replay with **zero numerical difference** on the recorded Mac. All **160 native
roots** and **160 achieved own reply values** pass comparison at 1e-9 chips;
maximum native error **1.2079226507921703e-13 chips**.

Own diagnosis, including input replay and retained details, took **26.361 seconds**
(below 1800). The separate native audit, including own replay, took **49.321
seconds**. All old strategies, configs and failed acceptance gates remain unchanged.
This milestone performs no training and claims no improvement in playing strength.

### Medium game: the candidate's decomposition

| Saved candidate | Exact exploitability (% pot) | Within partition (% pot) | Extra exact information (% pot) |
|---|---:|---:|---:|
| Sampled seed 20261301 | 4.480481 | 0.111073 | 4.369408 |
| Sampled seed 20261302 | 5.506634 | 0.533142 | 4.973492 |
| Sampled seed 20261303 | 3.074980 | 0.085407 | 2.989573 |
| Arithmetic mean of all three | 4.354032 | 0.243207 | 4.110824 |
| Separate full control, 4096 iterations | 0.271640 | 0.000174 | 0.271466 |

The previous sampled **median stays 4.480481%**. The 4.354032% mean is a different
statistic, not another learning improvement. The component means add to the mean
total; medians of components need not add to the median total.

For comparison, mean sampled medium total/within/extra values are:
exact/raw-public **0.236525 / 0.236525 / 0%**; texture
**6.555730 / 0.114799 / 6.440931%**; category
**6.359832 / 0.239764 / 6.120068%**. All individual results, both games and full
controls remain in the [tables](../results/range-mass-replies/report/tables.md),
`all-profiles.csv` and `mean-components.csv`.

### What this supports

For the saved sampled candidate on medium, the extra-information component is
much larger than the within-partition component in **every seed**. Large response
opportunities remain invisible to the compressed opponent. There are also
within-partition opportunities; they have not vanished.

This does **not** establish a universal 4.110824% abstraction floor. The same
representation's saved full control has much lower total and extra-information
values. Those profiles face different saved opponents and result from different
training work/update conditions. The evidence is consistent with an interaction
between information loss and the particular learned strategy, but does not
separately identify a cause or a guaranteed remedy. Near-stability against a
compressed opponent does not ensure robustness against an exact opponent.

We cannot conclude that more iterations alone, more buckets, a posterior feature,
or a different sampler will fix the failure. No such ablation was run. A useful
next bounded question is why the same partition supports very different
exact-opponent vulnerability across saved full and sampled profiles, using
matched fixed opponents or targeted river probes before selecting a remedy.

### Inspect a concrete decision

Run `python scripts/inspect_range_reply.py --seat 1` in the project environment.
This uses the prospectively fixed first seed, 20261301, medium OOP candidate.
The top saved-prefix loss group is row **819**, with one exact member:
seat 1 holds **9c 9d** on **Ts 9s 4d 2h**. The saved policy folds with probability
**0.992398**, calls **0.007600**, and almost never raises. The exact best reply
calls. Its target net-chip continuation values are:

| Action | Exact-reply-suffix value (target chips) |
|---|---:|
| Fold | -18.000000 |
| Call | -10.416672 |
| Raise to 144 | -46.122442 |
| Raise to 182 | -52.097346 |

This group's additive target gain is **2.940104 chips**. The entire seat-1
unilateral gain is **3.181651 chips**, of which **0.041201** is available within
the saved partition and **3.140451** is extra exact-information value. These are
unilateral gains, not already half-summed exploitability or a causal EV loss from
one feature. Current pot is 72 chips; reported percentage metrics use the game's
initial 36-chip pot.

The restricted reply still folds at this turn row in the retained reply profile.
The row is not merged, so the disagreement can depend on later river choices
available to the exact reply. Merely changing this turn action is not the same
as executing the whole optimized suffix. These are fixed-opponent simulation
values, not a general claim about folding or calling a set in poker.

## Evidence and verification

[PR #20](https://github.com/jimmy-sim/poker-ai/pull/20) publishes the plan first,
then checked code **38fbe0f400cfd36d22df35cea8c6c3e68477f644** before the own
diagnosis. Original source dirty status is false. Own diagnosis/details were
published in **5982ebbf4c6fb152c670b26beb81cac9203c89f2** before the clean-source
native audit. Config pins all six original raw inputs. Source/config/lock/model
bindings, CPU/Python/NumPy metadata and runtime are retained in the raw JSON.
All own exact/restricted profiles and every row loss, including zeros, are in the
gzip sidecar. No native strategy actions are exported.

[Raw diagnosis](../results/range-mass-replies/diagnosis.json),
[native audit](../results/range-mass-replies/independent.json),
[summary](../results/range-mass-replies/report/summary.json) and both inspected
figures support the writeup. Python 3.12 also replays the full result successfully.
Local checks pass **914 all-extras tests** on each Python 3.11.17/3.12.15;
base-only **883 passed, 22 optional skips**. Includes **28 new tests**. Ruff
lint/format, strict mypy and hooks pass. Hosted status is reported separately in
PR #20. This remains a two-known-game, tiny-range diagnosis using three sampled
seeds, not a population confidence interval or global Hold'em strength result.

The requested stopping point is reached after these checks. Issue #4 remains
open; no new training, feature/remedy selection, fresh/global admission or
default change follows this diagnosis.

## Questions to practise

1. **What do the two components mean?** Against a fixed saved opponent, the first
   is improvement possible with the same information partition; the second is
   the additional improvement an exact-information responder can obtain. Both
   seats are half-summed to match the original exploitability convention.
2. **Why use means here?** Summing and averaging commute. Taking medians does not.
   Report the earlier median as a separate statistic, not a sum of component medians.
3. **Does a dominant extra-information component demand a new feature?** It
   identifies an information-sensitive weakness of the saved profiles. The same
   partition's stronger full control prevents claiming a universal floor; a new
   feature or training change needs its own controlled test.
