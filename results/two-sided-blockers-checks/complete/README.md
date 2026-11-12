# Complete cached comparison and source proof

The measurement ran only after BOTH source jobs in CI43159009130 passed on
published21d3420, and both full local bases/focused all-extras checks passed.
`source-ci-run.json` binds that exact head, successful conclusion and attempt1.
The original measured source fingerprint is519887a07b6c7df3fd92bdfe8cf62edd828abc816521136113ae7f0cbaa69022.

The decoded GitHub logs are retained byte for byte as UTF-8, including their
BOM and timestamped blank-line trailing spaces. `git diff --check` therefore
reports timestamp whitespace in these two RAW EVIDENCE files; code/docs diff
checks exclude only `source-ci311.log` and `source-ci312.log`. Do not strip or
rewrite them to make that check quiet.

| Job | Tests | Seconds | UTF-8 bytes | SHA-256 |
| --- | --- | ---: | ---: | --- |
| 130985524876 / Python3.11 | 2814passed /58skip /149deselect /1historical warning | 935.75 | 33461 | 11c69de977bc4f924f6a88c7b3219dfc40dba4f9237422bb9f3017c353441698 |
| 130985524552 / Python3.12 | 2814passed /58skip /149deselect /1historical warning | 670.86 | 33073 | 8ae0c5495bb733644b661fdf647490de69d7d497c873e46aabcdd7fb8c588192 |

The historical warning is old river-refinement replay roundoff below its
unchanged1e-12 bound; it is not a newly relaxed C8 tolerance. Local source bases
and optional logs, including the initial filename-launcher errors and corrected
passes, are in `../source-local`.

`measurement.log` records the complete11.832719541s cached-data command under
the unchanged900s cap. Manifest4559326c3ebeeb28a9340f49f234e2d303af1a73531bcd9025e141e37fb48c64
binds all outputs in `results/two-sided-blockers`. No new trajectories, policy
intervention, original full-game replay or native audit ran.

`check_cache.py.txt` reconstructs all24details/96browser conditions and navigation
with learner/reference construction blocked. Both runtime JSON receipts and the
actual default CLI output are retained. `render_report.py.txt` revalidates the
complete cache and formats every panel into the all-case table/plots. It is a
separate postprocessing command, not an extension of the scientific clock.
The first run's Matplotlib font-cache warning remains in `report311.log`.
`cross-runtime-report.json` verifies all five numeric/text/plot files match byte
for byte on311/NumPy2.4.6 and312/NumPy2.5.4. This is cached-data verification,
not bit-exact new trajectory replay. Both figures were visually inspected.

All scripts here are retained execution records. The project command remains
`scripts/diagnose_two_sided_blockers.py`; the offline browser is
`scripts/inspect_two_sided_blockers.py`. No reference strategies enter training.
