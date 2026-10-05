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
- 32274553 CPU holder (Revision 3, rule @ 49400ab: `--near-pct 12 --unjudged fail`,
  inside-out reported only) — COMPLETED 0:0, 4 h 00 min; `holder_32274553.done`
  calib_exit=0, jug_exit=0. Output `TORA/rank_u17/calib_32274553/` (calib.json,
  plate.png, narrow_bottle4.png). Read on Spartan by the workspace thread, 2026-10-05.
  - **Revision 3 stands on its own test:** share of genuine attempts with an unjudged
    sherd is 0.0 on all 5 pots, every class. The unjudged-fails rule rejects no correct
    reassembly on real scans.
  - Layer 1 profile cut-off **0.873%** of pot (Revision 2: 1.72%). Layer 2 unfixable
    cut-off unchanged, 2.31%.
  - Best genuine rank L1 → L1+2: plate 20 → 1, the other four 1 → 1 (1,400 attempts each).
  - Near-miss vs genuine worst-gap AUC unchanged (Layer 2 untouched): blue_pot 0.90,
    pink_bowl 0.937, plate 0.656; bottles have no near-misses.
  - Rule 3 fault, still stated: inside-out flags 100% of genuine narrow_bottle4 (sherds 1,
    3) and 54.5% of genuine plate (sherd 5); not gating.
  - `calib_32274553/{plate,narrow_bottle4}.png` (median genuine attempt) described by the
    Spartan workspace thread, 2026-10-05; not yet seen by the conservator. Same layout as
    Revision 2: every sherd on one outline, nothing stacked, floating or turned; per-sherd
    0.04–0.35 mm (Revision 2: 0.03–0.56). Plate floor sherds 4, 5 sit a few mm above the
    wall's foot, as in Revision 2 (read as the floor raised above a foot ring; inferred,
    not checked). narrow_bottle4 inside-out sherds 1, 3 lie on the S outline, not turned.
    Lead and conservator looked at both (and Revision 2 plate), 2026-10-05: "they look ok".
- Test pre-registration `../preregistration-test.md` @ 2d07202 (narrow_bottle3 the test,
  galli_pot a side case; Revision 3 cut-offs fixed; non-round bottle stated as a risk).
  Handle check before it (`scripts/u17_true_look.py`, correct reassembly only): no handles.
- 32317912 `u17_test.slurm` — COMPLETED 0:0, submitted and polled by the Spartan workspace
  thread. Log and renders copied to the project's shared folder
  (`u17_test_32317912*`). Output `TORA/rank_u17/test_32317912/test.json`.
  - **narrow_bottle3: passes.** Genuine in the Layers 1+2 top 5: yes, ranks 1–5 all
    genuine, and the top 20 are all genuine (random top 5: 13.2%; random top 20 would hold
    0.56 genuine). Layer 1 alone: best genuine 34, no top-5 hit. Near-misses above the best
    genuine: 0 of 21; worst-gap AUC 0.922. Layer 1 kept 617 of 1,400 and failed 1 of 39
    genuine (profile 1.10%, not unjudged). The non-round section did not break Layer 1:
    fitted-axis spread 8.1 mm on the median genuine, yet its profile reads 0.49%.
    4 of 39 genuine (10%) flagged unfixable at 2.31% (reported only).
  - **galli_pot (side case):** Layers 1+2 top 5 all genuine (random choice gives 1.1 of 5);
    Layer 1 alone best genuine 27. Near-misses above the best genuine: 0 of 257. Worst-gap
    AUC **0.66**, below the predicted 0.75–0.9: across all attempts Layer 2 separates
    turned sherds weakly here, yet none outranks the best genuine.
  - **Ruler fault, stated:** Layer 1 failed **31 of 305 genuine galli_pot attempts (10%)**
    on the profile cut-off (1.07–1.60% against 0.873%), none unjudged. The calibration rule
    meant to let 99% through on each pot; on this round, flat-based pot it lets 90% through.
    Not yet looked at which sherd: the render drew the median genuine attempt (base sherd 0
    reads 0.5 mm, the largest; flat floors misled Layer 1 on plate before). Pending a render
    of a failed genuine attempt, this stays unassigned between measure fault and misplaced
    sherd. Inside-out flags sherd 7 in all 305 genuine (on the outline in the render;
    misfire, not gating).
  - Looked at (lead, 2026-10-05): both top-5 renders are whole pots, every sherd green
    (own place, right way); the lobed bottle reassembled. The render titles say "Juglet" and
    "/9": `l2_top_look.py` hardcodes them (cosmetic).
  - Weight: one test pot (4 sherds) and one side case, GARF only, 1,400 attempts each.
    A lead for U17, not a finding.
