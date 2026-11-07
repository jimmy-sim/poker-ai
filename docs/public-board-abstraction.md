# Public-board representation: protocol and correctness

Issue [#4](https://github.com/jimmy-sim/poker-ai/issues/4) asks whether the learner
can remember useful board information while sharing strategy rows across boards.
This protocol is declared before new representation-learning outcomes. The
[config](../configs/public-board-study.json) is prospective, not a result or an
implemented end-to-end experiment command.

## This block's definition of done

Implement two opt-in observation keys, document their exact observable inputs,
and test suit/flop-order invariance, reveal order, abstract recall, legal menus,
and independence from hidden opponent/future cards. Preserve the three existing
encodings and all old evidence. Publish checked code and this protocol in a PR.
Stop before collecting new learning or representation-compression outcomes.
Issue #4 stays open for the fixed-work comparison and later admission decision.

## Observable information and controls

All keys retain the existing potential-8 private bucket sequence, seat, button,
street, stacks, total commitments and complete betting history. Keys accept an
acting player's `Observation`, never a dealer state. The current actor is checked
before a key is built. No opponent cards, remaining deck or actual future runout
may be consulted. Private bucket features use their existing deterministic own
card/public board sampler; simulated potential is not knowledge of the dealt future.

The five controls use the same cards, actions, feature model and learner:

| Encoding | Public information added to the existing private bucket key |
|---|---|
| `exact` | Existing exact own cards and observed board control |
| `legacy_b8` | None; retained historical baseline |
| `public_b8` | Existing raw observed board control, unchanged |
| `canonical_b8` | Exact public ranks and suit relationships, with suit names removed |
| `texture_b8` | A coarse feature vector for every observed street prefix |

The canonical control considers all 24 global suit renamings and selects the
lexicographically smallest card tuple. Within that tuple only the first three
cards (the flop) are sorted; turn and river remain in reveal order. One global
renaming applies to the whole observed board. This preserves all public card
information except arbitrary suit names and flop deal order. It does not preserve
the exact relationship to private-card suits beyond the existing private bucket.
This is a card-encoding symmetry, not a claim that all merged decisions are
strategically equivalent: fixed asymmetric physical ranges would also need the
same global renaming to preserve a whole game's meaning. The bounded comparison
must measure that possible loss rather than assume canonical keys are exact.

The texture candidate stores these features for each available prefix of lengths
3, 4 and 5 (preflop has an empty sequence):

- Sorted rank multiplicities, padded to five entries, e.g. `(2,1,1,0,0)`.
- Sorted suit counts, padded to four entries, e.g. `(3,1,0,0)`.
- Number of ten-or-higher cards and number of aces, counting physical cards.
- Maximum number of distinct board ranks in any five-rank straight window.
  Windows include ace-low `A2345` and every ordinary window through `TJQKA`.

Each feature is calculated from that prefix alone. Storing every prefix prevents
the river key from forgetting the earlier abstract board. The flop is unordered;
turn and river order matters through their separate prefixes. Feature values
have finite small domains independent of the number of physical boards. The
combined key can still be large because private bucket/history sequences remain.

**Illustrative example:** `2c 3d 7h` and `3c 4d 8h` have the same coarse texture.
Their exact ranks differ, so the canonical control separates them. This is an
intentional public-information collision, not proof that they deserve the same
strategy. Texture also loses rank-to-suit associations and exact blocker effects;
the later error/learning measurements must assess those losses honestly.

Recall here means **abstract perfect recall**: a later strategy row cannot merge
different past abstract observations/actions of that player. It does not mean
remembering every physical card; that would defeat the abstraction. Test both
prefix retention and the complete materialized small game's recall structure.

## Prospective learning comparison, not run in this block

Use the two existing development games, not previously fresh cases relabeled as
unseen. Run all five controls with the fixed seeds, checkpoints and limits in the
config. The selected candidate is `texture_b8`; do not choose a winner afterward.
First verify mechanics/recall and the exact-control gate. A failure stops admission
to any later fresh-case/global stage; retain all planned development cells even
when a representation misses its target, unless the compute/safety cap aborts it.

Full-tree CFR+ checkpoints end at 4,096 iterations. Ordinary external sampling
uses linear weighting and one exact initialization, retained from issue #3.
Compare sampled runs at 100k, 1m and 10m charged node visits including initialization,
retaining actual overshoot/work. Profile 1,000 iterations three times before the
full grid; total runtime cap is two hours and node cap is 200,000 per game.
Exact initialization and materialized trees remain a scalability limitation.

Require the exact control's full exploitability <=0.1% pot, sampled median <=1%
and worst <=2.5%, and initialized average-row reach coverage >=95%. On both games
the candidate must also meet those sampled/coverage limits, full exploitability
excess over the exact full control <=0.5% pot, zero recall violations, and <=75%
as many strategy rows as the raw-public-8 control. A small game with no compression
can fail this criterion; do not soften it afterward. Independent own policy
value/best-response agreement must be within 1e-9 chips. Native reference output
is comparison-only and never enters own training or policies.

Report public and private collisions, chance-weighted collision reach,
key/table bytes and peak RSS, initialized versus subsequent coverage and initial-only
rows, exact-game exploitability and ordered pairwise cross-play EV. Use uniform
policy decision reach for collision/coverage weighting and report on-policy
coverage separately; normalization is total decision reach, not number of rows.
Keep all seeds and non-monotone curves. A three-seed range is not a confidence
interval. No new training runner or performance claim is delivered in this block.

## Historical reproduction

Adding source changes the deliberately strict issue #3 source freeze. Preserve
that manifest unchanged. Reproduce that historical study in a separate checkout
of `d587b81de598f9aca713cbff752bafeaefe127e0`, following
[the original protocol](fresh-validation.md). Current-source freeze rejection
after this change is expected; it must not be bypassed or relabeled as new evidence.

## Verification and remaining work

Protocol commit `d120490` was published before implementation/outcomes.
[PR #12](https://github.com/jimmy-sim/poker-ai/pull/12) implements both opt-in keys
and the board inspector. The 29 new tests cover card validation, all 24 suit
renamings, flop permutations, prefix retention, actual hidden-opponent/future
invariance, old key compatibility and both development games' menus/recall.
A separate regression confirms the archived source freeze rejects changed code.
Matching-source gate unit tests use explicitly labeled in-memory metadata
fixtures; no archived report, manifest or admission receipt is changed.

`make check` passes locally with **650 tests** on Python 3.11.17 and 3.12.15,
including all locked optional extras, Ruff and strict mypy. Hosted CI is reported
separately on the PR. The initial full-suite run failed on the old positive
historical-admission test; preserving the production rejection and separating its
test fixture resolves that failure. No gate or performance threshold was relaxed.

Try the read-only inspector or focused tests from the repository root:

```sh
.venv/bin/python scripts/inspect_public_board.py Ac Kc 2d 7c 7d
.venv/bin/python -m pytest -q tests/test_public_board.py
```

No learning/compression experiment has run, no global default changes, and issue
#4 remains open. Next milestone: implement and audit the configured fixed-work
comparison, retaining negative outcomes. Do not use these checks as evidence of
stronger play or measured memory savings.

## Questions to practice

1. **Why remember every street's features?** A final board feature can merge two
   different turn situations. Keeping the prefix sequence preserves what the
   player knew earlier at the abstract level.
2. **Does canonicalizing suits make the representation exact?** Only the public
   card encoding is preserved up to renaming. Private buckets and asymmetric
   fixed ranges can still make merged decisions strategically different.
3. **How will we decide whether texture helps?** Compare every fixed control at
   matched work and require both the preregistered accuracy and compression
   limits. Correctness tests alone do not answer that question.
