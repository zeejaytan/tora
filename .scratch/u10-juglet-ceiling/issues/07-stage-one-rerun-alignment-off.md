# 07: Stage 1 again, with the alignment term off

**What to find out:** Ticket 05's stage 1 compared adapters trained with the recipe that
ticket 06 showed damages placement. With the alignment term off, the ceiling adapter
beats the untouched model on its own practice vessels (.938 vs .897) and does not forget
(.921 vs .920 on everyday). This ticket reruns stage 1 with that recipe, so U10's
question gets a fair test: does handing TORA the Juglet's type shape seat more of its
sherds than generic vessel training does?

**Answers:** U10

**Blocked by:** 06 (the recipe and the ceiling adapter).

**Status:** in progress (conservator said start, 2026-09-25)

**Needs-eye:** the Juglet's median attempt per arm, staged in visual-qa beside the
correct reassembly, the same way as ticket 05's `u10_juglet_*` pairs. The pictures decide;
the table ranks.

## Arms, fixed before any Juglet draw (lead, 2026-09-25)

The one change from ticket 05 is `model.repa_stop=0` in training. Everything else is the
same: rank 128, alpha 256, dropout 0.1, last 6 blocks, head frozen, lr 2e-5, 20 passes,
same training files.

- **untouched:** not rerun. Ticket 05's jobs 31215861 (Juglet, 3 of 9) and 31216108
  (Fractura) stand. The evaluation code and scorer have not changed since; the only commit
  touching `sample.py` adds `mode=validate`, whose default is the old test path.
- **ceiling, alignment off:** ticket 06 arm A,
  `output/u10_noalign_ceiling_31280929_144409/last.ckpt` (pass 19). Strict diff passed.
- **generic, alignment off:** trained here with the same step (`u10_session.sh noalign
  generic`), `last.ckpt` (pass 19).
- **Which pass:** the last, as in ticket 05 (conservator, 2026-09-24). Declared here so the
  Juglet never chooses it. Each arm's own practice-vessel curve is reported beside it.

Settings are ticket 05's: `zeroshot/juglet_gt`, batch 1, 20 draws, mitsuba 512; Fractura
`zeroshot/fractura_fresh`, batch 4, 20 draws, pot by pot, never pooled.

## Readings, written before any draw

Same rule as ticket 05, on solid sherds, median over 20 Juglet draws, raw beside:
- **ceiling beats generic by 1 sherd or more** → the shape lever works when handed over:
  stage 2 becomes meaningful (a new ticket; the conservator decides).
- **ceiling fails to beat generic by 1** → shape handed over does not seat more of the
  Juglet's sherds, now with a fine-tune that does not damage placement. U10 closes
  answered, and O8 / G1 get the "break edges are what is left" line that was withheld in
  ticket 05.
- **generic matches the ceiling and both beat untouched** → the gain came from the
  fine-tune, not the shape (a C4 line).
- **either adapter loses a sherd or more to untouched on the Juglet** → name it, and
  report the practice-vessel score beside it. A harmless recipe that still loses on the
  Juglet is a different finding from ticket 05's.

Fractura: any pot where an adapter loses or gains a sherd or more (median) is named.

## Acceptance

- [ ] Generic trained with alignment off; its alignment term logs 0 after the first
      batch; strict diff passes; its practice-vessel curve reported beside the untouched
      .958 and ticket 04's generic curve.
- [ ] 20 Juglet draws per adapter arm: own-place median and range, swap-allowed, distance
      of unseated sherds (% of pot size and mm).
- [ ] The rule applied by `own_place.py --decide`, quoted verbatim.
- [ ] Fractura per pot for both arms.
- [ ] Lead's debugging renders looked at; viewer pairs staged for the conservator.
- [ ] Weight stated: one pot, 20 draws, one training run per arm, one sampling seed.
      Which of the three kinds named.
- [ ] Every `sbatch` has a laptop-side poll; sacct State/ExitCode recorded here.
- [ ] Written back to U10 (and O8, G1, C4 as the reading says), dated.

## How it runs on Spartan

One batch job on `gpu-a100-short` (`scripts/hpc/u10_rerun07.slurm`), steps back to back:
train generic alignment off (about 40 min), then Juglet and Fractura for both adapter
arms (about 10 min), each through `u10_juglet_arm.slurm` run as a plain script with
`ADAPTER=` and `LABEL=noalign`. Every step is a known-working path from tickets 04–06, so
no held allocation is needed for debugging. Scoring is CPU, inside the same job as
before.
