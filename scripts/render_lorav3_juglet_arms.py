"""The Juglet on all three arms of job 29880370 -- per sherd, unbinned, full clouds.

Whole-pot outline is not admissible on this material, so the lower row is the
measured quantity itself: how far each sherd sits from where the conservator's
hand reassembly puts it, in percent of pot size. The upper row draws the MEDIAN
draw of five, so picture and figure describe the same attempt.

Two rulers are shown deliberately.
  identity-true  sherd p against sherd p. What a conservator means by "that
                 piece is in the right place".
  Hungarian      what `compute_part_acc` reports: pieces may be RELABELLED to
                 whichever assignment passes most of them. It is the published
                 number, and it can credit a sherd standing in another's place.

Usage:
    python scripts/render_lorav3_juglet_arms.py --runs artifacts/lorav3_29880370/runs
"""
import sys, json
from pathlib import Path
import numpy as np
from scipy.optimize import linear_sum_assignment
sys.path.insert(0, "scripts")
from readout import chamfer, unit_box_scale, TAU
from check_identity_swap import pct

import argparse
_ap = argparse.ArgumentParser(description=__doc__,
                              formatter_class=argparse.RawDescriptionHelpFormatter)
_ap.add_argument("--runs", type=Path,
                 default=Path("artifacts/lorav3_29880370/runs"),
                 help="directory holding the twelve fetched lorav3_* run dirs")
RUNS = _ap.parse_args().runs
ARMS = ["baseline", "adapter_off", "adapter_on"]
SEATED = pct(TAU)                      # tau=0.01 chamfer-sum -> % of pot size
CAP = 1200                             # points per sherd; floor measured at 0.00%

data = {}
for arm in ARMS:
    z = np.load(RUNS / f"lorav3_juglet_{arm}_29880370/clouds/juglet_gt_sample00000.npz")
    gt, ids, pred = z["pts_gt"], z["part_ids"], z["generations_pred"]
    unit = unit_box_scale(gt)
    parts = sorted(set(ids.tolist()))
    sizes = {p: int((ids == p).sum()) for p in parts}
    anchor = max(parts, key=lambda p: sizes[p])
    G = [gt[ids == p][:CAP] / unit for p in parts]
    per, hung = [], []
    for d in range(pred.shape[0]):
        Q = [pred[d][ids == p][:CAP] / unit for p in parts]
        C = np.array([[chamfer(G[i], Q[j]) for j in range(len(parts))]
                      for i in range(len(parts))])
        per.append([pct(C[i, i]) for i in range(len(parts))])
        r, c = linear_sum_assignment((C >= TAU).astype(float))
        hung.append(int((C[r, c] < TAU).sum()))
    data[arm] = dict(gt=gt, ids=ids, pred=pred, unit=unit, parts=parts, anchor=anchor,
                     sizes=sizes, per=np.array(per), hung=hung)

parts, anchor = data["baseline"]["parts"], data["baseline"]["anchor"]
print(f"Juglet: {len(parts)} sherds. Anchor = p{anchor}, "
      f"{100*data['baseline']['sizes'][anchor]/5000:.0f}% of the pot, clamped at truth.")
print(f"seated = under {SEATED:.2f}% of pot size (tau=0.01 in the unit box)\n")
hdr = "arm          draw  " + "".join(f"{('p%d'%p):>7}" for p in parts) + "   own-place  relabelled"
print(hdr); print("-" * len(hdr))
for arm in ARMS:
    D = data[arm]; per = D["per"]
    for d in range(per.shape[0]):
        own = int(sum(v < SEATED for v in per[d]))
        print(f"{arm:<12}{d:>5}  " + "".join(f"{v:>7.1f}" for v in per[d])
              + f"   {own:>5} of 9  {D['hung'][d]:>6} of 9")
    worst = np.array([max(per[d][i] for i, p in enumerate(parts) if p != anchor)
                      for d in range(per.shape[0])])
    med = int(np.argsort(worst)[len(worst) // 2]); D["median_draw"] = med
    own = np.array([sum(v < SEATED for v in per[d]) for d in range(per.shape[0])])
    print(f"{arm:<12}{'mean':>5}  worst free sherd {worst.mean():5.1f}%   "
          f"own-place {own.mean():.1f}/9   relabelled {np.mean(D['hung']):.1f}/9   "
          f"(median draw {med})\n")

json.dump({a: dict(per=data[a]["per"].tolist(), hungarian=data[a]["hung"],
                   median_draw=int(data[a]["median_draw"]), anchor=int(anchor),
                   parts=[int(p) for p in parts], seated_pct=SEATED)
           for a in ARMS},
          open("artifacts/lorav3_29880370/juglet_per_sherd.json", "w"), indent=1)

import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig = plt.figure(figsize=(13.5, 8.4)); cmap = plt.get_cmap("tab10")
for c, arm in enumerate(ARMS):
    D = data[arm]; med = D["median_draw"]
    ax = fig.add_subplot(2, 3, c + 1)
    P = D["pred"][med] / D["unit"]
    for i, p in enumerate(D["parts"]):
        m = D["ids"] == p
        col = "0.6" if p == D["anchor"] else cmap(i % 10)
        ax.scatter(P[m][:, 0], P[m][:, 1], s=1.1, color=col, linewidths=0)
    ax.set_aspect("equal"); ax.set_xticks([]); ax.set_yticks([])
    ax.set_title(f"{arm} — draw {med} (median of 5)", fontsize=10)
    if c == 0:
        ax.set_ylabel("prediction, front view\ngrey = anchor, fixed at truth", fontsize=8)
    ax = fig.add_subplot(2, 3, c + 4)
    x = np.arange(len(D["parts"]))
    for d in range(D["per"].shape[0]):
        ax.plot(x, D["per"][d], marker="o", ms=3, lw=0.8, alpha=0.45, color="0.45", zorder=1)
    ax.plot(x, D["per"][med], marker="o", ms=5, lw=1.7, color="C3", zorder=3,
            label=f"median draw {med}")
    ax.axhline(SEATED, color="C2", ls="--", lw=1.2, label=f"seated = {SEATED:.1f}%")
    ax.set_xticks(x); ax.set_xticklabels([f"p{p}" for p in D["parts"]], fontsize=7)
    ax.set_ylim(0, 60); ax.set_xlabel("sherd", fontsize=8)
    if c == 0:
        ax.set_ylabel("distance from the hand reassembly\n(% of pot size, own place)", fontsize=8)
    ax.legend(fontsize=7, loc="upper left"); ax.grid(alpha=0.25, lw=0.5)
fig.suptitle("The Juglet on all three arms of job 29880370 — per sherd, all five draws\n"
             "grey lines are the other four draws. Nothing on any arm is a juglet.", fontsize=11)
fig.tight_layout(rect=[0, 0, 1, 0.93])
out = "artifacts/lorav3_29880370/juglet_arms_per_sherd.png"
fig.savefig(out, dpi=130); print("wrote", out)
