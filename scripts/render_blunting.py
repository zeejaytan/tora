"""Look at what the blunting actually did, at the scale it claims to work at.

Mandatory companion to `validate_wear_spectrum.py`, under the workspace rule
that any operation which moves or removes geometry is rendered before/after as
part of its validation. That rule exists because a wear bug -- surfaces pushed
TOWARD their neighbour on the 7-15% of scanned normals wound inward -- survived
three rounds of numeric validation and was obvious within seconds of drawing
the join.

AND THE HARDER HALF OF THE RULE: check the view resolves the scale being
tested. Four successive views of wear failed that way, each measuring correctly
and each too blunt to show the effect -- a slab sliced along the fracture face
instead of across it, a slice across the whole fragment where the displacement
was sub-pixel, a break-face height map swamped by the face's own undulation
(+-0.045 against a 0.002 change), and a high-passed version of it whose pixels
still averaged tens of vertices.

So this does not draw the surface. It draws THE MEASURED QUANTITY ITSELF, per
vertex, unbinned and unprojected: how far each point stood proud of its local
envelope before, how far it stands proud after, and how much material left.
Nothing is averaged into a pixel, so nothing can hide in a pixel.

THREE THINGS TO LOOK FOR, in order of how badly each would matter:

  1. ONE-SIDEDNESS. Every displacement must be removal. A single vertex on the
     wrong side of zero is material ADDED by an abrasion model, which is the
     defect class that has bitten this project twice. Drawn as a hard count,
     not a distribution, because the count is the claim.

  2. PEAKS GO, VALLEYS STAY. The before/after asperity height should collapse
     toward zero for points that stood proud, and lie on the diagonal for
     points that sat in hollows. A model that smooths symmetrically pulls BOTH
     toward zero, and that is visible here at a glance.

  3. THE CURVE SURVIVES. Removal is drawn on the break face itself. It should
     look like frost on the high points, not like the face being shaved down.
     Large smooth regions of heavy removal mean the cutoff is eating the shape.

Usage:
  python scripts/render_blunting.py --src dataset/real_heldout_norm.hdf5 \
      --dataset real_heldout_norm --object blue_pot --out artifacts/blunt.png
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import (_band_mask, _local_mean, _outward_directions,  # noqa: E402
                      blunt_asperities)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def load(path, dsname, want=""):
    with h5py.File(path, "r") as h:
        ds = h[dsname]
        obj = want or sorted(ds.keys())[0]
        grp = ds[obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        return obj, [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                      np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--object", default="")
    ap.add_argument("--piece", type=int, default=-1,
                    help="which fragment to draw; default = the one with the "
                         "largest contact band")
    ap.add_argument("--cut", type=float, default=0.005)
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    obj, pieces = load(args.src, args.dataset, args.object)
    masks = [_band_mask(pieces, i, pieces[i][0]) for i in range(len(pieces))]
    i = (args.piece if args.piece >= 0
         else int(np.argmax([(m[1] > 0.02).sum() for m in masks])))

    worn = blunt_asperities(pieces, cut_frac=args.cut, strength=args.strength,
                            passes=args.passes, masks=masks)

    v0, f0 = pieces[i]
    v1 = worn[i][0]
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    size = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    band = masks[i][1] > 0.02
    idx = np.where(band)[0]
    print(f"{obj}: fragment {i} of {len(pieces)}, {len(idx)} band vertices "
          f"of {len(v0)}; object size {size:.4f}")

    out = _outward_directions(v0, idx, size)
    disp = ((v1[idx] - v0[idx]) * out).sum(axis=1) / size * 100     # % of object
    # ONE ruler, taken from the untouched surface, for both readings. Measuring
    # "after" against a freshly recomputed envelope compares it with a ruler
    # that moved: removing material lowers the envelope, so a face truncated
    # perfectly flat still reads as standing proud of its new mean. That is how
    # a first version reported peaks "keeping 81% of their height" on a surface
    # whose peaks had genuinely been cut.
    env0 = _local_mean(v0[idx], v0[idx], args.cut * size)
    h_before = ((v0[idx] - env0) * out).sum(axis=1) / size * 100
    h_after = ((v1[idx] - env0) * out).sum(axis=1) / size * 100

    added = int((disp > 1e-9).sum())
    moved = int((disp < -1e-12).sum())

    fig, ax = plt.subplots(1, 3, figsize=(16.5, 5.0))
    fig.suptitle(
        f"{obj} fragment {i} — blunting at a {100 * args.cut:.1f}% cutoff, "
        f"strength {args.strength}, {args.passes} passes\n"
        f"everything below is PER VERTEX, unbinned: "
        f"{len(idx)} band vertices",
        fontsize=11)

    # 1. one-sidedness. The count IS the claim, so it is stated, not implied.
    a = ax[0]
    a.hist(disp, bins=200, color="#444444")
    a.axvline(0, color="crimson", lw=1.2)
    a.set_yscale("log")
    a.set_xlabel("displacement along the outward direction, % of object size")
    a.set_ylabel("vertices (log)")
    a.set_title(f"1. material must only LEAVE\n"
                f"{added} vertices moved outward"
                + ("  ** MATERIAL ADDED **" if added else "  (none — correct)"),
                fontsize=10,
                color="crimson" if added else "darkgreen")
    a.text(0.02, 0.95, f"{moved} vertices lost material\n"
                       f"most removed: {-disp.min():.4f}% of object",
           transform=a.transAxes, va="top", fontsize=8.5)

    # 2. peaks go, valleys stay. Symmetric smoothing would flatten both arms.
    a = ax[1]
    lim = float(np.percentile(np.abs(h_before), 99.5))
    a.plot([-lim, lim], [-lim, lim], color="#888888", lw=0.8, ls="--",
           label="unchanged")
    a.axhline(0, color="crimson", lw=0.8)
    sub = np.random.default_rng(0).choice(
        len(idx), min(60000, len(idx)), replace=False)
    a.scatter(h_before[sub], h_after[sub], s=0.6, alpha=0.15, color="#1f4e79",
              linewidths=0)
    a.set_xlim(-lim, lim)
    a.set_ylim(-lim, lim)
    a.set_xlabel("height above local envelope BEFORE, % of object")
    a.set_ylabel("... AFTER")
    peaks = h_before > 0.1 * lim
    hollows = h_before < -0.1 * lim
    kept = (float(np.mean(h_after[hollows] / h_before[hollows]))
            if hollows.any() else float("nan"))
    cut = (float(np.mean(h_after[peaks] / h_before[peaks]))
           if peaks.any() else float("nan"))
    a.set_title(f"2. peaks truncated, hollows left alone\n"
                f"peaks keep {100 * cut:.0f}% of their height, "
                f"hollows keep {100 * kept:.0f}%", fontsize=10)

    # 3. where it happened, on the face. Frost on the high points is right;
    #    broad smooth regions of removal mean the cutoff is eating the shape.
    a = ax[2]
    P = v0[idx] - v0[idx].mean(0)
    U = np.linalg.svd(P.T @ P)[0]
    x, y = P @ U[:, 0], P @ U[:, 1]
    s = a.scatter(x / size * 100, y / size * 100, c=-disp, s=1.2,
                  cmap="inferno", vmin=0,
                  vmax=float(np.percentile(-disp, 99.5)), linewidths=0)
    a.set_aspect("equal")
    a.set_xlabel("% of object size")
    a.set_title("3. material removed, on the break face\n"
                "frost on the high points = right; broad patches = "
                "cutoff too coarse", fontsize=10)
    plt.colorbar(s, ax=a, label="removed, % of object size")

    fig.tight_layout(rect=(0, 0, 1, 0.90))
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=150)
    print(f"wrote {args.out}")
    print(f"  one-sidedness: {added} vertices gained material "
          f"({'FAIL' if added else 'pass'})")
    print(f"  peaks keep {100 * cut:.1f}% of their height, "
          f"hollows keep {100 * kept:.1f}%")
    print("  A picture can answer the wrong question as convincingly as a")
    print("  statistic can. These are per-vertex and unbinned so that the")
    print("  scale of the view cannot be the thing being looked at.")


if __name__ == "__main__":
    main()
