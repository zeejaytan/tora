"""Debug: do the TRUE assembly's sherds touch? Whole surfaces densely sampled, no break
finder. Per neighbouring pair: distances from A's samples to B's surface samples, signed by
B's face normal (negative = inside B), over A samples within 2% of pot of B. Then the same
from A's BREAK-FINDER samples to B's break samples. Plus a cut perpendicular to the wall
at the contact. Key side.

Usage: python scripts/l2_contact.py --hdf5 X --object grp/obj --out fig.png
"""
import argparse
import sys
from pathlib import Path

import h5py
import matplotlib
import numpy as np
from scipy.spatial import cKDTree

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import l2_measure as L  # noqa: E402
from readout import unit_box_scale  # noqa: E402

DENSE = 0.2
ap = argparse.ArgumentParser()
ap.add_argument("--hdf5", required=True)
ap.add_argument("--object", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
with h5py.File(a.hdf5, "r") as f:
    g = f[a.object]["pieces"]
    scans = [(g[str(i)]["vertices"][:], g[str(i)]["faces"][:]) for i in range(len(g))]
box = unit_box_scale(np.concatenate([v for v, _ in scans]))
scans = [(v * 100.0 / box, fc) for v, fc in scans]
dn = [L.resample(v, fc, DENSE, np.random.default_rng(j)) for j, (v, fc) in enumerate(scans)]
br = [L.prep_sherd(v, fc, 100.0, np.random.default_rng(L.SEED)) for v, fc in scans]
trees = [cKDTree(p) for p, _, _ in dn]
print("pair   n_contact  |d| q10/q50/q90      signed q10/q50/q90 (neg = inside)   break->break q50")
best = None
for i in range(len(scans)):
    for j in range(len(scans)):
        if i == j:
            continue
        d, k = trees[j].query(dn[i][0], distance_upper_bound=2.0)
        m = np.isfinite(d)
        if m.sum() < 200:
            continue
        pa, (pb, nb_, _) = dn[i][0][m], dn[j]
        s = np.einsum("ij,ij->i", pa - pb[k[m]], nb_[k[m]])
        bb = cKDTree(br[j]["p"]).query(br[i]["p"], distance_upper_bound=7.7)[0]
        bb = bb[np.isfinite(bb)]
        q = lambda x: "/".join(f"{v:5.2f}" for v in np.percentile(x, [10, 50, 90]))
        print(f"{i}-{j}  {m.sum():9d}  {q(d[m])}   {q(s)}        {np.median(bb) if len(bb) else -1:.2f}")
        if i < j and (best is None or m.sum() > best[0]):
            best = (m.sum(), i, j, pa)
_, i, j, pa = best
c = pa[len(pa) // 2]
fig, ax = plt.subplots(1, 3, figsize=(18, 6))
near = dn[i][0][np.linalg.norm(dn[i][0] - c, axis=1) < 4]
w = np.linalg.svd(near - near.mean(0), full_matrices=False)[2][2]     # wall normal
J = pa[np.linalg.norm(pa - c, axis=1) < 6]
line = np.linalg.svd(J - J.mean(0), full_matrices=False)[2][0]
line -= w * (line @ w); line /= np.linalg.norm(line)
e2 = np.cross(line, w)
for kk, off in enumerate([-2.0, 0.0, 2.0]):
    cc = c + off * line
    for idx, col in ((i, "tab:blue"), (j, "tab:orange")):
        p = dn[idx][0]; m = np.abs((p - cc) @ line) < 0.1
        ax[kk].scatter((p[m] - cc) @ w, (p[m] - cc) @ e2, s=3, c=col)
    for idx, col in ((i, "navy"), (j, "red")):
        p = br[idx]["p"]; m = np.abs((p - cc) @ line) < 0.5
        ax[kk].scatter((p[m] - cc) @ w, (p[m] - cc) @ e2, s=30, c=col, marker="x")
    ax[kk].set_aspect("equal"); ax[kk].set_xlim(-6, 6); ax[kk].set_ylim(-6, 6)
    ax[kk].set_xlabel("across wall, % of pot"); ax[kk].set_title(f"cut {kk}: sherd {i} blue / {j} orange; x = break samples")
fig.suptitle(f"{a.object} TRUE join, cut perpendicular to the join line")
plt.savefig(a.out, dpi=70)
