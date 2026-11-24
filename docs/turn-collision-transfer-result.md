# Collision-conditioned exact-turn transfer: structural stop

**November 23, 2026 — inconclusive for poker strength.** The one-time
[prospective protocol](turn-collision-transfer.md) required three first-eligible
card/range inputs, each with at least four exact acting turn rows sharing an
original q8 turn key. The final low/wet in-position stratum had no eligible
candidate in its fixed 20-attempt allowance. The experiment stopped before
training. There is no candidate-versus-control exploitability result or default
change.

## One-time selection result

| Registered stratum | Attempts | First eligible attempt | Largest collided exact turn rows | Result |
| --- | ---: | ---: | ---: | --- |
| Medium/dry, out of position | 3 | 3 | 12 | Structurally selected |
| Medium/wet, out of position | 2 | 2 | 12 | Structurally selected |
| Low/wet, in position | 20 | None | 2 | Exhausted; required minimum 4 |

The two selected turn boards were `2s Th 5c 9h` and `Qs Kd As 3c`. These are
now **structurally inspected, known inputs**, not unseen cases. The low/wet
stratum had 17 attempts with zero collided rows and three with two; none met
the frozen four-row threshold. All 25 raw board/range inputs, their SHA-256
hashes, 50 ordered drawn/screened events, row counts and tree sizes are in the
[33-file screen archive](../results/turn-collision-transfer/screen/manifest.json).
Every attempt had no river collision and stayed below 200,000 tree nodes. The
two medium templates each had 133,131 nodes; the low template had 14,331.
These counts describe only the restricted input games and this fixed
collision-conditioned selection stream.

The selector used `PCG64(20261624)` on clean published source
`5019cf1eb2533785660d4ed2ec94c9820c368ed9` with the pinned Python
3.11.17/NumPy 2.4.6 base environment on Apple M4 macOS (10 logical CPUs).
Its internal clock was 78.67509958299343 seconds; the complete launcher took
123.26527941599488 seconds, below the 900-second whole cap. The difference
includes startup and source/input guards. No policy, best response, score,
reference output or training trajectory was read during selection. The
qualified-source [receipt](../results/turn-collision-transfer/selection-source-checks/manifest.json)
and [hosted CI](https://github.com/jimmy-sim/poker-ai/actions/runs/45306928141)
preceded the screen. The required optional Python 3.12 first-run watchdog
failure and subsequent complete same-source pass remain separate in that
receipt; no timeout or scientific threshold changed.

## Interpretation and stopping rule

This is **inconclusive**, not a negative poker-strength measurement. The
unchanged exact-turn candidate and q8 control were never trained or scored on
this cohort. In particular, the two medium inputs cannot be used as a
two-spot replacement inside this experiment: the published protocol required
all three strata before training. No cohort freeze, fictional proof, profile,
compute admission, own study or OpenSpiel comparison ran. The low/IP failure
shows the registered structural opportunity was absent within the one-time
20-candidate stream; it does not estimate collision prevalence for all boards
or establish how either representation plays low/IP poker.

The next research question should follow from this structural limitation and
the previously saved policy weaknesses, with a **new prospective protocol**.
It must identify structurally inspected cases as known, keep the failed
three-stratum gate intact, and avoid treating the two medium inputs as a
quiet continuation of this experiment. No further selection or training is
authorized by this result alone.

## Reproduce and inspect

The archived verifier checks all 25 raw input hashes, the 50 event pairs,
prior-input exclusions, board textures, range-card uniqueness, first-eligible
order, caps, source/result pins and the incomplete three-stratum stop. From
the repository root, with `../poker-env.sh` and the retained pinned base
environment installed:

```sh
source ../poker-env.sh
UV_PROJECT_ENVIRONMENT=results/runs/guarded-skip-requalification-20261118/envs/base311 \
  UV_PYTHON=3.11.17 uv run --locked python \
  results/turn-collision-transfer/screen/launcher/package_screen.py.txt verify
python3 -m json.tool results/turn-collision-transfer/screen/summary.json
```

To inspect either selected board/range input, open
`results/turn-collision-transfer/screen/attempts/collision_medium_dry_oop-03.json`
or `collision_medium_wet_oop-02.json` in the same directory. There are **no
trained river decisions** from this stopped experiment. The earlier known-game
[decision report](known-turn-exact-mechanism-result.md) and its saved-policy
inspection command remain the appropriate examples of actual turn/river
behavior; they do not establish this experiment's transfer result.

### Three checks on the conclusion

1. **Why was there no strength comparison?** The third stratum had no
   candidate meeting the predeclared structural threshold by attempt 20.
2. **Do the first two selections count as unseen validation?** No. Their
   boards and ranges were structurally inspected, and no policy outcome was
   collected on them.
3. **Would lowering four rows to two rescue the result?** That would change
   the frozen selection gate after seeing its outcome, so it is not part of
   this experiment.

Codex assisted with execution, evidence audit and this report. Human hands-on
time and personal learning were not reported.
