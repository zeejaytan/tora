# 08: Train the generic corpus worn: does it give the Juglet back sherd 1?

**What to find out:** Ticket 07's adapters no longer damage placement, but on the Juglet
each costs about one sherd against untouched, and it is always sherd 1 (home 20/20
untouched, 2/20 generic, 0/20 ceiling). Shape family made no difference. The hypothesis
(ticket 07) is that every U10 training break fits perfectly by construction
(`coincident_share` ≈ 1), while the Juglet is real and worn, so the adapter learns to rely
more on a perfect fit. This ticket trains the same generic corpus with its break faces
worn and asks whether that keeps sherd 1 and seats more of the Juglet.

**Answers:** O7 (the BEHAVIOURAL box: wear augmentation shown to earn its place, on an
erosion operator it was not trained on, against a cruder augmentation). It also reports
back to U10's "what that leaves" line.

**Blocked by:** 07 (the alignment-off recipe and the fresh generic adapter it trained).

**Status:** needs-triage (drafted 2026-09-25; conservator decides the arms and says go)

**Needs-eye:** before training, one worn join from the corpus, before/after, in a section
window that resolves 0.1 mm. After, the Juglet median attempt per new arm in visual-qa,
beside `u10_juglet_generic_noalign` and the correct reassembly.

## Why this is a fair test now and was not before

Worn training has been tried twice here (wear v2, wear v3), and both results read as "does
not help". Both trained with TORA's alignment term on. Wear v3 also had the pose head free.
Ticket 06 showed alignment alone makes an adapter lose placement, with wear v3's exact
signature (best at pass 0, then falling). So no fair worn-training run exists yet. The
one piece of evidence the other way: on the erosion ladder, wear made a pot fail by
*swapping* two sherds, while the Juglet *scatters* (`juglet-cause` tickets 09–10, one pot,
weak).

## Arms, fixed before any draw (proposed)

All arms use ticket 07's recipe unchanged: alignment off, r128, alpha 256, dropout 0.1,
last 6 blocks, head frozen, lr 2e-5, 20 passes, `last.ckpt`. They also use the same
vessels and the same split as `u10_generic.hdf5`. Only the break faces differ.

- **fresh generic:** ticket 07's adapter, not retrained.
- **worn generic:** wear v3's operator (`wear_ops.recede_surface` then chips, the
  `WEAR_LEVELS` in `build_bbad_vessel_trainset.py`: light 0.15% recession + 2 chips,
  moderate 0.30% + 3 chips), applied to break faces only. Each breakage is stored fresh,
  light and moderate as three training objects (TORA's loader, `tora/data/dataset.py`,
  has no per-pass variant choice). Training is capped at ticket 07's **step count**
  (`trainer.max_steps`), so each arm sees the same number of examples. The arms differ
  only in surface. Wear v3 calibrated 0.30% against a real worn pot's
  contact-band gap. At the Juglet's 65 mm that is about 0.2 mm of retreat.
- **noise generic (the cruder baseline O7 asks for):** Gaussian jitter on break-face
  vertices only, with RMS displacement matched to the worn arm's. It uses the same three copies and
  the same step cap.
- **untouched:** ticket 05's Juglet and ticket-11 ladder baselines stand. Check that it is
  the same model file before reusing.

Ceiling worn is left out: shape made no difference in ticket 07, and one lever at a time.

## Readings, written before any draw

Juglet, solid sherds, median of 20 draws (raw beside), sherd-home counts reported:
- **worn beats fresh generic by 1 sherd or more, and sherd 1 is home in 10+ of 20** →
  the adapter's Juglet cost was the perfect-fit training. Goes to U10 and O8.
- **noise does as well as worn** → the benefit is augmentation in general, not
  wear-shaped. O7's box stays unmet on its second half.
- **worn within 1 sherd of fresh, and sherd 1 still lost** → this wear does not undo the
  cost. The perfect-fit hypothesis is not supported, at this dose. The sherd-1 loss stays
  unexplained; record it as that, not as "wear does not matter".
- **worn beats untouched by 1 or more** → the first fine-tune here that helps the Juglet.
  Name it, weight one pot.

Erosion ladder (`zeroshot/erosion_ceramics`, 8 real Fractura pots × 5 abrasion levels,
20 draws; the operator is GARF's mollifier, which is **not** the training operator, so it
is not circular): per pot and level, worn vs fresh generic and worn vs noise, as a sign
test. Never pooled. This is O7's box.

Guard: each new arm's practice-vessel curve is reported beside fresh generic's .974 and
untouched .958. An arm that falls below untouched is named before its Juglet number is
read.

## Acceptance

- [ ] Worn and noise files built. The share of break-face vertices identical to a
      neighbour's falls from ≈1. The contact-band gap percentiles are reported against wear
      v3's real-pot reference. The file is not trusted until it has been rendered.
- [ ] Rendered before training: one join, fresh / worn / noise, at 0.1 mm.
- [ ] Two adapters trained. Alignment logs 0. Strict diff passes. Curves reported.
- [ ] Juglet: 20 draws per arm, own place, sherd-home counts, readings applied.
- [ ] Ladder per pot and level, sign tests, readings applied.
- [ ] Viewer pairs staged; conservator's look.
- [ ] Weight stated. Which of the three kinds named. Written back to O7 (and U10/O8 if
      the first reading fires).
- [ ] Every `sbatch` has a laptop poll; sacct State/ExitCode recorded here.

## Cost (estimate)

Build: CPU job. Training: about 40 min per arm, based on ticket 07 (same step count).
Juglet: about 5 min per arm. Ladder: about 50 min for 3 arms (job 30337242). Total about
3 A100-hours.
