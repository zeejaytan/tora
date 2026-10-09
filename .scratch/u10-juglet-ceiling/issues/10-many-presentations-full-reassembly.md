# 10: Can TORA reach a full Juglet reassembly if it is given as many attempts as GARF?

**What to find out:** GARF, with rough or worn break-face training, made 2 genuine full
reassemblies of the Juglet (all 9 sherds in their own place and the right way round) in
about 1,400 attempts spread over many presentations (`GARF/intent/G1`). TORA's best is 8 of 9
own place (rough 1×, ticket 09), but that rests on 80 attempts, and **all of them used one
presentation** (sampling seed 42: the same sampled points and the same random input turn of
each sherd; only the 20 starts differed). On GARF the presentation decided the Juglet result
(`GARF/.scratch/rough-worn-dose/issues/03`, `07`). So TORA has not been given a fair chance.
This ticket gives each trained adapter 26 presentations × 20 attempts.

**Answers:** O8 (what stops TORA reassembling the Juglet: whether rough-trained TORA can do
it at all, given enough attempts)
**Blocked by:** 09 (the adapters)
**Status:** resolved (2026-10-05)
**Needs-eye:** any attempt that scores 9 of 9 right way round goes to visual-qa beside the
conservator's reassembly before it is called a full reassembly.

Knob: `SEEDS="42 1 … 25"` in `scripts/hpc/u10_juglet_arm.slurm` (one `sample.py` per seed,
`seed=<n>`; 42 = today's run). No retraining.

| arm | adapter (last.ckpt) | LABEL | attempts |
|---|---|---|---|
| rough 1× (08 light) s42 | `output/u10_noalign_noise_31298232_202030` | t10 | 520 |
| rough 1× (08 light) s7 | `output/u10_noalign_noise_31307631_234440` | t10s7 | 520 |
| rough 1× (09 d100) s42 | `output/u10_noalign_noise_d100_31343498_010350` | t10 | 520 |
| rough 1× (09 d100) s7 | `output/u10_noalign_noise_d100_31360433_043708` | t10s7 | 520 |
| fresh s42 (control) | `output/u10_noalign_pooled_31296425_185502` | t10 | 520 |
| fresh s7 (control) | `output/u10_noalign_pooled_31331447_153840` | t10s7 | 520 |

Readings, fixed before results (counts from `scripts/own_place.py`: own place, and right way
round = `oriented`; full = 9 of 9 right way round):
- **Control:** seed 42 for each adapter reproduces its ticket-08/09 Juglet result (e.g.
  d100 s7 best 8 of 9 own place, 1 attempt). If it does not, nothing else is read until the
  difference is explained.
- **The seed must change the presentation.** If the 26 seeds give near-identical per-seed
  means (spread ≤ 0.1 sherd), the seed is not reaching the input turn and the test is void.
- **Any rough 1× attempt at 9 of 9 right way round** → a candidate full reassembly. Rendered,
  then staged in visual-qa; recorded as achieved only after the conservator's look.
- **9 of 9 own place but fewer right way round** → near-miss, reported as such, not full.
- **None in 2,080 rough attempts** → TORA rough 1× does not reach a full reassembly at the
  number of attempts that gave GARF two; the best count and how many attempts reached it
  are reported. At GARF's rate (about 1 in 700) about 3 would be expected, so none is a real
  difference in kind, not bad luck (chance about 1 in 20).
- **Fresh control:** if fresh reaches a full reassembly too, it comes from presentations and
  attempts, not from rough training. If rough reaches one and fresh does not in 1,040, that is
  a lead (not a proof) that the training earns it.
- Per-seed mean spread for rough 1× is reported beside GARF's (1.90 worn 4× across
  presentations), as a second reading of "presentation decides it".

Weight: one real pot; four training runs of one recipe, two of the control.

- [x] Script change pushed, jobs COMPLETED 0:0, sacct recorded here
- [x] Control reproduces 08/09 -- **it does not, and the cause is found (below)**: seed 42
      no longer gives the same presentation; the counts stand
- [x] Table per adapter: best own place (attempts), best right way round (attempts), full
      count, per-seed mean spread
- [x] Any candidate rendered and staged in visual-qa -- none to stage (no 9 of 9 right
      way round)
- [x] O8 updated with the result and the date

## Result (2026-10-05)

**Jobs** (repo `fe2ba41` for 32274395, `49400ab` for the rest; each log names the adapter
listed above and STRICT diff PASS; 26 of 26 `own_place.json` per job):

| job | arm | node | sacct | elapsed |
|---|---|---|---|---|
| 32274395 | rough 1x (08) s42, `noise` t10 | gpgpu126 | COMPLETED 0:0 | 39 min |
| 32274396 | rough 1x (08) s7, `noise` t10s7 | gpgpu126 | COMPLETED 0:0 | 34 min |
| 32274397 | rough 1x (09 d100) s42, `noise_d100` t10 | gpgpu127 | COMPLETED 0:0 | 29 min |
| 32274398 | rough 1x (09 d100) s7, `noise_d100` t10s7 | gpgpu127 | COMPLETED 0:0 | 26 min |
| 32274399 | fresh s42, `pooled` t10 | gpgpu126 | COMPLETED 0:0 | 32 min |
| 32274400 | fresh s7, `pooled` t10s7 | gpgpu127 | COMPLETED 0:0 | 27 min |

**Juglet, 26 presentations x 20 attempts per adapter**, solid sherds (raw cloud in
brackets where it differs). Own place of 9 (anchor included); right way round = own place
and points a median under 4.6 mm from their own home points (`oriented`):

| adapter | best own place (attempts) | best right way round (attempts) | full | per-seed mean own place: range (spread) | overall mean |
|---|---|---|---|---|---|
| rough 1x (08) s42 | 9 (2) [raw 9 (5)] | **7 (3)** | 0 | 2.10-4.95 (2.85) | 3.55 |
| rough 1x (08) s7 | 8 (9) [raw 9 (2)] | 6 (5) | 0 | 2.35-6.20 (3.85) | 3.73 |
| rough 1x (09 d100) s42 | 8 (2) [raw 9 (1)] | 5 (3) | 0 | 2.00-4.75 (2.75) | 3.50 |
| rough 1x (09 d100) s7 | 9 (1) | 6 (1) | 0 | 2.30-5.25 (2.95) | 3.57 |
| fresh s42 | 8 (1) | 5 (2) | 0 | 1.85-3.70 (1.85) | 2.65 |
| fresh s7 | 8 (1) | 4 (11) | 0 | 1.80-3.95 (2.15) | 2.79 |

Read against the readings fixed above:
- **No full reassembly: 0 of 2,080 rough attempts, 0 of 1,040 fresh.** Best is 7 of 9 right
  way round, 3 attempts, all rough 1x (08) s42; at least 7 right way round occurs nowhere
  else.
- **9 of 9 own place but fewer right way round** (near-misses, not full): 3 solid attempts
  (10 raw), every one with 2-6 sherds turned, mostly 150-180 degrees on their own face, or
  8-25% of pot size off their own points. The GARF spun-sherd trap, not near-success.
- **The seed changes the presentation:** per-seed mean spread 2.75-3.85 sherds for rough
  (GARF worn 4x: 1.90), far above the 0.1 void line. Presentation decides TORA's Juglet
  score as it does GARF's.
- **Fresh control:** no full reassembly either; rough stays about 0.8 sherd per attempt
  above fresh (3.59 vs 2.72 own place), and only rough reaches 6-7 right way round.
- **Control (seed 42 reproduces 08/09): failed, cause found -- the ruler is not broken,
  the presentation is not repeatable.** Old and new seed-42 runs of the same adapter differ
  in every draw, and the reference cloud `pts_gt` itself differs (up to 1.2 units; parts
  identical). Ruled out on Spartan: conda env untouched since 2026-04-20, no
  site-packages entry newer than 2026-09-24, `juglet_gt.hdf5` dated 2026-08-10, config
  2026-08-14, no tracked file modified, no change under `tora/` or `sample.py` between the
  old commits and `49400ab`. Cause (read from code, not yet tested by a run): the loader
  turns, samples and shuffles the nine sherds in a thread pool (`tora/data/dataset.py:370`,
  `:502`) and every thread draws from the one global numpy stream (`Rotation.random()`,
  `tora/data/transform.py:46`; `np.random.permutation`). Seed 42 fixes the dice, not which
  sherd's thread rolls first. Scoring is unaffected: each sherd is still scored point for
  point against its own home. Every adapter's old seed-42 mean (2.55-4.40 own place) lies
  inside its own new 26-presentation range. The conservator chose to read the result on
  this explanation (2026-10-05) rather than run a repeat check first.
- **Against GARF:** GARF reached 2 genuine full reassemblies in about 1,400 attempts. At that
  rate about 3 would be expected in 2,080, and none happening is about 1 chance in 20, as
  stated above. **Narrowed on reading:** that figure treats GARF's rate as known, and it
  rests on two events. Compared as two counts (2 of 1,400 against 0 of 2,080), all-zero on
  TORA's side is about 1 in 6 by chance. So: TORA rough 1x did not reach a full
  reassembly at the attempt count that gave GARF two; that is a lead that GARF does better
  here, not a proof.

**Which of the three:** the method -- TORA, rough-trained or not, did not reassemble the
Juglet in 3,120 attempts. Separately, a repeatability fault in the loader (the presentation
behind any TORA "seed N" run cannot be re-made), which costs reruns, not these counts.
Consequence: ticket 09's 8-of-9 attempt shown in visual-qa (`u10_juglet_rough1x_t09`) is
kept on disk but cannot be regenerated. Fix (not made; changes TORA's behaviour, ask
first): give each sherd its own stream seeded from (seed, sample, sherd).

**Weight:** one pot; four training runs of one recipe, two for
the control; 26 presentations each.
