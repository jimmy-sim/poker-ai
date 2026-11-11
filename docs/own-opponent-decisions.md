# Inspect the remaining saved-policy gap

This read-only issue #4 investigation follows the completed
[own-opponent comparison](own-opponent-learning.md). Its overall superiority
gate remains failed. The harder known spot improves on average, but seed
20261302 worsens and retains an extra-information vulnerability. The original
learning results, seeds, caps, gates and default stay unchanged.

The prospective issue comment
[6797629916](https://github.com/jimmy-sim/poker-ai/issues/4#issuecomment-6797629916)
registers the next question before new implementation or diagnostic output.
The [config](../configs/own-opponent-decisions.json) freezes the source own/native
hashes and the complete panel. This is not new training or a compute permit.

## Question and acceptance criteria

Which saved decisions account for the remaining vulnerability? Do target-policy
differences persist against a common saved opponent, or does changing the other
seat explain part of the difference between two self-play profiles?

Use both original games, all three seeds and all four arms at final10m logical
work with the original primary linear-average readout. Retain24profiles and
48responding-seat traces. Other checkpoints/readouts remain in the unchanged
original216-point report; they cannot rescue its failed primary.

For each game/seed, cross every four candidate target policies with every four
saved opposite-seat policies, for both target seats:6×4×4×2=192conditions. Hold
the same opponent fixed when comparing target policies. These unilateral gains
are not automatically self-play exploitability. Diagonals must match the audited
source responses; the new off-diagonals are explicitly own calculations and do
not inherit an external audit.

Acceptance requires:

- Full declared panels, both ordered seats, finite legal policies, source/config/
  archive hashes and prior complete-command/native receipts checked.
- Exact policy expansion and saved reply fingerprints. Every owned information
  row appears once in full details. All row/street/group losses account for the
  target's unilateral gain within1e-9chips. Half the two seat gains reproduces
  the original exact exploitability; within-group plus extra gap also matches.
- All192cross conditions present once. Diagonal roots match source values;
  swapping candidate/opponent and target seat gives the same hybrid profile
  with opposite EV sign. Identical target policies against a common opponent
  have identical EV; a self-play diagonal need not have zero exploitability.
- Learner and reference constructors blocked. No new policy is trained, exported
  to an agent or made a default. Existing inputs remain immutable; existing
  output folders are refused and completed-profile partials retained.
- Tests cover panel/schema/source tampering, missing/duplicate row accounting,
  diagonal/common-opponent identities and cached-reader integrity. Run relevant
  full local checks and both hosted jobs before merge. No training admission is
  inherited from the earlier source.
- A cached terminal browser checks the report's bound hashes and shows game,
  seed, method, responding seat, cards, board, saved probabilities, own-reply
  suffix values and reach-weighted row contribution. Explain fixed opponents,
  net-chip signs and zero-reach limitations. Full replay is a separate command.

The complete diagnostic command has a fixed900-second limit including source
loading, source-own mathematical replay, all traces/cross evaluations and writes.
This separate data-only bound changes neither original7200/900learning/audit cap.
Top10groups with up to4examples are display limits only; full owned-row details
and complete root/condition inventories remain in the report.

## Interpretation limits

Each original profile has its own fixed saved other seat. Comparing its row
losses with another profile changes that opponent too; it is not a controlled
one-row intervention. The cross panel holds opponents fixed for a separate
target-policy comparison. Replies use only legal own-card/public-board
information. Source-game/range/action assumptions are shared with the original
engine. These two known games, dependent policies and three seeds do not establish
general Hold'em strength, confidence intervals or a playing edge.

The next decision follows the saved evidence. Do not omit the unfavorable seed,
change the original gate, or start a new learning study without a separate
prospective protocol and its required admission checks. Codex assists; personal
learning and human hours are recorded only when actually reported.

## Recorded result — November 11, 2026

The complete command passes in 139.8018285 seconds, within its separate 900-second
bound. It retains all 24 profiles, 48 responding-seat traces and 192 cross
conditions. Every owned row, street total, displayed group, original root and
reply fingerprint checks; the largest trace-accounting discrepancy is
1.2273010890382813e-13 chips, below 1e-9. All common-opponent identities pass.
Learner and reference constructors remain blocked. This is diagnosis of saved
policies, not a new learning result or an independently audited off-diagonal study.

The [manifest](../results/opponent-decisions/manifest.json),
[full summaries](../results/opponent-decisions/summary.json),
[cross table](../results/opponent-decisions/cross.csv) and compressed full details
bind source commit `9bfe45c18472fc949a7236afa193300684757b7f` and the frozen inputs.
The [check records](../results/opponent-decisions-checks/) retain actual commands,
runtime guards, local checks and the diagnostic log. Both full local bases pass
2,625 tests, with 58 skipped and 149 deselected; both relevant optional checks
pass all 35 new tests. Hosted source/final-artifact CI are recorded separately.

### Where the harder spot's losses concentrate

All values below are unilateral **responding-seat 1 chips**, not half-summed
exploitability or percentages. The responding seat is the seat allowed to change
its choices; its saved other seat stays fixed. Turn plus river sums to the gain.

| Seed | Method | Total gain | Turn loss | River loss |
| --- | --- | ---: | ---: | ---: |
| 20261301 | paired coarse | 3.593254 | 3.462473 | 0.130781 |
| 20261301 | mixed | 0.055937 | 0.001486 | 0.054450 |
| 20261302 | paired coarse | 0.330994 | 0.300169 | 0.030825 |
| 20261302 | mixed | 0.678209 | 0.638238 | 0.039971 |
| 20261303 | paired coarse | 2.285528 | 2.165173 | 0.120354 |
| 20261303 | mixed | 0.297722 | 0.227953 | 0.069768 |

For the unfavorable seed 20261302, mixed responding-seat 1 groups 819 and 31
contribute 0.3988370387 and 0.2216959014 chips. Their sum is 91.50% of that
seat's 0.6782093457-chip gain. On board `Ts 9s 4d 2h`, they hold `9c 9d` and
`Qh Kh`, respectively, facing a 36-chip turn bet with pot 72. Both saved rows
almost always fold. The exact own reply calls, worth -16.994315 and -17.446327
net chips versus folding for -18, **using its own optimal later continuation**.
The negative values are net chip outcomes, not the cost of the call alone.

Their saved prefix reach mass is 0.4005350448, versus 0.1546846116 for the paired
control. The two controls therefore expose these decisions at different rates.
This mass includes chance and saved-policy reach; it is not a conditional action
frequency. A larger group loss does not prove one local choice caused the
training difference. In particular, the turn call can become valuable because
the later reply uses river information unavailable to a coarse continuation.
Turn-attributed loss is not evidence that the river representation is irrelevant.

### Hold the opponent fixed before comparing target policies

The table gives mixed minus paired-coarse **target EV in chips** against each
same saved opponent. Positive means the mixed target does better in that
particular matchup. All three seeds and both seats remain; values are rounded
from the complete 192-condition table. These new crosses are own calculations.

| Seed | Target seat | Coarse-self opponent | Paired-coarse opponent | Mixed opponent | Fine-self opponent |
| --- | ---: | ---: | ---: | ---: | ---: |
| 20261301 | 0 | +0.000760 | +0.007498 | +0.002295 | +0.002274 |
| 20261301 | 1 | +0.019432 | +0.026671 | +0.031874 | +0.028595 |
| 20261302 | 0 | +0.002853 | +0.010814 | +0.015751 | +0.025685 |
| 20261302 | 1 | -0.000811 | +0.003055 | -0.001882 | +0.002575 |
| 20261303 | 0 | +0.004523 | +0.000305 | +0.011536 | +0.013727 |
| 20261303 | 1 | +0.026815 | +0.035088 | +0.023856 | +0.029252 |

For seed 20261302, changing only the saved responding-seat 1 candidate from
paired to mixed while holding its opponent paired changes the gap from
0.3309940111 to 0.3279387575 chips. Keeping that mixed candidate and replacing
the saved opposite seat with mixed changes it to 0.6782093457. Thus the larger
self-profile vulnerability is chiefly associated with the changed opposite
seat's opportunities for a fine-information reply. It is not a uniform worsening
of the target's EV against all the saved opponents. These are fixed-profile
comparisons, not causal claims about the training mechanism or an equilibrium
ranking. The saved opponents do not execute the exact best reply used to measure
exploitability; better EV against them can coexist with worse exploitability.

The low-SPR profiles retain tiny gains and no extra-information root gap. Their
paired/mixed probability identities for seeds 20261302 and 20261303 also give
identical target EV against a common opponent, as required. Full details retain
even negligible and zero-reach rows; display limits do not select the assessment.

### Reproduce and browse

From the repository root, run the trace command with a **new** output directory;
the published directory is deliberately protected against overwrite:

```sh
.venv/bin/python scripts/trace_own_opponent_decisions.py --output results/runs/opponent-decisions-local
.venv/bin/python scripts/inspect_own_opponent_decisions.py --seat 1
.venv/bin/python scripts/inspect_own_opponent_decisions.py --seat 1 --rank 2
.venv/bin/python scripts/inspect_own_opponent_decisions.py --interactive
```

The full replay takes time; cached browsing checks bound hashes and loads once.
Use `n`/`p` for groups, `s` for seeds, `o` for methods, `g` for games, `t` for
responding seats and `q` to leave. The default selection remains the harder spot,
unfavorable seed and mixed method; add `--seat 1` to see the concentrated gap.
This is a simulation research browser, not advice for a live game.

### Next decision and practice questions

Inspect the same call with the saved, restricted-best and fine-best river
continuations, retaining the same fixed opponent and legal information. That
would separate an immediately bad call from a valuable call whose later coarse
continuation cannot realize the value. Register that complete diagnostic before
implementation; this result alone admits no new training or default change.

- **Why can matchup EV improve while exploitability worsens?** The saved
  opponents leave opportunities unused. Exploitability allows an optimal legal
  reply and can reveal weaknesses those opponents do not exploit.
- **Does a turn loss prove a turn-only bug?** No. The accounting uses optimal
  later replies; river information can change the value of calling now.
- **What does the cross table prove?** It controls the saved opponent for these
  known matchups. It does not establish causal learning effects, a general
  Hold'em edge, or a new independent audit of its off-diagonal entries.
