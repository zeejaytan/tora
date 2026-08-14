"""Before and after, at a scale where the difference is actually visible.

Conservator, 2026-08-13: the previous export was a mesh with no context -- five
identically shaped copies at the same coordinates, no before, no after, nothing
to tell them apart. Correct criticism. This replaces it.

THE REASON A PLAIN BEFORE/AFTER DOES NOT WORK, and it has to be said rather
than worked around silently: blunting removes about 0.018% of the object. Lay
the worn sherd over the fresh one and you see one sherd. That is the failure
this project has hit four times -- a view that measures the right thing and is
too coarse to show it. So there are two outputs and each is honest about its
own scale.

  1. A SECTION ACROSS THE BREAK FACE (png). Not along it -- across it, which is
     the mistake made the first time. Height is drawn as the amount each point
     stands proud of the surface's own local envelope, which is the ruler the
     wear model itself uses, so the teeth fill the plot instead of being lost
     under the curve of the face. Fresh and worn are two lines with the removed
     material shaded between them. The section runs from one edge of the break
     face, through the middle, to the other edge, so the failure at the edges
     and the correct behaviour in the middle appear in the same drawing.

  2. A MESH LAID OUT IN A ROW (glb), copies separated in space and named in
     view order, including the wear exaggerated 50x so it can be seen at all.
     The exaggeration is in the object name. The true-scale worn copy is there
     beside it so the honest difference can be checked against the amplified
     one.

WHAT TO LOOK FOR. In the middle of the face the worn line should sit below the
fresh one wherever the fresh line peaks, and lie on top of it in the hollows --
peaks cut, valleys untouched, which is what the conservator described wear
doing. Within about one cutoff of either edge the two lines should be almost
indistinguishable, which is the defect: blunting removes roughly one part in
eleven of what is available there, against nearly all of it in the middle.

Usage:
  python scripts/show_blunting_before_after.py --src dataset/real_heldout_norm.hdf5 \
      --dataset real_heldout_norm --object plate --out-dir artifacts/
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import (_band_mask, _local_mean, _outward_directions,  # noqa: E402
                      blunt_asperities)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import cm  # noqa: E402

EXAGGERATION = 50.0


def load(path, dsname, obj):
    with h5py.File(path, "r") as h:
        grp = h[dsname][obj]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        return [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                 np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]


def region_edge(faces, in_region):
    """Vertices of the region touching one outside it, along MESH edges.

    Not by distance: the two long edges of a thin ribbon are close together in
    space, so a proximity rule would mark the whole ribbon as edge.
    """
    e = faces[:, [0, 1, 1, 2, 2, 0]].reshape(-1, 2)
    a, b = e[:, 0], e[:, 1]
    cross = in_region[a] != in_region[b]
    out = np.zeros(len(in_region), bool)
    out[a[cross]] = True
    out[b[cross]] = True
    return out & in_region


def paint(v, f, cols):
    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    m.visual = trimesh.visual.ColorVisuals(mesh=m, vertex_colors=cols)
    return m


def heat(values, cmap, vmin, vmax):
    t = np.clip((values - vmin) / max(vmax - vmin, 1e-12), 0, 1)
    return (np.asarray(matplotlib.colormaps[cmap](t)) * 255).astype(np.uint8)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--object", required=True)
    ap.add_argument("--piece", type=int, default=-1)
    ap.add_argument("--cut", type=float, default=0.005)
    ap.add_argument("--strength", type=float, default=1.0)
    ap.add_argument("--passes", type=int, default=3)
    ap.add_argument("--sections", type=int, default=3)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    pieces = load(args.src, args.dataset, args.object)
    masks = [_band_mask(pieces, i, pieces[i][0]) for i in range(len(pieces))]
    i = (args.piece if args.piece >= 0
         else int(np.argmax([(m[1] > 0.02).sum() for m in masks])))
    worn = blunt_asperities(pieces, cut_frac=args.cut, strength=args.strength,
                            passes=args.passes, masks=masks)

    v0, f0 = pieces[i]
    v1 = worn[i][0]
    allv = np.concatenate([v for v, _ in pieces], axis=0)
    size = float(np.linalg.norm(allv.max(0) - allv.min(0)))
    R = args.cut * size
    band = masks[i][1] > 0.02
    idx = np.where(band)[0]
    print(f"{args.object}: fragment {i} of {len(pieces)}, {len(idx)} break-face "
          f"vertices of {len(v0)}, object size {size:.4f}, "
          f"cutoff {100 * args.cut:.1f}% = {R:.5f}")

    nrm = _outward_directions(v0, idx, size)
    env0 = _local_mean(v0[idx], v0[idx], R)
    h_fresh = ((v0[idx] - env0) * nrm).sum(axis=1) / size * 100
    h_worn = ((v1[idx] - env0) * nrm).sum(axis=1) / size * 100

    edge_v = region_edge(f0, band)
    d_edge, _ = cKDTree(v0[edge_v]).query(v0[idx], workers=-1)

    # ---- the section ------------------------------------------------------
    P = v0[idx] - v0[idx].mean(0)
    U = np.linalg.svd(P.T @ P)[0]
    along, across = P @ U[:, 0], P @ U[:, 1]

    fig, axes = plt.subplots(args.sections, 1,
                             figsize=(13.5, 3.1 * args.sections), sharex=False)
    axes = np.atleast_1d(axes)
    cuts = np.percentile(along, np.linspace(25, 75, args.sections))
    slab = 0.15 * R

    for k, (ax, s) in enumerate(zip(axes, cuts)):
        m = np.abs(along - s) < slab
        if m.sum() < 40:
            ax.text(0.5, 0.5, "too few points in this slice",
                    ha="center", transform=ax.transAxes)
            continue
        o = np.argsort(across[m])
        x = across[m][o] / size * 100
        yf, yw = h_fresh[m][o], h_worn[m][o]
        de = d_edge[m][o] / R

        ax.fill_between(x, yw, yf, where=yf > yw, color="#c1440e", alpha=0.45,
                        interpolate=True, label="material removed")
        ax.plot(x, yf, color="#333333", lw=1.0, label="fresh")
        ax.plot(x, yw, color="#1f77b4", lw=1.0, label="after blunting")
        inedge = de < 1.0
        if inedge.any():
            ax.fill_between(x, ax.get_ylim()[0], ax.get_ylim()[1],
                            where=inedge, color="#4a7c59", alpha=0.13,
                            label="within one cutoff of the face edge")
        ax.axhline(0, color="0.75", lw=0.7, ls="--")
        ax.set_ylabel("height above\nlocal envelope\n(% of object)", fontsize=8)
        ax.set_title(f"section {k + 1} of {args.sections}, across the break face"
                     f"  —  removed here: {(yf - yw).mean():.5f}% of object",
                     fontsize=9.5)
        if k == 0:
            ax.legend(fontsize=8, ncol=4, loc="upper right")
    axes[-1].set_xlabel("position across the break face (% of object size)")
    fig.suptitle(
        f"{args.object}: the break face in section, before and after blunting\n"
        f"peaks cut, hollows untouched — and in the shaded green bands at the "
        f"face edges, almost nothing removed", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    outp = Path(args.out_dir)
    outp.mkdir(parents=True, exist_ok=True)
    png = outp / f"{args.object}_section.png"
    fig.savefig(png, dpi=150)
    print(f"wrote {png}")

    # ---- the mesh, laid out in a row --------------------------------------
    ext = float(v0.max(0)[0] - v0.min(0)[0]) * 1.25
    disp = v1 - v0

    grey = np.tile(np.array([175, 175, 175, 255], np.uint8), (len(v0), 1))
    removed = np.zeros(len(v0))
    removed[idx] = np.maximum(h_fresh - h_worn, 0.0)
    avail = np.zeros(len(v0))
    avail[idx] = np.maximum(h_fresh, 0.0)
    eff = np.zeros(len(v0))
    ok = avail[idx] > 1e-9
    eff[idx[ok]] = np.clip(removed[idx[ok]] / avail[idx[ok]], 0, 1)
    zone = np.zeros(len(v0))
    zone[idx] = (d_edge < R).astype(float)

    vmax_rem = float(np.percentile(removed[idx], 99)) or 1.0
    scene = trimesh.Scene()
    order = [
        ("1_FRESH_original", v0, grey),
        ("2_WORN_true_scale", v1, grey),
        (f"3_WORN_exaggerated_x{int(EXAGGERATION)}", v0 + disp * EXAGGERATION, grey),
        ("4_material_removed", v0, heat(removed, "inferno", 0.0, vmax_rem)),
        ("5_efficiency_dark_is_failing", v0, heat(eff, "viridis", 0.0, 1.0)),
        ("6_edge_zone_green", v0, heat(zone, "summer", 0.0, 1.0)),
    ]
    for n, (name, verts, cols) in enumerate(order):
        vv = verts.copy()
        vv[:, 0] += n * ext
        scene.add_geometry(paint(vv, f0, cols), node_name=name)

    glb = outp / f"{args.object}_before_after.glb"
    scene.export(glb)
    print(f"wrote {glb}")
    print(f"  Six copies IN A ROW along X, {ext:.4f} apart, named in view order.")
    print(f"  1 and 2 are the honest before and after: they look identical,")
    print(f"  because the wear is {removed[idx].mean():.5f}% of the object. That")
    print(f"  is the point -- 3 shows the same displacement magnified "
          f"{int(EXAGGERATION)}x so it can be seen.")
    print("  4-6: what was taken, how much of what was available was taken")
    print("  (dark = failing), and where the face edge is.")


if __name__ == "__main__":
    main()
