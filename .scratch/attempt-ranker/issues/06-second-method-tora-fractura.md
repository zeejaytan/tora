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
  - **Ruler check, plate (first reading, to be confirmed).** In the median genuine render
    sherd 5 sits about 100 mm from the plate's centre, outside a plate about 110 mm
    across, so nothing is within 12% of pot to judge it against and its gap is infinite.
    An attempt can only be labelled genuine with sherd 5 there if TORA's correct plate has
    it there too: own place allows 7.1% of pot (`own_place.SEAT_PCT`). If confirmed, the miss
    is the **reference answer being wrong** (a correct plate with a detached sherd), not
    the ranker failing, and plate cannot test the ranker on TORA. Check sent:
    `u17_true_look.py` (3fc73b0) on one TORA and one GARF run, correct plate only.
