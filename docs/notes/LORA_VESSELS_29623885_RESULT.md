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

**The evaluation did not test what was trained** -- but not for the reason I first
gave. That reason (below, struck) was itself wrong, and the measurement is now in.

> The two sets use different, near opposite, wear operations: recession preserves
> curvature and opens the gap, erosion rounds curvature away and opens no gap.

`erode_fracture_band` DOES open the gap: measured, +9.5% at strength 1.0. I had
read "the ground-truth pose is preserved" as "the gap is preserved"; vertices can
retreat on both faces and leave the pose valid. And the conservator is right that
recession and erosion are one severity axis, not two kinds of damage -- that is
what `WEAR_SIMULATION.md` §2 says and what `wear_to_loss` implements. So the
question was never "which kind of wear", it was "how much", and both sets can be
put on the one ruler `wear_to_loss` is written in: how far the joins have opened.

### Both sets on one ruler (`scripts/compare_wear_severity.py`, 12 + 6 objects)

Join gap = 10th-percentile distance from each fragment to its nearest neighbour,
as a percentage of object size. Coincident = fraction of a fragment's vertices
lying EXACTLY on another fragment.

| set | level | join gap, % of object | coincident vertices |
|---|---|---|---|
| **train** bbad_vessels | fresh | **0.0000** | **44.4 %** |
| | worn_light | 0.0454 | 0 |
| | worn_moderate | **0.0978** | 0 |
| **test** erosion_sweep | 000 unworn | **1.1159** | 0 |
| | 050 | 1.1532 | 0 |
| | 100 full | **1.2294** | 0 |

**The dose of wear matches. The baseline it sits on does not.** Erosion at full
strength adds 0.11 points of gap; the moderate training dose adds 0.10. Those are
the same severity, exactly as argued. But the training fragments start at zero --
44% of their vertices are the SAME POINTS as their neighbour's, because they were
cut from one mesh -- while a completely untouched real pot already sits 1.12%
apart. The hardest training example is still **11x tighter than the easiest test
object**. On a 20 cm vessel: trained on joins 0 to 0.2 mm apart, tested on joins
2.2 to 2.5 mm apart.

Rendered, not just measured: `scripts/render_join_gap.py` -> `artifacts/join_gap.png`.
The per-vertex histograms show it directly. The fresh training object has a spike
at exactly 0 holding a third of its vertices and nothing structured after it. The
real pot has NOTHING below 0.15% -- about 3x its own vertex spacing, so this is a
real separation and not a sampling floor -- rising to a broad contact peak at 0.45%.

**This replaces the earlier hypothesis, which was backwards.** I guessed the
training gaps were ~5x too WIDE. They are ~11x too NARROW, and nearly half of each
training fragment's mating surface is a copy of its neighbour's. A model can seat
those by matching identical points and never read curvature at all. That shortcut
does not exist on any real object.

**It also explains the residual the wear story could not.** The FRESH unworn real
arm fell too (0.848 -> 0.759), with no abrasion applied. Under the wear-mismatch
story that made no sense. Under this one it is the same failure: the problem is
not wear, it is that every training join is a perfect-contact join and no real
join ever is.

Claim: **(2), the measurement measures a different thing than was trained** -- and
the cause is in our data build, not in TORA. This run still cannot say whether the
adapter works.

### WHY it harms: where the damage lands (2026-08-28)

Split the error into orientation and position, over all saved result JSONs.

| set | arm | part_acc | rot err | trans err | chamfer |
|---|---|---|---|---|---|
| sweep (n=90) | baseline | 0.794 | 36.86 deg | 0.0724 | 0.00100 |
| | adapter_off | 0.734 | **33.94** | **0.0701** | 0.00167 |
| | adapter_on | 0.616 | **46.57** | **0.0977** | 0.00244 |
| fresh (n=18) | baseline | 0.848 | 36.52 | 0.0716 | 0.00054 |
| | adapter_off | 0.854 | **31.12** | **0.0577** | 0.00062 |
| | adapter_on | 0.759 | 38.55 | 0.0766 | 0.00105 |

**This refutes the mechanism I was about to give.** "The model learned push-until-
contact, so it misjudges distance" predicts damage concentrated in TRANSLATION.
It is not: with the adapter on, rotation error rises 26% and translation 35% --
both, roughly together. A distance rule cannot make a fragment face the wrong way.

**What survives, and fits better.** The adapter sits in `self_qkv_proj`,
`self_out_proj`, `global_qkv_proj`, `global_out_proj` (`lora.py:76`) -- the
attention projections, i.e. the layers where fragments compare THEMSELVES TO EACH
OTHER. Our training set lets that comparison succeed by finding the neighbour
whose vertices are identical (44% coincident, gap exactly 0). That is a lookup,
not a reading of break shape. Sixty epochs tuned the comparison layers toward it.
On a real pot no vertex is shared, the nearest is ~2 mm away, and the only cue
left is the SHAPE of the break -- which the tuned comparison no longer grips.

Orientation is where that shows first, and does. A body sherd off a smooth wall is
a nearly featureless curved patch; the only thing saying which way round it goes is
the outline and relief of its broken edge. Rotation error 37 -> 47 deg is that
ability degrading.

**It also localises the harm, and NOT to the pose head.** Retraining the head alone
(adapter_off) did not damage orientation -- it improved it, 36.5 -> 31.1 deg on the
fresh real pots, with part_acc level (0.848 -> 0.854). The harm appears only when
the adapter in the comparison layers is switched on. So the earlier worry that
`train_head=true` bakes in irreversible damage is not supported: the head is fine.

UNEXPLAINED: on the sweep, adapter_off's part_acc falls (0.794 -> 0.734) while both
its mean errors improve. part_acc is a threshold count, so a distribution can shift
across the threshold while the mean improves, but that is a guess, not a finding.

Weight: one training run, no seed repeats; 30 objects x 3 draws (sweep), 6 x 3
(fresh). The mechanism is inferred from where the damage lands, not observed in the
features.

### What could still overturn this

The 1.12% gap on the real objects could be genuine material loss, or it could be
slop in the assembled ground-truth pose of `real_heldout_norm` -- claim (3). The
slab view looks like a consistent thin separation rather than floating fragments,
but that view cannot fully separate the two. Checking it means seating one real
object by hand and re-measuring.

## Next, cheapest first

1. DONE, and it inverted the guess -- see above. The training joins are 11x
   TIGHTER than the test joins, not 5x wider.
2. Rebuild the training set so its joins start where real joins start. The
   fragments must not share mating vertices: recede BOTH faces to a target gap
   ratio with `wear_to_loss`, aiming at a fresh-real gap of ~1.1% of object, and
   assert coincident vertices == 0 in the builder. This is the fix the
   measurement points at. CPU only.
3. Only then rerun the adapter. Building a recession-based evaluation sweep is no
   longer the decisive test -- the training data is.
4. Score the untouched baseline on the bbad_vessels val set -- still missing, so
   81.6% at epoch 59 currently has nothing to be compared against.
5. Lower lr (2e-5) / early stop ~epoch 10. The val curve flattened at epoch 9 and
   the remaining 50 epochs bought 1.1 points in-domain. Limits damage; does not
   make the data teach more.
6. train_head=false, so adapter_off becomes a true baseline. A diagnostic, not an
   improvement.

RETRACTED: widening the LoRA target set to GARF's full list. That assumed the
adapter was too small to learn the lesson. If the data or the evaluation is the
problem, more reach makes it worse, not better.
