# 15: If TORA can never mirror or bend a sherd mid-way, does it place more sherds right?

**Type:** experiment (GPU, one job)

**What to build:** a test-only option `model.rigid_from_t` in `tora/modeling/tora.py`.
From flow time `t <= rigid_from_t` on, at every step the model's guess of the finished
assembly (`x - t v`) is replaced by each input sherd moved as a solid piece to its best
proper fit (turn and slide only, no reflection). The step then heads for that. At the last
step the output *is* that solid assembly, so raw and solid output coincide. The trained
model is unchanged: TORA keeps all its shape knowledge, and only the moves it may make
change. Job: `scripts/hpc/juglet_rigid_sampling.slurm`.

**Answers:** O8

**Blocked by:** none

**Status:** in progress

**Needs-eye:** the best attempt of the rigid neck + base arm, staged in visual-qa, only if
the rigid arm clears the bar below.

## Why

The conservator's reading of `twoheld_best` (2026-09-24): sherd 4 is at the right place
but inside out; something tells TORA it belongs there, but TORA gets there by flipping it
instead of turning it. Ticket 14 and the scratch analysis found the mechanism: TORA's free
output makes a sherd its mirror image (right way out), and the final solid step then turns
the mirror image inside out (Kabsch det fix, `tora/procrustes.py:31-33`). Mirrored sherds
are never seated (0 of 234 across four arms). For sherd 4 the best proper turn brings it
to 6.0-7.5% of pot size from its own points, against 24.9% for TORA's placement (seat
threshold 7.1%).

Against it: sherds that were never mirrored still seat only 15-53% of the time, GARF and
PuzzleFusion++ (solid-only by construction) also fail on the Juglet, and ticket 12 found
TORA's outline of the Juglet no better than a failed pot's. This is the fair test of the
remaining question: TORA's shape knowledge plus solid-only moves, which no run so far has
tried.

## Arms (one job, same seed, 20 attempts each, untouched baseline model)

| arm | held | rigid_from_t |
|---|---|---|
| held0 | neck (0) | off (in-job control) |
| held0_rigid | neck (0) | 1.0 (every step) |
| held06 | neck + base (0, 6) | off (in-job control) |
| held06_rigid | neck + base (0, 6) | 1.0 (every step) |
| held06_late | neck + base (0, 6) | 0.5 (second half only) |

Scored on solid sherds, strict home (`scripts/check_inside_out.py`).

## Predictions (written 2026-09-24, before the run)

- **Instrument first.** In the rigid arms, raw and solid output agree to under 0.05% of
  pot size for every sherd, and no raw sherd is mirrored. Held sherds sit at 0.000%. The
  controls land within noise of job 30919372: neck about 14/160, neck + base about 45/140
  (same-seed reruns have drifted ~5/20 per sherd). If not, stop: the option did not do
  what it says.
- **Supported (the conservator's reading):** neck + base rigid seats at least 15 more
  sherds than its in-job control (e.g. 45 -> 60+ of 140), neck rigid is no lower than its
  control, and inside-out sherds drop toward zero.
- **Refuted:** rigid arms within 10 of their controls. Mirroring was a symptom; TORA's
  shape knowledge is not being wasted by it.
- **Harmful:** rigid arms more than 15 below their controls. Forcing solid moves takes the
  model off the path it was trained on.
- Between 10 and 15 above: inconclusive at 20 attempts; rerun with a second seed before
  any claim.

## Acceptance criteria

- [ ] Job run, laptop poll, final sacct State/ExitCode recorded
- [ ] Instrument check (raw = solid, no mirrors, held 0.000%, controls in range)
- [ ] Strict home per sherd, five arms, table; inside-out and mirrored counts per arm
- [ ] Verdict against the predictions; which of the three; weight
- [ ] If supported: best rigid attempt staged in visual-qa, conservator's look and note
- [ ] Written back to O8
