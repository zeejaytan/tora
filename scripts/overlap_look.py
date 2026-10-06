"""Draw where sherds pass through each other in chosen attempts (U17 Revision 4 render rule).

Reads attempt bundles and a u17_overlap.py report. For one pot, draws the Revision 3 top
attempt, the Revision 4 top attempt and the best-ranked genuine attempt under Revision 4,
each from the side and down the long axis, every sherd grey, the samples counted as inside
another sherd in red, or orange where they lie in the sherd's own join strip (left out of
Revision 5's area). Title carries each attempt's worst inside share and its class.

With --failed N, draws instead the N genuine attempts the gate rejected with the most
overlap (the pre-registration's rule: every rejected genuine is drawn before reporting).

Usage: python scripts/overlap_look.py --bundles DIR --report overlap_report.json
           --pot "tora/plate" --out look.png [--failed 3]
"""
import argparse
import json
import sys
from pathlib import Path

import matplotlib
import numpy as np
from scipy.spatial import cKDTree

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
import overlap_measure as O  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--bundles", required=True, type=Path)
ap.add_argument("--report", required=True, type=Path)
ap.add_argument("--pot", required=True, help="set/pot as the report keys it")
ap.add_argument("--out", required=True, type=Path)
ap.add_argument("--failed", type=int, default=0,
                help="draw the N rejected genuine attempts with the most overlap instead")
a = ap.parse_args()

full = json.loads(a.report.read_text())
rep = full["pots"][a.pot]
gate = "5" if full.get("field") == "area" else "4"
unit = "(% of pot)^2" if gate == "5" else "%"
if a.failed:
    why = sorted(rep["genuine_failed_why"], key=lambda w: -w["inside"])[: a.failed]
    picks = [(f"genuine, rejected: {w['inside']:.0f} on sherd {w['sherd']}", w["id"])
             for w in why]
else:
    picks = [("Revision 3, rank 1", rep["rev3"]["top5_ids"][0]),
             (f"Revision {gate}, rank 1", rep["rev4"]["top5_ids"][0]),
             (f"best genuine, Revision {gate} rank {rep['rev4']['best_genuine']}",
              rep["rev4"]["best_genuine_id"])]
if not picks:
    sys.exit(f"{a.pot}: nothing to draw")
pot, sh = O.load(a.bundles)
fig, ax = plt.subplots(2, len(picks), figsize=(6 * len(picks), 9), squeeze=False)
for c, (title, aid) in enumerate(picks):
    if aid is None:
        continue
    b = np.load(a.bundles / "bundles" / f"{aid}.npz")
    R, T = b["R"].astype(float), b["t"].astype(float) * 100.0 / pot
    placed = [(s["p"] @ r.T + t, s["n"] @ r.T) for s, r, t in zip(sh, R, T)]
    trees = [cKDTree(P) for P, _ in placed]
    allp = np.concatenate([P for P, _ in placed])
    cen = allp.mean(0)
    _, _, vt = np.linalg.svd(allp - cen, full_matrices=False)
    worst, worst_area = 0.0, 0.0
    for j, (X, M) in enumerate(placed):
        dep = np.zeros(len(X))
        for k, (P, N) in enumerate(placed):
            if k != j:
                dep = np.maximum(dep, O.inside(X, M, P, N, sh[k]["thick"], trees[k]))
        worst = max(worst, 100 * float((dep > 0).mean()))
        away = (dep > 0) & ~sh[j]["strip"]
        worst_area = max(worst_area, float(away.sum() * sh[j]["da"]))
        q = (X - cen) @ vt.T
        for r, (u, v) in enumerate([(0, 2), (0, 1)]):
            ax[r, c].scatter(q[dep == 0, u], q[dep == 0, v], s=0.3, c="0.6")
            ax[r, c].scatter(q[(dep > 0) & ~away, u], q[(dep > 0) & ~away, v], s=2, c="orange")
            ax[r, c].scatter(q[away, u], q[away, v], s=2, c="red")
            ax[r, c].text(*q[:, [u, v]].mean(0), str(j), fontsize=9)
    ax[0, c].set_title(f"{title}\n{worst:.1f}% of a sherd inside; away from joins "
                       f"{worst_area:.0f} (% of pot)^2 (red)")
    for r in range(2):
        ax[r, c].set_aspect("equal")
ax[0, 0].set_ylabel("side view (% of pot)")
ax[1, 0].set_ylabel("down the long axis (% of pot)")
fig.suptitle(f"{a.pot}: where sherds pass through each other; Revision {gate} cut-off "
             f"{full['overlap_cut']} {unit}")
fig.tight_layout()
a.out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(a.out, dpi=100)
print(f"-> {a.out}")
