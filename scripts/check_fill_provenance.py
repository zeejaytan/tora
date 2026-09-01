"""Is the fill number the lump filter used actually a measurement of THIS file?

`filter_lumps_from_splits.py` dropped 714 training examples on
`manifest[tag]["fill_fraction"]`. That value is not measured on the file it was
applied to: `build_bbad_vessel_trainset.py:394` copies it out of
`artifacts/corpus_screen.csv`, which was produced by job 29765705 on the OLD
`bbad_vessels.hdf5` at the FRESH wear level. v3 is a rebuild, and the examples
carrying the number are worn.

Drawing the cut at its boundary (`artifacts/lump_cut_boundary.png`) showed
panels whose redrawn fill sat on the other side of the threshold from the
manifest value it was filtered by -- e.g. Vase bcf5a4b7 kept at 0.598, redraws
0.669. So this remeasures fill on the v3 meshes themselves and reports how many
examples the two numbers disagree about. A threshold is only as good as the
agreement between the ruler and the thing it was applied to.

Usage:
  python scripts/check_fill_provenance.py --src dataset/bbad_vessels_v3.hdf5 \
      --dataset bbad_vessels --limit 0 --out artifacts/fill_provenance.csv
"""

import argparse
import json
import time
from pathlib import Path

import h5py
import numpy as np
import trimesh

from measure_gap_as_network_sees import load_meshes                # noqa: E402
from screen_vessel_corpus import fill_fraction                     # noqa: E402


def decode(arr):
    return [v.decode() if isinstance(v, bytes) else str(v) for v in arr]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", default="bbad_vessels")
    ap.add_argument("--max-fill", type=float, default=0.65)
    ap.add_argument("--limit", type=int, default=0, help="0 = every example")
    ap.add_argument("--out", default="artifacts/fill_provenance.csv")
    a = ap.parse_args()

    man = json.loads(Path(str(a.src) + ".manifest.json").read_text())

    with h5py.File(a.src, "r") as h:
        sgrp = h["data_split"][a.dataset]
        key = "train_all" if "train_all" in sgrp else "train"
        members = decode(sgrp[key][:])
        if a.limit:
            members = members[::max(1, len(members) // a.limit)][:a.limit]

        rows, t0 = [], time.time()
        for i, full in enumerate(members):
            tag = full.split("/", 1)[1]
            old = float(man[tag]["fill_fraction"])
            asm = trimesh.util.concatenate(load_meshes(h[a.dataset][tag]))
            new = fill_fraction(asm)
            rows.append((tag, old, new))
            if (i + 1) % 25 == 0:
                el = time.time() - t0
                print(f"  {i+1}/{len(members)}  {el:.0f}s elapsed, "
                      f"{el/(i+1)*len(members):.0f}s projected", flush=True)

    ok = [(t, o, n) for t, o, n in rows if n is not None]
    d = np.array([n - o for _, o, n in ok])
    old_lump = np.array([o >= a.max_fill for _, o, _ in ok])
    new_lump = np.array([n >= a.max_fill for _, _, n in ok])
    flip = old_lump != new_lump

    print(f"\n{len(rows)} examples, {len(rows)-len(ok)} unsectionable")
    print(f"fill difference (remeasured - manifest): median {np.median(d):+.3f}, "
          f"mean {d.mean():+.3f}, p90 |diff| {np.percentile(np.abs(d), 90):.3f}, "
          f"max |diff| {np.abs(d).max():.3f}")
    print(f"DISAGREE about the {a.max_fill} threshold: {flip.sum()} of {len(ok)}"
          f"  ({100*flip.mean():.1f}%)")
    print(f"  kept but is a lump when remeasured:  {(new_lump & ~old_lump).sum()}")
    print(f"  dropped but is a vessel when remeasured: {(old_lump & ~new_lump).sum()}")

    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        fh.write("tag,manifest_fill,remeasured_fill,disagrees\n")
        for t, o, n in rows:
            f = "" if n is None else int((o >= a.max_fill) != (n >= a.max_fill))
            fh.write(f"{t},{o:.4f},{'' if n is None else f'{n:.4f}'},{f}\n")
    print("wrote", out)


if __name__ == "__main__":
    main()
