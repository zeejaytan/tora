# 06: A second method: TORA's Fractura attempts

**What to build:** the same ranker on TORA's attempts, so the result is not one method's.

**Answers:** U17

**Blocked by:** 05

**Status:** resolved (2026-10-05)

- [x] Converter reads TORA's saved attempt clouds (the `u10_fractura_*` evaluation runs);
      the converter's own check passes (after the scale fix, 0dce053)
- [x] TORA attempts labelled for right way round
- [x] Decision recorded: are 20 attempts per pot enough? Yes: 28 runs x 20 = 560 per pot
- [x] Per pot: genuine ranks, top-5 hit, random baseline (job 32330575)

## Log

- Labels: `TORA/rank_u17/tora_fractura_labels.json` (b5291fb). Qualifying pots:
  narrow_bottle3 (9 genuine, 34 near-miss of 560), plate (5, 71 of 560). Decision: 560
  attempts per pot is enough, no rerun (`../preregistration-tora.md` @ c3559e7).
- 32329999 `u17_test_tora.slurm`, COMPLETED 0:0 (9 min 25 s), polled by the Spartan
  workspace thread. `TORA/rank_u17/tora_32329999/`; log and renders in the project folder
  as `u17_tora_32329999*`. Converter self-check 10/10 on both pots.
  - **narrow_bottle3 passes.** Best genuine rank 1 of 560 under Layers 1+2 (Layer 1 alone
    2); top 5 genuine, genuine, near, other, near; 0 of 34 near-misses above it; worst-gap
    AUC 0.758; random top 5 7.8%. Only 5 attempts pass Layer 1. 7 of 9 genuine fail it,
    all on sherd 2 (the small top sherd, 111 of 5,000 points): 4 on profile (3.4-8.8% of
    pot), 3 unjudged. Ranks 6-8 under Layers 1+2 are also all-own-place attempts with
    tighter gaps (1.30-1.73%) that Layer 1 dropped, so here Layer 1 cost places rather
    than earning them. Top-5 render: ranks 1 and 2 are whole bottles, every sherd on the
    outline. Median genuine render (profile 0.61%): sherds 0, 1, 3 on one outline,
    sherd 2 at the closed top where the wall turns in.
  - **plate misses.** Best genuine rank 161 under Layers 1+2 (Layer 1 alone 91); top 5
    near, other, near, near, other; 17 of 71 near-misses above it; AUC 0.479 (no
    separation); random top 5 4.4%. No attempt passes Layer 1. Every genuine attempt has
    sherd 5 unjudged and every one is flagged unfixable.
  - Ruler check, plate: the correct plate drawn from TORA's own clouds and from GARF's
    (`u17_true_look.py` @ 3fc73b0, Spartan workspace thread, 2026-10-05;
    `u17_true_plate*.{png,txt}` in the project folder) has sherd 5 at the hub beside
    sherd 4 in both. So the reference answer is fine. What differs: TORA's clouds are
    **3.13 times** the dataset's scale (box 1.892 vs GARF's 0.605, same axes).
- **Job 32329999 is void: broken measurement.** `rank_convert.py` read each sherd's move
  off TORA's cloud and applied it to the dataset's scans without undoing that scale, so
  every sherd kept its size while the moves between sherds grew 3.13 times: sherds
  drifted apart, gaps and profile deviations inflated, sherd 5 thrown about 100 mm out.
  Its self-check rebuilt from the run's own cloud, not the scans, so it could not see it.
  Both pots' numbers above, narrow_bottle3's pass included, mean nothing. Labels are
  unaffected (they compare the run's two clouds in one unit).
  - Fix: `run_frame` in `rank_convert.py` divides out the scale (and any shift) of the
    run's clouds against the scans, and refuses a run whose sherd centres then disagree
    with the scans' by more than 3% of pot. Changes under 5% scale or 0.5% shift are left
    alone, so GARF's bundles are unchanged. Synthetic check (4 sherds, each turned
    differently): sherd-centre distances off by 21-38 mm with the old converter at 3.13x,
    0.0 mm with the fix, at 3.13x and at 1x with a shift.
  - Next: rerun `u17_test_tora.slurm` unchanged under the same pre-registration (nothing
    was tuned; only the ruler is fixed). The renders of 32329999 were looked at; the
    prediction stands as written.
- 32330575 `u17_test_tora.slurm` (rerun, converter @ 0dce053, pre-registration unchanged
  @ c3559e7), COMPLETED 0:0, polled by the Spartan workspace thread. `TORA/rank_u17/
  tora_32330575/`; log and renders `u17_tora_32330575*` in the project folder. Converter:
  narrow_bottle3 clouds 2.56-2.58x the scans' scale, plate 3.11-3.13x, each with a shift,
  all undone; sherd centres then agree with the scans to 0.37-2.07% of pot (limit 3%).
  Self-check 10/10 on both.
  - **Ruler checks pass.** No genuine attempt fails Layer 1 on either pot (none unjudged,
    none over the profile cut-off). Median genuine renders: every sherd on one outline,
    per-sherd 0.14-0.26% (bottle), 0.03-0.25 mm (plate, floor sherds 4, 5 at the hub).
  - **narrow_bottle3 passes.** Top 5 under Layers 1+2: genuine, genuine, genuine,
    near-miss, genuine (random top 5 7.8%); best genuine rank 1 (Layer 1 alone 4); 0 of 34
    near-misses above it; worst-gap AUC 0.961; none flagged unfixable. Ranks 1-8 are all
    every-sherd-in-place attempts. Render: whole lobed bottles, sherd 2 at the foot.
  - **plate misses: the ranker failed** (prediction held). Best genuine rank 84 of 560
    (Layer 1 alone 119); top 5 other, other, other, near-miss, other; 32 of 71
    near-misses above it; AUC 0.411 (no better than chance). Render of the top 5: the four
    large rim sherds are right in every one; the two small floor sherds (4: 154 points, 5:
    59) are put on the rim or swapped at the hub, and still sit snugly against something,
    so their gaps (about 1% of pot) read like a correct join. The gap test cannot tell a
    small sherd seated in the wrong place from one in its own; the outline test cannot
    either, since a floor piece lies on the floor wherever it goes. Not a ruler fault
    (genuine attempts all pass and look right) and not the reference (correct plate
    drawn, sherd 5 at the hub). Weak already on GARF's plate (AUC 0.66).
  - Weight: two pots, one method, 560 attempts each; plate was seen in calibration. A
    lead for U17: the ranker found the right reassembly on a lobed bottle for a second
    method, and has a stated blind spot for small, featureless sherds (floor pieces).
- Conservator, 2026-10-05, on the plate top 5 (32330575): "there are more overlaps of
  sherds in the top 5 assembly". Confirmed on the render: the misplaced floor sherds lie
  across rim sherds. Neither layer measures overlap: Layer 2 (`l2_measure.py`) takes the
  distance from a sherd's break to the nearest neighbouring break, so a sherd sunk into
  another reads as a tight join. An overlap (interpenetration) test is the obvious missing
  check, and thesis aim 2 already names "hard rejection of interpenetrations". Not added
  to this test: plate and narrow_bottle3 are now seen, so any overlap rule needs its own
  pre-registration and calibration on GARF's calibration pots, and fresh pots to test on.
- Revision 4 built (conservator chose "Build it", 2026-10-05): `overlap_measure.py`
  (label-free), `u17_overlap.py` (cut-off on GARF's calibration pots, re-rank of every
  seen pot), `overlap_look.py` (draws the overlap in red), job `u17_overlap.slurm`, plan
  `../preregistration-overlap.md`. Synthetic ring: correct 0.25-0.38%, sherd slid half
  over its neighbour 34%. No fresh test pot exists; this run is calibration plus checks.
- 32345673 `u17_overlap.slurm` (Revision 4, plan @ 31c6a68; 32331355 stopped at the frame
  check, fixed by area-weighted centres), COMPLETED 0:0. `TORA/rank_u17/overlap_32345673/`;
  log, report and drawings `u17_overlap_32345673*` in the project folder.
  - Ruler checks: GARF clouds match the scans on all 7 pots (scale 1, no shift), so GARF's
    bundles stand. TORA's shift estimate moved at most 0.08% (bottle) and 0.26% (plate)
    of pot, under the 0.3% rebuild limit. Open mesh edges on GARF/TORA narrow_bottle3
    sherds 0 (20), 3 (10), narrow_bottle4 sherd 3 (4), galli_pot sherd 5 (4): their
    overlap direction is unreliable; nothing below rests on them.
  - Cut-off **37.8%** of a sherd's surface, set by GARF plate (q99 of genuine; other
    pots 4.3-17.2%). Non-regression holds: GARF narrow_bottle3, galli_pot and TORA
    narrow_bottle3 keep rank 1. **TORA plate not rescued**: best genuine 84 -> 81, top 5
    unchanged (worst sherd inside another 11-37%, all under the cut-off).
  - **Broken measurement, not a failed idea.** The GARF plate drawing (best genuine
    attempt) shows red along every join: GARF seats breaks slightly into each other, and
    the measure counts the join band as overlap. As a SHARE of a sherd's surface that band
    is small on a big sherd and most of a tiny one: GARF plate's 8 genuine attempts failed
    by the gate are all sherd 5 (59 of 5,000 points) at 38-47%. That set the cut-off far
    above TORA plate's misplaced sherds. The TORA plate drawing shows the measure does see
    the conservator's overlap: Revision 3's top attempt has floor sherd 4 lying across rim
    sherd 3, 17% of it red over its whole face; the best genuine attempt 1.6%, red only in
    specks.
  - As pre-registered, nothing retuned. Revision 4 stands as a failed gate (measurement
    broken: per-sherd share, inflated on small sherds by join bands). Any Revision 5
    (overlap as area in absolute terms, or the band within a wall of a break left out) is
    designed after looking at plate twice; plate cannot count for it, and it needs fresh
    attempts to be tested.
- **Revision 5 (2026-10-06, jobs 32352963/4 draws, 32352965 scoring, 32376045 drawings).**
  No fresh pot qualified, so no test. Seen attempts: plate's sherd-on-sherd leader caught
  (74 > 71), best genuine 84 -> 53, 32 near-misses still above. Cost: 40 of 305 correct
  galli_pot attempts rejected; drawn, the red runs along long pressed seams, not one sherd
  on another. Measurement broken; not adopted; Revision 3 stands. Full record in
  `preregistration-overlap5.md`.
