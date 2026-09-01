"""Look at the objects either side of the solid-lump cut, at the cut.

`filter_lumps_from_splits.py` removed 714 of 1882 training examples on one
scalar, `fill_fraction < 0.65`. That number was validated across its whole
range by `render_fill_ladder.py`, but a ladder spanning 0.04 to 0.99 says
nothing about the one place this cut can actually be wrong: THE BOUNDARY.
Drawing a random sample of survivors would show obvious vases and prove
nothing -- the easy middle is not where a threshold fails.

So this renders the WORST SURVIVORS against the NARROWEST MISSES: the highest-
fill examples still in `train`, and the lowest-fill examples just dropped. If
the kept row still reads as vessels with a real bore and the dropped row reads
as lumps with at most a scooped dish, the cut is in the right place. If the two
rows look alike, it is not, and 714 examples were discarded on a number that
does not mean what its label says.

Sections use the median of three orthogonal cuts with every scanline's measured
interior shaded -- the same routine and the same honesty constraint as the
ladder figure, whose outline-only first version confirmed both ends and left
the middle unreadable (`docs/lessons.md`).

Usage:
  python scripts/check_lump_cut.py --src dataset/bbad_vessels_v3.hdf5 \
      --dataset bbad_vessels --out artifacts/lump_cut_boundary.png
"""

import argparse
import json
from pathlib import Path

import h5py
import numpy as np
import trimesh

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                                   # noqa: E402

from measure_gap_as_network_sees import load_meshes               # noqa: E402
from screen_vessel_corpus import fill_fraction                    # noqa: E402
from render_fill_ladder import draw                               # noqa: E402


def decode(arr):
    return [v.decode() if isinstance(v, bytes) else str(v) for v in arr]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", default="bbad_vessels")
    ap.add_argument("--out", default="artifacts/lump_cut_boundary.png")
    ap.add_argument("--max-fill", type=float, default=0.65)
    ap.add_argument("--n", type=int, default=5)
    a = ap.parse_args()

    man = json.loads(Path(str(a.src) + ".manifest.json").read_text())

    with h5py.File(a.src, "r") as h:
        sgrp = h["data_split"][a.dataset]
        if "train_all" not in sgrp:
            raise SystemExit("no train_all -- run filter_lumps_from_splits.py first")
        kept = set(decode(sgrp["train"][:]))
        allm = decode(sgrp["train_all"][:])
        dropped = [m for m in allm if m not in kept]

        def fill_of(m):
            return float(man[m.split("/", 1)[1]]["fill_fraction"])

        # worst survivors: highest fill still in; narrowest misses: lowest out
        top_kept = sorted(kept, key=fill_of, reverse=True)[:a.n]
        low_drop = sorted(dropped, key=fill_of)[:a.n]

        fig, axes = plt.subplots(2, a.n, figsize=(3.4 * a.n, 7.4))
        for row, (members, label) in enumerate(
                [(top_kept, "KEPT"), (low_drop, "DROPPED")]):
            for col, full in enumerate(members):
                tag = full.split("/", 1)[1]
                rec = man[tag]
                meshes = load_meshes(h[a.dataset][tag])
                asm = trimesh.util.concatenate(meshes)
                got = fill_fraction(asm)
                cells = rec.get("cells_through_wall")
                title = (f"{label}  {tag.split('__')[0]} {tag.split('__')[1][:8]}\n"
                         f"fill {fill_of(full):.3f}"
                         + (f", redrawn {got:.3f}" if got is not None else "")
                         + (f"   cells {cells:.2f}" if cells is not None else ""))
                draw(axes[row, col], asm, title)
                for s in axes[row, col].spines.values():
                    s.set_edgecolor("#2a7" if row == 0 else "#b33")
                    s.set_linewidth(2.0)

    fig.suptitle(
        f"The solid-lump cut at the boundary (fill < {a.max_fill}).  "
        f"Top row = worst objects KEPT for training.  "
        f"Bottom row = mildest objects DROPPED.  "
        f"Pink = each scanline's measured interior.", fontsize=11)
    fig.tight_layout(rect=[0, 0, 1, 0.94])
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130)
    print("wrote", out)

    print("\nkept, highest fill:")
    for m in top_kept:
        print(f"  {fill_of(m):.3f}  {m.split('/', 1)[1]}")
    print("dropped, lowest fill:")
    for m in low_drop:
        print(f"  {fill_of(m):.3f}  {m.split('/', 1)[1]}")


if __name__ == "__main__":
    main()
