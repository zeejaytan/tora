"""Debug look at the Layers 1+2 top places (ticket 02): labels and a picture. Key side.

For the top N attempts by Layers 1+2 (Layer 1 pass, then worst-sherd gap), print each
one's own-place / right-way counts and per-sherd gaps, and draw the top K sherd by sherd:
green own place and right way round, amber own place but turned, red not in its place.
Two views per attempt (along and across the vessel's long axis, by PCA of the attempt).

Usage: python scripts/l2_top_look.py --bundles B --l2 juglet_l2.json --ranks ranks.json \\
    --key idmap.json --out top.png [--n 20 --k 5]
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from l2_report import gaps  # noqa: E402
from own_place import SEAT_PCT, score_draw  # noqa: E402
from label_attempts import run_name  # noqa: E402

ap = argparse.ArgumentParser()
for k in ("bundles", "l2", "ranks", "key", "out"):
    ap.add_argument(f"--{k}", required=True, type=Path)
ap.add_argument("--n", type=int, default=20)
ap.add_argument("--k", type=int, default=5)
a = ap.parse_args()
l2 = {r["id"]: r for r in json.loads(a.l2.read_text())["attempts"]}
rk = {r["id"]: r for r in json.loads(a.ranks.read_text())["attempts"]}
idmap = json.loads(a.key.read_text())
worst = {i: max(gaps(r)) for i, r in l2.items()}
order = sorted(rk, key=lambda i: (not rk[i]["layer1_pass"], worst[i], rk[i]["profile_mm"]))
z = np.load(a.bundles / "sherds.npz")
V = [z[f"v{j}"].astype(float) for j in range(int(z["k"]))]

print("rank12 rank1 own/right-way worst  per-sherd gap (% of pot; * = turned, ! = not own)")
looks = []
for n, aid in enumerate(order[: a.n], 1):
    run, t = idmap[aid]["run"], idmap[aid]["attempt"]
    d = np.load(run, allow_pickle=True)
    dr = score_draw(d["pts_gt"].astype(float), d["generations_proposed"][t].astype(float),
                    d["points_per_part"])
    own = [s == "own" for s in dr.status]
    right = [o and p < SEAT_PCT for o, p in zip(own, dr.point_pct)]
    g = gaps(l2[aid])
    cells = " ".join(f"{x:4.2f}{'' if r else ('*' if o else '!')}"
                     for x, o, r in zip(g, own, right))
    print(f"{n:6d} {rk[aid]['rank']:5d}   {sum(own)}/{sum(right)}     {worst[aid]:4.2f}  {cells}"
          f"   {run_name(run)} #{t}")
    if n <= a.k:
        looks.append((n, aid, own, right))

fig, ax = plt.subplots(2, len(looks), figsize=(4.2 * len(looks), 8.5))
for c, (n, aid, own, right) in enumerate(looks):
    b = np.load(a.bundles / "bundles" / f"{aid}.npz")
    P = [v @ R.T + t for v, R, t in zip(V, b["R"].astype(float), b["t"].astype(float))]
    allp = np.concatenate(P)
    cen = allp.mean(0)
    e = np.linalg.svd(allp - cen, full_matrices=False)[2]
    for j, p in enumerate(P):
        col = "tab:green" if right[j] else ("orange" if own[j] else "red")
        s = p[:: max(1, len(p) // 1500)] - cen
        ax[0, c].scatter(s @ e[1], s @ e[0], s=1, c=col)
        ax[1, c].scatter(s @ e[1], s @ e[2], s=1, c=col)
        m = p.mean(0) - cen
        ax[0, c].text(m @ e[1], m @ e[0], str(j), fontsize=9)
    for r in (0, 1):
        ax[r, c].set_aspect("equal")
    ax[0, c].set_title(f"L1+2 rank {n} (L1 {rk[aid]['rank']}): worst gap {worst[aid]:.2f}%\n"
                       f"own {sum(own)}/9, right way {sum(right)}/9")
fig.suptitle("Juglet, top places by Layers 1+2. green right way, orange own place turned, "
             "red not own place. Top: side view; bottom: down the long axis (mm)")
plt.tight_layout()
plt.savefig(a.out, dpi=60)
print(f"-> {a.out}")
