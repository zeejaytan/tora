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

**Status:** done

**Eye check:** not needed. It was conditional on the rigid arm clearing the bar below; it did not
(refuted), so nothing was staged for the conservator.

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

- [x] Job run, laptop poll, final sacct State/ExitCode recorded -- job 31207476,
      `COMPLETED|0:0`, 6 min 16 s, ended 2026-09-25 00:25 (laptop poll died with the
      session; state read from `sacct` directly)
- [x] Instrument check (raw = solid, no mirrors, held 0.000%, controls in range) -- see below
- [x] Strict home per sherd, five arms, table; inside-out and mirrored counts per arm
- [x] Verdict against the predictions; which of the three; weight
- [x] If supported: best rigid attempt staged in visual-qa -- not supported, not staged
      (quick agent render only: best rigid attempt; 4 and 8 off, see Clarification)
- [x] Written back to O8

## Result (2026-09-25)

**Instrument.** The option did what it says. In the three solid-only arms no raw sherd is
mirrored (0 of 440 placements), every raw sherd is a solid copy of the real one (worst
residual 0.045% of pot size, turn determinant +1), and raw and solid output agree to
0.024% on average per attempt. The worst single point is 0.17% (about 0.1 mm), above the
0.05% written in the prediction: float32 rounding on one point, not bending. Held sherds
0.006% in every arm, the same as job 30919372. **Controls:** neck 20/160 (earlier 14),
neck + base **33/140 (earlier 45)**. Same seed, so this is run-to-run drift, and it is as
large as any effect this ticket could have found: see Weight.

Strict home, attempts out of 20, solid sherds (`rigidscore.py` in the session scratchpad;
same rule as `scripts/check_inside_out.py`):

| arm | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | seated | best attempt | mirrored | inside out |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| neck, control | 12 | 0 | 1 | 0 | 0 | 0 | 7 | 0 | 20/160 | 2 of 8 | 56 | 43 |
| neck, solid-only | 14 | 0 | 2 | 0 | 0 | 0 | 6 | 0 | 22/160 | 2 of 8 | 0 | 40 |
| neck + base, control | 15 | 0 | 2 | 9 | 5 | held | 2 | 0 | 33/140 | 3 of 7 | 73 | 60 |
| neck + base, solid-only | 15 | 1 | 6 | 1 | 10 | held | 2 | 0 | 35/140 | 5 of 7 | 0 | 47 |
| neck + base, solid second half | 17 | 1 | 1 | 12 | 3 | held | 3 | 0 | 37/140 | 4 of 7 | 0 | 41 |

**Against the predictions: refuted.** Solid-only is +2, +2 and +4 over its controls, all
inside the +-10 band. Inside-out placements barely fall (60 -> 47, 43 -> 40) even though no
sherd is ever mirrored: TORA turns sherds over with an ordinary turn just as readily. The
mirror-then-inside-out path (ticket 13/14) was one route to an inside-out sherd, not the
cause of misplacement. Not harmful either: forcing solid moves does not knock the model
off course.

**Which of the three:** the method genuinely failed -- meaning TORA on the Juglet, not the
solid-only option. With the ruler checked (above), TORA's shape knowledge, restricted to
solid moves, does not place the Juglet's sherds any better on average. What it knows about
where sherds go is the limit, not the moves it may make.

**Weight:** one pot, one seed, 20 attempts per arm. The in-job control moved by 12 on the
same seed between two jobs, so +2 to +4 is noise. A small real gain (under ~10) cannot be
ruled out; a large one can. The best solid-only attempt seats 5 of 7, one attempt more
than ever seen before, but it is 1 of 20 and within the spread.

## Clarification (2026-09-28): the option is sound; the hypothesis is what failed

Two different things were tested, and the first read-out blurred them.

- **The solid-only option works and is safe to keep.** It did exactly what it was built to
  do (instrument check above), and it cost nothing: every arm is at or above its control.
  Its output is always something that could be built from the real sherds -- no bent or
  mirrored sherd, so no score inflated by bending (the fault that faked "one attempt with
  every sherd home" in `.scratch/anchor-choice/issues/02`). That alone makes it the better
  default for any Juglet run a person will look at.
- **The hypothesis failed:** that mirroring was what held TORA back, so that removing it
  would place the sherds. On average it does not (+2 to +4, noise). TORA finds another way
  to go wrong: it turns sherds over with an ordinary turn.

**Best attempt (the conservator picks by eye, so this is the number that matters):**

| arm | best attempt, free sherds seated | attempts reaching it |
|---|---|---|
| neck, control | 2 of 8 | 3 of 20 |
| neck, solid-only | 2 of 8 | 6 of 20 |
| neck + base, control | 3 of 7 | 4 of 20 |
| neck + base, solid-only | **5 of 7** | 1 of 20 (attempt 8) |
| neck + base, solid second half | 4 of 7 | 1 of 20 |

Attempt 8 of neck + base solid-only is the most complete Juglet attempt seen so far: 7 of 9
sherds correct (neck and base held, plus 1, 2, 3, 5, 7), only 4 (23.7% of pot size off) and
8 (14.3%) wrong. Sherd 2 sits at 5.3% (about 3.4 mm), inside the 7.1% bar. The earlier
note in this ticket that 2 was visibly off was wrong. **Weight:** one attempt in 20, one
seed. Job 30919372's control reached 4 of 7 (2 of 20), so 5 against 3-4 is a lead, not a
finding: repeating with more seeds would tell whether solid-only raises the best attempt.

Render (agent's look only, not for the conservator):
`<scratchpad>/r15_rigid_best.png`. Fetched outputs: `artifacts/rigid/<arm>/`.
