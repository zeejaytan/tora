# 01: Move the fixed sherd and see whether good placements follow it

**What to build:** Juglet, untouched baseline model, 20 draws each with the held
(anchor) sherd set to 0 (default), 6 (the base) and 4 (lower body), via the new
test-only `+data.anchor_part` override. Score each sherd by own-place (home within
7.1% of pot size, ~4.6 mm) and render one representative draw per arm.
Job: `scripts/hpc/juglet_anchor_choice.slurm`.

**Answers:** O8

**Blocked by:** none

**Status:** done

**Why:** on baseline job 30130049 the sherds sharing the longest break edge with the
held sherd (1, 7) went home 15/20 and 14/20; sherds not touching it (4, 5, 6) 0-2/20.
Fractura shows the same pattern within size bands (0.61 vs 0.28). All correlational.
If contact with the held sherd is the mechanism, moving the held sherd moves the
good placements.

**Predictions, written before the run (2026-09-21):**

- anchor0 reproduces 30130049 home counts [20,15,3,4,2,2,0,14,0] (same seed). If
  not, the other arms are compared against the new anchor0, not the old job.
- **Supported:** anchor6 -> sherds 3, 4, 5, 8 rise above their anchor0 counts
  together, while 1 and 7 fall. anchor4 -> 2, 5, 6, 7 rise. Both arms must show it.
- **Refuted:** the neighbours of the new held sherd do no better than before, and
  1 and 7 stay high -> something about 1 and 7 themselves (shape, size, position on
  the pot), not contact, makes them easy.
- **Inconclusive:** every sherd drops in anchor6 and anchor4. The model only trained
  with the largest sherd held; a small held sherd is out of distribution and a
  general collapse says that, not anything about contact.

- [x] Job run: 30917498, sacct `COMPLETED|0:0`, ~4 min on gpu-a100
- [x] anchor0 reproduction checked: NOT exact despite seed 42 -- 1 and 7 home 20 and 19
      (30130049: 15, 14). Run-to-run noise ~5/20 per sherd; arms compared to anchor0
- [x] Per-sherd home counts, three arms, table (below)
- [x] One draw per arm rendered and looked at: `artifacts/anchor/anchor_choice_30917498.png`
- [x] Verdict against the predictions above, written back to O8

## Result

Held sherd at home in all 60 attempts (offset 0.000%), so the override took effect.

| held | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | non-held home |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | held | 20 | 2 | 4 | 0 | 5 | 0 | 19 | 0 | 50/160 |
| 6 | 2 | 0 | 2 | 13 | 20 | 15 | held | 0 | 1 | 53/160 |
| 4 | 14 | 0 | 0 | 0 | held | 14 | 19 | 5 | 1 | 53/160 |

- **anchor6: supported.** Neighbours 3, 4, 5 rise (4->13, 0->20, 5->15); 8 does not
  (0->1). 1 and 7 fall to 0.
- **anchor4: partly.** Lower neighbours 5, 6 rise (5->14, 0->19); upper neighbours 2, 7
  do not (2->0, 19->5); non-neighbour 0 home 14/20. The prediction as written ("2,5,6,7
  rise") fails for 2 and 7.
- **Not the out-of-distribution collapse:** totals 50/53/53.
- Reading: the held sherd's *region* comes right, not just the sherds that touch it.
- Block check (`scripts/blocks.py`): the far region, rigidly fitted as one piece, still
  sits 15-28% of pot size off vs 3-4% for the near region (the same ruler, the control) --
  it is not a correct block misplaced. That ruler uses point-to-point distance, stricter
  than own-place chamfer, so its per-sherd counts run low; only the gap is read.

Scripts: `scripts/` beside this folder (run from `tora/`, arg = job id where needed).

## Correction (2026-09-24)

The counts above were read off TORA's raw output, where sherds may bend. Rescored on
solid sherds (rigid): neck held [held,20,2,4,0,5,0,17,0]; base held
[0,0,1,13,19,15,held,0,1]; sherd 4 held [0,0,0,0,held,14,17,5,1] (totals 48, 49, 37 of
160). The half-follows-the-held-sherd pattern survives. **Struck:** "sherd 4 held -> neck
home 14 of 20" (0 on solid sherds). The block check (15-28% vs 3-4%) was on raw output and
is not re-run. O8 carries the corrected table.

Second fault, same day (`.scratch/juglet-cause/issues/14`): own-place chamfer counts a
sherd home when it lies in its place turned over or spun end for end. Strict home (also
near its own true points), same job: neck held [held,13,0,0,0,0,0,1,0] = 14/160; base
held [0,0,0,11,11,12,held,0,0] = 34/160; sherd 4 held [0,0,0,0,held,4,3,0,0] = 7/160.
**Struck:** "with the neck held, the upper body is right". Sherd 7's 17 of 20 were 1
truly seated; the rest lay in its place turned. With the neck held, only sherd 1 is
reliably right. The base is the best single reference; "each sherd is placeable from the
right start" now holds for 3, 4, 5 (base held) and 1 (neck held), weakly for 5, 6 (sherd
4 held), and not for 2, 7, 8.

