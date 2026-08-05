"""Render the ACTUAL wear measurement, per vertex. No proxies.

Four attempts to picture this wear failed the same way — each view's range was set
by a scale coarser than the effect:

  1. slab sliced ALONG the fracture face   -> showed the face head-on; material
                                              appeared to vanish when it had only
                                              moved out of the slice
  2. slab sliced across, whole fragment    -> a 0.002 displacement is sub-pixel
  3. raw break-face height map             -> dominated by the face's overall
                                              undulation (+/-0.045); texture
                                              change of 0.002 invisible
  4. high-passed height map, 260x260 grid  -> each pixel averages tens of mesh
                                              vertices, so vertex-scale texture
                                              is averaged away again

Meanwhile `relief_p90` moved 0.223 -> 0.164 on the same fragment throughout. The
measurement was never in doubt; every picture was simply too coarse.

So this renders the measured quantity DIRECTLY: per-vertex local normal variation
— exactly what `relief_p90` summarises — as colour on the break face, plus its
distribution. If wear smooths the surface, the field goes cool and the histogram
shifts left. Nothing is binned, averaged or projected first.

Usage:
  python scripts/visualise_wear_relief.py --object limb3 --out relief.png
"""

import argparse
import sys
from pathlib import Path

import h5py
import numpy as np
import trimesh
from scipy.spatial import cKDTree

sys.path.insert(0, str(Path(__file__).resolve().parent))
from wear_ops import _band_mask, apply_wear, wear_conditions  # noqa: E402

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def per_vertex_relief(v, f, mask, radius_frac=0.01, max_pts=40000, seed=0):
    """Local normal variation at each band vertex — what relief_p90 measures.

    1 - mean(cos angle) between a vertex's normal and its neighbours' within a
    fixed physical radius. High = sharp fracture texture, low = abraded.
    """
    idx = np.where(mask)[0]
    if len(idx) < 50:
        return None, None
    rng = np.random.default_rng(seed)
    if len(idx) > max_pts:
        idx = rng.choice(idx, max_pts, replace=False)

    m = trimesh.Trimesh(vertices=v, faces=f, process=False)
    try:
        vn = np.asarray(m.vertex_normals, dtype=np.float64)
    except Exception:
        return None, None

    scale = float(np.linalg.norm(v.max(0) - v.min(0))) + 1e-9
    r = radius_frac * scale
    pts = v[idx]
    tree = cKDTree(pts)
    nb = tree.query_ball_point(pts, r, workers=-1)

    out = np.zeros(len(idx))
    for i, ne in enumerate(nb):
        if len(ne) < 3:
            continue
        cos = vn[idx[ne]] @ vn[idx[i]]
        out[i] = 1.0 - float(np.clip(cos, -1, 1).mean())
    return pts, out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--src", default="/data/gpfs/projects/punim2657/TORA/dataset/real_heldout_norm.hdf5")
    ap.add_argument("--dataset", default="real_heldout_norm")
    ap.add_argument("--object", default="limb3")
    ap.add_argument("--fragment", type=int, default=-1)
    ap.add_argument("--out", default="relief.png")
    args = ap.parse_args()

    with h5py.File(args.src, "r") as h:
        grp = h[args.dataset][args.object]
        g = grp["pieces"] if "pieces" in grp else grp
        keys = sorted(g.keys(), key=lambda s: int(s) if s.isdigit() else s)
        pieces = [(np.asarray(g[k]["vertices"][:], dtype=np.float64),
                   np.asarray(g[k]["faces"][:], dtype=np.int64)) for k in keys]

    idx = args.fragment
    if idx < 0:
        best, idx = -1, 0
        for i in range(len(pieces)):
            _, fe = _band_mask(pieces, i, pieces[i][0])
            n = int((fe > 0.5).sum())
            if n > best:
                best, idx = n, i
    print(f"{args.object}: fragment {idx}", flush=True)

    conds = [("original", None)] + [(n, kw) for n, kw in wear_conditions()
                                    if n != "fresh"]

    results, frame = [], None
    for name, kw in conds:
        ps = pieces if kw is None else apply_wear(pieces, **kw)
        v, f = ps[idx]
        _, feather = _band_mask(ps, idx, v)
        pts, rel = per_vertex_relief(v, f, feather > 0.5)
        if pts is None:
            print(f"  {name}: band too small")
            continue
        if frame is None:
            c = pts.mean(0)
            _, _, vt = np.linalg.svd(pts - c, full_matrices=False)
            frame = (c, vt[0], vt[1])
        results.append((name, pts, rel))
        print(f"  {name:<15s} mean local relief {rel.mean():.4f}   "
              f"p90 {np.percentile(rel, 90):.4f}", flush=True)

    if not results:
        return

    c, e1, e2 = frame
    allrel = np.concatenate([r for _, _, r in results])
    vmax = float(np.percentile(allrel, 96))

    n = len(results)
    fig = plt.figure(figsize=(3.5 * n, 7.4))
    for k, (name, pts, rel) in enumerate(results):
        ax = fig.add_subplot(2, n, k + 1)
        d = pts - c
        sc = ax.scatter(d @ e1, d @ e2, c=rel, s=1.1, cmap="inferno",
                        vmin=0, vmax=vmax, linewidths=0)
        ax.set_title(f"{name}\nmean {rel.mean():.4f}", fontsize=9)
        ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
        if k == 0:
            ax.set_ylabel("break face")

        ax2 = fig.add_subplot(2, n, n + k + 1)
        ax2.hist(rel, bins=np.linspace(0, vmax * 1.2, 50), color="tab:blue",
                 alpha=0.8)
        ax2.axvline(rel.mean(), color="red", lw=1.2)
        ax2.set_xlabel("local relief")
        ax2.set_yticks([])
        if k == 0:
            ax2.set_ylabel("vertices")

    fig.colorbar(sc, ax=fig.get_axes(), fraction=0.015,
                 label="local normal variation (bright = sharp, dark = abraded)")
    fig.suptitle(f"{args.object} fragment {idx}: fracture texture under each wear "
                 f"condition\nper-vertex, unbinned — the quantity relief_p90 "
                 f"actually measures")
    fig.savefig(args.out, dpi=135, bbox_inches="tight")
    print(f"  wrote {args.out}", flush=True)


if __name__ == "__main__":
    main()
