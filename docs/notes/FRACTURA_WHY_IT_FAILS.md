# Why TORA does badly on Fractura — and why it is not the fracture surface

Started from a fair question: these eight ceramics were broken last week, not
dug up. Fresh edges, sharp and unworn. If TORA's weakness were worn fracture
surfaces, it should sail through these. It does not. So what is it?

Two separate things were happening, and they had been reported as one.

## 1. The "zero fragments placed" reading was the ruler, not the model

`tora/eval/evaluator.py` multiplies the point clouds back to the object's own
units before scoring, and `compute_part_acc` then thresholds squared chamfer at
a fixed `0.01` — documented in the source as "0.01 meter by default". The
tolerance is therefore an absolute physical distance, and it is only meaningful
if every dataset arrives in metres. They do not:

| subset | median scale | stored in |
|---|---|---|
| Breaking Bad vessels | 0.49 | normalised |
| Fractura bone_syn_pig / rib | 0.56 / 0.60 | normalised |
| Fractura ceramics (real) | 74 | millimetres |
| Fractura bones (real) | 24 | millimetres |
| Fractura egg (real) | 52 | millimetres |

A squared-CD threshold of 0.01 is a linear tolerance of 0.1 units. On Breaking
Bad that is 20% of the object's half-extent — generous. On a ceramic pot stored
in millimetres it is 0.1 mm on a vessel ~150 mm across, about 0.16% — roughly
125x tighter in linear terms. Nothing but the anchor can pass it, and the anchor
is clamped at ground truth by construction with chamfer ~0. Hence every real
Fractura object scoring *exactly* `1/n_parts`: 0.250 on the 4-part pots, 0.500
on the 2-part bones. That is the arithmetic of a free anchor, not a measurement.

Rescored in the normalised frame at the Breaking-Bad-equivalent threshold
(0.04 squared, `scripts/rescore_part_acc.py`), off the saved clouds of job
29886425:

```
object                   draws  t=2.7e-06   t=0.001   t=0.01   t=0.04 *   t=0.16
ceramics/blue_pot           10      20.0%     20.0%    20.0%     38.0%     72.0%
ceramics/narrow_bottle4     10      25.0%     25.0%    25.0%     40.0%    100.0%
```

So fragments do land in roughly the right region. This is the same bug found and
resolved once already in jobs 27858648 / 27859890 (see the correction header of
`TORA_GOOD_VS_BAD_ANALYSIS.md`); `real_heldout_norm.hdf5` was built in response,
but the raw Fractura subsets were never rebuilt normalised, so scoring them
directly reproduces the identical broken reading.

**Do not stop here.** The temptation after finding a broken metric is to declare
the failure imaginary. It is not.

## 2. There is a real failure, and rotation error shows it

Rotation error is scale-invariant: the model only ever sees data normalised to
[-1, 1] (`dataset.py`, `scale = np.max(np.abs(pts_gt)); pts_gt /= scale`), and
the angle between two orientations does not care what units the file used. The
units bug cannot touch it.

`compute_transform_errors` skips the anchor but divides by *all* parts, so the
reported mean is diluted by one free zero. The right column below multiplies
back by `n/(n-1)` to give the error on fragments the model actually had to
place. Same checkpoint throughout; real subsets from job 24342475.

| run | objects | rot, as reported | rot, non-anchor |
|---|---|---|---|
| Breaking Bad vessels (synthetic) | 107 | 20.9° | **22.4°** |
| real held-out pots, normalised | 6 | 29.9° | **35.9°** |
| Fractura bones — REAL fracture | 16 | 28.3° | **52.3°** |
| Fractura egg — REAL fracture | 3 | 42.5° | **56.6°** |
| Fractura bone_syn_pig — SIMULATED | 21 | 55.4° | **61.4°** |
| Fractura bone_syn_rib — SIMULATED | 11 | 61.5° | **64.4°** |
| Fractura ceramics — REAL fracture | 8 | 61.4° | **79.1°** |

## What this rules out

**It is not wear.** Every Fractura object is a fresh break. The original
intuition was right on this point.

**It is not real-versus-simulated fracture surface.** This is the one the
project had written down as the answer, and the table refutes it: Fractura's
*simulated* pig and rib bones fail at 61–64°, worse than Fractura's *real*
bones at 52°. If simulated fracture were the easy case, that ordering would be
the other way round.

**It is not piece count or object complexity.** Within the ceramics, per-pot
non-anchor rotation error is flat against fragment count:

```
pink_bowl        3 parts  78.0°     plate            6 parts  77.0°
narrow_bottle2   3 parts  78.2°     galli_pot       10 parts  80.9°
narrow_bottle4   4 parts  70.1°     narrow_bottle1  12 parts  93.1°
narrow_bottle3   4 parts  82.7°     blue_pot         5 parts  79.5°
```

A three-fragment bowl — the easiest reassembly in the set — comes out 78° wrong.

The split is by **dataset**, not by material, fracture type, or difficulty:
everything from Fractura is bad, everything not from Fractura is fine, and our
own real pots (35.9°) sit with the good group.

## What has not been tested

Naming these so the above is not mistaken for a full answer:

- **Orientation convention.** The Fractura configs set no `up_axis`, so they
  default to `y`. If Fractura is stored z-up this is a systematic global
  rotation. Against this: the training pipeline randomises the global rotation
  (`init_rot`), so the model should be object-pose invariant, and our own y-up
  real pots score fine. Worth ten minutes, not more.
- **Scan noise and mesh density.** Artec Spider at 0.05 mm produces surfaces
  unlike anything in Breaking Bad. This would affect real subsets only, and the
  simulated bones are also bad — so it cannot be the whole story.
- **Point budget.** 5000 points are shared across the object, allocated by
  area; blue_pot's smallest fragment gets 107. Thin, but piece count does not
  correlate with error, which argues against it.
- **How Fractura's ground truth poses were established.** The GARF paper does
  not document it. The conservator has confirmed the ceramics are in correct
  assembly, which closes this for the ceramics but not for the bones and eggs.
- **The renders.** Nobody has looked at all eight assemblies yet. Two were
  viewed and showed fragments compacted into an interpenetrating blob rather
  than scattered — consistent with the numbers above, but two is not eight.

## Weight this can bear

Eight pots, 10 draws each, one checkpoint. The rotation comparison spans 172
objects across seven runs, which is why it is stated more firmly than the
part-accuracy rescoring — that rests on two saved objects, because the
visualiser saved one sample per batch and all eight pots fit in one batch.
`scripts/hpc/eval_ceramics_arms.slurm` now saves all eight.
