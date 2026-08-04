"""Show, in cross-section, what wear actually does to a join between two sherds.

Raised by the conservator: if two fracture faces are straightish and both wear
by the same amount, the pieces can simply seat closer together and still mate —
the FIT is not damaged, the vessel just ends up marginally smaller. Only the
separation measured AT THE ORIGINAL POSES changes.

That matters, because the gap metric used throughout this work measures exactly
that separation at fixed poses. If the conservator is right, then for
straight-edged joins the metric records a difficulty that a person reassembling
the pot would not experience — and where wear genuinely hurts is on irregular,
interlocking faces, where lost material destroys the interlock that tells you
how the pieces go together.

This slices a thin slab through the contact between two adjacent fragments and
draws the profile before and after wear, so the question can be settled by
looking rather than by argument. It also reports whether the faces are straight
or interlocking, which is the property the argument turns on.

Usage:
  python scripts/visualise_wear_join.py --object blue_pot --out join.png
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import apply_wear, recede_surface  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def closest_pair(pieces):
    """The two fragments with the most contact — the clearest join to look at."""
    best, bi, bj = -1, 0, 1
    for i in range(len(pieces)):
        for j in range(i + 1, len(pieces)):
            a = pieces[i][0]
            b = pieces[j][0]
            sa = a if len(a) <= 40000 else a[::max(1, len(a) // 40000)]
            d, _ = cKDTree(b if len(b) <= 40000 else b[::max(1, len(b) // 40000)]).query(sa, workers=-1)
            scale = np.linalg.norm(np.concatenate([a, b]).max(0) - np.concatenate([a, b]).min(0))
            n = int((d < 0.01 * scale).sum())
            if n > best:
                best, bi, bj = n, i, j
    return bi, bj


def slab(pts, centre, normal, half_thickness):
    d = (pts - centre) @ normal
    return pts[np.abs(d) < half_thickness]


def roughness_of_face(a, b, scale):
    """How interlocking is this join? Spread of the contact band along the normal."""
    d, _ = cKDTree(b).query(a, workers=-1)
    band = a[d < 0.02 * scale]
    if len(band) < 50:
        return float("nan"), band
    c = band.mean(0)
    u, s, vt = np.linalg.svd(band - c, full_matrices=False)
    # smallest singular direction = face normal; its spread = how non-flat the face is
    return float(s[2] / (s[0] + 1e-12)), band


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5")
    ap.add_argument("--dataset", default="real_heldout_norm")
    ap.add_argument("--object", default="blue_pot")
    ap.add_argument("--recession", type=float, default=0.0030)
    ap.add_argument("--out", default="join.png")
    args = ap.parse_args()

    with h5py.File(args.src, "r") as h:
        grp = h[args.dataset][args.object]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                   np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]

    i, j = closest_pair(pieces)
    print(f"{args.object}: clearest join is fragments {i} and {j}", flush=True)

    pair = [pieces[i], pieces[j]]
    allv = np.concatenate([pair[0][0], pair[1][0]])
    scale = float(np.linalg.norm(allv.max(0) - allv.min(0)))

    flat, band = roughness_of_face(pair[0][0], pair[1][0], scale)
    print(f"  face non-flatness (0 = perfectly flat plate, >0.1 = strongly interlocking): {flat:.4f}")
    print(f"  -> this join is {'STRAIGHTISH' if flat < 0.05 else 'INTERLOCKING'}", flush=True)

    worn_rec = recede_surface(pair, recession_frac=args.recession)
    worn_all = apply_wear(pair, smoothing=1.0, recession=args.recession,
                          chip_count=4, chip_size=0.0022)

    # slice a slab through the middle of the contact band, perpendicular to the
    # face's longest direction, so the profile of BOTH faces is visible
    c = band.mean(0)
    u, s, vt = np.linalg.svd(band - c, full_matrices=False)
    normal, along, across = vt[2], vt[0], vt[1]
    ht = 0.004 * scale

    fig, axes = plt.subplots(1, 3, figsize=(16, 5.5))
    for ax, (title, ps) in zip(axes, [("original", pair),
                                      ("recession only", worn_rec),
                                      ("full wear (chip+smooth+recede)", worn_all)]):
        for k, (v, _) in enumerate(ps):
            sl = slab(v, c, normal, ht)
            if len(sl) == 0:
                continue
            x = (sl - c) @ along
            y = (sl - c) @ across
            m = (np.abs(x) < 0.12 * scale) & (np.abs(y) < 0.12 * scale)
            ax.scatter(x[m], y[m], s=1.2, alpha=0.55,
                       c="tab:blue" if k == 0 else "tab:red",
                       label=f"fragment {i if k == 0 else j}")
        ax.set_title(title)
        ax.set_aspect("equal")
        ax.legend(markerscale=8, loc="upper right", fontsize=8)
        ax.set_xlabel("along the join")
    axes[0].set_ylabel("across the join")
    fig.suptitle(f"{args.object}: cross-section through the join "
                 f"(non-flatness {flat:.3f}, recession {args.recession})")
    fig.tight_layout()
    fig.savefig(args.out, dpi=140)
    print(f"  wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
