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

The fix, in `tora/eval/metrics.py`, restores the frame the threshold was
stated in. Breaking Bad: *"We re-scale each of them to fit a unit-length box for
parameter choice consistency. This normalization scheme allows our method to be
scale invariant"* (Sellan et al. 2022), and *"we set tau = 0.01 following [20]"*.
So tau lives inside a unit-length box. `unit_box_scale` divides both clouds by
the longest side of the **ground truth** bounding box before thresholding —
ground truth, never the prediction, because a scattered prediction has a bigger
box than the object it is trying to rebuild and would be handed a more forgiving
tolerance for failing. `scripts/check_metric_scale_invariance.py` is the gate:
the same geometry stored in millimetres, metres and normalised must score the
same number, and it does (0.600 in all three, where the old absolute metric
ranged 0.400–1.000).

This is the same bug found and resolved once already in jobs 27858648 / 27859890
(see the correction header of `TORA_GOOD_VS_BAD_ANALYSIS.md`);
`real_heldout_norm.hdf5` was built in response, but the raw Fractura subsets were
never rebuilt normalised, so scoring them directly reproduced the identical
broken reading.

### Fixing the ruler did not rescue the result

**Correction, 2026-09-02.** An earlier version of this section reported that
blue_pot went from 0% to 38% and narrow_bottle4 from 0% to 40% once rescored,
and concluded "fragments do land in roughly the right region." **That was wrong
and is withdrawn.** The offline rescorer used a fixed threshold of 0.04 derived
from assuming the dataloader frame has a bounding box of side 2 (max|coord| = 1
implies a half-extent of 1). It does not: `center_pcd` centres by centroid, not
by bounding-box centre, so narrow_bottle4's box side is **1.695**, and the
correct equivalent is ≈0.0287 — the threshold used was about 40% too loose. A
`t=0.16` column, 5.6× looser than the benchmark, was printed beside it and read
as if it bracketed the answer.

Rescored correctly with the evaluator's own `unit_box_scale`, off all eight
saved objects of job 29888540:

```
pot                parts   anchor floor   raw pred   proposed
narrow_bottle4         4         25.0%      25.0%      25.0%
blue_pot               5         20.0%      30.0%      20.0%
narrow_bottle3         4         25.0%      25.0%      25.0%
narrow_bottle1        12          8.3%       8.3%      10.0%
pink_bowl              3         33.3%      33.3%      33.3%
plate                  6         16.7%      16.7%      16.7%
narrow_bottle2         3         33.3%      33.3%      33.3%
galli_pot             10         10.0%      10.0%      13.0%
MEAN                             21.5%      22.7%      22.0%
```

At the benchmark's own tolerance, correctly applied, the model seats essentially
nothing beyond the free anchor: 22.7% against a 21.5% floor is roughly one extra
fragment across eighty attempts.

So both statements are true and neither cancels the other. **The ruler was
broken and worth fixing** — it made a real number unreadable and would have
faked the same finding on any future dataset stored in millimetres. **And the
failure it was hiding is real.** Do not stop at "the metric was broken" — that
is the tempting conclusion and it is not the one the evidence supports.

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
- **The renders.** Two of eight have been looked at. pink_bowl (3 fragments,
  the easiest reassembly in the set) has a clean hemispherical ground truth;
  its predicted assembly is the three fragments compacted into one
  interpenetrating slab, all three overlapping through each other rather than
  seated edge to edge. That is what a 78° mean rotation error looks like, and
  it is consistent with the anchor-floor part accuracy. Two is not eight.

## Weight this can bear

Eight pots, 10 draws each, one checkpoint. The rotation comparison spans 172
objects across seven runs, which is why it is stated most firmly. The corrected
part-accuracy table now rests on all eight saved objects, not two:
`scripts/hpc/eval_ceramics_arms.slurm` was changed to save every sample in the
batch (`max_samples_per_batch: 8`) precisely so a threshold mistake could be
repaired from the npz without spending GPU time again — which is what happened.

Three scale-invariant measures agree, which is the reason this is stated as a
real failure rather than another broken ruler: non-anchor rotation error 53–79°,
`translation_error_unit` 0.110 (fragments sitting about 11% of the object's
longest dimension away from home — roughly 17 mm on a 150 mm pot), and
`object_chamfer_unit` 0.0101. None of the three can be moved by the storage
units.
