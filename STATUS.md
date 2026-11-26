# Status

- Maintained by `jiaxi999@163.com` (GitHub `JiaxiLEE622`). Started 2026-11. One maintainer, no
  institutional backing, no funding, no staff. The name describes an intention — to keep a
  dataset-side record of what a public dataset card actually supports — not an existing
  organisation.
- Current release: `EEO-DSR-V0.5`, schema `eeo-dataset-review/0.5`, observation
  `eeo-sync-observation/0.1`. The code tree also contains an untagged V0.6 research
  commit with the dataset-side driver and DROID variance probe, plus an uncommitted
  V0.6 positioning draft (`README.md`, `METHOD.md`, `checks/README.md`,
  `ONE-PAGER-V0.6.md`, `schema/MIGRATION-V0.6.md`).
- What exists: method, record and observation schemas, validator with 150 self-test cases,
  threshold declaration, entry/licensing text, Phase 0 disclosure census with three dated results
  (2026-11-25, 2026-11-25-r2 and 2026-11-26), and the cosine threshold helper smoke test.
- Post-V0.5 research (untagged): `tools/dataset_driver.py` implements episode→cluster aggregation,
  deff/n_eff, zero-failure bounds, cluster budget, and the rho-low cap, with an external known-answer
  fixture. The corrected DROID probe is in `research/v0.6/variance-probe/2026-11-26-r2/`:
  cell-axis n_eff interval `[53,714, 93,994]`, 93 clusters with within-cluster variation,
  point ICC 0.766531; zero-variance share is a readout, not a veto. No NEES record is issued
  without a cluster-bootstrap rho interval.
- What does not exist: the dedup detector (`episode-embedding-cosine-v1`), the clock model
  implementation, episode fingerprints, cluster-level bootstrap, any real-corpus NEES reading,
  label-consistency verification, and D1b (cards versus an index). None of these are promised.
- Scale, stated plainly: one maintainer, a handful of releases, no external users yet. Treat the
  outputs as a working record, not as an authority.

## Calibration state

- `neev.dedup.calibration_status` is `not_established` in every current record. `calibration` is
  `null`; `threshold_binding.calibration_fixture_id` is `null`.
- `tools/cosine_threshold_smoke.py` is a smoke test of cosine arithmetic on synthetic random
  vectors. It is not a detector calibration, cannot establish a false-merge or false-split rate,
  and must not be cited as evidence. A 0/59 bound is valid only when a real fixture can actually
  fail; the synthetic construction cannot.
- The real gate waits for the detector: hard negatives, W passed on the command line, at least 59
  pairs per class, exact one-sided bounds printed, runner executed, fixture and result hashes in
  the record.

## Releases

| Version | Git | Tag | Holds | Status |
|---|---|---|---|---|
| V0 | no commit by design | none | package credential only | kept as a recorded artifact, not a git release |
| V0.1 | `284f42ebfb52b815e5e852ea809c7a484f3e9252` | `v0.1` → `03d1874c98588072353e9e3d4880c8a3048a41b1` | entry and licensing layer, 0.1 schemas | published, still citable |
| V0.2 | `4e2defbd88dfe44246f7182a8197fc2eb0b947ce` | `v0.2` → `ce6c10976f0e1b38fada799f354e8ed500a185b6` | 0.2 schemas, Phase 0 first result | published, superseded by V0.3, not rewritten |
| V0.3 | `298cbf58f1f812df33f3f7e7249e8fddda0d3af6` | `v0.3` → `6882a76c54f293851aac99586b6db92668b72de8` | 0.3 schemas, withdrawn dedup gate, release gate, CI | published, superseded by V0.4, not rewritten |
| V0.4 | `7e45f1898c67cdef643a6c6dceb468e92b9985e6` | `v0.4` → `5b136c72c63a7e6ec28da9e85b580d64238ad635` | 0.4 schemas, Phase 0 source list and dual hash, FAIL/MISSING split summary | published, superseded by V0.5, not rewritten |
| V0.5 | `d2b55852d239f4c117d47026e412b9ebe5b41203` | `v0.5` → `0087d05fff1eea429f4e19b36d7459e7a80ec791` | 0.5 schemas, disclosure census, judgeability, strict S2, 20-page set | published, current release |
| V0.6 research | untagged local commit | none | dataset-side driver, DROID variance probe, known-answer fixture | untagged research, not released |

The V0.2 tag stays where it is. Corrections are published as a new version; earlier releases
stay citable and are not rewritten.

## Verification state

- Every release runs `tools/release_preflight.py` and writes `releases/<version>/preflight.json`
  before the tag is created. A gate record is a file, not a claim.
- Tags are annotated and immutable: never moved, never deleted, never force-pushed. A correction
  gets a new version and a new tag. Tag rulesets on the remote are configured separately from
  branch protection; the repository policy is in `RELEASE_GATE.md`.
- CI runs `tools/run_all_checks.py` on every push and pull request
  (`.github/workflows/reproduce.yml`).
