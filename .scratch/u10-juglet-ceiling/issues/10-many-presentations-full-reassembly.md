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
**Status:** in-progress
**Working in:** project thread "Check the juglet full-reassembly run" (2026-10-05)
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

- [ ] Script change pushed, jobs COMPLETED 0:0, sacct recorded here
- [ ] Control reproduces 08/09
- [ ] Table per adapter: best own place (attempts), best right way round (attempts), full
      count, per-seed mean spread
- [ ] Any candidate rendered and staged in visual-qa; conservator's look recorded
- [ ] O8 updated with the result and the date
