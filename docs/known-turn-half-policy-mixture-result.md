# Fixed half mixture of saved turn policies: negative

**Issue #4; PR #118; November 27, 2026 (PST).** This is the frozen result of the [prospective protocol](known-turn-half-policy-mixture.md). The candidate averages legal-action probabilities, 50:50 at every exact information row, from PR #116's final 40m linear-average q8 control and exact-turn policy. It is a behavior-policy mixture, not a new trained strategy or a random choice of one complete parent. All four inputs were already selected, trained and outcome-inspected in PR #116. They are known, dependent, collision-containing medium out-of-position restricted games.

## Registered strength decision

The metric is exact restricted-game NashConv/2 divided by the 36-chip initial pot; lower means less best-response gain against the saved strategy. The primary comparator is the same-game q8 parent. Every parent was trained to 40,205,562 charged visits. The offline mixture used no training work or RNG; its inherited `PCG64(0)` metadata is not a replication seed.

| Known input; turn board | q8 control | Exact-turn parent | 50:50 mixture | Mixture minus q8 |
| --- | ---: | ---: | ---: | ---: |
| Dry A; `4c Ks 9d Ts` | 0.018245221 | 0.013575482 | 0.014945376 | −0.003299845 |
| Wet A; `7s 9h 6s 2s` | 0.017125132 | 0.017677381 | 0.015469824 | −0.001655308 |
| Dry B; `5c 8s Jh 9c` | 0.030011787 | 0.020656811 | 0.024008320 | −0.006003468 |
| Wet B; `Ad Kc Jd 9s` | 0.017896174 | 0.016751887 | 0.015685627 | −0.002210546 |

**Classification: negative.** All four mixture values exceed the preregistered `≤0.01`-pot absolute limit. The redundant `≤0.025` worst-value check passes, and all four paired differences satisfy the preregistered `≤−0.001` improvement threshold, including dry and wet inputs. Paired improvement cannot replace the failed absolute gate. The mixture is better than *both* saved parents on wet A and wet B, but worse than the exact-turn parent on dry A and dry B. No default was promoted.

The [fixed machine report](../results/known-turn-half-policy-mixture/report/report.json) binds each value to the saved policy SHA-256, both published parent scores, zero perfect-recall violations, and the [independent audit](../results/known-turn-half-policy-mixture/native/manifest.json). Its largest own/OpenSpiel 2.0.2 scalar difference was `7.105427357601002e-15` chips, below `1e-9`. The installed Apache-2.0 license SHA-256 was `cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30`; reference outputs entered no training or policy construction. The [complete own archive](../results/known-turn-half-policy-mixture/own/manifest.json) retains all four mixed policy snapshots, each with 8,340 validated exact information rows, scores, hashes and per-case events. Own whole-process time was 99.004 seconds (<900) with peak RSS 1,436,631,040 bytes (<1,500,000,000); audit time was 103.162 seconds (<900) with peak RSS 1,247,379,456 bytes. The qualified [source](../results/known-turn-half-policy-mixture/source-checks/manifest.json), fictional [proof](../results/known-turn-half-policy-mixture/own-proof/manifest.json), and [data-only admission](../results/known-turn-half-policy-mixture/admission/manifest.json) preceded these measurements. The first optional Python 3.12 qualification timeout and a pre-proof sandbox launch denial remain retained separately; neither is a poker score.

## One already inspected decision

PR #116's fixed report had already ranked dry A's `2s 9s` turn row, on `4c Ks 9d Ts`, first by the q8 control's additive turn best-response gain. Its legal actions are `check`, `raise_to 36`, `raise_to 182`. At exact information row 2430, q8 assigns `[0.029241, 0.967571, 0.003188]`, exact-turn assigns `[0.055657, 0.928994, 0.015349]`, and the saved mixture assigns `[0.042449, 0.948283, 0.009269]`. This verifies the per-row probability average on a representative **previously inspected** hand. PR #116's parent row values assumed each parent's own saved opponent and optimized best-reply continuation. This report does not calculate a mixed-policy local contribution, so those parent values cannot explain the mixture's aggregate score or serve as universal action advice.

Inspect the same saved row and final score without training:

```sh
PYTHONPATH=src:scripts results/runs/guarded-skip-requalification-20261118/envs/base311/bin/python - <<'PY'
import json
from pathlib import Path
from known_turn_half_policy_mixture.plan import ARMS, parent_context
from poker_ai.postflop.controlled_checkpoints import read_snapshot

root = Path.cwd()
game, row = 'collision_medium_dry_oop_a', 2430
saved = json.loads((root / 'results/known-turn-half-policy-mixture/own/result.json').read_text())['rows'][0]
context = parent_context(root, game, ARMS[1])
mixed = read_snapshot(root / 'results/known-turn-half-policy-mixture/own/game00-mixed.json.gz', context.exact, saved['receipt'], saved['metadata'])
prior = json.loads((root / 'results/known-turn-collision-medium-transfer/report/report.json').read_text())
known = next(d for d in prior['diagnostics'] if d['game'] == game and d['exact_info'] == row)
print(known['hole'], known['board'], known['legal_actions'])
for observation in known['observations']:
    if observation['readout'] == 'linear_average' and observation['work_label'] == 40000000:
        print(observation['arm'], observation['saved_probabilities'])
print('mixture', mixed[row, :len(known['legal_actions'])].tolist())
report = json.loads((root / 'results/known-turn-half-policy-mixture/report/report.json').read_text())
print('classification', report['classification'], 'dry A', report['cases'][0])
PY
```

These four deterministic inputs have no seed-sampling interval or valid independence claim. The result says that this particular mixture reduces q8 exploitability on these already known games but remains above the absolute strength target. It does not test unseen boards/ranges, a full Hold'em game, or a human opponent. A distinct future question must be registered before any new outcome or training; this failed absolute gate remains unchanged.

## Final source and report qualification

The exact negative-report head `71b0c62b` passed [final local and hosted qualification](../results/known-turn-half-policy-mixture/final-checks/manifest.json). Base Python 3.11 and 3.12 each passed 5,864 fast tests, with 73 skips and 150 marked slow tests deselected, plus Ruff, formatting and strict mypy. Optional Python 3.11 passed 2,601 tests; optional 3.12 passed 2,599 with two skips. Every lane passed clean pre/post exact-source, published-evidence, runtime and lock guards; optional lanes also checked the installed OpenSpiel license. All-file hooks and report-head hosted CI passed both 3.11 shards, full 3.12 and aggregate. The receipt retains two pre-test operational launch failures: one background attempt did not start a process, and one guard stopped on ambient uv 0.13.9 before tests because 0.13.5 is required. The corrected pinned run passed without changing source, protocol, thresholds or scientific data. Receipt-head CI and solo review are tracked separately before merge.
