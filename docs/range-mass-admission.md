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

## Status

Prospective plan published in [PR #18](https://github.com/jimmy-sim/poker-ai/pull/18)
before implementation and measured outcomes. Runner, replay, audit and renderer
implemented. Local all-extras checks pass 845 tests on Python 3.11.17/3.12.15;
base-only checks pass 818 with 18 optional skips. Ruff lint/format, strict mypy
and hooks pass. This includes 25 new tests. No research training has run yet.
