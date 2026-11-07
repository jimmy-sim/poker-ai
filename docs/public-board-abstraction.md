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

Implementation, actual checks and publication evidence will be recorded below.
No new abstraction learning/compression outcome has been measured at protocol
publication. Next: implement the two keys and correctness tests, then stop at
that reviewable milestone before the fixed-work runner.
