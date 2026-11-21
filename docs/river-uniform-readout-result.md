# Fixed river average-readout panel: compute gate rejected

**Status (November 21, 2026):** poker-strength comparison **inconclusive**.
The prospective profile completed all 36 prescribed 100,000-node-work paths,
but its predeclared conservative 10m-work forecast was **8,885.116605 seconds**
against the strict **7,200-second** admission cap. The long own study did not
start. Neither uniform nor linear averaging is shown to improve the four
selected spots, and no default changes.

## What was fixed before measurement

The [prospective contract](river-uniform-readout-spots.md) fixed one PCG64
cohort-selection seed, four structural strata on already known public betting
templates, training seeds 20261411–20261413, an unchanged signed B4
exact-river path, uniform-average candidate and same-path linear-average
control, work labels 100k/1m/10m, exploitability and coverage gates, three
profile repeats, worker partition, compute caps, and own-before-reference
publication. The four card/range inputs were [selected and frozen
once](../configs/river-uniform-readout-freeze.json) before any scoring. They
are not unseen public templates. Source commit `3e837b7` and source fingerprint
`a982d8c3537f9d50aa721001a0436766f34e862732b8e1b514fdc79355a963f6`
preserved the historical source pins. The complete [source
qualification](../results/river-uniform-readout/source-checks/manifest.json)
and [fictional own proof](../results/river-uniform-readout/own-proof/manifest.json)
were published and GitHub-byte-verified before this profile. The first
optional Python 3.12 local timeout and setup failures remain in those
archives; one bounded same-source requalification and all required hooks
passed. Source-receipt hosted CI 44890447788 passed both Python jobs.

## One fixed profile and its gate

The single [raw profile and failure receipt](../results/river-uniform-readout/profile/manifest.json)
ran at `9ce74c258a1e6bf7ee074739299cf7135a8c8bcd` on an Apple M4,
macOS 27.2.1, Python 3.11.17 and NumPy 2.4.6. Three spawned workers completed
all 36 paths (12 fixed spot/seed paths, three repeats), including each path's
context construction, 100k-work learner, own scoring and snapshot replay.
Actual final node work per path ranged from 100,003 to 100,170. The entire
profile used 54.230126 seconds of its 900-second cap; launcher wall time was
54.709598 seconds. Maximum reported worker peak RSS was 241,221,632 bytes.
No worker or path failed. The runner retained `failure.json` because the
forecast gate failed after the complete profile; the raw path files were not
deleted or selected by outcome.

The frozen rule scales each complete path time to 10m/actual final work,
takes the **largest of its three repeats**, sums those maxima in the fixed
worker partition, then takes the largest worker sum `T`. The three worker
sums were 1,918.269436, 1,919.388448 and **1,921.279151 seconds**. Thus
`2 × (2 × T + 600) = 8,885.116605 seconds`, exceeding the strict 7,200-second
cap by **1,685.116605 seconds**. Recomputing the frozen forecast from the
complete failed record reproduced `forecast.json` exactly. This is a
rejected compute admission, not a failed poker result. The separate admission
and 10m own run were not launched; the 1m/10m paired seed metrics, final
coverage, full-work memory/runtime and independent native scalar audit do
not exist. The 100k profile artifacts are timing evidence, not a substitute
for the prespecified strength comparison.

## Interpretation and next decision

The conservative formula counted the entire path, including fixed overhead,
at the 100-fold work scale and doubled the slowest fixed-worker sum with a
600-second margin. The observed 100k profile was fast enough to finish, but
the *prespecified* extrapolation did not admit the longer run. We cannot infer
the uniform-minus-linear exploitability direction, acceptance gates, or
representative final river decisions from this incomplete comparison.
No reference strategy was loaded, and no candidate was tuned or promoted.
This experiment ends at its failed compute gate. Any further strength test
would need a distinct prospective question and budget, not a retry or changed
threshold for this cohort.

To inspect the exact gate and retained paths:

```sh
python3 -m json.tool results/river-uniform-readout/profile/forecast.json
python3 -m json.tool results/river-uniform-readout/profile/verification.json
python3 -m json.tool results/river-uniform-readout/profile/repeat0/path00/summary.json
```

To recompute the forecast from the published failed record without editing it,
install the committed lockfile (`make setup`), then run:

```sh
uv run --locked python - <<'PY'
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path.cwd() / "scripts"))
from river_uniform_readout.forecast import forecast

folder = Path("results/river-uniform-readout/profile")
record = json.loads((folder / "failure.json").read_text())
record["status"] = "completed"  # Restore the pre-gate worker status in memory only.
calculated = forecast(record)
assert calculated == json.loads((folder / "forecast.json").read_text())
print(calculated["status"], calculated["strict_bound_seconds"])
PY
```

Codex assisted with implementation, checks and this report. Human hands-on
time was not reported. No independent full-game poker-strength claim follows
from these finite restricted spots or from this rejected forecast.
