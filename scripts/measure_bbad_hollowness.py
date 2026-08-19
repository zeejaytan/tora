"""Are Breaking Bad's "vessels" hollow pots, or solid blobs shaped like pots?

The conservator's warning, 2026-08-19, and it could disqualify the whole corpus:
some Breaking Bad meshes are solid rather than thin-walled.

That is not a detail. It is the difference the conservator has been pointing at
all along -- the thickness spectrum, eggshell at one end and solid bone at the
other. A sherd's fracture is a RIBBON through a wall a few millimetres thick. A
solid object's fracture is a broad face through the body. They are different
geometry, they wear differently, and a model trained on solid "vases" would be
learning the wrong thing about pottery.

It is also plausible rather than paranoid: fracture modes tetrahedralises the
interior through a cage, so an input that is not watertight and hollow comes out
of that pipeline solid whatever it looked like as a surface.

TWO INDEPENDENT CHECKS, because either alone can mislead.

  MEASURED: `wear_ops._wall_estimate` finds, for points on the surface, the
  nearest surface facing back at them. On a shell that is the far wall, a few
  percent of the object away. On a solid there is nothing facing back within
  reach and it returns zero -- which is the honest answer for a solid, and the
  same estimator that handles bone in the wear model.

  DRAWN: a thin slab cut through the middle. Hollow shows two thin walls with
  space between; solid shows a filled cross-section. This is the check that
  cannot be argued with, and it is the one the workspace rules require before
  reporting anything about geometry.

Usage:
  python scripts/measure_bbad_hollowness.py --src dataset/breaking_bad_vol.hdf5 \
      --out artifacts/bbad_hollowness.png
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import _wall_estimate  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

CATS = ["Bottle", "Vase", "Mug", "Bowl", "Cup", "Teapot", "Plate", "WineBottle",
        "BeerBottle", "Teacup", "PillBottle", "WineGlass"]


def assemble(node_fr):
    """All pieces of one fracture instance, as one mesh."""
    vs, fs, off = [], [], 0
    for k in sorted(node_fr.keys(), key=lambda s: int(s) if s.isdigit() else s):
        g = node_fr[k]
        v = np.asarray(g["vertices"][:], dtype=np.float64)
        f = np.asarray(g["faces"][:], dtype=np.int64)
        vs.append(v)
        fs.append(f + off)
        off += len(v)
    return np.concatenate(vs), np.concatenate(fs)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", default="everyday")
    ap.add_argument("--per-cat", type=int, default=6)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    h = h5py.File(args.src, "r")
    ev = h[args.dataset]

    rows, shown = [], []
    for c in CATS:
        if c not in ev:
            continue
        objs = sorted(ev[c].keys())
        step = max(1, len(objs) // args.per_cat)
        walls = []
        for o in objs[::step][:args.per_cat]:
            node = ev[c][o]
            fr = sorted(node.keys())[0]
            v, f = assemble(node[fr])
            size = float(np.linalg.norm(v.max(0) - v.min(0)))
            w = _wall_estimate(v, f, np.arange(len(v)))
            walls.append(100 * w / size if w > 0 else 0.0)
            if len(shown) < 8 and len(walls) == 1:
                shown.append((c, v, size))
        found = [w for w in walls if w > 0]
        rows.append((c, len(walls), len(found),
                     float(np.median(found)) if found else 0.0))

    print("HOLLOW OR SOLID? wall found by the same estimator the wear model uses")
    print(f"  {'category':<16s} {'objects':>8s} {'wall found':>12s} "
          f"{'median wall':>13s}")
    print("  " + "-" * 54)
    for c, n, nf, med in rows:
        print(f"  {c:<16s} {n:>8d} {nf:>7d}/{n:<4d} "
              + (f"{med:>12.2f}%" if med > 0 else f"{'none':>13s}"))
    tot_n = sum(r[1] for r in rows)
    tot_f = sum(r[2] for r in rows)
    print("  " + "-" * 54)
    print(f"  {'TOTAL':<16s} {tot_n:>8d} {tot_f:>7d}/{tot_n:<4d}")
    print(f"\n  For comparison, our real scanned pottery: blue_pot walls "
          f"0.48-2.90% of object, plate 0.22-1.70%.")
    print("  A wall of zero means nothing faces back within reach -- solid.")

    # ---- the slice, which cannot be argued with --------------------------
    fig, axes = plt.subplots(1, len(shown), figsize=(2.6 * len(shown), 3.1))
    axes = np.atleast_1d(axes)
    for a, (c, v, size) in zip(axes, shown):
        ctr = v.mean(axis=0)
        P = v - ctr
        u = np.linalg.svd(P.T @ P)[0]
        long_ax, e1, e2 = u[:, 0], u[:, 1], u[:, 2]
        # a thin slab through the middle, cut ACROSS the object
        sel = np.abs(P @ e2) < 0.01 * size
        q = P[sel]
        a.scatter((q @ e1) / size, (q @ long_ax) / size, s=1.4, linewidths=0,
                  color="#1f4e79")
        a.set_aspect("equal")
        a.set_xticks([]); a.set_yticks([])
        a.set_title(f"{c}\nslice through the middle", fontsize=8.5)
    fig.suptitle(
        "Hollow or solid? A slab cut through each object.\n"
        "Two thin walls with space between = a vessel. A filled section = a "
        "solid blob shaped like one.", fontsize=10)
    fig.tight_layout(rect=(0, 0, 1, 0.86))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
