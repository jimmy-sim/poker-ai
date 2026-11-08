# Range-mass full-control admission

Issue [#4](https://github.com/jimmy-sim/poker-ai/issues/4), November 7, 2026.
Codex-assisted implementation and reporting; personal hands-on time not recorded.

## Question and stopping rule

Does the single candidate defined in [the frozen protocol](range-mass-representation.md)
retain enough accuracy while reducing strategy rows on the two known games?
A full-control run visits the whole finite game tree each iteration. It tests
what this representation can learn without the noise of sampling branches.
It does not establish the strength of a general Hold'em agent.

Before measuring outcomes, retain the unchanged
[`range-mass-protocol.json`](../configs/range-mass-protocol.json): five
representations, two fixed games, checkpoints 1/16/64/256/1024/4096, fused Numba
CFR+, 900 seconds including setup and JIT, and at most 200,000 tree nodes.
Save every own average strategy, average-active mask, work count, input/context
hash and partition diagnostic. No performance-based early stopping or selection.

Final exact-control exploitability must be at most 0.1% of the initial pot.
Candidate excess over exact must be at most 0.5% of the pot, with at most 75%
of raw-public strategy rows. All final controls need 95% uniform-reach average
coverage and zero abstract-recall violations. Audit all 60 frozen policies with
OpenSpiel 2.0.2 (Apache-2.0), comparison-only, at 1e-9 chips tolerance.
The license and shared-engine limitations remain in [solver validation](solver_validation.md).

## Evidence plan

Publish the tested runner, replay, native audit and renderer before training.
Require a clean source snapshot and recheck all recorded source/input hashes.
Replay policies and diagnostics before rendering; verify native values themselves,
complete grids, range-context bindings and work receipts. Preserve negative gates.
Reports must distinguish an incomplete run, a numerical audit failure, and a
completed experiment that fails its strength/compression requirements.

Reviewed evidence will live in `results/range-mass-admission/`; reproductions
belong in ignored `results/runs/`. Sampled learning, fresh games, global admission,
and default changes do not run in this milestone even if this gate passes.

## Commands and verification

In a clean checkout with uv 0.13.5, `make admit-range-mass` trains, audits and
renders into ignored `results/runs/range-mass-admission/`. The 900-second cap is
for training/setup; native audit and replay are timed separately. Existing
outputs cause an error rather than being overwritten. For reviewed evidence,
run the three scripts with explicit paths and commit the raw study/policies
before the clean-source native audit. `make report-range-mass` only replays and
renders the reviewed files; it does not train or call the reference solver.

Software tests use a clearly labeled, tiny NumPy fixture by monkeypatching the
solver factory. Production has no backend override: it still requires the frozen
fused Numba backend. Tests cover context/input/source/policy hashes, missing or
duplicate checkpoints, work counts, partition/active-mask consistency, numerical
replay, deadline retention and native-value tampering. Fixture scores are never
research results.

## Recorded result

**Full-control admission passes on both known games.**
[All checkpoints, diagnostics and figures](../results/range-mass-admission/report/tables.md)
come from the unchanged protocol, not selected seeds or a revised threshold.

| Game | Exact (% pot) | Old texture (% pot) | Category (% pot) | Range mass (% pot) | Range/raw rows |
|---|---:|---:|---:|---:|---:|
| Low OOP | 0.00000245451 | 0.00000266778 | 0.00000258098 | 0.00000257087 | 118/364 |
| Medium OOP | 0.000182290 | 2.522516 | 2.593658 | 0.271640 | 1662/3336 |

All entries are exact-game exploitability of **own average policies at 4,096
full-tree CFR+ iterations**, divided by initial pot and multiplied by 100.
Exploitability is NashConv/2, not a measured match win rate. The medium candidate's
excess over exact is 0.271458 percentage points, below the fixed 0.5 limit.
Its row ratio is 49.82%; the low ratio is 32.42%, both below 75%.
All final controls have 100% uniform-reach average coverage and zero abstract
recall violations. These deterministic results have no sampling confidence
interval: the entire stated finite tree is evaluated, but game selection and
representation approximation remain limitations.

The full run completed all 60 own-policy snapshots in **12.884 seconds**, including
setup, below 900 seconds. Independent audit, including own replay, took **7.229
seconds**. All 60 native value/exploitability comparisons pass at 1e-9 chips;
maximum error **1.2789769243681803e-13 chips**, own replay error **zero**.
The native solver evaluates the same frozen own policies and exported mechanics;
this is not a comparison against a native-trained Hold'em strategy or a separate
engine correctness proof. OpenSpiel outputs never enter the learner.

Published source order in [PR #18](https://github.com/jimmy-sim/poker-ai/pull/18):

- `62b40a3`: prospective execution plan, before implementation/outcomes.
- `b58b49f6afb17bc838d5da6f1c7cb8843210ba51`: checked source used for training,
  dirty status false, all source/config hashes retained in the study.
- `3bd359ae8e54a0922f5bdc10e6cb6d8e37f48221`: published raw study and own policies,
  used as the native audit's clean source snapshot.

The [raw study](../results/range-mass-admission/study.json), own-policy gzip and
[native audit](../results/range-mass-admission/independent.json) retain source,
config, context, input/model/lock hashes, environment, work receipts and timings.
The raw study intentionally says native audit pending; the separately checked
[summary](../results/range-mass-admission/report/summary.json) combines the audit
and replay to report admission. No raw receipt was rewritten after the audit.

## Storage and scope limits

The new description uses more rows than old category (1,662 versus 1,428 on
medium), buying a large accuracy improvement in this specific comparison.
It uses fewer strategy rows than raw-public, but **does not establish lower total
memory**: medium UTF-8 key content rises from 1,079,292 to 1,307,649 bytes, while
unpadded regret/average arrays fall from 130,560 to 65,088 bytes. Even the sum
of these two components is larger for the candidate; Python object, padded-array
and tree costs are additional. Recorded process peak RSS is 303,071,232 bytes,
a process-lifetime high-water mark, not an isolated representation cost.

These games have tiny declared ranges and each receives its own training.
The static feature pools combo identities and ignores betting-conditioned
beliefs; earlier remaining river conflicts are not claimed solved. The plateau
in the medium curve does not alone identify the residual error's cause.
Results do not establish global generalization, competitive heads-up strength,
real-money profitability or an empirical win rate. They are not compared to
old sampled 7.37% results as though training conditions matched.

This is a good stopping point: the candidate is **eligible for the separately
specified sampled comparison**, not accepted as the global agent. No sampled,
fresh-game or global run occurred. Issue #4 remains open. Next is the unchanged
fixed-node-work comparison across all controls and three seeds, followed by the
separate fresh-game gate only if the development rules pass.

## Software checks and questions

Local `make check` passes **845 all-extras tests** on Python 3.11.17 and 3.12.15;
base-only checks pass **818 with 18 optional skips**. Includes 25 new tests.
Ruff lint/format, strict mypy and commit hooks pass. These software checks are
separate from the measured admission gate and hosted CI.

1. **Why run full-tree learning first?** It reduces the uncertainty from sampled
   branch visits, so we can test representation accuracy before spending a larger
   sampled budget. It still optimizes a compressed game and is not a global proof.
2. **Why is 0.272% an improvement but not a win-rate claim?** It is exact
   exploitability within the fixed finite spot, measured against best responses.
   It does not measure profit against human players or outside the fixed actions.
3. **Does halving rows halve memory?** No. Longer context/feature keys cost more
   bytes, and tree/object overhead remains. The report records the components
   separately instead of calling row compression total memory savings.
