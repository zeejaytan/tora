# 01: First run end to end: the Juglet, with the vessel check only

**What to build:** GARF's 1,400 Juglet attempts ranked without the answer key, using
only Layer 1 (does it form a vessel), with the rank of the 2 genuine full reassemblies
reported against random choice. This is the thinnest complete path: converter → attempt
bundles → ranker → report, run on Spartan. See `../spec.md`.

**Answers:** U17

**Blocked by:** None (can start immediately)

**Status:** done (2026-10-02): result below; Layer 1 alone does not reach the top 5

- [x] Converter turns one GARF evaluation run's rigid ("solid") attempts plus the Juglet's
      full-detail sherds into one bundle per attempt, each moved to a random position; the
      id-to-attempt map is a separate file only the report reads
- [x] Converter's own check: a genuine attempt re-posed and scored with `own_place.py`
      comes back 9 own place, 9 right way round
- [x] Ranker Layer 1: axis fit and wall-profile deviation in mm (7 mm bins), inside-out
      sherds (reuse `check_inside_out.py`'s test); attempts failing either go to the bottom
- [x] Test: the same bundle under two random moves gives the same scores
- [x] Test: the ranker runs with reference files unreadable and its output is unchanged;
      any attempt to open one fails the test
- [x] Pre-registration file (all cut-offs in mm and degrees) committed **before** the
      labelled run; the report prints its commit hash
- [x] Spartan CPU batch job ranks all 1,400 attempts; laptop-side poll; final sacct
      State/ExitCode recorded here
- [x] Report: rank of each genuine attempt, whether one is in the top 5, random baseline
      (~0.7%), how many attempts Layer 1 drops, and where the 19 near-misses land

## Result (job 32107634, 2026-10-02)

`sacct`: **COMPLETED 0:0**, ended 2026-10-02T23:17:24. (First submit, 32105506, FAILED 1:0 at the
fence gate before ranking: numpy loads from `~/.local` on Spartan; allow-list widened in
the next commit.) Pre-registration e3f1b27. Outputs on Spartan
`TORA/rank_u17/juglet_32107634/`; laptop copy `artifacts/rank_u17/juglet_32107634/`.

- Gates on Spartan: converter 40/40 agree; moved 20 attempts, change 0.000 mm; fence
  catches the dataset and id map, ranker runs fenced unchanged. Labels recomputed: 2
  genuine, 19 near-miss, as expected.
- Genuine attempts: **rank 142** (noise_d100 ds1 #19, deviation 1.65 mm) and **rank 299**
  (worn_d400_s7 ds4 #11, 1.86 mm) of 1,400. **Not in the top 5** (random: 0.71%).
- Layer 1 dropped 169 (12%): 163 for an inside-out sherd, 6 on profile. No 9/9-own-place
  attempt was dropped. Every attempt's profile is under 5 mm (5th–95th pct 1.50–4.65 mm),
  so the 7 mm SfS++ cut-off is loose on this handmade pot, as the spec predicted.
- Rank tracks correctness weakly (Spearman −0.46 against own-place count): median rank
  1,019 for 1-sherd attempts, 215–284 for 8–9.
- 7 of 19 near-misses rank above the best genuine; one is rank 5. Expected: Layer 1
  cannot see a sherd spun on its own face.
- **Look (debug render, `ranks_1_142_1400.png`):** rank 1 (6 own place, 4 right way
  round) scores best (1.0 mm) because sherds overlap, stacked in one height band on the
  same wall curve, so the profile is very consistent. SfS++ pairs its profile test with
  an overlap limit (50 mm²); this Layer 1 has none, so it **rewards overlap**. Rank 1,400
  is a plain wreck (two sherds standing off the wall). The genuine attempt's own wall
  spreads ~1.5 mm, the same as the scanned pot (ruler check 1.53 mm): among the top
  half, ordering is within the pot's own unevenness.

Reading: the ruler is sound (gates, labels, renders agree); this is the method (Layer 1
as pre-registered) not being able to rank finely, not a broken measurement. It is a weak
filter. Overlap belongs in Layer 2's per-join test (ticket 02), not as a retune here.
- 32265963 `rank_u17_juglet_v2.slurm` — COMPLETED 0:0. Repaired Layer 1 (`--profile outer`,
  inside-out reported only) with the Fractura cut-off 1.723% of pot (calib_32160629) =
  1.12 mm on the Juglet. Output `TORA/rank_u17/jug_v2_32265963/`.
  - Layer 1 keeps 532 of 1,400. Genuine noise_d100_ds1 #19: 0.65 mm, kept, rank 357 →
    **9** with Layer 2. Genuine worn_d400_s7_ds4 #11: **1.58 mm, dropped**, rank 703 → 533.
    Top 5 has no genuine (before this repair, Layers 1+2 ranked them 1 and 13).
  - Cause, looked at (scratchpad render of both genuine attempts): all of the deviation is
    sherd 0 (0.65 / 1.58 mm; all others 0.02–0.24). Sherd 0 is the neck **with the
    handle**; the handle loop sits off the outline in the (r, h) plane. Broken measurement
    for a handled vessel (the measure assumes a round pot, as SfS++ does), not a misplaced
    sherd. Fractura calibration pots have no handles, so calibration could not see it.
  - Tried and rejected: dropping points whose surface normal line misses the axis. Plain
    wall sherds 7 and 2 miss by 2–4 mm (median), the handle sherd by 0.6 mm; no separation.
  - Layer 2 controls unchanged (spin-on-truth AUC 0.98; near-miss AUC 0.76; small-move
    control still fails).
