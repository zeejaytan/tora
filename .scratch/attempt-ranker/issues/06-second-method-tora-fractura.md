# 06: A second method: TORA's Fractura attempts

**What to build:** the same ranker on TORA's attempts, so the result is not one method's.

**Answers:** U17

**Blocked by:** 05

**Status:** ready-for-agent

- [ ] Converter reads TORA's saved attempt clouds (the `u10_fractura_*` evaluation runs);
      the converter's own check passes
- [ ] TORA attempts labelled for right way round
- [ ] Decision recorded: are 20 attempts per pot enough? If not, a TORA rerun of 200
      attempts per qualifying pot (GPU, expected under an hour), polled
- [ ] Per pot: genuine ranks, top-5 hit, random baseline

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
