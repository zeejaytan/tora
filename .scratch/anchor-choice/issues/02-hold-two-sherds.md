# 02: Hold one sherd in each half and see whether both halves come right

**What to build:** `+data.anchor_part` accepts a list (test-only; each held sherd
treated as the single one is: true orientation in, pinned by the sampler). Juglet,
untouched baseline model, 20 draws each: held {0} (in-job control), {0,6} (neck +
base), {0,4} (neck + lower body). Score own-place per sherd, render the median draw
per arm. Job: `scripts/hpc/juglet_two_held.slurm`.

**Answers:** O8

**Blocked by:** none

**Status:** ready-for-agent

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

- [ ] Job run, final sacct State/ExitCode recorded
- [ ] Both held sherds at home in every draw
- [ ] Per-sherd home counts, three arms
- [ ] Median draw per arm rendered and looked at before any verdict
- [ ] Verdict against the predictions, written back to O8
