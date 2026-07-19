"""Build thinwalled.hdf5: a tiny wrapper file that exposes a filtered val split
over thin-walled-pottery categories from breaking_bad_vol.hdf5, using an HDF5
external link so no underlying data is duplicated.

Thin-walled pottery categories chosen to match classic ceramic vessel forms:
    Bowl, Cup, Plate, Mug, Teacup, Teapot, Vase
(Excludes glass Bottles/Wine, ToyFigure, Mirror, Ring, Statue, Spoon, etc.)
"""
import os
import numpy as np
import h5py

SRC = "/data/gpfs/projects/punim2657/TORA/dataset/breaking_bad_vol.hdf5"
DST = "/data/gpfs/projects/punim2657/TORA/dataset/thinwalled.hdf5"
POTTERY = {"Bowl", "Cup", "Plate", "Mug", "Teacup", "Teapot", "Vase"}

with h5py.File(SRC, "r", libver="latest", swmr=True) as fs:
    val_raw = [r.decode() for r in fs["data_split/everyday/val"][:]]
    train_raw = [r.decode() for r in fs["data_split/everyday/train"][:]]

def filt(names):
    return [n for n in names if n.split("/")[1] in POTTERY]

val_sel = filt(val_raw)
train_sel = filt(train_raw)

from collections import Counter
print(f"Kept {len(val_sel)}/{len(val_raw)} val fragments")
print(f"Kept {len(train_sel)}/{len(train_raw)} train fragments (not used for eval)")
print("Per-category val counts:")
for k, v in sorted(Counter(n.split("/")[1] for n in val_sel).items(), key=lambda kv: -kv[1]):
    print(f"  {k:10s} {v}")

if os.path.exists(DST):
    os.remove(DST)

# dtype must match source split arrays (bytes string)
str_dt = h5py.special_dtype(vlen=bytes)
with h5py.File(DST, "w", libver="latest") as fd:
    # Split lists under the dataset_name "thinwalled" (must match the filename prefix
    # that TORA's datamodule uses to key dataset_paths).
    g = fd.create_group("data_split/thinwalled")
    g.create_dataset("val", data=np.array([s.encode() for s in val_sel], dtype=object), dtype=str_dt)
    g.create_dataset("train", data=np.array([s.encode() for s in train_sel], dtype=object), dtype=str_dt)
    # External link so h5[name] (e.g. "everyday/Bowl/hash/mode_N") transparently
    # reads from the original 25 GB file, without copying any point cloud data.
    fd["everyday"] = h5py.ExternalLink(os.path.basename(SRC), "/everyday")

print(f"\nWrote {DST}")
print(f"File size: {os.path.getsize(DST)/1e6:.2f} MB")

# Sanity: open the new file and access one fragment through the external link
with h5py.File(DST, "r", libver="latest", swmr=True) as f:
    n = f["data_split/thinwalled/val"][0].decode()
    print(f"\nSanity read: first val fragment = {n}")
    grp = f[n]
    if "pieces" in grp:
        grp = grp["pieces"]
    print(f"  piece count = {len(grp.keys())}")
    print(f"  first piece keys = {list(list(grp.values())[0].keys())[:8]}")
