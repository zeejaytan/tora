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

**Status:** ready-for-agent

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

## Acceptance

- [ ] Arm C scored first (minutes, no training).
- [ ] Arms A and B trained. For each, every pass's choosing score is reported beside
      ticket 04's original ceiling curve, plus the flow and alignment losses per pass.
- [ ] Each arm's reading is quoted against the rules above, with the weight: one run per
      arm, 5 practice vessels, one draw per vessel per pass.
- [ ] Which of the three kinds of failure it is, named.
- [ ] Every `sbatch` has a laptop-side poll. The final `sacct` State/ExitCode and the GPU
      hours are recorded here.
- [ ] Written back: one line in U10's *Stage 1 result* saying which suspect held, dated.

## How it runs on Spartan

- **One held allocation** on `gpu-a100-short` (`scripts/gpu_session.sh`, 8 CPUs max),
  steps queued back to back: C (about 10 min), A (about 40 min), B (about 40 min), then
  `gpu_session.sh stop`. That is about 1.5 h, inside the 4 h wall. Ticket 04 took 32–41
  min per arm.
- Reuse `scripts/hpc/u10_session.sh`'s train and baseline steps with the overrides above.
  Do not write a new training script.
- The Juglet is never touched here.
