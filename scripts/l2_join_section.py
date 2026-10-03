"""Debug: a thin cut across one TRUE join (sherds a, b), both sherds' surfaces densely
sampled, break samples marked; plus the true assembly's gap after the same nudge the
attempts get (like-for-like floor). Key side.

Usage: python scripts/l2_join_section.py --hdf5 X --object grp/obj --out fig.png
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
scans = [(v * 100.0 / box, fc) for v, fc in scans]
rng = np.random.default_rng(L.SEED)
sh = [L.prep_sherd(v, fc, 100.0, rng) for v, fc in scans]

# like-for-like: true assembly gap before and after the nudge
print("sherd  faces  gap0  gap_after  nudge%  nudge_deg")
for j, s in enumerate(sh):
    Q = np.concatenate([x["p"] for k, x in enumerate(sh) if k != j])
    tr = cKDTree(Q)
    g0 = L.gap(s["p"], tr)[0]
    R, t, mv, ang = L.nudge(s["p"], tr, Q)
    g1 = L.gap(s["p"] @ R.T + t, tr)[0]
    print(f"{j:5d} {len(scans[j][1]):6d} {g0 or -1:5.2f} {g1 or -1:9.2f} {mv:7.2f} {ang:9.2f}")

# densest-contact pair: sherd 0 and the sherd whose break samples are nearest it
d = [np.inf] + [np.median(cKDTree(sh[k]["p"]).query(sh[0]["p"])[0]) for k in range(1, len(sh))]
b = int(np.argmin(d))
dense = [L.resample(v, fc, 0.15, np.random.default_rng(0)) for v, fc in (scans[0], scans[b])]
# join line: sherd-0 break samples within 3% of sherd b's break
dd, _ = cKDTree(sh[b]["p"]).query(sh[0]["p"])
J = sh[0]["p"][dd < 3]
c = J.mean(0)
line = np.linalg.svd(J - c, full_matrices=False)[2][0]     # along the join
fig, ax = plt.subplots(1, 3, figsize=(18, 6))
for k, off in enumerate([-0.3, 0.0, 0.3]):
    cc = c + off * (J - c).std(0).max() * 2 * line
    for (p, n, _), col in zip(dense, ["tab:blue", "tab:orange"]):
        m = np.abs((p - cc) @ line) < 0.15
        e1 = np.cross(line, [0, 0, 1.0]); e1 /= np.linalg.norm(e1); e2 = np.cross(line, e1)
        ax[k].scatter((p[m] - cc) @ e1, (p[m] - cc) @ e2, s=2, c=col)
    for s_, col in zip((sh[0], sh[b]), ["navy", "red"]):
        m = np.abs((s_["p"] - cc) @ line) < 0.6
        ax[k].scatter((s_["p"][m] - cc) @ e1, (s_["p"][m] - cc) @ e2, s=25, c=col, marker="x")
    ax[k].set_aspect("equal"); ax[k].set_xlim(-8, 8); ax[k].set_ylim(-8, 8)
    ax[k].set_title(f"cut {k}: sherd 0 (blue) / {b} (orange); x = break samples")
fig.suptitle(f"{a.object} TRUE join, axes in % of pot; wall {sh[0]['thick']:.2f}%")
plt.savefig(a.out, dpi=70)
