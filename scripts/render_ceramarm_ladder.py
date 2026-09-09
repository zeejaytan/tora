"""One real pot drawn across the five wear rungs, with the measured quantity below it.

Job 30337242. The upper row is the MEDIAN draw of twenty at each rung, so the
picture and the figure under it describe the same attempt. The lower row is the
measured quantity itself, per sherd, unbinned: how far each sherd sits from the
scanned truth, as a percentage of pot size. A whole-pot outline can look
plausible while individual sherds are exchanged, which is why the per-sherd row
is the instrument and the render is the check on it.

The anchor sherd is drawn grey: it is held at truth and is never evidence.

Usage:
    python scripts/render_ceramarm_ladder.py --pot blue_pot --arm baseline
"""
import sys, argparse
from pathlib import Path
import numpy as np
sys.path.insert(0, "scripts")
from readout import chamfer, unit_box_scale, TAU
from check_identity_swap import pct

ap = argparse.ArgumentParser(description=__doc__,
                             formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument("--runs", type=Path, default=Path("artifacts/ceramarm_30337242"))
ap.add_argument("--pot", default="blue_pot")
ap.add_argument("--arm", default="baseline")
ap.add_argument("--out", type=Path, default=None)
args = ap.parse_args()

RUNGS = ["e000", "e025", "e050", "e075", "e100"]
CAP = 1200
SEATED = pct(TAU)

index = {}
for npz in sorted((args.runs / args.arm / "clouds").glob("*.npz")):
    index[str(np.load(npz, allow_pickle=True)["name"]).split("/")[-1]] = npz

cols = []
for rung in RUNGS:
    tag = f"{args.pot}_{rung}"
    if tag not in index:
        continue
    z = np.load(index[tag], allow_pickle=True)
    gt, ids, pred = z["pts_gt"], z["part_ids"], z["generations_pred"]
    unit = unit_box_scale(gt)
    parts = sorted(set(ids.tolist()))
    anchor = max(parts, key=lambda p: int((ids == p).sum()))
    G = [gt[ids == p][:CAP] / unit for p in parts]
    per = []
    for d in range(pred.shape[0]):
        Q = [pred[d][ids == p][:CAP] / unit for p in parts]
        per.append([pct(chamfer(G[i], Q[i])) for i in range(len(parts))])
    per = np.array(per)
    free = [i for i, p in enumerate(parts) if p != anchor]
    worst = per[:, free].max(axis=1)
    med = int(np.argsort(worst)[len(worst) // 2])
    cols.append(dict(rung=rung, ids=ids, pred=pred, unit=unit, parts=parts,
                     anchor=anchor, per=per, med=med,
                     seated=float(np.median([(p < SEATED).sum() for p in per]))))
    print(f"{tag:22s} median draw {med:2d}   own-place seated "
          f"{cols[-1]['seated']:.1f} of {len(parts)}   worst free sherd "
          f"{worst[med]:5.1f}% of pot")

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
n = len(cols)
fig = plt.figure(figsize=(2.7 * n, 7.6)); cmap = plt.get_cmap("tab10")
for c, D in enumerate(cols):
    ax = fig.add_subplot(2, n, c + 1)
    P = D["pred"][D["med"]] / D["unit"]
    for i, p in enumerate(D["parts"]):
        m = D["ids"] == p
        col = "0.65" if p == D["anchor"] else cmap(i % 10)
        ax.scatter(P[m][:, 0], P[m][:, 1], s=1.0, color=col, linewidths=0)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(f"{D['rung']} — draw {D['med']}", fontsize=10)
    if c == 0:
        ax.set_ylabel("prediction, front view\ngrey = anchor, held at truth", fontsize=8)
    ax = fig.add_subplot(2, n, c + n + 1)
    x = np.arange(len(D["parts"]))
    for d in range(D["per"].shape[0]):
        ax.plot(x, D["per"][d], marker="o", ms=2, lw=0.6, alpha=0.3, color="0.5", zorder=1)
    ax.plot(x, D["per"][D["med"]], marker="o", ms=5, lw=1.7, color="C3", zorder=3,
            label=f"median draw")
    ax.axhline(SEATED, color="C2", ls="--", lw=1.2, label=f"seated = {SEATED:.1f}%")
    ax.set_xticks(x); ax.set_xticklabels([f"p{p}" for p in D["parts"]], fontsize=7)
    ax.set_ylim(0, 60); ax.grid(alpha=0.25, lw=0.5)
    ax.set_xlabel(f"{D['seated']:.1f} of {len(D['parts'])} seated", fontsize=8)
    if c == 0:
        ax.set_ylabel("distance from the scan truth\n(% of pot size, own place)", fontsize=8)
        ax.legend(fontsize=7, loc="upper left")
fig.suptitle(f"{args.pot} on the {args.arm} arm, job 30337242 — "
             f"simulated abrasion increasing left to right\n"
             f"grey lines are the other nineteen draws", fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.92])
out = args.out or args.runs / f"ladder_{args.pot}_{args.arm}.png"
fig.savefig(out, dpi=130); print("wrote", out)
