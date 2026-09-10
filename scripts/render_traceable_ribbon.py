"""Draw the path the profile length is measured along, on the Juglet.

`measure_strip_feasibility.traceable_length` reports how far you can walk along
a break ribbon. The number is the same whether the walk follows the break or
short-cuts across the wall from one edge of the ribbon to the other, so the
number cannot be trusted until the walk is looked at. This draws it.

Each selected break-face point is coloured by its walking distance from one end
of the longest path. If the walk follows the ribbon, the colour sweeps smoothly
from one end of the break to the other. If it cuts across the wall or hops
between the two mating faces, the colour breaks into patches.

The two endpoints of the longest path are marked, and the path itself is drawn
as a line so it can be compared against the shape of the break.
"""

import argparse

import h5py
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt                                # noqa: E402
from scipy.sparse import coo_matrix                            # noqa: E402
from scipy.sparse.csgraph import connected_components, dijkstra  # noqa: E402
from scipy.spatial import cKDTree                              # noqa: E402

from measure_strip_feasibility import (EDGE_SPACINGS, GRAPH_MAX_PTS,  # noqa
                                       median_spacing, voxel_thin)
from wear_fracture_spectrum import load_sherds, mating_faces   # noqa: E402


def walk(pts, spacing):
    """Same graph as traceable_length, but returns the path, not just its length."""
    voxel = max(spacing * 1.5, 1e-12)
    thin = pts
    while len(thin) > GRAPH_MAX_PTS:
        thin = voxel_thin(pts, voxel)
        if len(thin) > GRAPH_MAX_PTS:
            voxel *= 1.3
    d2, _ = cKDTree(thin).query(thin, k=2, workers=-1)
    sp = float(np.median(d2[:, 1]))
    pairs = cKDTree(thin).query_pairs(EDGE_SPACINGS * sp, output_type="ndarray")
    w = np.linalg.norm(thin[pairs[:, 0]] - thin[pairs[:, 1]], axis=1)
    n = len(thin)
    g = coo_matrix((np.concatenate([w, w]),
                    (np.concatenate([pairs[:, 0], pairs[:, 1]]),
                     np.concatenate([pairs[:, 1], pairs[:, 0]]))),
                   shape=(n, n)).tocsr()
    _nc, lab = connected_components(g, directed=False)
    keep = np.flatnonzero(lab == int(np.argmax(np.bincount(lab))))
    sub = g[keep][:, keep]
    d0 = dijkstra(sub, indices=0)
    a = int(np.argmax(np.where(np.isfinite(d0), d0, -1.0)))
    d1, pred = dijkstra(sub, indices=a, return_predecessors=True)
    b = int(np.argmax(np.where(np.isfinite(d1), d1, -1.0)))
    path = []
    j = b
    while j >= 0:
        path.append(j)
        j = pred[j]
    return thin[keep], d1, np.array(path[::-1]), float(d1[b])


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--juglet", required=True)
    p.add_argument("--group", default="juglet_gt")
    p.add_argument("--juglet-mm", type=float, default=65.0)
    p.add_argument("--out", required=True)
    a = p.parse_args()

    rng = np.random.default_rng(0)
    with h5py.File(a.juglet, "r") as h:
        lo = np.full(3, np.inf)
        hi = np.full(3, -np.inf)
        for t in h[a.group]:
            if "pieces" not in h[a.group][t]:
                continue
            for k in h[a.group][t]["pieces"]:
                v = np.asarray(h[a.group][t]["pieces"][k]["vertices"][:],
                               dtype=np.float64)
                lo, hi = np.minimum(lo, v.min(0)), np.maximum(hi, v.max(0))
        jf = a.juglet_mm / float((hi - lo).max())
        tag = sorted(t for t in h[a.group] if "pieces" in h[a.group][t])[0]
        sherds = load_sherds(h, a.group, tag, 200000, rng)
        allv = np.concatenate([v for v, _ in sherds], axis=0)
        diag = float(np.linalg.norm(allv.max(0) - allv.min(0)))
        faces, _near, _kept = mating_faces(sherds, diag)

    runs = []
    for i, (v, _n) in enumerate(faces):
        pts, d, path, L = walk(v, median_spacing(v, rng))
        runs.append((L * jf, i, pts * jf, d * jf, path))
    runs.sort()
    pick = [runs[len(runs) // 2], runs[-1]]   # the median face and the longest

    fig = plt.figure(figsize=(14.5, 7.6))
    for col, (L, idx, pts, d, path) in enumerate(pick):
        for row, (elev, azim) in enumerate([(24, -60), (78, -60)]):
            ax = fig.add_subplot(2, 2, row * 2 + col + 1, projection="3d")
            fin = np.isfinite(d)
            s = ax.scatter(pts[fin, 0], pts[fin, 1], pts[fin, 2], c=d[fin],
                           s=2.2, cmap="viridis")
            pp = pts[path]
            ax.plot(pp[:, 0], pp[:, 1], pp[:, 2], color="#c0392b", lw=1.6)
            ax.scatter(*pp[0], color="#c0392b", s=60, marker="o")
            ax.scatter(*pp[-1], color="#c0392b", s=60, marker="s")
            ax.view_init(elev=elev, azim=azim)
            ax.set_box_aspect((np.ptp(pts[:, 0]), np.ptp(pts[:, 1]),
                               np.ptp(pts[:, 2])))
            ax.set_title(("break face " + str(idx) + ", traceable " +
                          format(L, ".1f") + " mm" +
                          ("   (median face)" if col == 0 else
                           "   (longest face)")) if row == 0 else
                         "same, looking down on it",
                         fontsize=10.5)
            ax.tick_params(labelsize=6)
            if row == 0 and col == 1:
                cb = fig.colorbar(s, ax=ax, shrink=0.62, pad=0.09)
                cb.set_label("walking distance along the break, mm",
                             fontsize=8.5)
                cb.ax.tick_params(labelsize=7)

    fig.suptitle("Juglet break faces: the path the profile length is measured "
                 "along.\nColour = distance walked from the red circle. "
                 "A smooth sweep means the walk followed the break; patches "
                 "would mean it cut across the wall.", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    fig.savefig(a.out, dpi=150, facecolor="white")
    print("wrote " + a.out)
    for L, idx, _p, _d, _pa in runs:
        print("  face " + str(idx) + "  traceable " + format(L, "6.2f") + " mm")


if __name__ == "__main__":
    main()
