"""Draw the join gap that `compare_wear_severity.py` measures, so the number
can be checked by eye rather than trusted.

The rule this exists for (workspace AGENTS.md): render geometry before
reporting a result about it, and when a proxy view is doubtful, render the
MEASURED QUANTITY ITSELF -- per-vertex, unbinned, unprojected.

Two panels per row:
  left   a thin slab cut through the object, points coloured by fragment. If
         fragments touch, the colours interleave with no white between them.
  right  every vertex's distance to the nearest OTHER fragment, as a fraction
         of object size. This is exactly what joint_gap takes the 10th
         percentile of; the marked line is that percentile.

Usage:
  python scripts/render_join_gap.py --out artifacts/join_gap.png
"""

import argparse
from pathlib import Path

import h5py
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.spatial import cKDTree

ROOT = Path("/data/gpfs/projects/punim2657/TORA")
CASES = [
    ("dataset/bbad_vessels.hdf5", "bbad_vessels", "fresh", "TRAIN  fresh"),
    ("dataset/bbad_vessels.hdf5", "bbad_vessels", "worn_moderate", "TRAIN  worn_moderate"),
    ("dataset/erosion_sweep.hdf5", "erosion_sweep", "000", "TEST  real, unworn"),
    ("dataset/erosion_sweep.hdf5", "erosion_sweep", "100", "TEST  real, eroded 1.0"),
]


def load_parts(grp):
    pg = grp["pieces"]
    keys = sorted(pg.keys(), key=lambda s: int(s) if s.isdigit() else s)
    return [np.asarray(pg[k]["vertices"][:], dtype=np.float64) for k in keys]


def pick(dg, want):
    """First tag carrying this wear level, preferring one with >=4 fragments."""
    best = None
    for tag in sorted(dg.keys()):
        if want == "fresh" and "__fresh" not in tag:
            continue
        if want == "worn_moderate" and "worn_moderate" not in tag:
            continue
        if want in ("000", "100") and not tag.endswith("_e" + want):
            continue
        n = len(dg[tag]["pieces"].keys())
        if n >= 4:
            return tag
        best = best or tag
    return best


def nn_other(parts, max_pts=30000, seed=0):
    rng = np.random.default_rng(seed)
    subs = [v if len(v) <= max_pts else v[rng.choice(len(v), max_pts, replace=False)]
            for v in parts]
    trees = [cKDTree(s) for s in subs]
    d_all = []
    for i, s in enumerate(subs):
        best = np.full(len(s), np.inf)
        for j, t in enumerate(trees):
            if i != j:
                d, _ = t.query(s, workers=-1)
                best = np.minimum(best, d)
        d_all.append(best)
    return subs, d_all


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="artifacts/join_gap.png")
    ap.add_argument("--root", default=str(ROOT))
    args = ap.parse_args()
    root = Path(args.root)

    fig, axes = plt.subplots(len(CASES), 2, figsize=(12, 4 * len(CASES)))
    for r, (src, dset, lvl, title) in enumerate(CASES):
        h = h5py.File(root / src, "r")
        dg = h[dset]
        tag = pick(dg, lvl)
        parts = load_parts(dg[tag])
        allv = np.concatenate(parts)
        size = float(np.linalg.norm(allv.max(0) - allv.min(0)))
        subs, dists = nn_other(parts)

        # --- left: a slab through the centroid, cut across the longest axis
        c = allv.mean(0)
        ax = axes[r, 0]
        u, v, w = 0, 1, 2
        half = 0.004 * size                      # slab 0.8% of object thick
        for i, s in enumerate(subs):
            m = np.abs(s[:, w] - c[w]) < half
            if m.sum():
                ax.scatter(s[m, u], s[m, v], s=1.2, alpha=0.85,
                           color=plt.cm.tab10(i % 10), linewidths=0)
        ax.set_aspect("equal")
        ax.set_title(f"{title}\n{tag}  ({len(parts)} fragments), slab through centre",
                     fontsize=9)
        ax.set_xticks([]); ax.set_yticks([])

        # --- right: the measured quantity, per vertex
        d = np.concatenate(dists) / size * 100
        ax = axes[r, 1]
        ax.hist(d[d < 5], bins=400, color="#444")
        p10 = np.percentile(d, 10)
        ax.axvline(p10, color="crimson", lw=1.5,
                   label=f"10th pct = {p10:.3f} % of object")
        ax.axvline(0, color="royalblue", lw=1.0, ls=":",
                   label=f"exactly 0: {100 * np.mean(d <= 1e-9 / size * 100):.1f} % of vertices")
        ax.set_yscale("log")
        ax.set_xlim(-0.05, 3.0)
        ax.set_xlabel("distance from each vertex to the nearest OTHER fragment"
                      "  (% of object size)", fontsize=8)
        ax.legend(fontsize=8)
        ax.set_title("the measured quantity, per vertex, unprojected", fontsize=9)
        h.close()
        print(f"{title:26s} {tag:40s} p10={p10:.4f}%  zero={100*np.mean(d<=1e-7):.1f}%",
              flush=True)

    fig.suptitle("Join gap: what the model was trained on vs what it was tested on",
                 fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.985])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=130)
    print("wrote", out)


if __name__ == "__main__":
    main()
