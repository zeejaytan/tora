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

## Reading

The adapter HURTS, on every arm, and the pose-head retraining hurts too on worn
material. Worn sweep: 0.794 baseline -> 0.734 with the retrained head -> 0.616
with the adapter on. This is claim (1) -- the method genuinely did not transfer.
The measurement is sound (gate passed, renders agree) and there is no ground-truth
problem on the sweep or fresh arms.

Caveats that limit the weight: the hyperparameters (lr 2e-4, 60 epochs) were
inherited from GARF's full fine-tune recipe and were only ever exercised here
inside a run with 80x more trainable capacity. Nothing has yet tested whether a
lower lr or an earlier stop behaves differently. The in-domain val curve says the
adapter stopped learning by epoch 9, which is consistent with the lr being too
high for 5M parameters.

Untested next knobs, cheapest first:
1. lower lr (2e-5) and/or stop at ~epoch 10 -- the val curve points straight here
2. train_head=false, so `adapter_off` is a true baseline and the two effects separate
3. widen the LoRA target set to GARF's full list (ff.net.2, norm/timestep linears);
   needs Gate C re-run
