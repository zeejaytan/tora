# 02: Hold one sherd in each half and see whether both halves come right

**What to build:** `+data.anchor_part` accepts a list (test-only; each held sherd
treated as the single one is: true orientation in, pinned by the sampler). Juglet,
untouched baseline model, 20 draws each: held {0} (in-job control), {0,6} (neck +
base), {0,4} (neck + lower body). Score own-place per sherd, render the median draw
per arm. Job: `scripts/hpc/juglet_two_held.slurm`.

**Answers:** O8

**Needs-eye:** `visual-qa/preview/manifest_twoheld_best.json` (stage: `python visual-qa/viewer/stage_pair.py visual-qa/viewer/pairs/twoheld_best.json`)

**Blocked by:** none

**Status:** ready-for-human

**Why:** ticket 01 showed which half comes right is caused by which sherd is held,
never both halves. The halves share long breaks (0-3, 1-5, 7-4), so it is not lack of
contact. Test: is each half failing only for want of a fixed reference?

**Predictions, written before the run (2026-09-21):**

- **Reference is what's missing:** with {0,6} and {0,4}, upper (1, 7) AND lower
  (3, 4/6, 5) sherds go home together, most draws; non-held home rises well above
  the {0} control. If 2 and 8 also come right -> the failure was carrying placement
  across the pot. If they stay wrong -> they are a separate problem (8 smallest,
  2 borders the missing piece).
- **Not the reference:** one half still fails with a sherd held in it -> something
  about that half itself, not the lack of a fixed point.
- **Inconclusive:** everything drops below the {0} control -> two held sherds are out
  of distribution for this model (trained with one), not a statement about the pot.
- Both held sherds must sit at 0.000% offset in every draw, or the override failed.

- [x] Job run, final sacct State/ExitCode recorded -- job 30919372, `COMPLETED|0:0`,
      4 min 49 s, ended 2026-09-21 21:04 (laptop poll died early twice; state read
      from `sacct` directly)
- [x] Both held sherds at home in every draw -- worst held offset 0.000% in all three arms
- [x] Per-sherd home counts, three arms
- [x] Median draw per arm rendered and looked at before any verdict (matplotlib, raw
      output -- superseded, see Correction)
- [x] Scored on solid sherds (rigid, unbent), not raw output
- [x] Best solid attempt staged in visual-qa as real sherd meshes (pair `twoheld_best`)
- [ ] Conservator's witnessed look and note on `twoheld_best`, with agent reply
- [x] Verdict against the predictions, written back to O8

## Result (2026-09-24, solid sherds)

Attempts out of 20 in which each sherd went home, each real sherd placed rigidly
(`generations_proposed`). **Strict home**: on its own home patch (own-place chamfer,
SEAT_PCT 7.1% of pot size, about 4.6 mm) *and* each point on average within the same
distance of its own true point, so a sherd turned over or spun end for end in its place
does not count (`.scratch/juglet-cause/issues/14`). Chamfer-only count in brackets.

| held | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | free sherds home | best attempt |
|---|---|---|---|---|---|---|---|---|---|---|---|
| {0} control | held | 13 (20) | 0 (1) | 0 (4) | 0 | 0 (5) | 0 | 1 (17) | 0 | 14/160 (9%) [47] | 2 of 8 |
| {0,6} neck + base | held | 18 (20) | 1 (6) | 7 (16) | 3 (10) | 13 (16) | held | 2 (4) | 1 (7) | **45/140 (32%)** [79] | 4 of 7 |
| {0,4} neck + lower body | held | 13 (17) | 0 (4) | 0 | held | 0 (4) | 2 (7) | 6 (18) | 0 | 21/140 (15%) [50] | 2 of 7 |

**Against the predictions:**

- **Reference is what's missing: supported for the lower half, with the base.** Sherds 3
  and 5 go truly home 7 and 13 of 20, where the control has 0 and 0. Free placements rise
  from 9% to 32%. **No attempt is whole**: the best seat 4 of the 7 free sherds.
- **Not "both halves together":** sherd 7 fell from 17 to 4 of 20 on the chamfer count
  when the base was also held. Strictly it was only ever 1 of 20 with the neck alone: it
  was mostly lying in its place turned over.
- **2 and 8 stay wrong** (1 and 1 of 20 strict): a separate problem.
- **Sherd 4 is a weaker second reference than the base** (15% vs 32%).
- **Not out of distribution:** both two-held arms beat the control.

**Which of the three:** the method, given one correct sherd per half, places over half the
rest. Held sherds 0.000% in all 60 attempts. Held sherds come from the answer key; in use
a person would seat them.

**Weight:** one pot, one job, 20 attempts per arm. 9% -> 32% (strict) is far beyond noise.
Earlier filters for picking the best attempt without the answer key were at chance
(`.scratch/juglet-draw-selection/`). The inside-out rule (ticket 14) does better: fewest
flags picks attempt 0, which seats 4, the maximum, reached by 2 of 20 attempts. That is
one pick on one pot.

## Correction (2026-09-24)

The first write-up of this ticket (commit c3bc45d) scored TORA's **raw** output, in which
the model may bend a sherd to fit, and reported 31% -> 64% and "one attempt with every
sherd home". Posing the real meshes for visual-qa showed sherds 2, 4, 7, 8 did not move
rigidly (2-3.5 mm best-fit residual). On solid sherds the whole attempt is gone (its
sherd 4 was bent into place). **Measurement was broken**; the direction of the finding
survived. Same trap as `scripts/measure_nonrigid_cheating.py` (2026-08-10).

A second fault in the ruler was then found: own-place chamfer counts a sherd home when it
lies on its home patch turned over or spun end for end. The conservator saw sherd 4
inside out in `twoheld_best`. The counts were rescored as strict home (above; ticket 14);
the solid-sherd chamfer counts 29% / 56% / 36% and "best attempt 8 of 9" are superseded.
`twoheld_best`'s attempt 3 seats 3 of 7 strictly. **Measurement was broken again**;
the direction survived, the size shrank.

Look: visual-qa pair `twoheld_best` (real meshes, mm, correct left / attempt 3 right).
Scripts: `.scratch/anchor-choice/scripts/twoheld.py`, `render_twoheld.py`,
`render_best.py` (raw; superseded), `pose_meshes.py` (solid, for the viewer).
