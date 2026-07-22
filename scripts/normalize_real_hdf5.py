"""Normalize real-fracture HDF5s to the same unit-scale convention as the
shipped synthetic data.

Why this exists
---------------
The shipped synthetic fracture data (`bone_synthetic.hdf5`) is pre-normalized:
per object, max(|vertex|) == 0.5 (unit extent). The real Fractura meshes were
ingested in raw scan units, giving max(|vertex|) ~= 60-110.

`PointCloudDataset` normalizes model input either way (`scale = max(|pts_gt|);
pts_gt /= scale`), so TRAINING AND INFERENCE ARE UNAFFECTED by this. But
`Evaluator.compute` multiplies predictions and GT back by `scales` before
scoring, and `compute_part_acc` / `recall@{1cm,5cm}` use an ABSOLUTE 0.01
threshold. On raw-unit real objects that threshold is ~0.01% of object size
(vs 2% for synthetic), so part_accuracy is structurally pinned at anchor-only
(the anchor is clamped to GT, CD=0, and passes trivially; nothing else can).

This rescales every piece of an object by a single shared per-object factor,
so relative geometry -- and therefore the assembly problem itself -- is exactly
preserved. Only `scales`, and hence metric thresholding, changes.
"""

import argparse
import shutil

import h5py
import numpy as np

TARGET_MAX_ABS = 0.5  # matches synthetic convention (max|v| == 0.5)


def object_scale(pieces_group) -> float:
    """Max abs coordinate over all pieces of one object (pre-normalization)."""
    m = 0.0
    for p in pieces_group.keys():
        v = pieces_group[p]["vertices"][:]
        if v.size:
            m = max(m, float(np.abs(v).max()))
    return m


def normalize_file(src: str, dst: str, dataset_names: list[str]) -> None:
    shutil.copyfile(src, dst)
    with h5py.File(dst, "r+") as f:
        for ds in dataset_names:
            if ds not in f:
                print(f"  [skip] no group '{ds}'")
                continue
            for obj in f[ds].keys():
                grp = f[ds][obj]
                if "pieces" not in grp:
                    continue
                pieces = grp["pieces"]
                s = object_scale(pieces)
                if s <= 0:
                    continue
                factor = TARGET_MAX_ABS / s
                for p in pieces.keys():
                    d = pieces[p]["vertices"]
                    d[...] = (d[:] * factor).astype(d.dtype)
                print(f"  {ds}/{obj:24s} max|v| {s:9.3f} -> {s * factor:.3f}  (x{factor:.6f})")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dst", required=True)
    ap.add_argument("--dataset-names", nargs="+", required=True)
    a = ap.parse_args()
    print(f"normalizing {a.src} -> {a.dst}  (target max|v| = {TARGET_MAX_ABS})")
    normalize_file(a.src, a.dst, a.dataset_names)
    print("done")
