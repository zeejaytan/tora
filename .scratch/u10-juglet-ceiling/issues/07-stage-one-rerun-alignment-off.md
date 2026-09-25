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

- [x] Generic trained with alignment off; its alignment term logs 0; strict diff passes;
      its practice-vessel curve reported beside untouched .958 and ticket 04's .912.
- [x] 20 Juglet draws per adapter arm: own-place median and range, swap-allowed, distance
      of unseated sherds (% of pot size and mm).
- [x] The rule applied by `own_place.py --decide`, quoted verbatim.
- [x] Fractura per pot for both arms.
- [ ] Lead's debugging renders looked at (done); viewer pairs staged for the conservator,
      and the conservator's look (pending).
- [x] Weight stated: one pot, 20 draws, one training run per arm, one sampling seed.
      Which of the three kinds named.
- [x] Every `sbatch` has a laptop-side poll; sacct State/ExitCode recorded here.
- [ ] Written back to U10, dated (done, provisional); O8 and G1 after the look and
      refute-finding; C4 not needed.

## How it runs on Spartan

One batch job on `gpu-a100-short` (`scripts/hpc/u10_rerun07.slurm`), steps back to back:
train generic alignment off (about 40 min), then Juglet and Fractura for both adapter
arms (about 10 min), each through `u10_juglet_arm.slurm` run as a plain script with
`ADAPTER=` and `LABEL=noalign`. Every step is a known-working path from tickets 04–06, so
no held allocation is needed for debugging. Scoring is CPU, inside the same job as
before.

Submitted 2026-09-25: **job 31290347** (tora `c5e14ee`), laptop poll. Final sacct:
**COMPLETED 0:0, 42 min 37 s** (about 0.7 A100-hours). All four arm steps exited 0.

## Results (2026-09-25)

**Generic training, alignment off.** Alignment term 0.000 at all 17 logged readings;
strict diff passes (only the adapter moved). Own place (solid) on its 5 practice vessels,
untouched .958:

| pass | 0 | 2 | 4 | 6 | 8 | 10 | 12 | 14 | 16 | 18 | 19 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ticket 04 generic (alignment on) | | | | | | | | | | | .912 |
| generic, alignment off | .953 | .965 | .957 | .959 | .956 | .955 | .949 | .971 | .970 | .971 | .974 |

Rotation error at pass 19: 3.8°. Like the ceiling in ticket 06, the recipe no longer
damages placement on vessels of its own type. Ceiling alignment off (ticket 06 arm A):
.897 → .938.

**Juglet, 20 draws per arm, solid sherds (raw beside):**

| Arm | own place, median (range) | swap-allowed | not in own place, from home |
|---|---|---|---|
| untouched (ticket 05, 31215861) | 3 of 9 (2–5); raw 3 | 4.5 | 18.5% of pot size (12.1 mm) |
| generic, alignment off | **2** of 9 (1–4); raw 3 | 5 | 20.9% (13.6 mm) |
| ceiling, alignment off | **2.5** of 9 (1–7); raw 3 | 5 | 27.0% (17.6 mm) |

How often each sherd is home, out of 20 (sherd 0 is the held anchor):

| sherd | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
|---|---|---|---|---|---|---|---|---|---|
| untouched | 20 | **20** | 3 | 2 | 0 | 4 | 0 | 17 | 0 |
| generic | 20 | **2** | 3 | 7 | 1 | 2 | 2 | 7 | 3 |
| ceiling | 20 | **0** | 5 | 10 | 2 | 2 | 4 | 11 | 0 |

The scorer's reading (`own_place.py --decide`), quoted verbatim:
> own-place medians: untouched 3, generic 2, ceiling 2.5. Ceiling minus generic = +0.5
> sherd(s); the rule needs +1.
> CEILING LOSES: shape is not what the Juglet is missing, even when handed over. Close
> U10 (the method genuinely failed, for this lever), skip stage 2, and write back to
> tora/intent/O8 and GARF/intent/G1 that the break edges are what is left.

On the raw output all three medians are 3 (ceiling minus generic 0); same reading.

**Fractura, per pot, solid sherds, median of 20** (untouched from ticket 05):

| Pot | sherds | untouched | generic | ceiling |
|---|---|---|---|---|
| blue_pot | 5 | 5 | 5 | 5 |
| galli_pot | 10 | 8 | 7.5 | **7** |
| narrow_bottle1 | 12 | 2 | **3** | **3** |
| narrow_bottle2 | 3 | 3 | 3 | 3 |
| narrow_bottle3 | 4 | 1 | 1 | 1 |
| narrow_bottle4 | 4 | 4 | 4 | 4 |
| pink_bowl | 3 | 3 | 3 | 3 |
| plate | 6 | 4 | 4 | 4 |

Named: ceiling −1 on galli_pot; both +1 on narrow_bottle1. The galli_pot collapse of
ticket 05 (8 → 4.5 / 2) is gone.

**Look (lead, debugging view, `artifacts/u10/r07/montage07.png`).** Mitsuba renders of
both arms, typical, best and worst draws, beside the correct reassembly. Each is a whole
pot at the right size; nothing collapsed. Both adapters go wrong in the lower body and
base: the base sherd flips outward in generic d3/d5 and ceiling d1/d2. The ceiling's best
draw (d0, 7 of 9) is close to correct except two small lower sherds. Viewer pairs for the
eye: `u10_juglet_{generic,ceiling}_noalign`.

## Reading (against the rules above)

- **Ceiling fails to beat generic by 1** (+0.5 solid, 0 raw). By the rule, handing TORA
  the Juglet's type shape does not seat more of its sherds, now with a fine-tune that
  does not damage placement on vessels of its own type.
- **Either adapter loses to untouched on the Juglet:** generic by 1 sherd (3 → 2), ceiling
  by 0.5. Both lose the same sherd: sherd 1, home in 20/20 untouched draws, 2/20 generic,
  0/20 ceiling. The ceiling gains sherds 3 and 7 part of the time. A recipe that is
  harmless on its own vessels still costs the Juglet one sherd, whichever shapes it
  learned. That is a different finding from ticket 05's.
- Generic does not match the ceiling *and* beat untouched, so no C4 line.

**Which of the three:** the method genuinely failed, for this lever. The measure is the
same scorer and settings as ticket 05, the strict diff passes, the alignment term is 0,
and the renders are whole pots at scale. The reference is `juglet_gt`, the conservator's
hand reassembly; its one open doubt (sherd 7, ≤3.5 mm) cannot move a median by a sherd.

**Weight:** one pot, 20 draws per arm, one training run per arm, one sampling seed. The
+0.5 gap is inside the draw-to-draw spread (ceiling ranges 1–7). "Shape is not what the
Juglet is missing" is the rule's wording and stronger than one pot can carry. What this
run does show is that giving TORA the right shape family, with a sound recipe, did not
seat more of this pot's sherds.

**Not yet written back to O8 / G1:** the pre-registered "break edges are what is left"
line waits for the conservator's look and a refute-finding pass.
