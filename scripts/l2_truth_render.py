"""Debug picture: a true assembly's break samples coloured by gap to the nearest neighbour
break sample (% of pot), plus one sherd's break mask, face-on and edge-on. Key side.

Usage: python scripts/l2_truth_render.py --hdf5 X --object grp/obj --out fig.png
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

ap = argparse.ArgumentParser()
ap.add_argument("--hdf5", required=True)
ap.add_argument("--object", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
with h5py.File(a.hdf5, "r") as f:
    g = f[a.object]["pieces"]
    scans = [(g[str(i)]["vertices"][:], g[str(i)]["faces"][:]) for i in range(len(g))]
box = unit_box_scale(np.concatenate([v for v, _ in scans]))
rng = np.random.default_rng(L.SEED)
sh = [L.prep_sherd(v * 100.0 / box, fc, 100.0, rng) for v, fc in scans]
P = np.concatenate([s["p"] for s in sh])
lab = np.concatenate([np.full(len(s["p"]), j) for j, s in enumerate(sh)])
gap = np.full(len(P), np.nan)
for j in range(len(sh)):
    d, _ = cKDTree(P[lab != j]).query(P[lab == j], distance_upper_bound=L.ZONE_PCT)
    gap[lab == j] = d
c = P.mean(0)
e = np.linalg.svd(P - c, full_matrices=False)[2]
fig, ax = plt.subplots(1, 3, figsize=(20, 7))
for k, (i1, i2) in enumerate([(0, 1), (0, 2), (1, 2)]):
    x, y = (P - c) @ e[i1], (P - c) @ e[i2]
    far = ~np.isfinite(gap)
    ax[k].scatter(x[far], y[far], s=1, c="lightgrey")
    sc = ax[k].scatter(x[~far], y[~far], s=2, c=gap[~far], cmap="viridis", vmin=0, vmax=4)
    ax[k].set_aspect("equal")
fig.colorbar(sc, ax=ax, label="gap to neighbour break, % of pot (grey: no neighbour)")
med = np.nanmedian(np.where(np.isfinite(gap), gap, np.nan))
fig.suptitle(f"{a.object} TRUE assembly: break samples, median gap {med:.2f}% of pot")
plt.savefig(a.out, dpi=60)
# break mask + all samples, sherd 0, plus a zoom at the join
v, fc = scans[0]
p, n, _ = L.resample(v * 100.0 / box, fc, L.SPACING_PCT, np.random.default_rng(L.SEED))
fig, ax = plt.subplots(1, 2, figsize=(14, 7))
cc = p.mean(0)
ee = np.linalg.svd(p - cc, full_matrices=False)[2]
for k, (i1, i2) in enumerate([(0, 1), (0, 2)]):
    ax[k].scatter((p - cc) @ ee[i1], (p - cc) @ ee[i2], s=1, c="lightgrey")
    b = sh[0]["p"]
    ax[k].scatter((b - cc) @ ee[i1], (b - cc) @ ee[i2], s=2, c="r")
    ax[k].set_aspect("equal")
fig.suptitle(f"{a.object} sherd 0: break samples red (wall {sh[0]['thick']:.2f}% of pot)")
plt.savefig(a.out.replace(".png", "_mask.png"), dpi=60)
