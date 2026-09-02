"""Normalize real-fracture HDF5s to the same unit-scale convention as the
shipped synthetic data.

Why this exists
---------------
The shipped synthetic fracture data (`bone_synthetic.hdf5`) is pre-normalized:
per object, max(|vertex|) == 0.5 (unit extent). The real Fractura meshes were
ingested in raw scan units, giving max(|vertex|) ~= 60-110.

CORRECTION, 2026-09-02. This header used to say:

    "`PointCloudDataset` normalizes model input either way (`scale =
    max(|pts_gt|); pts_gt /= scale`), so TRAINING AND INFERENCE ARE UNAFFECTED
    by this."

That is FALSE, and it is why the raw-unit Fractura subsets were left unfixed
and scored as though the model had failed on them. `scales` is not only metric
bookkeeping: `tora/modeling/tora.py` reads it out of the batch and passes it
into the flow model at every denoising step, and `PointCloudEncodingManager`
turns it into a sinusoidal code concatenated onto ALL N points
(`tora/modeling/flow_model/embedding.py`). It is a conditioning INPUT.

Breaking Bad objects arrive at max|v| = 0.5 and training jitters that with
random_scale_range (0.75, 1.25), so the model has only ever seen this input in
roughly [0.375, 0.625]. The real Fractura ceramics arrive at 44.7-119.9 --
100-190x outside that band, and far into the aliasing regime of an encoding
whose top frequency is 2^9. So normalizing changes inference too. Whether that
change rescues the score is measured by `scripts/hpc/eval_scale_ladder.slurm`;
`scripts/check_scale_conditioning.py` is the gate that keeps the two effects
separable.

The metric half of the story, which was correct: `Evaluator.compute` used to
multiply predictions and GT back by `scales` before scoring, and
`compute_part_acc` / `recall@{1cm,5cm}` used an ABSOLUTE 0.01 threshold. On
raw-unit real objects that threshold is ~0.01% of object size (vs 2% for
synthetic), so part_accuracy was structurally pinned at anchor-only (the anchor
is clamped to GT, CD=0, and passes trivially; nothing else can). That is now
fixed in the evaluator itself (`tora/eval/metrics.py:unit_box_scale`, gated by
`scripts/check_metric_scale_invariance.py`), so this script is no longer needed
to make the metric readable -- only to change what the model is told.

This rescales every piece of an object by a single shared per-object factor,
so relative geometry -- and therefore the assembly problem itself -- is exactly
preserved. `scales` changes, and so does the model's conditioning.

NOTE: this does NOT rename the group inside the file, while
`PointCloudDataModule._initialize_dataset_paths` derives the dataset name from
the filename stem. A normalized copy must therefore be named
`<groupname>.hdf5`. The runtime knob `data.normalize_object_scale=true` avoids
both that trap and a duplicate 3 GB file, and is the preferred route now.
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
