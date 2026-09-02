"""Gate: restating an object in other units must change ONLY `scales`.

WHY. `scales` is not metric bookkeeping. tora/modeling/tora.py passes it into
the flow model at every denoising step, and PointCloudEncodingManager turns it
into a sinusoidal code concatenated onto all N points
(tora/modeling/flow_model/embedding.py:151). Breaking Bad objects arrive at
max|v| = 0.5 and training adds random_scale_range (0.75, 1.25), so the model has
only ever seen this input in roughly [0.375, 0.625]. The real Fractura subsets
are stored in millimetres and arrive at 24-120 -- two orders of magnitude out,
and far into the aliasing regime of an encoding whose top frequency is 2^9.

scripts/normalize_real_hdf5.py states the opposite in its header ("TRAINING AND
INFERENCE ARE UNAFFECTED by this"). That sentence is why the raw-unit Fractura
subsets were never re-run, and it is wrong.

WHAT THIS ASSERTS. `PointCloudDataset.normalize_object_scale` rescales the
object before the [-1, 1] normalization, which is exactly what saving the scan
in other units would do. For the experiment to mean anything, that knob must
move `scales` and NOTHING else -- if it also perturbed the coordinates or the
normals, a change in the score would not isolate the conditioning input.

So: load the same object twice from the same file, once raw and once
normalized, with the RNG seeded identically, and require

    pointclouds, pointclouds_gt, pointclouds_normals, rotations, translations
        identical to float tolerance
    scales                                differs by the expected factor

Run on Spartan (needs the tora env):
  python scripts/check_scale_conditioning.py \
      --data dataset/ceramics.hdf5 --dataset-name ceramics
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np

from tora.data.dataset import PointCloudDataset

# The band the model was actually trained on: Breaking Bad stores max|v| = 0.5
# and PointCloudDataModule's random_scale_range default is (0.75, 1.25).
TRAIN_SCALE_LO, TRAIN_SCALE_HI = 0.5 * 0.75, 0.5 * 1.25

COMPARED = [
    "pointclouds",
    "pointclouds_gt",
    "pointclouds_normals",
    "pointclouds_normals_gt",
    "rotations",
    "translations",
    "points_per_part",
]


def build(data_path, dataset_name, normalize, multiplier=1.0):
    return PointCloudDataset(
        split="val",
        data_path=data_path,
        dataset_name=dataset_name,
        min_parts=3,
        max_parts=12,
        anchor_free=False,
        num_points_to_sample=5000,
        min_points_per_part=20,
        random_scale_range=None,
        disable_augmentation=True,
        num_threads=1,          # the pool interleaves RNG draws; 1 keeps it reproducible
        normalize_object_scale=normalize,
        scale_multiplier=multiplier,
    )


def get(ds, index, seed=0):
    np.random.seed(seed)
    return ds[index]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", required=True)
    ap.add_argument("--dataset-name", required=True)
    ap.add_argument("--index", type=int, default=0)
    ap.add_argument("--tol", type=float, default=1e-4)
    a = ap.parse_args()

    raw = build(a.data, a.dataset_name, normalize=False)
    nrm = build(a.data, a.dataset_name, normalize=True)

    n = min(len(raw), 8)
    print(f"{a.dataset_name}: {len(raw)} objects, checking {n}\n")
    print(f"{'object':22s} {'scale raw':>10s} {'scale norm':>10s} {'in train band?':>15s} "
          f"{'max coord diff':>15s}")

    ok = True
    worst = 0.0
    for i in range(n):
        s_raw = get(raw, i, seed=100 + i)
        s_nrm = get(nrm, i, seed=100 + i)

        diffs = {}
        for k in COMPARED:
            x, y = np.asarray(s_raw[k]), np.asarray(s_nrm[k])
            if x.shape != y.shape:
                print(f"  FAIL {s_raw['name']}: {k} shape {x.shape} vs {y.shape}")
                ok = False
                diffs[k] = float("inf")
                continue
            diffs[k] = float(np.abs(x.astype(np.float64) - y.astype(np.float64)).max())

        d = max(diffs.values())
        worst = max(worst, d)
        sr, sn = float(s_raw["scales"]), float(s_nrm["scales"])
        band = "yes" if TRAIN_SCALE_LO <= sr <= TRAIN_SCALE_HI else "NO"
        print(f"{str(s_raw['name']).split('/')[-1]:22s} {sr:10.3f} {sn:10.3f} {band:>15s} "
              f"{d:15.2e}")

        if d > a.tol:
            ok = False
            print("      offending fields: " +
                  ", ".join(f"{k}={v:.2e}" for k, v in diffs.items() if v > a.tol))
        if abs(sn - PointCloudDataset.NORMALIZED_MAX_ABS) > 1e-3:
            ok = False
            print(f"      FAIL: normalized scale is {sn}, expected "
                  f"{PointCloudDataset.NORMALIZED_MAX_ABS}")
        if abs(sr - sn) < 1e-6:
            ok = False
            print("      FAIL: the two scales are equal, so this object proves nothing.")

    print()
    if ok:
        print(f"PASS: every compared tensor matched to {worst:.2e} (tol {a.tol:.0e}).")
        print("Only `scales` moved, so a score change between these two runs is")
        print("attributable to the scale conditioning input and nothing else.")
    else:
        print("FAIL: normalizing changed more than `scales`. The scale-ladder")
        print("experiment does NOT isolate the conditioning input; fix this first.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
