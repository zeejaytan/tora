# 03: Does a scale *below* the trained band damage the result too?

**Type:** `wayfinder:task` (AFK)
**What to build:** An answer to whether TORA degrades when the object's stored size is
too *small*, and an audit of which past Juglet conclusions were drawn from runs sitting
there.

**Answers:** O8

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

## Why it is live

The scale ladder (job 29891327) established a cliff between 15 and 50 and that the model
is fine from 0.5 to 5. **It never tested below 0.5.** The trained band is [0.375, 0.625].

`juglet_norm` runs report `scales = 0.041` — nine times below the floor. The wear
comparison that produced wear_v1 and wear_v2 (job 29027773) ran there. `juglet_gt` runs
sit at 0.511 and are clean.

If the low side is also damaging, then the wear experiments were scored on a handicapped
input and their "no movement in rotation" reading is not a fair test of wear.

## Acceptance criteria

- [ ] Every Juglet-related eval run on Spartan audited for its recorded `scales`, and a
      table produced of which conclusions rest on out-of-band runs
- [ ] The ladder extended downward — rungs giving scale roughly 0.04, 0.08, 0.15, 0.25
      alongside 0.5 as the in-band control — reusing `scripts/hpc/eval_scale_ladder.slurm`
      with the existing gate. **Ask before submitting**
- [ ] The gate (`scripts/check_scale_conditioning.py`) passes, so only `scales` moves
- [ ] Renders at the worst rung and at 0.5, same pot, same seed
- [ ] A verdict on whether job 29027773's wear comparison must be re-run in band
- [ ] Names which of the three this is
