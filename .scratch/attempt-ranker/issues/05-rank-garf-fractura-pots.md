# 05: Rank the Fractura pots (GARF)

**What to build:** the ranker run unchanged on each qualifying Fractura pot, so U17 rests
on more than one pot.

**Answers:** U17

**Blocked by:** 02, 04

**Status:** ready-for-agent

- [ ] Converter reads the Fractura full-detail sherds; the converter's own check passes on
      one genuine attempt per pot
- [ ] Cut-offs in % of pot, set on the set-aside pots by `../calibration-fractura.md`
      (conservator's permission 2026-10-03), then fixed in the test pre-registration
      before narrow_bottle3 and galli_pot are scored
- [ ] Per pot: rank of each genuine attempt, top-5 hit, random baseline, Layer 1 alone vs
      Layers 1+2
- [ ] Spartan job polled; sacct State/ExitCode recorded here

## Log

- 32157454 `u17_calibrate.slurm` — COMPLETED 0:0 (1 h). Layer 1 on the 5 calibration
  pots (bin 10.77% of pot), rule `calibration-fractura.md` @ 2f47cf0. Output
  `TORA/rank_u17/calib_32157454/calib.json`.
  - Rule result: Layer 1 profile cut-off **23.42%** of pot, set entirely by plate (99th
    percentile of genuine: blue_pot 2.35, narrow_bottle2 1.86, narrow_bottle4 2.60,
    pink_bowl 3.82, plate 23.42). Layer 2 unfixable cut-off **2.31%** (plate; others
    0.80–1.48).
  - Layer 1 misbehaves on two pots: inside-out rule flags **all** 1,394 genuine
    narrow_bottle4 attempts and 55% of genuine plate attempts; plate's genuine profile
    deviation is 18.5% (median) against 1.3–3.4% elsewhere. Not yet explained; debug
    look 32159300.
  - Layer 2 on these pots (development only): near-miss vs genuine worst gap AUC
    blue_pot 0.90, pink_bowl 0.94, plate 0.66. Best genuine rank L1 → L1+2: plate
    25 → 1, narrow_bottle4 3 → 1, others 1 → 1.
