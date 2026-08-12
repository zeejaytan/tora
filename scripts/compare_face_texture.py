"""Why the plate blunts less: its fracture texture lives at a coarser scale.

The claim this draws, made from the validation numbers and worth checking by eye
before it is believed: blunting cuts structure below a chosen cutoff, the cutoff
sits at 0.3-0.5% of object size, and on the plate the break-face texture is
mostly ABOVE that -- so the cut passes underneath it. On blue_pot, coxae and
vert9 the texture reaches down into the cut.

Two views, because either alone can mislead:

  THE SPECTRUM, per octave. Deviation from the local mean at radius R contains
  everything finer than R as well, so the raw curve rises with R on any surface
  and says little about where structure LIVES. The increment between successive
  radii does: it is the structure added by that octave alone. A peak in that
  curve is the scale of the texture.

  THE FACE ITSELF, per vertex and unbinned, coloured by the relief at one
  octave. Four earlier views of wear in this project measured correctly and
  were each too coarse to show the effect, so nothing here is averaged into a
  pixel and every panel states the physical scale it resolves.

Relief is the NORMAL deviation, never the full distance to the local mean. On
these meshes the sideways component is two to three times the relief at fine
scales and no amount of wear can remove it; measuring the total was what hid a
real blunting effect for three validation runs.

Usage:
  python scripts/compare_face_texture.py --src dataset/real_heldout_norm.hdf5 \
      --dataset real_heldout_norm --objects blue_pot plate coxae vert9 \
      --out artifacts/face_texture.png
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import _local_mean  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.gridspec import GridSpec  # noqa: E402

RADII = np.logspace(np.log10(0.002), np.log10(0.128), 13)
CUT_LO, CUT_HI = 0.003, 0.005          # the blunting cutoffs in use
FINE, MID = 0.004, 0.016               # octaves drawn on the face


def load(path, dsname, obj):
    with h5py.File(path, "r") as h:
        grp = h[dsname][obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        return [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                 np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]


def biggest_band(pieces, band_frac=0.02, max_pts=250000, seed=0):
    """Points on the widest contact band, and the object size."""
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    size = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    rng = np.random.default_rng(seed)
    best, band = -1, None
    for i, (vi, _) in enumerate(pieces):
        for j, (vj, _) in enumerate(pieces):
            if j == i:
                continue
            a = vi if len(vi) <= max_pts else vi[rng.choice(len(vi), max_pts, False)]
            b = vj if len(vj) <= max_pts else vj[rng.choice(len(vj), max_pts, False)]
            d, _ = cKDTree(b).query(a, workers=-1)
            sel = d < band_frac * size
            if int(sel.sum()) > best:
                best, band = int(sel.sum()), a[sel]
    return band, size


def normals(pts, k=24):
    _, nb = cKDTree(pts).query(pts, k=min(k, len(pts)), workers=-1)
    P = pts[nb] - pts[:, None, :]
    return np.linalg.eigh(np.einsum("nki,nkj->nij", P, P))[1][:, :, 0]


def relief_at(pts, nrm, size, rf):
    """Normal deviation from the local mean at radius rf, per vertex."""
    d = pts - _local_mean(pts, pts.copy(), rf * size)
    return np.abs((d * nrm).sum(axis=1)) / size * 100


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--objects", nargs="+", required=True)
    ap.add_argument("--face-a", default="blue_pot")
    ap.add_argument("--face-b", default="plate")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    data = {}
    for obj in args.objects:
        pieces = load(args.src, args.dataset, obj)
        band, size = biggest_band(pieces)
        nrm = normals(band)
        cum = np.array([relief_at(band, nrm, size, rf).mean() for rf in RADII])
        data[obj] = dict(band=band, size=size, nrm=nrm, cum=cum)
        print(f"{obj}: {len(band)} band points, object size {size:.4f}, "
              f"spacing {100 * np.median(cKDTree(band).query(band, k=2)[0][:, 1]) / size:.3f}%")

    fig = plt.figure(figsize=(15.5, 9.0))
    gs = GridSpec(2, 3, figure=fig, height_ratios=[1.0, 1.15], hspace=0.32,
                  wspace=0.26)
    colours = {"blue_pot": "#1f4e79", "plate": "#c1440e",
               "coxae": "#4a7c59", "vert9": "#7d5ba6"}

    # --- where structure lives -------------------------------------------
    ax = fig.add_subplot(gs[0, 0])
    for obj, d in data.items():
        ax.plot(100 * RADII, d["cum"], "-o", ms=3, color=colours.get(obj),
                label=obj, lw=1.6)
    ax.axvspan(100 * CUT_LO, 100 * CUT_HI, color="0.85", zorder=0)
    ax.text(100 * CUT_HI * 1.1, ax.get_ylim()[1] * 0.05, "blunting\ncuts here",
            fontsize=8, color="0.35")
    ax.set_xscale("log")
    ax.set_xlabel("scale (% of object size)")
    ax.set_ylabel("relief, % of object size")
    ax.set_title("Structure on the break face\n(includes everything finer)",
                 fontsize=10)
    ax.legend(fontsize=8)

    # per octave: the increment IS where the texture sits
    ax = fig.add_subplot(gs[0, 1])
    mid = np.sqrt(RADII[1:] * RADII[:-1])
    for obj, d in data.items():
        inc = np.diff(d["cum"])
        ax.plot(100 * mid, inc, "-o", ms=3, color=colours.get(obj), label=obj,
                lw=1.6)
    ax.axvspan(100 * CUT_LO, 100 * CUT_HI, color="0.85", zorder=0)
    ax.set_xscale("log")
    ax.set_xlabel("scale (% of object size)")
    ax.set_ylabel("relief added by this octave")
    ax.set_title("WHERE the texture sits\npeak = the scale of the teeth",
                 fontsize=10)
    ax.legend(fontsize=8)

    # how much of each object's texture the cut can reach
    ax = fig.add_subplot(gs[0, 2])
    names, frac = [], []
    for obj, d in data.items():
        below = np.interp(CUT_HI, RADII, d["cum"])
        names.append(obj)
        frac.append(100 * below / d["cum"][-1])
    ax.bar(names, frac, color=[colours.get(n) for n in names])
    ax.set_ylabel("% of all relief lying BELOW the cut")
    ax.set_title("How much the cutoff can reach\n(low = blunting passes under it)",
                 fontsize=10)
    for i, v in enumerate(frac):
        ax.text(i, v + 0.3, f"{v:.1f}%", ha="center", fontsize=9)
    ax.tick_params(axis="x", labelsize=8)

    # --- the faces themselves --------------------------------------------
    def draw(axis, obj, rf, vmax, title):
        d = data[obj]
        r = relief_at(d["band"], d["nrm"], d["size"], rf)
        P = d["band"] - d["band"].mean(0)
        U = np.linalg.svd(P.T @ P)[0]
        x, y = (P @ U[:, 0]) / d["size"] * 100, (P @ U[:, 1]) / d["size"] * 100
        s = axis.scatter(x, y, c=r, s=0.7, cmap="magma", vmin=0, vmax=vmax,
                         linewidths=0)
        axis.set_aspect("equal")
        axis.set_title(title, fontsize=9.5)
        axis.set_xlabel("% of object size")
        plt.colorbar(s, ax=axis, fraction=0.046, label="relief, % of object")

    vfine = max(np.percentile(relief_at(data[o]["band"], data[o]["nrm"],
                                        data[o]["size"], FINE), 99)
                for o in (args.face_a, args.face_b) if o in data)
    draw(fig.add_subplot(gs[1, 0]), args.face_a, FINE, vfine,
         f"{args.face_a} at {100 * FINE:.1f}% — the scale we cut at\n"
         f"texture is present here, so blunting bites")
    draw(fig.add_subplot(gs[1, 1]), args.face_b, FINE, vfine,
         f"{args.face_b} at {100 * FINE:.1f}% — same scale, same colour range\n"
         f"far less to cut")
    vmid = float(np.percentile(relief_at(data[args.face_b]["band"],
                                         data[args.face_b]["nrm"],
                                         data[args.face_b]["size"], MID), 99))
    draw(fig.add_subplot(gs[1, 2]), args.face_b, MID, vmid,
         f"{args.face_b} at {100 * MID:.1f}% — its own texture scale\n"
         f"note the colour range: {vmid / vfine:.0f}x the panels left")

    fig.suptitle("The plate is not smoother — its fracture texture is COARSER, "
                 "and sits above the scale the blunting cuts at\n"
                 "every point drawn per vertex, unbinned; relief is the normal "
                 "deviation, never the total distance", fontsize=11)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(args.out, dpi=140, bbox_inches="tight")
    print(f"wrote {args.out}")

    print("\n  relief at each scale, % of object size")
    print("  " + "obj".ljust(10) + "".join(f"{100 * r:>7.2f}%" for r in RADII))
    for obj, d in data.items():
        print("  " + obj.ljust(10) + "".join(f"{v:>8.3f}" for v in d["cum"]))


if __name__ == "__main__":
    main()
