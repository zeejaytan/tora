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
- 32159300 `l1_look.slurm` — COMPLETED 0:0. `artifacts/rank_u17/l1look_32159300/`. Both
  are **broken measurements**, not wrong placements (axis and wall profile are right in
  both pictures: every sherd lies on one clean profile curve).
  - plate: deviation comes from the two floor sherds (4: 30.7%, 5: 24.3% median; rim
    sherds 3–4%). Layer 1 takes one outer radius per height band; on a flat floor one
    band spans centre to rim, so a centre sherd "misses" the rim radius by the floor's
    width. Inside-out flag on sherd 5 (404/741): a nearly flat floor sherd, curvature
    direction arbitrary.
  - narrow_bottle4: sherds 1 and 3 flagged in every genuine attempt. Both run from belly
    over the shoulder into the neck (S-shaped); one sphere fitted to an S curve puts its
    centre outside the pot. narrow_bottle3 is the same kind of bottle.
- Repair (conservator's option 1, 2026-10-03): `--profile outer` + inside-out reported
  only; rule file Revision 2; commit bdd585e. A first try (`loo`, nearest point in the
  (r, h) plane, both surfaces) failed its synthetic check and was never run.
- 32160629 `u17_calibrate.slurm` (Revision 2) — submitted, polled. Outputs
  `TORA/rank_u17/calib_32160629/` (calib.json, plate.png, narrow_bottle4.png).
- 32160629 — COMPLETED 0:0 (1 h 24 min). Rule @ bdd585e (Revision 2).
  - Layer 1 profile cut-off **1.72%** of pot (was 23.42%); per-pot 99th percentile of
    genuine: blue_pot 0.64, narrow_bottle2 0.47, narrow_bottle4 0.82, pink_bowl 0.98,
    plate 1.72. Layer 2 unfixable cut-off unchanged, 2.31%.
  - Genuine attempts passing Layer 1: 100% on four pots, 98.9% on plate. No sherd unjudged
    in any attempt on any pot.
  - Rule 3 fault, stated: inside-out rule still flags 100% of genuine narrow_bottle4 and
    54.5% of genuine plate (not gating any more).
  - Layer 1 barely separates classes here (near-misses pass too, as expected: their sherds
    are in place, only turned); narrow_bottle4 "other" 5 of 6 fail. Best genuine rank
    L1 → L1+2: plate 14 → 1, others 1 → 1.
  - Looked at `artifacts/rank_u17/calib_32160629/{plate,narrow_bottle4}.png`: every sherd's
    outer surface on one outline, per-sherd 0.03–0.56 mm. Measure reads what it should.
