"""Debug look at Layer 1 on one calibration pot (key side): why correct attempts fail.

Prints, over the pot's genuine attempts, how often each sherd is flagged inside out.
Draws the genuine attempt with the median profile deviation: (1) height along the fitted
axis against distance from it, per sherd (the wall profile Layer 1 compares sherds to),
with the smoothed profile; (2) a side view with the fitted axis; flagged sherds in red
outline.

Usage: python scripts/l1_look.py --root CALIB_DIR --bundles DIR --labels labels.json \\
    --pot plate --pot-mm 100 --bin-pct 10.77 --out look.png
"""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path

import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rank_attempts as RA  # noqa: E402
from check_inside_out import curvature  # noqa: E402

ap = argparse.ArgumentParser()
for k in ("root", "bundles", "labels", "out"):
    ap.add_argument(f"--{k}", required=True, type=Path)
ap.add_argument("--pot", required=True)
ap.add_argument("--pot-mm", type=float, required=True)
ap.add_argument("--bin-pct", type=float, required=True)
a = ap.parse_args()
RA.BIN_MM = a.bin_pct * a.pot_mm / 100

rk = {r["id"]: r for r in json.loads((a.root / a.pot / "ranks.json").read_text())["attempts"]}
idmap = json.loads((a.root / a.pot / "key" / "idmap.json").read_text())
lab = {(r["pot"], r["run"], r["attempt"]): r for r in json.loads(a.labels.read_text())}
gen = [aid for aid, m in idmap.items()
       if (l := lab[(f"fractura_fresh/{a.pot}", Path(m["run"]).parts[-4], m["attempt"])])
       ["oriented"] == l["n"]]
flags = Counter(j for aid in gen for j in rk[aid]["inside_out"])
print(f"{a.pot}: {len(gen)} genuine attempts; flagged inside out, per sherd: {dict(flags)}")
dev = [rk[aid]["sherd_dev_mm"] for aid in gen]
print("per-sherd profile deviation, median over genuine (% of pot):",
      [round(100 * float(np.median([d[j] for d in dev])) / a.pot_mm, 2) for j in range(len(dev[0]))])

aid = sorted(gen, key=lambda i: rk[i]["profile_mm"])[len(gen) // 2]
RA._init(str(a.bundles))
b = np.load(a.bundles / "bundles" / f"{aid}.npz")
placed = [(v @ R.T + t, n @ R.T) for (v, n), R, t in
          zip(RA._SH, b["R"].astype(float), b["t"].astype(float))]
P = np.concatenate([p for p, _ in placed])
N = np.concatenate([n for _, n in placed])
step = max(1, len(P) // RA.AXIS_PTS)
d, c, rms = RA.fit_axis(P[::step], N[::step])
res = RA.layer1(placed)
print(f"drawn attempt: profile {100 * res['profile_mm'] / a.pot_mm:.2f}% of pot, "
      f"inside out {res['inside_out']}, axis rms {res['axis_rms_mm']:.2f} mm")
centre = P.mean(0)
fig, ax = plt.subplots(1, 3, figsize=(16, 5.5))
e1 = np.cross(d, [1, 0, 0] if abs(d[0]) < 0.9 else [0, 1, 0]); e1 /= np.linalg.norm(e1)
e2 = np.cross(d, e1)
for j, (p, _) in enumerate(placed):
    s = p[:: max(1, len(p) // 3000)]
    h = (s - c) @ d
    r = np.linalg.norm((s - c) - np.outer(h, d), axis=1)
    col = f"C{j}"
    ax[0].scatter(r, h, s=1, c=col, label=f"sherd {j}" + (" (flagged)" if j in res["inside_out"] else ""))
    ax[1].scatter((s - c) @ e1, h, s=1, c=col)
    ax[2].scatter((s - c) @ e1, (s - c) @ e2, s=1, c=col)
    cd, ok = curvature(p[:: max(1, len(p) // 3000)])
    m = p.mean(0)
    for k, (x, y) in enumerate((((m - c) @ e1, (m - c) @ d), ((m - c) @ e1, (m - c) @ e2))):
        dd = (cd @ e1, cd @ d) if k == 0 else (cd @ e1, cd @ e2)
        ax[k + 1].arrow(x, y, 15 * dd[0], 15 * dd[1], color="k" if ok else "grey", width=0.4)
        ax[k + 1].text(x, y, str(j) + ("!" if j in res["inside_out"] else ""), fontsize=11)
for k in (1, 2):
    cc = ((centre - c) @ e1, (centre - c) @ (d if k == 1 else e2))
    ax[k].plot(*cc, "k*", ms=14)
ax[1].axvline(0, color="k", lw=0.8)
ax[0].set_xlabel("distance from fitted axis (mm)"); ax[0].set_ylabel("height along axis (mm)")
ax[0].legend(markerscale=8, fontsize=8)
ax[1].set_title("side view, axis vertical; arrow = towards curvature centre; * = attempt centre")
ax[2].set_title("down the axis")
for x in ax:
    x.set_aspect("equal")
fig.suptitle(f"{a.pot}: genuine attempt with median Layer 1 deviation "
             f"({100 * res['profile_mm'] / a.pot_mm:.1f}% of pot); ! = flagged inside out")
plt.tight_layout()
plt.savefig(a.out, dpi=70)
print(f"-> {a.out}")
