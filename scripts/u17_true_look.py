"""Look at a Fractura pot's correct reassembly, sherd by sherd (U17, before the test).

Label-free: draws only the scanned sherds in their true places (pts_gt from one run's
clouds/*.npz), never an attempt or a score. Used to check the held-out pots for handles
or other parts off the round outline before the test pre-registration is committed.
Two views across the pot's long axis (PCA) and one down it.

Usage: python scripts/u17_true_look.py --run RUN_DIR --pot narrow_bottle3 --out look.png
"""
import argparse
import sys
from pathlib import Path

import matplotlib
import numpy as np
from scipy.spatial import cKDTree

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--run", required=True, type=Path)
ap.add_argument("--pot", required=True)
ap.add_argument("--out", required=True, type=Path)
a = ap.parse_args()

# GARF runs keep clouds under <run>/version_0/clouds, TORA's under <run>/clouds
for f in sorted(f for sub in ("version_0/clouds", "clouds") for f in (a.run / sub).glob("*.npz")):
    d = np.load(f, allow_pickle=True)
    if str(d["name"]).endswith(a.pot):
        break
else:
    sys.exit(f"no cloud for {a.pot} under {a.run}")
pts, ppp = d["pts_gt"].astype(float), np.asarray(d["points_per_part"]).astype(int)
ppp = ppp[ppp > 0]
pts = pts.reshape(-1, 3)[: ppp.sum()]
c = pts - pts.mean(0)
_, sv, vt = np.linalg.svd(c, full_matrices=False)
# the pot's axis: the PCA direction whose spread differs most from the other two
odd = 0 if sv[0] - sv[1] >= sv[1] - sv[2] else 2
frame = np.stack([vt[(odd + 1) % 3], vt[(odd + 2) % 3], vt[odd]])
q = c @ frame.T
cut = np.cumsum(ppp)[:-1]
fig, ax = plt.subplots(1, 3, figsize=(15, 5))
for i, s in enumerate(np.split(q, cut)):
    for k, (u, v, t) in enumerate([(0, 2, "side A"), (1, 2, "side B"), (0, 1, "down the axis")]):
        ax[k].scatter(s[:, u], s[:, v], s=1, label=f"sherd {i}" if k == 0 else None)
        ax[k].set_title(t)
        ax[k].set_aspect("equal")
ax[0].legend(markerscale=8, fontsize=8)
fig.suptitle(f"{a.pot}: correct reassembly ({len(ppp)} sherds), dataset units; no attempt drawn")
fig.tight_layout()
a.out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(a.out, dpi=110)
print(f"{a.pot}: {len(ppp)} sherds, points per sherd {ppp.tolist()} -> {a.out}")
# how far each sherd's centre sits from the others' (dataset units): a sherd far from
# every other one in the CORRECT reassembly has no neighbour to be judged against
cen = [s.mean(0) for s in np.split(c, cut)]
lo, hi = c.min(0), c.max(0)
print(f"box sides {np.round(hi - lo, 3).tolist()} (longest = 1 pot size)")
for i, s in enumerate(np.split(c, cut)):
    near = min(cKDTree(o).query(s)[0].min()
               for j, o in enumerate(np.split(c, cut)) if j != i)
    print(f"sherd {i}: centre {np.round(cen[i], 3).tolist()}, nearest other sherd {near:.4f}")
