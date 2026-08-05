"""Can repeated smoothing push past the saturation limit?

This became the central question once the conservator identified SMOOTHNESS as
the axis that destroys the interlocking information, and therefore the axis that
determines whether these methods work. Material loss is modest in real sherds and
our simulated levels already match (0.2-2.7%); smoothness is where the difficulty
lives.

And on that axis we are capped. Smoothing saturates: galli_pot stalls at relief
0.288 and plate at 0.234, while the Juglet — the object being solved — sits at
0.171. We currently cannot generate training data as smooth as the target.

But the saturation was only ever measured against KERNEL SIZE (0.05 -> 0.08 ->
0.12 gave 0.1707 -> 0.1789 -> 0.1820, i.e. no further smoothing and slightly
worse). Repeated application at a fixed small kernel is a different operation:
each pass averages an already-averaged surface, the way real abrasion works
cycle after cycle rather than in one deep cut.

If iteration breaks the plateau, the training data can span the range that
matters. If it does not, that is a hard limit on how far simulated wear can go,
and it should be stated plainly rather than discovered later by someone training
on data that cannot represent their material.

Usage:
  python scripts/test_iterated_smoothing.py --objects galli_pot,plate,limb3
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fracture_mesh_ops import erode_fracture_band, piece_relief_stats  # noqa: E402

JUGLET_SMOOTHNESS = 0.171


def relief(pieces):
    return float(np.mean([piece_relief_stats(v, f)["relief_p90"] for v, f in pieces]))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5")
    ap.add_argument("--dataset", default="real_heldout_norm")
    ap.add_argument("--objects", default="galli_pot,plate,limb3")
    ap.add_argument("--passes", type=int, default=6)
    ap.add_argument("--kernel", type=float, default=0.05)
    args = ap.parse_args()

    print("Does REPEATED smoothing break the saturation plateau?")
    print(f"  target: the Juglet sits at {JUGLET_SMOOTHNESS:.3f} (lower = smoother)")
    print(f"  single-pass saturation: galli_pot 0.288, plate 0.234")
    print()

    with h5py.File(args.src, "r") as h:
        ds = h[args.dataset]
        for obj in [o.strip() for o in args.objects.split(",") if o.strip()]:
            grp = ds[obj]
            g = grp["pieces"] if "pieces" in grp else grp
            keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
            pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                       np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]

            r = relief(pieces)
            print(f"  {obj}: original {r:.4f}")
            cur = pieces
            for p in range(1, args.passes + 1):
                sm = erode_fracture_band(cur, strength=1.0,
                                         kernel_frac_max=args.kernel)
                cur = [(sm[i], cur[i][1]) for i in range(len(cur))]
                r = relief(cur)
                mark = "  <-- PAST the Juglet" if r < JUGLET_SMOOTHNESS else ""
                print(f"      pass {p}: {r:.4f}{mark}", flush=True)
            print(flush=True)


if __name__ == "__main__":
    main()
