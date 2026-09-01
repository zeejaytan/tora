"""Make an hdf5 dataset's internal name agree with its filename.

`tora/data/datamodule.py:96` takes the dataset name from the FILE STEM, and
`tora/data/dataset.py:156` then looks up `h5["data_split"][<stem>]`, while
`dataset.py:161` resolves each split member as `h5[<member>]` -- and members
are written as "<group>/<tag>". So all three must agree with the filename.

`bbad_vessels_v3.hdf5` was built with the group still called `bbad_vessels`,
which is not loadable under any config: with `dataset_names: ["bbad_vessels"]`
the datamodule finds no file, and with `["bbad_vessels_v3"]` the dataset raises
KeyError on the data_split lookup. It fails at load, not silently, but only
after the queue wait.

The rename is metadata only -- hdf5 groups are hard links, so moving a 2.7 GB
group copies nothing -- plus a rewrite of the small split membership lists.
Reversible by running it back the other way.

Usage:
  python scripts/align_dataset_group_to_filename.py \
      --src dataset/bbad_vessels_v3.hdf5 --dry-run
"""

import argparse
from pathlib import Path

import h5py
import numpy as np


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()

    src = Path(a.src)
    want = src.name.split(".")[0]                 # exactly datamodule.py:96

    with h5py.File(src, "r" if a.dry_run else "r+") as h:
        groups = [k for k in h.keys() if k != "data_split"]
        if groups == [want]:
            print(f"already aligned: group and file stem are both '{want}'")
            return
        if len(groups) != 1:
            raise SystemExit(f"expected one data group beside data_split, "
                             f"found {groups}. Not guessing.")
        have = groups[0]
        print(f"file stem '{want}', internal group '{have}' -- renaming\n")

        sgrp = h["data_split"][have]
        splits = list(sgrp.keys())
        n = {s: len(sgrp[s]) for s in splits}
        print("  splits:", ", ".join(f"{s} {n[s]}" for s in splits))
        print(f"  examples in the data group: {len(h[have].keys())}")

        if a.dry_run:
            print("\nDRY RUN -- nothing written.")
            return

        # 1. the data group: a hard link, so no bytes move
        h.move(have, want)

        # 2. the split lists, with their "<group>/<tag>" prefixes rewritten
        h.create_group(f"data_split/{want}")
        for s in splits:
            members = [v.decode() if isinstance(v, bytes) else str(v)
                       for v in sgrp[s][:]]
            fixed = [want + "/" + m.split("/", 1)[1] if "/" in m else m
                     for m in members]
            h["data_split"][want].create_dataset(
                s, data=np.array([f.encode() for f in fixed], dtype=object),
                dtype=h5py.special_dtype(vlen=bytes))
        del h["data_split"][have]

        # 3. read back and resolve one member per split the way dataset.py does
        print("\nverifying by resolving members the way dataset.py does:")
        for s in splits:
            got = [v.decode() for v in h["data_split"][want][s][:]]
            assert len(got) == n[s], f"{s}: {len(got)} != {n[s]}"
            probe = got[0]
            if "pieces" not in h[probe]:
                raise SystemExit(f"{s}: h5['{probe}'] has no 'pieces' -- the "
                                 f"prefix rewrite did not land")
            print(f"  {s:14s} {len(got):5d} members, h5['{probe}'] resolves  OK")


if __name__ == "__main__":
    main()
