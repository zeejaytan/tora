#!/usr/bin/env python3
"""Build a small real-fracture TRAINING split from Fractura's real objects.

Fractura's `bones`/`ceramics`/`egg` datasets ship with `data_split/<name>/train`
EMPTY (0 samples) — every real object is assigned only to `val` (confirmed by
inspecting `fractura_real.hdf5` directly). No officially released TORA
checkpoint could therefore have trained on any real fracture object; this is
a structural fact about the shipped dataset, not a checkpoint-specific quirk.

This script copies a chosen subset of real objects (whole multi-part objects,
not 2-piece pairs) into a new HDF5 with a real, non-empty `train` split, so a
fine-tuning run can be tested at all. Deliberately EXCLUDES the six objects
already used in `pairs_real.hdf5` (vert9, limb3, coxae, galli_pot, plate,
blue_pot) so that HDF5 can be reused unmodified as a genuinely held-out
post-fine-tune evaluation set — no new eval data engineering needed.

Usage:
  python scripts/build_finetune_real_hdf5.py \\
    --source /path/to/dataset/fractura_real.hdf5 \\
    --out /path/to/dataset/real_finetune.hdf5
"""

import argparse

import h5py
import numpy as np


def copy_piece(src: h5py.Group, dst: h5py.Group) -> None:
    v = np.asarray(src["vertices"][:], dtype=np.float64)
    f = np.asarray(src["faces"][:], dtype=np.int64)
    dst.create_dataset("vertices", data=v)
    dst.create_dataset("faces", data=f)
    shared = (np.asarray(src["shared_faces"][:], dtype=np.int64)
              if "shared_faces" in src else np.zeros(len(f), dtype=np.int64))
    dst.create_dataset("shared_faces", data=shared)


# Held out for pairwise-oracle re-eval after fine-tuning (already in pairs_real.hdf5).
HELD_OUT = {
    "bones": ["vert9", "limb3", "coxae"],
    "ceramics": ["galli_pot", "plate", "blue_pot"],
    "egg": [],
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--category", default="real_finetune")
    args = ap.parse_args()

    train_keys, val_keys = [], []
    with h5py.File(args.source, "r") as src, h5py.File(args.out, "w") as dst:
        for group_name in ("bones", "ceramics", "egg"):
            grp = src[group_name] if group_name in src else src["data_split"][group_name]
            # object names come from data_split listing, not group iteration
            names_raw = src["data_split"][group_name]["val"][:]
            names = [n.decode() if isinstance(n, bytes) else str(n) for n in names_raw]
            held_out = set(HELD_OUT.get(group_name, []))
            for obj_name in names:
                short_name = obj_name.split("/")[-1]
                src_obj = src[obj_name]
                src_pieces = src_obj["pieces"] if "pieces" in src_obj else src_obj
                out_name = f"{args.category}/{group_name}__{short_name}"
                out_grp = dst.create_group(out_name)
                out_pieces = out_grp.create_group("pieces")
                keys = sorted(src_pieces.keys(), key=int)
                for k in keys:
                    copy_piece(src_pieces[k], out_pieces.create_group(k))
                if short_name in held_out:
                    val_keys.append(out_name.encode())
                    print(f"  [held out -> val] {out_name} ({len(keys)} pieces)")
                else:
                    train_keys.append(out_name.encode())
                    print(f"  [train]           {out_name} ({len(keys)} pieces)")

        ds_root = dst.create_group("data_split")
        split = ds_root.create_group(args.category)
        split.create_dataset("train", data=np.array(train_keys, dtype=object))
        split.create_dataset("val", data=np.array(val_keys, dtype=object))

    print(f"\nwrote {args.out}: {len(train_keys)} train objects, {len(val_keys)} val objects")


if __name__ == "__main__":
    main()
