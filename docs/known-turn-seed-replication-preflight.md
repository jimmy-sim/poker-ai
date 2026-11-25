# Seed-replication preflight: deterministic exact-turn training

**Issue #4; November 24, 2026 (PST). Result: stop before a seed study.** The proposed question was whether [PR #114's](https://github.com/jimmy-sim/poker-ai/pull/114) matched-work exact-turn improvement repeats across training seeds on its two already known wet/dry games. That PR is history-merged with all checks green and a **negative** frozen strength result: wet 40m exact-turn exploitability is `0.01004401976136313` initial pots, above its unchanged `0.01` absolute limit, although both candidate-control pairs improve. This preflight reads its published source and saved policies only. It trains no policy, changes no learner, and collects no new poker outcome.

## Finding and evidence

Changing a seed label cannot change this trainer's trajectory:

1. The [PR #114 worker](../scripts/study_known_turn_work_budget.py) constructs a `PathSpec` and calls `capture_path`. The [capture adapter](../scripts/turn_exact_transfer/capture.py) writes `path.seed` to identity and snapshot metadata, but calls `medium_dry_full.learning.train(tree, labels, ...)` **without a seed argument**.
2. That [trainer constructor](../scripts/medium_dry_full/learning.py) always creates `Generator(PCG64(0))` with `traversal="full"`, signed regret and linear averaging. Exact initialization uses `expected_pass` for both seats. Each later full step uses `expected_pass`; the only `rng.choice` call in [ControlledTrainer](../src/poker_ai/postflop/controlled_training.py) is in `select`, passed only to the separate `external_updates` branch. The `full` branch never invokes it. The observer also rejects any change to the RNG state between complete passes.
3. Every one of the 24 published PR #114 checkpoint metadata states (four paths × three work checkpoints × two readouts) equals the untouched `PCG64(0)` state. The check below reads the [published own archive](../results/known-turn-work-budget/own/manifest.json); it does not run training.

From the repository root, reproduce the saved-state check with the pinned project environment:

```sh
source ../poker-env.sh
uv run --locked python - <<'PY'
import json
from pathlib import Path
from numpy.random import Generator, PCG64

initial = Generator(PCG64(0)).bit_generator.state
folders = sorted(Path("results/known-turn-work-budget/own/study").glob("path*"))
assert len(folders) == 4
for folder in folders:
    saved = json.loads((folder / "summary.json").read_text())
    states = [row["metadata"]["rng_state"] for row in saved["captures"]]
    assert len(states) == 6 and all(state == initial for state in states)
    print(folder.name, saved["path"]["game"], saved["path"]["arm"], "RNG unchanged")
PY
```

The static call path explains **why** seed choice has no effect; the saved states corroborate it on the completed run. Merely changing `PathSpec.seed` would alter metadata, while `train` would still use `PCG64(0)`. Even changing that constructor's seed without changing the algorithm would leave the full expected updates unchanged. Multiple nominal seeds would be identical trajectories, not independent estimates of variability or reproducibility. No seed list, new protocol, compute admission or duplicate 40m study was started.

## Next question, if separately authorized

A useful alternative is a **prospectively selected set of distinct board and range inputs** under the unchanged exact-turn learner and matched-work q8 control. Input selection, known versus genuinely uninspected status, work budget, metrics, absolute and paired gates, compute forecast/caps, and publication order would need a separate protocol before any outcome is collected. Variation across games would measure sensitivity to game inputs, **not** training-seed uncertainty; previously inspected cases must remain labeled known. This is a proposal only. PR #114's negative acceptance and all historical thresholds, source pins and failed evidence remain unchanged. Do not promote a default from this preflight.
