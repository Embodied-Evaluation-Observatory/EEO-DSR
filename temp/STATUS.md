# Status

- Maintained by `jiaxi999@163.com` (GitHub `JiaxiLEE622`). Started 2026-11. One maintainer, no
  institutional backing, no funding, no staff. The name describes an intention — to keep a
  dataset-side record of what a public dataset card actually supports — not an existing
  organisation.
- Current release: `EEO-DSR-V0.6.5` on `main` (`f1a389343372ad35d1a8903b610fb38f4f319f9e`, tag `v0.6.5` → `c6bbfff337c043b8ceeec9b3a3841d53eb4915ba`), schema still `eeo-dataset-review/0.5`
  pending the `chain.readout` migration, observation `eeo-sync-observation/0.1`.
  V0.6 separates ITR / NEES / ICR and makes G1-G3 labeling obligations rather than a single release gate;
  the public and interface rules are in `GOVERNANCE-ADDENDUM.md`.
- What exists: method, record and observation schemas, validator with 150 self-test cases,
  threshold declaration, entry/licensing text, Phase 0 disclosure census with three dated results
  (2026-11-25, 2026-11-25-r2 and 2026-11-26), the cosine threshold helper smoke test, and
  `tools/feature_representation.py` plus `tools/reference_deviation.py`; a real DROID fingerprint
  sample (1,999 episodes, two declared state/action representations) and a hard-negative calibration
  at a research placeholder W.
- 2026-11-27 worktree (not committed): paired fixed/full comparison with paired 2×2 and continuous
  width/endpoint comparison; energy-distance diagnostic with 0.9 subsampling intervals and pooled
  nulls; bidirectional TRI↔Gates site deviation; 43 success-conflict label-consistency readout;
  three equivalence classes; 20-card Phase 0 baseline (old three-state wording; four-state not rerun) plus a separate 2-card RoboMIND/RH20T supplement; local pre-check layer and aggregate register.
  See `research/v0.6/2026-11-27-recap/`, `research/v0.6/reference-and-representation/2026-11-27-readout/`
  and `MINIMAL-SIGNABLE.md`.
- V0.6 research (now in V0.6.5): `tools/dataset_driver.py` implements episode→cluster aggregation,
  deff/n_eff, zero-failure bounds, cluster budget, and the rho-low cap, with an external known-answer
  fixture. The corrected DROID single-source probe is in `research/v0.6/variance-probe/2026-11-26-g3-single-source/`:
  three axes on 73,413 rows, site K=69 / n_eff=589.745, task_text K=2,418 / n_eff=6,053.998,
  native K=2,220 / n_eff=5,953.539. The mirror `building||language_instruction` text-unit axis
  (K=53,714; point ICC 0.766531) is not a task axis and is not published as one. No NEES record
  is issued without a calibrated conditional interval; the current readout is point-only.
- What does not exist: the production dedup detector (`episode-embedding-cosine-v1`), the clock model
  implementation, a buyer reference distribution, a declared DROID train/test split for D5b, any
  real-corpus NEES reading, D2 inter-annotator agreement, `near-take` equivalence-class definition,
  D1b (cards versus an index), a 50–100-card Phase 0 expansion or public dashboard, a formal ITR
  record, and reconciliation of the tie-break subset K=2,432 with the single-source task_text K=2,418. Cluster-level bootstrap exists as a research tool, but its nominal 95% coverage is not
  established. None of these are promised.
- Scale, stated plainly: one maintainer, a handful of releases, no external users yet. Treat the
  outputs as a working record, not as an authority.

## Calibration state

- `neev.dedup.calibration_status` is `not_established` in every current record. `calibration` is
  `null`; `threshold_binding.calibration_fixture_id` is `null`.
- `tools/cosine_threshold_smoke.py` is a smoke test of cosine arithmetic on synthetic random
  vectors. It is not a detector calibration and must not be cited as evidence; a 0/59 bound is valid
  only when a real fixture can fail.
- The 1,999-episode DROID sample has real same-task / same-scene negatives and controlled re-encoded
  positives at 0.5% and 2% feature noise. At W=0.90, summary FPR 2/246 and 0.5%-copy FNR 5/150;
  traj16 FPR 0/246 and 0.5%-copy FNR 0/150. Exact one-sided bounds are in the fixture. W remains a
  research placeholder, not a buyer threshold.
- The real gate still waits for a declared buyer W, a fixture that can actually fail, at least 59
  pairs per class, and the record fields with fixture/result hashes. The production detector is not
  implemented. At W=0.90 the 2% copy FNR is 96/150 for summary and 60/150 for traj16; `0/150` and
  `2/246` are Clopper–Pearson upper bounds, not working points.

## Releases

| Version | Git | Tag | Holds | Status |
|---|---|---|---|---|
| V0 | no commit by design | none | package credential only | kept as a recorded artifact, not a git release |
| V0.1 | `284f42ebfb52b815e5e852ea809c7a484f3e9252` | `v0.1` → `03d1874c98588072353e9e3d4880c8a3048a41b1` | entry and licensing layer, 0.1 schemas | published, still citable |
| V0.2 | `4e2defbd88dfe44246f7182a8197fc2eb0b947ce` | `v0.2` → `ce6c10976f0e1b38fada799f354e8ed500a185b6` | 0.2 schemas, Phase 0 first result | published, superseded by V0.3, not rewritten |
| V0.3 | `298cbf58f1f812df33f3f7e7249e8fddda0d3af6` | `v0.3` → `6882a76c54f293851aac99586b6db92668b72de8` | 0.3 schemas, withdrawn dedup gate, release gate, CI | published, superseded by V0.4, not rewritten |
| V0.4 | `7e45f1898c67cdef643a6c6dceb468e92b9985e6` | `v0.4` → `5b136c72c63a7e6ec28da9e85b580d64238ad635` | 0.4 schemas, Phase 0 source list and dual hash, FAIL/MISSING split summary | published, superseded by V0.5, not rewritten |
| V0.5 | `d2b55852d239f4c117d47026e412b9ebe5b41203` | `v0.5` → `0087d05fff1eea429f4e19b36d7459e7a80ec791` | 0.5 schemas, disclosure census, judgeability, strict S2, 20-page set | published, superseded by V0.6, not rewritten |
| V0.6 | `0426c4e9cfd2f846f28f4ee02b67a990e4c90a10` | `v0.6` → `ca070eb4ef1594b9febc2ecd524dfda159adb6eb` | V0.6 positioning, ITR/NEES/ICR split, README About/License | published, superseded by V0.6.1, not rewritten |
| V0.6.1 | `f82c56481e3999b121b0f2975f2cbc1c3ea40d91` | `v0.6.1` → `022f73596664f45a9bd88dddb056751dfcff0cf9` | G1/G2/G3 first batch | published, superseded by V0.6.2, not rewritten |
| V0.6.2 | `d4176c007e6a631f39cad29ce056dad2190900f1` | `v0.6.2` → `333fb6969f44f150e87e607eac00c6520972de25` | cell coverage-vs-B, site/task_text B choice, two-rate Phase 0, row universes, width sign fix | published, superseded by V0.6.3, not rewritten |
| V0.6.3 | `9660e199a90df82545d15f4a8938cdc43722b4f2` | `v0.6.3` → `a84e1b6a06dfdf3d0eeff2bfd6eb23888d7dc07f` | interval method check, reference deviation tool, shared fingerprint upstream | published, superseded by V0.6.4, not rewritten |
| V0.6.4 | `d218ed91067c3bb1a2be53210c00788743a76581` | `v0.6.4` → `7a8b4fdcb4c67c32e647bb0c17e7c178ea1da354` | governance addendum, public/interface rules, G2 split rule, row-universe labels | published, superseded by V0.6.5, not rewritten |
| V0.6.5 | `f1a389343372ad35d1a8903b610fb38f4f319f9e` | `v0.6.5` → `c6bbfff337c043b8ceeec9b3a3841d53eb4915ba` | cell full-K control, G2 split, DROID fingerprint sample and hard-negative calibration | published, current release |

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
