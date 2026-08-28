# Job 29623885 — the first genuine adapter run (LoRA on 371 vessel shapes)

Completed 2026-08-27 01:08, 02:31:35 wall, A100. Supersedes job 29527496, which
was a full fine-tune wearing an adapter (see `docs/lessons.md`).

## The freeze held this time

Stage 5 gate, `scripts/diff_adapter_checkpoint.py --fail-on-frozen`:

```
FROZEN encoder:         0 changed, 492 identical
FROZEN flow backbone:   0 changed, 171 identical
POSE HEAD final_mlp:    5 changed        (train_head=true, expected)
```

Training log: `[lora] freeze holds: 5,113,344 trainable after the training loop's
own hooks ran, 15 norm layers holding eval`. Lightning summary: 5.1M trainable,
398M frozen, `feature_extractor ... eval`.

So the on/off comparison is real. It was not real last time.

## Training

r=128, alpha=256, dropout=0.1, last_n_blocks=6, train_head=true, lr 2e-4,
60 epochs. Train 2521 / val 262 fragmented vessels, parts [3,20].
Checkpoint saved is `epoch-59.ckpt` (= `last.ckpt`); no best-on-val selection.

In-domain validation (every 10 epochs, 262 held-out simulated-fracture vessels):

| epoch | part_acc | chamfer |
|---|---|---|
| 9  | 0.805 | 4.87e-4 |
| 19 | 0.807 | 4.68e-4 |
| 29 | 0.820 | 3.96e-4 |
| 39 | 0.807 | 4.31e-4 |
| 49 | 0.808 | 4.28e-4 |
| 59 | 0.816 | 3.90e-4 |

+1.1 points over fifty epochs, non-monotonic. The adapter had essentially
converged by epoch 9 and then wandered. Per-batch train loss is flat and noisy
from epoch ~8 (0.03-0.19, no trend).

## Nine evaluation arms

`adapter_off` is NOT the untouched baseline: the pose head was retrained and has
no off switch. Three arms, not two.

Worn erosion sweep, n=30 — the arm that matters:

| arm | part_acc | best-of-5 | rot_err | rec@10deg | rec@5cm | chamfer |
|---|---|---|---|---|---|---|
| adapter_on  | 0.6163 | 0.7144 | 46.57 | 0.0444 | 0.0889 | 0.0024 |
| adapter_off | 0.7337 | 0.7878 | 33.94 | 0.1667 | 0.3778 | 0.0017 |
| baseline    | 0.7941 | 0.8622 | 36.86 | 0.1000 | 0.3222 | 0.0010 |

Fresh (unworn) real held-out, n=6:

| arm | part_acc | best-of-5 | rot_err | rec@10deg | rec@5cm | chamfer |
|---|---|---|---|---|---|---|
| adapter_on  | 0.7593 | 0.8722 | 38.55 | 0.0000 | 0.1667 | 0.0010 |
| adapter_off | 0.8537 | 0.8722 | 31.12 | 0.0556 | 0.4444 | 0.0006 |
| baseline    | 0.8481 | 0.9278 | 36.52 | 0.0556 | 0.2778 | 0.0005 |

Juglet, n=1 object, 9 fragments, 5 runs:

| arm | part_acc | best-of-5 | rot_err | rec@5cm | chamfer |
|---|---|---|---|---|---|
| adapter_on  | 0.5111 | 0.6667 | 58.56 | 0.0000 | 0.0021 |
| adapter_off | 0.6444 | 0.7778 | 61.40 | 0.0000 | 0.0011 |
| baseline    | 0.6222 | 0.7778 | 46.75 | 0.2000 | 0.0011 |

## What the renders show (mitsuba, `artifacts/lora29623885/`)

Reference: juglet on its side, neck left, closed rounded base right.

All three arms seat the body and neck correctly -- the single large fragment
carrying most of the vessel. Every difference between the arms is in the small
fragments at the base end (1-3 sherds out of 9).

- `adapter_off` best run (7/9): base end CLOSES. Blue/green/yellow sit as a
  rounded cap in roughly the right place. Best of the three by eye.
- `baseline` best run (7/9): base end splays outward like a fan, green/magenta/
  blue well outside the silhouette. Vessel does not close.
- `adapter_on` best run (6/9): base end loose, fragments hanging below and one
  flying outside the silhouette on the right.

Visual ranking (off > baseline > on) matches the numeric part_acc ranking on this
object. The renders agree with the metric here; they are not adding a correction,
they are confirming one. Colour differs between arms because the fragment-index
to colour map is run-dependent; the input scramble is pixel-identical across arms,
so the comparison is fair.

## Reading -- CORRECTED 2026-08-28, see below

The original reading of this run was WRONG and is kept here only so the
correction is legible.

> The adapter HURTS, on every arm. Worn sweep: 0.794 baseline -> 0.734 with the
> retrained head -> 0.616 with the adapter on. This is claim (1) -- the method
> genuinely did not transfer.

Two things were wrong with that.

**The stated mechanism was wrong.** I argued the Breaking Bad fragments carry no
fracture texture, so the adapter could only learn silhouette. Gate A
(`GATE_A_RESULT.md`, 20 RePAIR fresco fragments) found real eroded archaeological
fracture carries no interlocking texture at any scale a scan resolves EITHER. The
absence of micro-texture is not a difference between train and test, so it cannot
explain a train/test gap. The conservator caught this.

**The evaluation did not test what was trained.** The two sets use different, near
opposite, wear operations:

| | effect on the break face | effect on the gap |
|---|---|---|
| train, `recede_surface` | curvature PRESERVED (doses picked to protect it -- 0.20% excluded for moving one curve by 6.6%) | join OPENS |
| test, `erode_fracture_band` | creases ROUNDED AWAY, 25-50% of relief stripped at strength 1.0 | none -- vertices move in place so the GT pose stays valid |

So the adapter was taught to read break curvature across an open gap, and then
measured on objects whose curvature had been smoothed off and whose mates still
touch. The erosion sweep is a sound test of abraded breaks. It is not a test of
this adapter. Recession IS wear and does teach curvature-reading, as the
conservator argued; it is simply not the wear the sweep applies.

Revised claim: closer to (2) -- the measurement is not broken, but it measures a
different thing than was trained. This run cannot say whether the adapter works.

## What the correction does NOT explain

The FRESH unworn real held-out arm also fell, 0.848 -> 0.759. No abrasion, no
opened gap, so a wear mismatch cannot account for it.

Hypothesis, UNVERIFIED: the training gaps are much too wide. `build_bbad_vessel
_trainset.py` records the same 0.05% retreat opening joins by 6-10% on these
coarse meshes against 1.1-1.9% on the fine scans, because BB fragments were cut
from one mesh and mate exactly, so the retreat has nowhere to hide. An adapter
taught to expect a wide clean gap would seat sherds too loosely on any real
object. Consistent with the render (adapter_on base-end sherds hang loose, vessel
does not close) and with chamfer more than doubling (0.0010 -> 0.0024). Consistent
is not confirmed.

## Next, cheapest first

1. Measure the join gap on all three sets with ONE instrument (train, erosion
   sweep, real_heldout_norm). CPU, minutes. If the training gaps really are ~5x
   wider, the fix is a dose, not a redesign.
2. Build the evaluation that matches the training: a sweep using RECESSION rather
   than the mollifier. Decisive test of whether the adapter learned anything.
3. Score the untouched baseline on the bbad_vessels val set -- still missing, so
   81.6% at epoch 59 currently has nothing to be compared against.
4. Lower lr (2e-5) / early stop ~epoch 10. The val curve flattened at epoch 9 and
   the remaining 50 epochs bought 1.1 points in-domain. Limits damage; does not
   make the data teach more.
5. train_head=false, so adapter_off becomes a true baseline. A diagnostic, not an
   improvement.

RETRACTED: widening the LoRA target set to GARF's full list. That assumed the
adapter was too small to learn the lesson. If the data or the evaluation is the
problem, more reach makes it worse, not better.
