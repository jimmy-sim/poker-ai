# Declared-range river mass representation

## Definition of done, published before implementation/outcomes

Continue issue #4 after the river diagnosis. Define **one** candidate,
`texture_range_q8_b8`, and publish its exact inputs, quantization, limits and
control grid before implementation/partition measurement/learning. Implement the
opt-in encoder, inspectable feature, structural/privacy/recall tests and pure
acceptance-rule tests using explicitly synthetic metrics. Update journal step 20
and GitHub; stop before training, compression measurements, fresh/global work or
default changes. No candidate performance is accepted by software fixtures.

## Exact feature definition

Keep the existing private eight-bucket history, public texture and own made-hand
category history. Append one feature only on the river, when all five board cards
are already visible. Earlier streets append an empty feature. No speculative
future boards, actual opponent deal, policy, solver output or action-conditioned
posterior is an input.

Each seat has a **fixed declared prior**: the weighted physical combos from the
versioned spot config. Canonicalize combo card order and entry order, reject
duplicates/invalid cards/nonpositive or nonfinite weights, and normalize each
seat's range separately. The standalone prior builder accepts exact integer weights; finite floats use
their shortest decimal string (`Fraction(str(weight))`). The spot adapter starts
from the existing loader's validated floating weights. This protocol pins unit
weights, so no integer precision conversion is involved; preserving arbitrary
raw JSON integers beyond that loader's precision is outside this contract. Exact
rational arithmetic fixes normalization and quantization boundaries. Normalized
priors, role order and a version tag determine a SHA256 context namespace.
Reordering combos or multiplying weights by an exactly common scale preserves
that namespace. Changing the prior requires a new context; artifact loading must
also bind the whole spot/model/config/source hashes.

For acting own cards plus observed river board, classify every declared opponent
combo by its **prior** weight:

1. Blocked: it overlaps your cards or the board.
2. Loss: legal combo beats your evaluated best five-card hand.
3. Tie: legal combo ties your hand.
4. Win: your hand beats that legal combo.

These four unconditional masses sum exactly to one. Do not renormalize away
blocked mass in the feature. Reject observations with no compatible positive
opponent mass rather than inventing a distribution. The optional inspector may
also report showdown equity conditional on compatibility; that is explanatory,
not another feature or an action recommendation.

For each mass p use `min(7, floor(8*p))`. Bins 0..7 have width 1/8, with p=1 in
bin 7. Quantize rationally, not with an epsilon around floating boundaries.
Zero and small positive masses can share bin 0; p=.875 and p=1 share bin 7.
No sweep or post-outcome adjustment of this eight-interval choice is allowed.

The versioned key is `[feature version, context SHA256, existing category key,
river mass bins]`, then the unchanged finite matrix wraps public texture.
Context is immutable for an encoder instance. Full key names intentionally bind
raw physical declared ranges: jointly renaming suits preserves feature values
and the induced partition up to context namespace, rather than equating keys
across distinct contexts. Reject wrong-seat/terminal views. Do not allow the
inherited global quantizer serializer to silently discard the range context.
No deployable strategy/checkpoint format is introduced here.

## Why this candidate, and what it loses

The diagnosis found relative strength and blocker differences that categories
miss. Instead of appending an ordered per-opponent-combo outcome vector whose
size grows with the range, pool weights into four fixed coordinates. This is a
coarser hypothesis than the prior diagnostic probe; its 24-to-4 conflict count
must not be reused as a result for this candidate.

**Illustrative arithmetic using the retained spot inputs:** with equal prior
weights on `Kh Qh` / `9c 9d`, own `Tc Td` and public `Ts 9s 4d 2h`, river `9h`
has masses `(0,1/2,0,1/2)` and bins `(0,4,0,4)`. River `9d` blocks the nines,
so masses are `(1/2,0,0,1/2)` and bins `(4,0,0,4)`. These demonstrate encoding,
not learned EV gains. King versus jack rivers also change relative outcome mass.

Pooling loses combo identity, suit/rank associations beyond the retained base,
and fine mass differences. Static priors do not update after bets; remaining
same-signature examples from the diagnosis are expected limitations. The current
ranges are two-combo assumptions, not inferred or representative full-game
ranges. Supplying the actual opponent hand as a one-combo 'prior' is prohibited.
Range dependence must be explicit in future reports and any fresh-case design.

## Fixed future acceptance contract

The [config](../configs/range-mass-protocol.json) pins the model, two known games
and diagnostic motivation hashes. Controls are exact, raw public, old texture,
old category and this candidate. All learn from scratch; no diagnostic/reference
strategy initializes them.

First stage: six full-tree CFR+ checkpoints through 4,096, using the same own fused
Numba backend. This plans **60 own snapshots**, not results produced here. Cap
full-stage wall time at 900 seconds and each game at 200,000 tree nodes. Require
on **both** known games at the final checkpoint:

- Exact full exploitability <=0.001 initial pots (0.1% pot).
- Candidate full excess over exact <=0.005 pots (0.5 percentage points of pot).
- Candidate strategy rows <=75% of the raw-public control.
- Uniform-reach averaged-row coverage >=95% for all final controls; report
  initialized, subsequently sampled, initial-only and fallback quantities
  separately at the later sampled stage.
- Zero recall violations and compatible owners/action menus for every control.
- All 60 own snapshots replay with correct context/input/source/work/coverage
  receipts and independent value/BR disagreement <=1e-9 chips.

The metric assessor in this milestone tests mathematical thresholds and complete
identity grids using synthetic inputs. It is **not** a future artifact loader or
proof of source/work replay; the eventual runner/auditor must supply those checks
before any real admission claim. Missing/duplicate checkpoints, audit entries or
context bindings cannot pass. The synthetic full metric assessment binds a
canonical protocol/context fingerprint; the sampled assessment must match it. A full-stage pass only permits the sampled
comparison, never fresh/global admission or deployment.

Later sampled stage, also not run here: the same three fixed seeds and
100k/1m/10m node-work checkpoints, ordinary external sampling, linear weighting
and one exact initialization. All five controls give 90 planned sampled policies.
At final work, both exact and candidate require median exploitability <=1% pot
and worst seed <=2.5%; average coverage >=95%, zero recall and native checks remain
required. Include initialization in measured work; allow only one complete-iteration
overshoot. Budget 7,200 seconds; profile 1,000 iterations three times per cell.
Record all controls/seeds/checkpoints, keys/table storage, RSS, work, coverage,
policy receipt hashes and cross-play. Passing rules cannot be relaxed afterward.

The pure sampled-threshold assessor is also tested with synthetic grids and
requires a passing full-stage metric assessment for the same protocol/contexts.
Numeric receipt checks require full work `2 * iteration * tree_nodes`; sampled
work must cross the requested budget in exactly one recorded complete iteration,
with initialization included. Method/weighting/initialization flags, zero recall,
all final-control coverage and total stage runtime caps are checked. These
numeric consistency checks still require raw source/policy/work replay later. It does not launch learning or
replace independent artifact verification. A failure stops the candidate;
preserve it without another feature/seed/config selected to rescue the result.
No new cases/global training until a separately frozen fresh-case stage follows
accepted development evidence. Existing failed gates remain unchanged.

## Correctness acceptance tests

Cover exact mass conservation/weighting and rational bin edges; blocker,
relative-strength and known unresolved examples; combo/weight-scale ordering;
whole-input suit symmetry and hole/flop order; wrong-seat/terminal and all-blocked
rejection; independence from actual hidden opponent/future cards; no new range
feature before the river; context-key separation and serialization rejection;
refinement of the category partition, legal menus and perfect recall on both
games. Structural tests can build those trees but publish no row-count/compression
or learning claim. Test full/sampled boundary limits, missing/duplicate grids,
wrong contexts, nonfinite metrics, required audits and global-admission denial.

## Status

At first publication, implementation/tests were pending. Correctness is now
complete as recorded below; no training or performance measurement occurred.


## Completed correctness milestone

Protocol `2031519` was published before implementation. The optional encoder,
finite-matrix adapter, inspector and pure metric assessors are now implemented.
All existing learner/encoder/report source files, prior model files and failed
study inputs remain byte-identical; new research modules are added separately.
The range-aware subclass refuses global save/load operations that could discard
its context. No deployable strategy or admission runner is introduced.

Actual local verification with all extras passes **819 tests on Python 3.11.17**
and **819 on Python 3.12.15**, including **66 new focused tests**. A separate
base-only install passes **794 tests with 16 optional skips**. Ruff lint/format,
strict mypy and hooks pass. The reused base/3.12 environments initially contained
duplicate editable-path files pointing at older worktrees, causing collection
errors. Removing the verified stale entries restored the intended package path;
all relevant checks were rerun. No source or threshold was changed to resolve
that environment issue. Hosted checks are recorded separately on PR #17.

Structural tests verify refinement, compatible menus and zero perfect-recall
violations on both known games, and the two published blocker/relative-strength
counterexamples split. A limitation test intentionally retains the same-static-
prior `Qd`/`Qh` example whose action-conditioned opponent weights differ. Tests
also verify context separation even when feature bins stay identical, exact
rational boundaries, missing/duplicate audit rejection, numeric work/budget gates
and full-to-sampled protocol/context binding. The metric fixtures explicitly
carry `synthetic_fixture=True`; their pass flags are not experimental results.

No candidate row counts, compression ratios, learned policies, exploitability,
training times or generalization results were produced. The **60 full** and
**90 sampled** snapshots above are planned grids. The next milestone implements
and runs only the full-control admission first; if it fails, retain the failure
and stop before the sampled stage. A separate future artifact verifier must
check actual source/config/policy/work receipts and independent value/BR results.

Try the feature, using equal declared prior weights from the pinned medium spot:

```sh
.venv/bin/python scripts/inspect_range_feature.py 9h
.venv/bin/python scripts/inspect_range_feature.py 9d
.venv/bin/python -m pytest -q tests/test_range_mass.py tests/test_range_protocol.py
```

Expected bins in blocked/loss/tie/win order are `(0,4,0,4)` and `(4,0,0,4)`.
The context SHA stays the same. The inspector's `1/2` losing mass on `9h` is a
**starting prior**, whereas the previous inspector's 83.9% quads weight followed
observed betting. This candidate deliberately does not implement that posterior.
Its conditional static showdown equity is explanatory and never supplies an
action rule. Bin values are interval labels, not action probabilities or chips.
`q8` names the eight mass intervals; `b8` names the unchanged private buckets.

Use `make test-range-mass` for the same focused checks with uv. These commands
build no learned strategy. [PR #17](https://github.com/jimmy-sim/poker-ai/pull/17),
[config](../configs/range-mass-protocol.json), and journal step 20 retain the
prospective choice and the current stopping point.

## Questions to practice

1. **Why keep blocked mass instead of conditioning it away?** Removing a strong
   opponent combo is information even when every remaining combo loses to us.
   The four unconditional masses preserve that change before quantization.
2. **Why bind the range context?** The same cards can have different relative
   strength under different priors. Keys and stage contracts must identify the
   assumptions they use, so a pass/checkpoint cannot silently cross contexts.
3. **Do green tests mean the agent is stronger?** No. They establish encoding
   and acceptance-rule behavior. Real compression, full/sampled exploitability
   and independent audits remain unmeasured for this candidate.
