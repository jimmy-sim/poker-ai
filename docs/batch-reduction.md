# Same checks, less reduction dispatch: prospective plan

November 9, 2026, issue #4. Codex-assisted; developer hands-on time unknown.
This plan/config precede implementation and measurements. The own cost evidence
in [PR33](https://github.com/jimmy-sim/poker-ai/pull/33) is already published.

## Question and definition of done

Can array methods perform the **same** finite/nonnegative checks with less
Python wrapper dispatch, without changing the training path? The measured mean's
direct NumPy all/any callees take 1.121222/1.097186 aggregate instrumented seconds
for B4/B16, including reductions. That is motivation, not a predicted speedup.
Action sampling is still the largest individual self-time frame.

Introduce a new optional implementation. Keep the old trainer, helpers, source
receipts and data frozen. Retain every validation, per-sample shape/menu/order
check, overflow rejection and copy/sum/divide operation. Change only NumPy
all/any dispatch to ndarray methods in the batch mean. B1 delegates the original.
Keep original whole-update validation. No unchecked or trusted-input shortcut,
new dependency, JIT or compiled core is part of this step.

Done means independent sparse/math and failure/alias tests, exact tiny-game
trajectory/dual-book/counter/RNG/observer identity and complete relevant local
and hosted source checks, followed by all72 real original prefix identities and
the same complete216-row forecast. Fixed config, seeds, caps, work and formula
stay unchanged. Any failed or partial attempt is retained. No unchanged favorable
retry, smaller grid, relaxed cap/tolerance or omitted slow case is allowed.

A new fitting forecast would be permission to prepare a separately checked,
published admission, not permission to erase the old failed forecast or claim
stronger play. Any eventual long study keeps the full72 paths/10m work/7200 own
and900 native caps and the original quality/report rules. It starts only when the
remaining authorized window can accommodate the full caps and safe verification.
If not, save the checked next-step boundary without scheduling future work.

## Acceptance tests fixed before code

- Independent sparse expected means and B2 enumerated products; missing rows
  contribute zero, visits sum, clipping occurs only after the mean.
- Exact old results and exception classes for nonfinite increments/sums, negative
  averages, invalid counts/visits/keys/shapes/menu widths and incomplete/excess
  streams. No input/output alias or changed accumulation order.
- Both regret rules, all batch sizes, multiple seeds and both average books on a
  nonuniform tiny game; compare every observable array, random state, counter,
  work crossing, observer fingerprint and continuation checkpoint to old code.
- Formal source-bound checks before any actual Hold'em prefix. Real72 endpoints
  match all archived states exactly;216 timing rows preserve repeat identities.
- Read-only replay with learners/reference constructors blocked; source/config/
  worker/partial-grid/deadline/schema failure tests and reproducible reports.

The narrow dispatch candidate may fail to save useful time. Report that result
honestly. This is still known-game diagnostic work, not fresh or global-agent
admission. No reference strategy enters the learner.
