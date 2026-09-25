# 06: Why does training the adapter make placement worse?

**What to find out:** Ticket 04 trained both U10 adapters for 20 passes. Both got *worse*
at seating sherds on their own practice vessels (the 5 choosing vessels): ceiling
.897 untouched → .77 by pass 4 → .815 at pass 19; generic .958 → .912. Fine-tuning is
meant to improve that, so something in the recipe pulls the wrong way. This ticket
tests the likely causes one at a time, so a later attempt at U10 knows what to change.
It does not re-run the Juglet.

**Answers:** U10 (whether stage 1's loss says anything about shape, or only about this
recipe; see U10 *Stage 1 result*)

**Blocked by:** 04 (the trained adapters and their logs).

**Status:** done (2026-09-25)

**Needs-eye:** none. This is a diagnosis on synthetic practice vessels, not a reassembly
claim. The lead renders one practice vessel (untouched vs the original pass 19 vs the
winning arm's pass 19) as a debugging view before reporting.

## What the logs already show (lead, 2026-09-25)

Read from both runs' wandb files (`TORA/output/u10_train_{ceiling,generic}_31200602_*`).
TORA's training score is `loss = flow_loss + align_loss` (`tora/modeling/tora.py:430`),
weighted equally:
- **Placement part** (`flow_loss`) about 0.005, with no clear trend over 20 passes. It is
  logged every 50 steps and is noisy.
- **Alignment part** (`align_loss`) is the CKA match of TORA's internal features to the
  frozen Uni3D teacher. It is about 95% of the total. It fell from 0.24 to 0.10 (ceiling)
  and from 0.26 to 0.15 (generic).
- The arm whose alignment fell most (ceiling) also lost the most placement.

GARF, whose adapter recipe U10 copied, has no alignment term. Its fine-tune is scored on
placement alone.

## Suspects, in the order they are tested

1. **The alignment term.** Training spends its effort matching Uni3D's view of the new
   shapes, not placing sherds.
2. **Forgetting.** 20 vessels whose breaks repeat the same bands wear away general skill
   the base model learned from thousands of objects.
3. **The frozen head.** The adapter changes the features, and the pose head cannot follow.
   GARF trains its heads (`mlp_out_trans`, `mlp_out_rot`) and `shape_embedding`.

## Arms (all on the ceiling corpus, the larger fall)

Everything is as ticket 04 except the one named change: rank 128, alpha 256, dropout 0.1,
all 6 blocks, lr 2e-5, 20 passes, the same 349 training breakages, choosing score every
pass.

| Arm | Change | Tests |
|---|---|---|
| C | none, no training. The untouched model and the existing ceiling pass 19 scored on Breaking Bad `everyday` validation (lr 0, as ticket 04's `baseline` step) | suspect 2 |
| A | `model.repa_stop=0` (alignment off) | suspect 1 |
| B | alignment off **and** `lora.train_head=true` | suspect 3, given 1 |

`repa_stop` is applied in `on_train_batch_end` (`tora.py:474`), so the first batch still
carries alignment. Arm A checks that the logged `train/alignment_loss` is 0 from the
second step on; if not, stop and fix before reading anything.

Arm B's "adapter off" is **not** the untouched model (the head moved: the wear v3 trap).
It is compared against the untouched model's own score, never against itself switched off.
The strict weight diff is expected to fail on the head only; the ticket records which
tensors moved.

## Readings, written before any run

Untouched on the ceiling practice vessels: **.897**. Pass-to-pass noise: about 2 points
(ticket 04).

- **A stays at .87 or above at every pass from 4 to 19** → the alignment term is the main
  cause. Any later adapter on TORA trains with alignment off.
- **A falls to .82 or below at any pass** (like the original) → alignment is not the main
  cause. Suspects 2 and 3 carry it.
- Between → partial. Report both curves.
- **C: pass 19 scores 3 points or more below untouched on `everyday`** (own place, solid
  sherds) → the adapter damaged general skill, not just skill on these shapes.
- **B beats the untouched .897 by 2 points or more at any pass after pass 1** → there is a
  recipe that improves on the untouched model on in-distribution vessels. That makes a
  second attempt at U10 meaningful. The attempt is a new ticket, and the conservator
  decides.
- **Nothing beats untouched** → adapters trained on this corpus do not improve TORA even
  in-distribution. Record that in U10 and stop this line.

## Results

**Arm C (forgetting), 2026-09-25, holder 31280929, step exit 0.** 496 Breaking Bad
`everyday` validation breakages (2–33 pieces), one draw each, the same fixed subset for
both models (`limit_val_samples=480`, which takes every n-th breakage):

| | own place (solid) | own place (raw) | rotation error |
|---|---|---|---|
| untouched | .920 | .921 | 10.2° |
| ceiling pass 19 (ticket 04 `last.ckpt`) | .877 | .877 | 16.3° |

A fall of 4.3 points, which crosses the 3-point line: **the adapter damaged general
skill, not only skill on these shapes.** Suspect 2 holds. It does not yet say *why*
training forgot; that is what A and B test. Weight: one draw per breakage, one adapter;
the adapter loaded 24 non-zero blocks, so this was the trained adapter and not the
untouched model twice.

**Arms A and B, same holder, both steps exit 0.** Own place (solid) on the 103 practice
breakages (5 vessels), one draw per breakage per pass. Untouched: .897.

| pass | 0 | 2 | 4 | 6 | 8 | 10 | 12 | 14 | 16 | 18 | 19 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| ticket 04 (alignment on) | .893 | .870 | .769 | .803 | .816 | .815 | .825 | .822 | .809 | .815 | .804 |
| A: alignment off | .889 | .915 | .923 | .919 | .921 | .916 | .908 | .934 | .938 | .950 | .938 |
| B: alignment off, head trained | .904 | .905 | .917 | .913 | .915 | .924 | .923 | .935 | .935 | .935 | .935 |

Rotation error at pass 19: ticket 04 21.0°, A 9.7°, B 9.3° (untouched about 12°).
Placement loss (`flow_loss`) in A: from about 0.005 at the start to 0.0006–0.002 in the
last passes, where ticket 04's did not trend.

Checks: A's alignment term logged 0.204 on the first batch and 0.000 on all 269 later
readings. A's strict diff PASSES (only the 48 adapter tensors differ). B's fails on
exactly the 5 pose-head tensors (`flow_model.final_mlp.{0,2,4}`), as expected, and on
nothing else.

Holder 31280929: CANCELLED+ (ended by `gpu_session.sh stop`), ExitCode 0:0, 1 h 26 min.

**Follow-up job 31287146** (`scripts/hpc/u10_diag06.slurm`): COMPLETED, 0:0, 8 min.
- **A's adapter on the same `everyday` subset: .921 own place, 10.0° rotation error**,
  against untouched .920 / 10.2°. With alignment off, the forgetting arm C found is gone.
- **Look (lead's debugging render, not a witness):** 11 practice breakages (every 10th),
  one draw each, montages at `artifacts/u10/r06/montage_{a,b}.png`. Each run renders the
  pot in its own random orientation (the adapter wrapping draws random numbers first), so
  each prediction is read against **its own run's** correct picture, not across runs;
  the scores are unaffected (the loaders don't shuffle, so every run scores the same breakages). Ticket 04's adapter is visibly wrong
  on most of them: s1 neck sunk into the body, s2 and s9 sherds flung off the pot, s6 rim
  floating, s8 shoulder sherds turned. Arm A matches its correct picture on 9 of 11. On
  s2 the rim sits high, and s4 is wrong on one side (the untouched model is also off on
  s4). The pictures show A back at the untouched model's level. They do **not** show the
  4-point gain; at 11 breakages they can't.

## Reading (against the rules above)

- **A stays at .87 or above at every pass from 4 to 19** (lowest .908), so **the
  alignment term is the main cause.** Ticket 04's training spent its effort matching
  Uni3D's view of the new shapes, and that moved the adapter away from placing sherds.
- **C crosses the 3-point line** (.920 → .877): ticket 04's adapter forgot general skill.
  A's adapter does not (.921), so the forgetting came from the alignment term too, not
  from the narrow corpus as such. Suspect 2 is explained by suspect 1.
- **B beats untouched by 2 points or more after pass 1** (.917 at pass 4, .935 at pass
  19), and so does A (.938 at pass 19). **A recipe exists that improves on the untouched
  model on held-out vessels of the trained type**, by about 4 more sherds seated per 100.
- **Training the head adds nothing visible** (B .935 vs A .938 at pass 19, curves within
  noise). Suspect 3 is not supported.

**Which of the three:** the method failed, where "the method" is ticket 04's recipe
(alignment on during fine-tuning), not TORA and not adapters. The measure is sound: A's
strict diff passes, and the alignment term was confirmed at 0. The reference is sound:
synthetic vessels with a known answer.

**Weight:** one training run per arm, one seed, 5 practice vessels (103 breakages), one
draw per breakage per pass. The +4 points is about twice the pass-to-pass noise, so it is
a lead, not a measured gain. The forgetting result rests on 496 breakages but one draw
each. Nothing here touches the Juglet.

**What it means for U10:** stage 1 lost to a recipe fault, not to shape. A Juglet
rerun of stage 1 with alignment off (both adapters retrained) is now a fair test of
U10's question. Running it is the conservator's call, and it goes in a new ticket.

## Acceptance

- [x] Arm C scored first (minutes, no training). Forgetting confirmed, see Results.
- [x] Arms A and B trained. Each is reported pass by pass beside ticket 04's curve. The
      table shows every other pass; the flow and alignment losses are summarised under Checks.
- [x] Each arm's reading is quoted against the rules above, with the weight.
- [x] Which of the three kinds of failure it is, named: the method, meaning ticket 04's recipe.
- [x] Every `sbatch` had a laptop-side poll. Holder 31280929 CANCELLED+ 0:0 (1 h 26 min),
      job 31287146 COMPLETED 0:0 (8 min): about 1.6 A100-hours.
- [x] Written back to U10 *Stage 1 result*, 2026-09-25.

## How it runs on Spartan

- **One held allocation** on `gpu-a100-short` (`scripts/gpu_session.sh`, 8 CPUs max),
  steps queued back to back: C (about 10 min), A (about 40 min), B (about 40 min), then
  `gpu_session.sh stop`. That is about 1.5 h, inside the 4 h wall. Ticket 04 took 32–41
  min per arm.
- Reuse `scripts/hpc/u10_session.sh`'s train and baseline steps with the overrides above.
  Do not write a new training script.
- The Juglet is never touched here.
